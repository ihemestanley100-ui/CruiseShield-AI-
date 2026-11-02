"""J4 end-to-end login verification over TestClient (socket-gated).

Full journey: anonymous 401 → bad login → investigator login, reads,
writes, AI perm, admin fence → logout revokes → auditor/demo_viewer
boundaries → admin reset → logout-all → audit trail. Runs where
sockets exist (unsandboxed here, CI/user envs).
"""
import pytest
from env_probe import CAN_SOCKETS

import app.config as config_mod
from app import auth as auth_mod
from app import ratelimit as rl

needs_sockets = pytest.mark.skipif(
    not CAN_SOCKETS,
    reason="socket creation forbidden in this sandbox; runs in CI/user envs")

SECRET = "test-secret-j4-e2e"
RECORD = auth_mod.hash_password("demo-pass-1")
XRW = {"X-Requested-With": "XMLHttpRequest"}


def _users(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:investigator:%s,boss:admin:%s,ann:auditor:%s,"
        "vie:demo_viewer:%s" % (RECORD, RECORD, RECORD, RECORD))


def _login(client, username):
    resp = client.post("/api/v1/auth/login",
                       json={"username": username,
                             "password": "demo-pass-1"})
    assert resp.status_code == 200, username
    return resp.cookies["csai_session"]


@needs_sockets
def test_j4_full_login_journey(client, tmp_store, monkeypatch):
    _users(monkeypatch)
    rl.reset()
    assert client.get("/api/v1/alerts").status_code == 401
    bad = client.post("/api/v1/auth/login",
                      json={"username": "judge", "password": "wrong"})
    assert bad.status_code == 401
    assert "csai_session" not in bad.cookies

    inv = _login(client, "judge")
    me = client.get("/api/v1/auth/me").json()
    assert me["role"] == "investigator"
    assert "write" in me["permissions"]
    assert client.get("/api/v1/alerts").status_code == 200
    decision = client.post(
        "/api/v1/cases/case_84721/decisions",
        json={"decision": "Escalate", "target_status": "TRIAGED",
              "reason": "J4 E2E write.", "actor_id": "judge"},
        headers=XRW)
    assert decision.status_code == 200
    ai = client.post("/api/v1/investigations/inv_84721/ai-analysis",
                     headers=XRW)
    assert ai.status_code == 503  # perm passed; no provider key here
    assert ai.json()["error"]["code"] == "MODEL_NOT_CONFIGURED"
    reset = client.post("/api/v1/demo/reset",
                        json={"scenario_id": "scn_primary"}, headers=XRW)
    assert reset.status_code == 403
    assert reset.json()["error"]["code"] == "ADMIN_REQUIRED"

    assert client.post("/api/v1/auth/logout", headers=XRW).status_code == 200
    stale = client.get("/api/v1/alerts",
                       headers={"Cookie": "csai_session=%s" % inv})
    assert stale.status_code == 401  # revoked server-side, not just cookie
    mid = [a["action"] for a in tmp_store.state["audits"]]
    assert "auth.login" in mid and "auth.logout" in mid

    _login(client, "ann")
    assert client.get(
        "/api/v1/cases/case_84721/audit").status_code == 200
    denied = client.post("/api/v1/cases/case_84721/decisions",
                         json={"decision": "Escalate",
                               "target_status": "TRIAGED", "reason": "x"},
                         headers=XRW)
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"

    _login(client, "vie")
    assert client.get("/api/v1/alerts").status_code == 200
    assert client.get(
        "/api/v1/cases/case_84721/audit").status_code == 403

    _login(client, "boss")
    reset = client.post("/api/v1/demo/reset",
                        json={"scenario_id": "scn_primary"}, headers=XRW)
    assert reset.status_code == 200

    second = _login(client, "judge")
    # Epoch granularity is 1 s: separate pre/post tokens deterministically.
    import time as _time
    _time.sleep(1.1)
    assert client.post("/api/v1/auth/logout-all",
                       headers=XRW).status_code == 200
    for token in (inv, second):
        gone = client.get("/api/v1/alerts", headers={
            "Cookie": "csai_session=%s" % token})
        assert gone.status_code == 401
    _login(client, "judge")
    assert client.get("/api/v1/alerts").status_code == 200

    # The admin reset above rebuilt the audit trail; only post-reset
    # auth events remain (pre-reset login/logout asserted in `mid`).
    actions = [a["action"] for a in tmp_store.state["audits"]]
    assert actions[-3:] == ["auth.login", "auth.logout_all", "auth.login"]
