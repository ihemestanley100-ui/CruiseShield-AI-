"""Notification subsystem: per-identity read state over alerts."""
import pytest
from env_probe import CAN_SOCKETS

import app.config as config_mod
from app import auth as auth_mod
from app import ratelimit as rl

needs_sockets = pytest.mark.skipif(
    not CAN_SOCKETS,
    reason="socket creation forbidden in this sandbox; runs in CI/user envs")

SECRET = "test-secret-notif-032-chars-long!!"
TOKEN = "test-platform-token-notif-not-a-secret"
RECORD = auth_mod.hash_password("pw-notif")
XRW = {"X-Requested-With": "XMLHttpRequest"}


@pytest.fixture()
def armed(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:investigator:%s,boss:admin:%s,ann:auditor:%s"
        % (RECORD, RECORD, RECORD))
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", TOKEN)
    rl._buckets.clear()
    yield


@pytest.fixture()
def open_mode(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", "")
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "")
    rl._buckets.clear()
    yield


def _login(client, username):
    resp = client.post("/api/v1/auth/login",
                       json={"username": username, "password": "pw-notif"})
    assert resp.status_code == 200, username
    return {"csai_session": resp.cookies["csai_session"]}


def _tok():
    return {"Authorization": "Bearer " + TOKEN}


@needs_sockets
def test_list_open_mode(client, tmp_store, open_mode):
    resp = client.get("/api/v1/notifications")
    assert resp.status_code == 200
    body = resp.json()
    assert body["synthetic_notice"] == "Synthetic data."
    assert body["unread_count"] >= 1
    first = body["notifications"][0]
    assert {"notification_id", "title", "status", "created_at",
            "read"} <= set(first)
    assert first["read"] is False


@needs_sockets
def test_mark_one_persists(client, tmp_store, open_mode):
    nid = client.get("/api/v1/notifications").json(
        )["notifications"][0]["notification_id"]
    resp = client.post("/api/v1/notifications/read",
                       json={"notification_ids": [nid]})
    assert resp.status_code == 200
    assert resp.json()["marked"] == [nid]
    again = client.get("/api/v1/notifications").json()
    mine = [n for n in again["notifications"]
            if n["notification_id"] == nid][0]
    assert mine["read"] is True
    assert tmp_store.state["notification_reads"]["local-default"][nid]


@needs_sockets
def test_mark_all_and_unknown_ignored(client, tmp_store, open_mode):
    resp = client.post("/api/v1/notifications/read",
                       json={"notification_ids": ["nope-1"],
                             "all": True})
    assert resp.status_code == 200
    assert client.get("/api/v1/notifications").json()[
        "unread_count"] == 0
    resp = client.post("/api/v1/notifications/read",
                       json={"notification_ids": ["nope-1"]})
    assert resp.json()["marked"] == []


@needs_sockets
def test_validation(client, tmp_store, open_mode):
    bad = client.post("/api/v1/notifications/read",
                      json={"notification_ids": ["x"] * 501})
    assert bad.status_code == 400
    bad = client.post("/api/v1/notifications/read",
                      json={"notification_ids": [42]})
    assert bad.status_code == 400
    bad = client.post("/api/v1/notifications/read",
                      json={"notification_ids": [""]})
    assert bad.status_code == 400


@needs_sockets
def test_armed_anonymous_denied(client, tmp_store, armed):
    assert client.post("/api/v1/notifications/read",
                       json={"all": True}).status_code == 401
    assert client.get("/api/v1/notifications").status_code == 401


@needs_sockets
def test_armed_sessions_isolated(client, tmp_store, armed):
    judge = _login(client, "judge")
    boss = _login(client, "boss")
    nid = client.get("/api/v1/notifications",
                     cookies=judge).json(
        )["notifications"][0]["notification_id"]
    resp = client.post("/api/v1/notifications/read",
                       json={"notification_ids": [nid]},
                       headers=XRW, cookies=judge)
    assert resp.status_code == 200
    # Boss (different identity) still sees it unread.
    other = client.get("/api/v1/notifications", cookies=boss).json()
    mine = [n for n in other["notifications"]
            if n["notification_id"] == nid][0]
    assert mine["read"] is False
    assert other["unread_count"] >= 1


@needs_sockets
def test_armed_token_identity_and_write_gate(client, tmp_store, armed):
    resp = client.get("/api/v1/notifications", headers=_tok())
    assert resp.status_code == 200
    nid = resp.json()["notifications"][0]["notification_id"]
    resp = client.post("/api/v1/notifications/read",
                       json={"notification_ids": [nid]},
                       headers=_tok())
    assert resp.status_code == 200
    assert tmp_store.state["notification_reads"]["platform-token"][nid]
    # Read-only role cannot write read-state.
    ann = _login(client, "ann")
    resp = client.post("/api/v1/notifications/read",
                       json={"all": True}, headers=XRW, cookies=ann)
    assert resp.status_code == 403
