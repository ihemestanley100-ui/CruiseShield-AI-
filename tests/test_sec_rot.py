"""SEC-ROT: SESSION_SECRET rotation without downtime."""
from __future__ import annotations

from starlette.requests import Request

import app.main as main
from app import auth as auth_mod
from app import config as config_mod

OLD = "old-secret-old-secret-old-secret-01"
NEW = "new-secret-new-secret-new-secret-02"
RECORD = auth_mod.hash_password("demo-pass-1")


def _users(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", NEW)
    monkeypatch.setattr(config_mod, "SESSION_SECRET_PREVIOUS", OLD)
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "")
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:investigator:%s,boss:admin:%s" % (RECORD, RECORD))


def _req(cookie):
    return Request({"type": "http", "method": "GET", "scheme": "http",
                    "server": ("t", 80), "client": ("9.9.9.9", 1234),
                    "path": "/x", "query_string": b"",
                    "headers": [(b"host", b"t"),
                                (b"cookie",
                                 ("csai_session=%s" % cookie).encode())]})


def test_parse_any_order_and_safety():
    token = auth_mod.create_session("u", "investigator", OLD)
    assert auth_mod.parse_session_any(token, [NEW, OLD])["user"] == "u"
    assert auth_mod.parse_session_any(token, [NEW]) is None
    assert auth_mod.parse_session_any(token, []) is None
    assert auth_mod.parse_session_any("junk", [OLD]) is None
    assert auth_mod.parse_session_any("", [""]) is None


def test_overlap_then_cutover(tmp_store, monkeypatch):
    _users(monkeypatch)
    users = {"judge": ("investigator", RECORD)}
    old_token = auth_mod.create_session("judge", "investigator", OLD)
    new_token = auth_mod.create_session("judge", "investigator", NEW)
    ring = [NEW, OLD]
    assert auth_mod.verify_session_live(
        old_token, NEW, tmp_store, users, secrets=ring) is not None
    assert auth_mod.verify_session_live(
        new_token, NEW, tmp_store, users, secrets=ring) is not None
    cut = [NEW]
    assert auth_mod.verify_session_live(
        old_token, NEW, tmp_store, users, secrets=cut) is None
    assert auth_mod.verify_session_live(
        new_token, NEW, tmp_store, users, secrets=cut) is not None


def test_claims_honor_previous(tmp_store, monkeypatch):
    _users(monkeypatch)
    old_token = auth_mod.create_session("judge", "investigator", OLD)
    assert main._session_claims(_req(old_token))["user"] == "judge"
    assert main._session_of(_req(old_token)) == ("judge", "investigator")
    monkeypatch.setattr(config_mod, "SESSION_SECRET_PREVIOUS", "")
    assert main._session_claims(_req(old_token)) is None
