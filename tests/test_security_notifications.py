"""D-029 / L13 Part 9 (in-app leg): security notifications. Socket-free."""
import json
import time

import pytest
from starlette.requests import Request

import app.main as main
from app import auth as auth_mod
from app import config as config_mod
from app import mfa as mfa_mod
from app import ratelimit as rl

SECRET = "test-secret-not-a-real-credential"
RECORD = auth_mod.hash_password("demo-pass-1")
UA_DESK = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
           "Chrome/126.0 Safari/537.36")
UA_MOB = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
          "AppleWebKit/605.1.15 Mobile/15E148")


@pytest.fixture(autouse=True)
def _buckets():
    rl.reset()
    yield
    rl.reset()


class _Clock:
    def __init__(self, start):
        self.now = start

    def __call__(self):
        return self.now


@pytest.fixture()
def clock(monkeypatch):
    clk = _Clock(1_700_000_000.0)
    monkeypatch.setattr(time, "time", clk)
    return clk


def _users(monkeypatch, roles=""):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(config_mod, "MFA_REQUIRED_ROLES", roles)
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:investigator:%s,boss:admin:%s" % (RECORD, RECORD))


def _scope(path, method="GET", cookie=None, xrw=False, xff=None,
           ua=None):
    headers = [(b"host", b"t")]
    if cookie is not None:
        headers.append((b"cookie", ("csai_session=%s" % cookie).encode()))
    if xrw:
        headers.append((b"x-requested-with", b"XMLHttpRequest"))
    if xff is not None:
        headers.append((b"x-forwarded-for", xff.encode()))
    if ua is not None:
        headers.append((b"user-agent", ua.encode()))
    return {"type": "http", "method": method, "scheme": "http",
            "server": ("t", 80), "client": ("9.9.9.9", 1234),
            "path": path, "query_string": b"", "headers": headers}


def _login(user, password="demo-pass-1", xff=None, ua=None):
    req = Request(_scope("/api/v1/auth/login", method="POST",
                         xff=xff, ua=ua))
    return main.auth_login({"username": user, "password": password},
                           req)


def _cookie(resp):
    raw = resp.headers["set-cookie"]
    part = [p for p in raw.split(";") if "csai_session=" in p][0]
    return part.split("csai_session=", 1)[1]


def _code(user, counter=1):
    return mfa_mod.totp(mfa_mod.derive_secret(SECRET, user, counter))


def _list(cookie):
    return main.list_notifications(
        Request(_scope("/api/v1/notifications", cookie=cookie)))


def _mark(cookie, body):
    return main.mark_notifications_read(
        body, Request(_scope("/api/v1/notifications/read",
                             method="POST", cookie=cookie, xrw=True)))


def _enroll_confirm(cookie, user, xff_e, xff_c):
    enroll = main.mfa_enroll(Request(
        _scope("/api/v1/auth/mfa/enroll", method="POST",
               cookie=cookie, xrw=True, xff=xff_e)))
    assert enroll.status_code == 200
    codes = json.loads(enroll.body.decode())["recovery_codes"]
    confirmed = main.mfa_confirm(
        {"code": _code(user)},
        Request(_scope("/api/v1/auth/mfa/confirm", method="POST",
                       cookie=cookie, xrw=True, xff=xff_c)))
    assert confirmed.status_code == 200
    return codes


# --- emission ------------------------------------------------------------


def test_elevated_login_emits_security_notice(monkeypatch, tmp_store):
    _users(monkeypatch)
    _login("judge", xff="10.4.0.1", ua=UA_DESK)
    cookie = _cookie(_login("judge", xff="10.4.9.9", ua=UA_DESK))
    items = _list(cookie)["notifications"]
    sec = [n for n in items if n.get("kind") == "security"]
    assert len(sec) == 1
    assert sec[0]["title"] == "Unusual sign-in activity"
    assert "elevated" in sec[0]["detail"]
    assert "new_ip" in sec[0]["detail"]
    assert sec[0]["read"] is False


def test_low_login_emits_nothing(monkeypatch, tmp_store):
    _users(monkeypatch)
    _login("judge", xff="10.4.0.2", ua=UA_DESK)
    _login("judge", xff="10.4.0.2", ua=UA_DESK)
    assert tmp_store.user_notifications_for("judge") == []


def test_ticket_path_still_emits(monkeypatch, tmp_store, clock):
    _users(monkeypatch, roles="admin")
    pending = _cookie(_login("boss"))
    _enroll_confirm(pending, "boss", "10.5.0.1", "10.5.0.2")
    clock.now += 31
    body = json.loads(_login("boss", xff="10.9.9.9",
                             ua=UA_MOB).body.decode())
    assert body["mfa_required"] is True
    kinds = [e["kind"] for e in
             tmp_store.user_notifications_for("boss")]
    assert "risk.login" in kinds
    assert "mfa.enabled" in kinds


