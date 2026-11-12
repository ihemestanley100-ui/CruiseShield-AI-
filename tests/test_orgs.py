"""D-042 org admin: profile, members, invitations. Socket-free."""
import pytest
from starlette.requests import Request

import app.config as config_mod
import app.main as main
from app import auth as auth_mod
from app import ratelimit as rl

SECRET = "test-secret-orgs-032-chars-ok!!!"
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
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "")
    monkeypatch.setattr(config_mod, "FOUNDER_USER", "")
    return monkeypatch


def _req(cookie=None):
    hdrs = [(b"host", b"t")]
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


def test_org_profile_roundtrip(tmp_store, armed):
    cookie = _login("boss")
    assert main.get_org(_req(cookie))["profile"] == {
        "name": "", "contact_email": "", "updated_at": ""}
    body = main.put_org({"name": "Acme Shield",
                         "contact_email": "ops@acme.example"},
                        _req(cookie))
    assert body["profile"]["name"] == "Acme Shield"
    assert body["profile"]["updated_at"]
    with pytest.raises(main.AppError) as exc:
        main.put_org({"name": " "}, _req(cookie))
    assert exc.value.code == "ORG_NAME_INVALID"
    with pytest.raises(main.AppError) as exc:
        main.put_org({"contact_email": "bad"}, _req(cookie))
    assert exc.value.code == "EMAIL_INVALID"
    with pytest.raises(main.AppError) as exc:
        main.get_org(_req(_login("judge")))
    assert exc.value.code == "ADMIN_REQUIRED"


def test_members_view(tmp_store, armed):
    cookie = _login("boss")
    main.admin_create_user(
        {"username": "ann", "password": "long-password-1",
         "role": "auditor", "email": "ann@example.com"}, _req(cookie))
    members = main.list_members(_req(cookie))["members"]
    assert [m["username"] for m in members] == ["ann", "boss", "judge"]
    assert all("record" not in m for m in members)
    by_name = {m["username"]: m for m in members}
    assert by_name["judge"]["origin"] == "env"
    assert by_name["ann"]["email"] == "ann@example.com"


def test_disable_enable_guards(tmp_store, armed):
    armed.setattr(config_mod, "FOUNDER_USER", "boss")
    cookie = _login("boss")
    main.admin_create_user({"username": "ann",
                            "password": "long-password-1",
                            "role": "investigator"}, _req(cookie))
    assert main.auth_login(
        {"username": "ann", "password": "long-password-1"},
        _req()).status_code == 200
    body = main.admin_disable_user({"username": "ann"}, _req(cookie))
    assert body == {"username": "ann", "disabled": True}
    with pytest.raises(main.AppError) as exc:
        main.auth_login({"username": "ann",
                         "password": "long-password-1"}, _req())
    assert exc.value.code == "INVALID_CREDENTIALS"
    body = main.admin_enable_user({"username": "ann"}, _req(cookie))
    assert body == {"username": "ann", "disabled": False}
    assert main.auth_login(
        {"username": "ann", "password": "long-password-1"},
        _req()).status_code == 200
    with pytest.raises(main.AppError) as exc:
        main.admin_disable_user({"username": "boss"}, _req(cookie))
    assert exc.value.code == "ORG_SELF_DISABLE"
    with pytest.raises(main.AppError) as exc:
        main.admin_enable_user({"username": "boss"}, _req(cookie))
    assert exc.value.code == "ORG_SELF_DISABLE"


def test_founder_protected(tmp_store, armed):
    armed.setattr(config_mod, "FOUNDER_USER", "judge")
    cookie = _login("boss")
    with pytest.raises(main.AppError) as exc:
        main.admin_disable_user({"username": "judge"}, _req(cookie))
    assert exc.value.code == "ORG_FOUNDER_PROTECTED"


def test_invite_issue_and_redeem(tmp_store, armed):
    cookie = _login("boss")
    issued = main.admin_invite({"email": "new@example.com",
                                "role": "auditor"}, _req(cookie))
    assert issued["role"] == "auditor" and issued["token"]
    assert any(a["action"] == "invitation.issue"
               for a in tmp_store.state["audits"])
    assert all(issued["token"] not in str(a)
               for a in tmp_store.state["audits"])
    body = main.redeem_invitation(
        {"token": issued["token"], "username": "newbie",
         "password": "long-password-1"}, _req())
    assert body["user"]["role"] == "auditor"
    assert body["user"]["origin"] == "invite"
    assert body["user"]["email_verified"] is False
    assert body["trial"]["credits"] == 2
    assert main.auth_login(
        {"username": "newbie", "password": "long-password-1"},
        _req()).status_code == 200


def test_invite_errors(tmp_store, armed):
    cookie = _login("boss")
    with pytest.raises(main.AppError) as exc:
        main.admin_invite({"email": "bad", "role": "auditor"},
                          _req(cookie))
    assert exc.value.code == "EMAIL_INVALID"
    with pytest.raises(main.AppError) as exc:
        main.admin_invite({"email": "a@b.co", "role": "root"},
                          _req(cookie))
    assert exc.value.code == "ROLE_UNKNOWN"
    with pytest.raises(main.AppError) as exc:
        main.admin_invite({"email": "a@b.co", "role": "auditor"},
                          _req(_login("judge")))
    assert exc.value.code == "ADMIN_REQUIRED"
    with pytest.raises(main.AppError) as exc:
        main.redeem_invitation({"token": "junk", "username": "x",
                                "password": "long-password-1"}, _req())
    assert exc.value.code == "INVITE_INVALID"
    issued = main.admin_invite({"email": "one@example.com",
                                "role": "investigator"}, _req(cookie))
    main.redeem_invitation(
        {"token": issued["token"], "username": "uno",
         "password": "long-password-1"}, _req())
    with pytest.raises(main.AppError) as exc:
        main.redeem_invitation(
            {"token": issued["token"], "username": "dos",
             "password": "long-password-1"}, _req())
    assert exc.value.code == "INVITE_SPENT"


def test_invite_expired(tmp_store, armed):
    from app import orgs as orgs_mod

    cookie = _login("boss")
    issued = orgs_mod.issue_invitation(
        tmp_store, "old@example.com", "investigator", "boss",
        SECRET, now=1000.0)
    with pytest.raises(ValueError, match="INVITE_INVALID"):
        orgs_mod.redeem_invitation(
            tmp_store, issued["token"], "late",
            "long-password-1", SECRET, now=1000.0 + 8 * 24 * 3600)
    assert tmp_store.registered_user("late") is None
    assert cookie


def test_redeem_rate_limited(tmp_store, armed):
    for _ in range(10):
        with pytest.raises(main.AppError):
            main.redeem_invitation({"token": "junk", "username": "x",
                                    "password": "long-password-1"},
                                   _req())
    resp = main.redeem_invitation({"token": "junk", "username": "x",
                                   "password": "long-password-1"},
                                  _req())
    assert resp.status_code == 429
