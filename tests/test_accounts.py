"""D-037 account registry: provision, register, resolve. Socket-free."""
import pytest
from starlette.requests import Request

import app.config as config_mod
import app.main as main
from app import accounts as accounts_mod
from app import auth as auth_mod
from app import ratelimit as rl

SECRET = "test-secret-accounts-032-chars!!"
TOKEN = "test-platform-token-acct-not-secret"
RECORD = auth_mod.hash_password("demo-pass-1")


@pytest.fixture(autouse=True)
def _buckets():
    rl.reset()
    yield
    rl.reset()


@pytest.fixture()
def armed(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:investigator:%s,boss:admin:%s" % (RECORD, RECORD))
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", TOKEN)
    monkeypatch.setattr(config_mod, "ALLOW_PUBLIC_REGISTRATION", "0")
    return monkeypatch


def _req(cookie=None, headers=()):
    hdrs = [(b"host", b"t")] + list(headers)
    if cookie is not None:
        hdrs.append((b"cookie", ("csai_session=%s" % cookie).encode()))
    return Request({"type": "http", "method": "POST", "scheme": "http",
                    "server": ("t", 80), "client": ("9.9.9.9", 1234),
                    "path": "/x", "query_string": b"", "headers": hdrs})


def _login(user, password="demo-pass-1"):
    resp = main.auth_login({"username": user, "password": password},
                           _req())
    raw = resp.headers["set-cookie"]
    part = [p for p in raw.split(";") if "csai_session=" in p][0]
    return part.split("csai_session=", 1)[1]


def test_resolve_overlay_wins_and_disabled_excluded(tmp_store, armed):
    store = tmp_store
    store.upsert_registered_user(accounts_mod.build_record(
        "judge", "admin", RECORD, origin="admin"))
    store.upsert_registered_user(accounts_mod.build_record(
        "ghost", "admin", RECORD, origin="admin"))
    ghost = store.registered_user("ghost")
    ghost["disabled"] = True
    store.upsert_registered_user(ghost)
    users = accounts_mod.resolve_users(store)
    assert users["judge"][0] == "admin"
    assert "ghost" not in users
    assert users["boss"][0] == "admin"


def test_admin_provision_success_and_login(tmp_store, armed):
    cookie = _login("boss")
    body = main.admin_create_user(
        {"username": "ann", "password": "long-password-1",
         "role": "auditor", "email": "ann@example.com",
         "phone": "+15551234567"}, _req(cookie))
    assert body["user"]["username"] == "ann"
    assert "record" not in body["user"]
    assert body["audit"]["action"] == "user.provision"
    assert tmp_store.registered_user("ann")["role"] == "auditor"
    resp = main.auth_login({"username": "ann",
                            "password": "long-password-1"}, _req())
    assert resp.status_code == 200


def test_admin_provision_forbidden(tmp_store, armed):
    payload = {"username": "x", "password": "long-password-1",
               "role": "investigator"}
    with pytest.raises(main.AppError) as exc:
        main.admin_create_user(payload, _req())
    assert exc.value.code == "ADMIN_REQUIRED"
    with pytest.raises(main.AppError) as exc:
        main.admin_create_user(
            payload, _req(headers=[(b"authorization",
                                    b"Bearer " + TOKEN.encode())]))
    assert exc.value.code == "ADMIN_REQUIRED"
    with pytest.raises(main.AppError) as exc:
        main.admin_create_user(payload, _req(_login("judge")))
    assert exc.value.code == "ADMIN_REQUIRED"
    pending = auth_mod.create_session("boss", "admin", SECRET,
                                      mfa_pending=True)
    with pytest.raises(main.AppError) as exc:
        main.admin_create_user(payload, _req(pending))
    assert exc.value.code == "MFA_REQUIRED"


def test_admin_provision_validation(tmp_store, armed):
    cookie = _login("boss")
    bad = [
        ({"username": "", "password": "long-password-1",
          "role": "investigator"}, "USERNAME_INVALID"),
        ({"username": "a:b", "password": "long-password-1",
          "role": "investigator"}, "USERNAME_INVALID"),
        ({"username": "new1", "password": "short",
          "role": "investigator"}, "PASSWORD_TOO_SHORT"),
        ({"username": "new1", "password": "long-password-1",
          "role": "root"}, "ROLE_UNKNOWN"),
        ({"username": "new1", "password": "long-password-1",
          "role": "investigator",
          "email": "not-an-email"}, "EMAIL_INVALID"),
        ({"username": "new1", "password": "long-password-1",
          "role": "investigator", "phone": "abc"}, "PHONE_INVALID"),
        ({"username": "judge", "password": "long-password-1",
          "role": "investigator"}, "USERNAME_TAKEN"),
    ]
    for payload, code in bad:
        with pytest.raises(main.AppError) as exc:
            main.admin_create_user(payload, _req(cookie))
        assert exc.value.code == code, payload
    main.admin_create_user(
        {"username": "ann", "password": "long-password-1",
         "role": "auditor", "email": "ann@example.com"}, _req(cookie))
    with pytest.raises(main.AppError) as exc:
        main.admin_create_user(
            {"username": "ann2", "password": "long-password-1",
             "role": "auditor", "email": "ann@example.com"},
            _req(cookie))
    assert exc.value.code == "CONTACT_TAKEN"


def test_register_disabled_by_default(tmp_store, armed):
    with pytest.raises(main.AppError) as exc:
        main.auth_register({"username": "amy",
                            "password": "long-password-1"}, _req())
    assert (exc.value.code, exc.value.status) == (
        "REGISTRATION_DISABLED", 403)


def test_register_enabled_success(tmp_store, armed):
    armed.setattr(config_mod, "ALLOW_PUBLIC_REGISTRATION", "1")
    body = main.auth_register(
        {"username": "amy", "password": "long-password-1",
         "role": "admin", "email": "amy@example.com"}, _req())
    assert body["user"]["role"] == "investigator"
    assert body["user"]["origin"] == "self"
    assert body["trial"]["credits"] == 2
    assert body["audit"]["action"] == "user.register"
    assert tmp_store.trial_for("amy")["status"] == "active"
    resp = main.auth_login({"username": "amy",
                            "password": "long-password-1"}, _req())
    assert resp.status_code == 200


def test_register_uniqueness(tmp_store, armed):
    armed.setattr(config_mod, "ALLOW_PUBLIC_REGISTRATION", "1")
    main.auth_register({"username": "amy", "password": "long-password-1",
                        "email": "amy@example.com",
                        "phone": "+15550001111"}, _req())
    for payload, code in [
            ({"username": "amy", "password": "long-password-1"},
             "USERNAME_TAKEN"),
            ({"username": "judge", "password": "long-password-1"},
             "USERNAME_TAKEN"),
            ({"username": "bob", "password": "long-password-1",
              "email": "amy@example.com"}, "CONTACT_TAKEN"),
            ({"username": "bob", "password": "long-password-1",
              "phone": "+15550001111"}, "CONTACT_TAKEN")]:
        with pytest.raises(main.AppError) as exc:
            main.auth_register(payload, _req())
        assert exc.value.code == code, payload


def test_register_rate_limited(tmp_store, armed):
    armed.setattr(config_mod, "ALLOW_PUBLIC_REGISTRATION", "1")
    for i in range(10):
        body = main.auth_register(
            {"username": "user%02d" % i,
             "password": "long-password-1"}, _req())
        assert body["user"]["username"] == "user%02d" % i
    resp = main.auth_register({"username": "one-too-many",
                               "password": "long-password-1"}, _req())
    assert resp.status_code == 429
    assert resp.headers["retry-after"]
    import json

    assert json.loads(resp.body)["error"]["code"] == \
        "REGISTER_RATE_LIMITED"


def test_public_user_strips_record():
    rec = accounts_mod.build_record("u", "investigator", RECORD)
    assert accounts_mod.public_user(rec) == {
        "username": "u", "role": "investigator", "email": "",
        "phone": "", "email_verified": False, "phone_verified": False,
        "disabled": False, "origin": "admin", "created_at": rec[
            "created_at"]}
