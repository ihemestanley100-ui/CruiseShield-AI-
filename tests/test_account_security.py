"""D-039 account security: password, sessions, prefs. Socket-free."""
import pytest
from starlette.requests import Request

import app.config as config_mod
import app.main as main
from app import auth as auth_mod
from app import ratelimit as rl

SECRET = "test-secret-account-032-chars-ok!"
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


def _req(cookie=None, ua=None):
    hdrs = [(b"host", b"t")]
    if cookie is not None:
        hdrs.append((b"cookie", ("csai_session=%s" % cookie).encode()))
    if ua is not None:
        hdrs.append((b"user-agent", ua.encode()))
    return Request({"type": "http", "method": "POST", "scheme": "http",
                    "server": ("t", 80), "client": ("9.9.9.9", 1234),
                    "path": "/x", "query_string": b"", "headers": hdrs})


def _login(user, password="demo-pass-1", ua=None):
    resp = main.auth_login({"username": user, "password": password},
                           _req(ua=ua))
    raw = resp.headers["set-cookie"]
    part = [p for p in raw.split(";") if "csai_session=" in p][0]
    return part.split("csai_session=", 1)[1]


def test_password_change_rotates_and_kills_sessions(tmp_store, armed):
    old_cookie = _login("judge")
    body = main.auth_change_password(
        {"current_password": "demo-pass-1",
         "new_password": "brand-new-password-1"}, _req(old_cookie))
    assert body == {"ok": True, "reauthenticate": True}
    with pytest.raises(main.AppError) as exc:
        main.auth_login({"username": "judge",
                         "password": "demo-pass-1"}, _req())
    assert exc.value.code == "INVALID_CREDENTIALS"
    assert main.auth_login(
        {"username": "judge", "password": "brand-new-password-1"},
        _req()).status_code == 200
    with pytest.raises(main.AppError) as exc:
        main.auth_me(_req(old_cookie))
    assert exc.value.code == "LOGIN_REQUIRED"
    assert any(a["action"] == "auth.password.change"
               for a in tmp_store.state["audits"])
    rec = tmp_store.registered_user("judge")
    assert rec["origin"] == "password-change"


def test_password_change_rejects(tmp_store, armed):
    cookie = _login("judge")
    with pytest.raises(main.AppError) as exc:
        main.auth_change_password(
            {"current_password": "wrong",
             "new_password": "brand-new-password-1"}, _req(cookie))
    assert exc.value.code == "INVALID_CREDENTIALS"
    assert any(a["action"] == "auth.password.failed"
               for a in tmp_store.state["audits"])
    with pytest.raises(main.AppError) as exc:
        main.auth_change_password(
            {"current_password": "demo-pass-1",
             "new_password": "short"}, _req(cookie))
    assert exc.value.code == "PASSWORD_TOO_SHORT"
    with pytest.raises(main.AppError) as exc:
        main.auth_change_password(
            {"current_password": "demo-pass-1",
             "new_password": "brand-new-password-1"}, _req())
    assert exc.value.code == "LOGIN_REQUIRED"
    pending = auth_mod.create_session("judge", "investigator", SECRET,
                                      mfa_pending=True)
    with pytest.raises(main.AppError) as exc:
        main.auth_change_password(
            {"current_password": "demo-pass-1",
             "new_password": "brand-new-password-1"}, _req(pending))
    assert exc.value.code == "MFA_REQUIRED"


def test_sessions_listed_with_classes(tmp_store, armed):
    cookie_a = _login("judge", ua="Mozilla/5.0 (Windows NT 10.0)")
    cookie_b = _login("judge", ua="Mozilla/5.0 (iPhone; CPU iPhone)")
    body = main.list_sessions(_req(cookie_a))
    assert len(body["sessions"]) == 2
    classes = sorted(s["ua_class"] for s in body["sessions"])
    assert classes == ["desktop-windows", "mobile"]
    blob = str(body)
    assert "demo-pass-1" not in blob and "csai_session" not in blob
    with pytest.raises(main.AppError):
        main.list_sessions(_req())
    assert cookie_b


def test_revoke_other_session(tmp_store, armed):
    cookie_a = _login("judge")
    cookie_b = _login("judge")
    nonce_b = auth_mod.parse_session(cookie_b, SECRET)["nonce"]
    body = main.revoke_session({"nonce": nonce_b}, _req(cookie_a))
    assert body == {"ok": True, "dropped": True}
    with pytest.raises(main.AppError) as exc:
        main.auth_me(_req(cookie_b))
    assert exc.value.code == "LOGIN_REQUIRED"
    assert main.auth_me(_req(cookie_a))["user"] == "judge"
    with pytest.raises(main.AppError) as exc:
        main.revoke_session({"nonce": nonce_b}, _req(cookie_a))
    assert exc.value.code == "SESSION_UNKNOWN"
    with pytest.raises(main.AppError) as exc:
        main.revoke_session({"nonce": "nope"}, _req(cookie_a))
    assert exc.value.code == "SESSION_UNKNOWN"


def test_logout_drops_registry(tmp_store, armed):
    cookie = _login("judge")
    assert len(main.list_sessions(_req(cookie))["sessions"]) == 1
    main.auth_logout(_req(cookie))
    assert tmp_store.sessions_for("judge") == []


def test_prefs_defaults_update_and_security_locked(tmp_store, armed):
    cookie = _login("judge")
    assert main.get_notif_prefs(_req(cookie))["preferences"] == {
        "security": True, "product": True, "marketing": False}
    body = main.put_notif_prefs(
        {"marketing": True, "security": False}, _req(cookie))
    assert body["preferences"] == {
        "security": True, "product": True, "marketing": True}
    with pytest.raises(main.AppError) as exc:
        main.put_notif_prefs({"product": "yes"}, _req(cookie))
    assert exc.value.code == "PREF_INVALID"
    with pytest.raises(main.AppError):
        main.get_notif_prefs(_req())


def test_password_change_revokes_tracked_nonces(tmp_store, armed):
    """Same-second safe: kill-all revokes registry nonces, not epoch only."""
    old_cookie = _login("judge")
    nonce = auth_mod.parse_session(old_cookie, SECRET)["nonce"]
    main.auth_change_password(
        {"current_password": "demo-pass-1",
         "new_password": "brand-new-password-2"}, _req(old_cookie))
    assert tmp_store.is_revoked(nonce)
    assert tmp_store.sessions_for("judge") == []
