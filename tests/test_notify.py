"""D-043 delivery: templates, routing, emitters. Socket-free."""
import json

import pytest
from starlette.requests import Request

import app.config as config_mod
import app.main as main
from app import auth as auth_mod
from app import mfa as mfa_mod
from app import notify as notify_mod
from app import ratelimit as rl
from app import verify as verify_mod

SECRET = "test-secret-notify-032-chars-ok!"
RECORD = auth_mod.hash_password("demo-pass-1")
UA_DESK = "Mozilla/5.0 (Windows NT 10.0)"
UA_MOB = "Mozilla/5.0 (iPhone; CPU iPhone)"
FULL_CTX = {"username": "u", "level": "high", "signals": "s",
            "actor": "a", "remaining": "9", "purpose": "email"}


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
    monkeypatch.setattr(config_mod, "MFA_REQUIRED_ROLES", "")
    return monkeypatch


def _req(cookie=None, xff=None, ua=None):
    hdrs = [(b"host", b"t")]
    if cookie is not None:
        hdrs.append((b"cookie", ("csai_session=%s" % cookie).encode()))
    if xff is not None:
        hdrs.append((b"x-forwarded-for", xff.encode()))
    if ua is not None:
        hdrs.append((b"user-agent", ua.encode()))
    return Request({"type": "http", "method": "POST", "scheme": "http",
                    "server": ("t", 80), "client": ("9.9.9.9", 1234),
                    "path": "/x", "query_string": b"", "headers": hdrs})


def _cookie(resp):
    raw = resp.headers["set-cookie"]
    part = [p for p in raw.split(";") if "csai_session=" in p][0]
    return part.split("csai_session=", 1)[1]


def _login(user, password="demo-pass-1", xff=None, ua=None):
    return main.auth_login({"username": user, "password": password},
                           _req(xff=xff, ua=ua))


def test_templates_render_all():
    for event in notify_mod.TEMPLATES:
        subject, body, version = notify_mod.render(event, FULL_CTX)
        assert subject and body and version == 1


def test_render_errors():
    with pytest.raises(ValueError, match="NOTIF_EVENT_UNKNOWN"):
        notify_mod.render("nope", FULL_CTX)
    with pytest.raises(ValueError, match="NOTIF_CONTEXT_MISSING"):
        notify_mod.render("suspicious_login", {"username": "u"})
    with pytest.raises(ValueError, match="NOTIF_CHANNEL_UNKNOWN"):
        notify_mod.dispatch(None, "suspicious_login", "u", FULL_CTX,
                            channel="pager")


def test_retry_schedule_and_drivers():
    assert [notify_mod.next_retry(i) for i in range(4)] == [
        60, 300, 900, None]
    assert notify_mod.next_retry(-1) is None
    assert notify_mod.DRIVERS == ("log",)


def test_security_ignores_prefs_and_branch_suppresses(tmp_store, armed):
    tmp_store.save_notif_prefs("judge", {"marketing": True})
    entry = notify_mod.dispatch(tmp_store, "password_changed",
                                "judge", {})
    assert entry["status"] == "logged"
    tmp_store.save_notif_prefs("judge", {"product": False})
    fake = {"version": 1, "kind": "product", "subject": "P",
            "body": "Hi {username}"}
    armed.setitem(notify_mod.TEMPLATES, "product_update", fake)
    try:
        entry = notify_mod.dispatch(tmp_store, "product_update",
                                    "judge", {})
    finally:
        del notify_mod.TEMPLATES["product_update"]
    assert entry["status"] == "suppressed"


def test_outbox_cap(tmp_store):
    for _ in range(205):
        notify_mod.dispatch(tmp_store, "mfa_enabled", "judge", {})
    assert len(tmp_store.outbox()) == 200


def test_no_extra_interpolation(tmp_store):
    entry = notify_mod.dispatch(
        tmp_store, "password_changed", "judge",
        {"password": "SUPER-SECRET-XYZ"})
    assert "SUPER-SECRET-XYZ" not in entry["body"]


def test_password_change_emits(tmp_store, armed):
    cookie = _cookie(_login("judge"))
    main.auth_change_password(
        {"current_password": "demo-pass-1",
         "new_password": "brand-new-password-1"}, _req(cookie))
    events = [e["event"] for e in tmp_store.outbox()]
    assert "password_changed" in events


def test_verify_confirm_emits(tmp_store, armed):
    boss = _cookie(_login("boss"))
    main.admin_create_user(
        {"username": "ann", "password": "long-password-1",
         "role": "investigator", "email": "ann@example.com"},
        _req(boss))
    cookie = _cookie(main.auth_login(
        {"username": "ann", "password": "long-password-1"}, _req()))
    token = verify_mod.issue_token(SECRET, "ann", "email",
                                   "ann@example.com")
    main.verify_confirm({"token": token}, _req(cookie))
    events = [e["event"] for e in tmp_store.outbox()]
    assert "contact_verified" in events


def test_mfa_enable_disable_emit(tmp_store, armed):
    armed.setattr(config_mod, "MFA_REQUIRED_ROLES", "investigator")
    pending = _cookie(_login("judge"))
    main.mfa_enroll(_req(pending))
    code = mfa_mod.totp(mfa_mod.derive_secret(SECRET, "judge", 1))
    main.mfa_confirm({"code": code}, _req(pending))
    events = [e["event"] for e in tmp_store.outbox()]
    assert "mfa_enabled" in events
    main.mfa_disable({"username": "judge"}, _req(_cookie(_login("boss"))))
    events = [e["event"] for e in tmp_store.outbox()]
    assert "mfa_disabled" in events


def test_elevated_login_emits(tmp_store, armed):
    _login("judge", xff="10.1.0.1", ua=UA_DESK)
    assert tmp_store.outbox() == []
    _login("judge", xff="10.2.0.2", ua=UA_MOB)
    suspicious = [e for e in tmp_store.outbox()
                  if e["event"] == "suspicious_login"]
    assert len(suspicious) == 1
    assert "high" in suspicious[0]["body"]


def test_recovery_emits(tmp_store, armed):
    armed.setattr(config_mod, "MFA_REQUIRED_ROLES", "investigator")
    pending = _cookie(_login("judge"))
    codes = json.loads(main.mfa_enroll(_req(pending)).body.decode())[
        "recovery_codes"]
    code = mfa_mod.totp(mfa_mod.derive_secret(SECRET, "judge", 1))
    main.mfa_confirm({"code": code}, _req(pending))
    ticket = json.loads(_login("judge").body.decode())["ticket"]
    resp = main.mfa_challenge({"ticket": ticket, "recovery_code": codes[0]},
                              _req())
    assert resp.status_code == 200
    events = [e["event"] for e in tmp_store.outbox()]
    assert "recovery_used" in events