def test_mfa_disable_emits_with_actor(monkeypatch, tmp_store,
                                         clock):
    _users(monkeypatch, roles="admin")
    judge_full = _cookie(_login("judge"))
    _enroll_confirm(judge_full, "judge", "10.6.0.1", "10.6.0.2")
    boss_pending = _cookie(_login("boss"))
    _enroll_confirm(boss_pending, "boss", "10.6.0.3", "10.6.0.4")
    clock.now += 31  # consumed TOTP codes never verify twice
    # Active enrollment: the next login needs step-up via challenge.
    ticket = json.loads(_login("boss", xff="10.6.0.7").body.decode())
    assert ticket["mfa_required"] is True
    resp = main.mfa_challenge(
        {"ticket": ticket["ticket"], "code": _code("boss")},
        Request(_scope("/api/v1/auth/mfa/challenge", method="POST",
                       xff="10.6.0.8")))
    boss_full = _cookie(resp)
    denied = main.mfa_disable(
        {"username": "judge"},
        Request(_scope("/api/v1/auth/mfa/disable", method="POST",
                       cookie=boss_full, xrw=True, xff="10.6.0.9")))
    assert denied.status_code == 200
    notes = tmp_store.user_notifications_for("judge")
    kinds = [e["kind"] for e in notes]
    assert "mfa.disabled" in kinds
    detail = next(e["detail"] for e in notes
                  if e["kind"] == "mfa.disabled")
    assert "by boss" in detail


def test_recovery_code_use_emits_remaining(monkeypatch, tmp_store,
                                           clock):
    _users(monkeypatch, roles="admin")
    pending = _cookie(_login("boss"))
    codes = _enroll_confirm(pending, "boss", "10.7.0.1", "10.7.0.2")
    clock.now += 31
    ticket = json.loads(_login("boss").body.decode())["ticket"]
    resp = main.mfa_challenge(
        {"ticket": ticket, "recovery_code": codes[0]},
        Request(_scope("/api/v1/auth/mfa/challenge", method="POST",
                       xff="10.7.0.3")))
    assert resp.status_code == 200
    notes = tmp_store.user_notifications_for("boss")
    rec = next(e for e in notes if e["kind"] == "mfa.recovery_used")
    assert "%d remaining" % (len(codes) - 1) in rec["detail"]
    assert rec["level"] == "warn"


# --- listing, read-state, isolation --------------------------------------


def test_unread_count_includes_security_items(monkeypatch, tmp_store):
    _users(monkeypatch)
    _login("judge", xff="10.8.0.1", ua=UA_DESK)
    cookie = _cookie(_login("judge", xff="10.8.9.9", ua=UA_MOB))
    payload = _list(cookie)
    expect = sum(1 for n in payload["notifications"]
                 if not n["read"] and n["status"] == "OPEN")
    assert payload["unread_count"] == expect >= 1


def test_mark_read_and_mark_all_cover_security_ids(monkeypatch,
                                                   tmp_store):
    _users(monkeypatch)
    _login("judge", xff="10.9.0.1", ua=UA_DESK)
    cookie = _cookie(_login("judge", xff="10.9.9.9", ua=UA_DESK))
    sec_id = next(n["notification_id"]
                  for n in _list(cookie)["notifications"]
                  if n.get("kind") == "security")
    out = _mark(cookie, {"notification_ids": [sec_id]})
    assert sec_id in out["marked"]
    assert all(n["read"] for n in _list(cookie)["notifications"]
               if n["notification_id"] == sec_id)
    # A second event is covered by mark-all.
    _login("judge", xff="10.9.9.8", ua=UA_MOB)
    out = _mark(cookie, {"all": True})
    assert any(i.startswith("sec_") for i in out["marked"])
    assert all(n["read"] for n in _list(cookie)["notifications"]
               if n.get("kind") == "security")


def test_security_items_are_per_user(monkeypatch, tmp_store):
    _users(monkeypatch)
    _login("judge", xff="10.10.0.1", ua=UA_DESK)
    _login("judge", xff="10.10.9.9", ua=UA_DESK)
    boss_cookie = _cookie(_login("boss"))
    assert [n for n in _list(boss_cookie)["notifications"]
            if n.get("kind") == "security"] == []


def test_store_caps_each_user_at_fifty(monkeypatch, tmp_store):
    _users(monkeypatch)
    for i in range(55):
        tmp_store.notify_user("judge", "risk.login", "t%d" % i, "d")
    mine = tmp_store.user_notifications_for("judge")
    assert len(mine) == 50
    assert mine[0]["notification_id"] == "sec_0006"
    assert mine[-1]["notification_id"] == "sec_0055"


def test_stored_detail_carries_no_network_or_secret_material(
        monkeypatch, tmp_store):
    _users(monkeypatch)
    _login("judge", xff="10.11.0.1", ua=UA_DESK)
    _login("judge", password="demo-pass-1", xff="10.11.9.9",
           ua=UA_DESK)
    blob = json.dumps(tmp_store.state.get("user_notifications", []))
    assert "10.11.9.9" not in blob
    assert "Windows NT" not in blob
    assert "demo-pass-1" not in blob
