"""SEC-REV: access-review reports over audit data. Socket-free."""
import json

import pytest
from starlette.requests import Request

import app.config as config_mod
import app.main as main
from app import auth as auth_mod
from app import ratelimit as rl

SECRET = "test-secret-secrev-032-chars-ok!"
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
    return Request({"type": "http", "method": "GET", "scheme": "http",
                    "server": ("t", 80), "client": ("9.9.9.9", 1234),
                    "path": "/x", "query_string": b"", "headers": hdrs})


def _login(user, password="demo-pass-1"):
    resp = main.auth_login({"username": user, "password": password},
                           _req())
    raw = resp.headers["set-cookie"]
    part = [p for p in raw.split(";") if "csai_session=" in p][0]
    return part.split("csai_session=", 1)[1]


def _provision(cookie):
    main.admin_create_user(
        {"username": "ann", "password": "long-password-1",
         "role": "auditor", "email": "ann@example.com"}, _req(cookie))


def test_grant_deltas_in_audit_order(tmp_store, armed):
    cookie = _login("boss")
    _provision(cookie)
    main.admin_disable_user({"username": "ann"}, _req(cookie))
    main.admin_enable_user({"username": "ann"}, _req(cookie))
    report = main.access_review(_req(cookie))
    assert report["generated_at"]
    got = [(e["action"], e["target"], e["actor"]) for e in report["events"]]
    assert got == [("user.provision", "ann", "boss"),
                   ("user.disable", "ann", "boss"),
                   ("user.enable", "ann", "boss")]
    assert all(e["at"] for e in report["events"])


def test_non_grant_audits_excluded(tmp_store, armed):
    cookie = _login("boss")
    main.ingest_event({
        "event_id": "evt_rev_1", "occurred_at": "2026-11-07T12:00:00Z",
        "transaction": {"transaction_id": "txn_rev_1", "amount_minor": 5,
                        "channel": "MOBILE_APP",
                        "sender_account_id": "a", "receiver_account_id": "b"},
    }, _req(cookie))
    actions = {e["action"] for e in
               main.access_review(_req(cookie))["events"]}
    assert "auth.login" not in actions
    assert "event.ingested" not in actions


def test_snapshot_current_without_secrets(tmp_store, armed):
    cookie = _login("boss")
    _provision(cookie)
    report = main.access_review(_req(cookie))
    dumped = json.dumps(report)
    assert "pbkdf2" not in dumped
    assert RECORD not in dumped
    by_name = {m["username"]: m for m in report["current"]}
    assert by_name["ann"]["role"] == "auditor"
    assert by_name["ann"]["disabled"] is False
    assert by_name["boss"]["role"] == "admin"


def test_non_admin_denied(tmp_store, armed):
    with pytest.raises(main.AppError) as exc:
        main.access_review(_req(_login("judge")))
    assert exc.value.code == "ADMIN_REQUIRED"
    with pytest.raises(main.AppError) as exc:
        main.access_review(_req())
    assert exc.value.code == "ADMIN_REQUIRED"
