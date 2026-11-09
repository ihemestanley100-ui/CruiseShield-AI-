"""M3 session-authenticated investigation journey over TestClient.

Login -> transactions -> signals -> case -> signal outcome -> case
decision -> audit trail, with session cookies and CSRF headers.
Complements test_api_flow.py (open/write-token mode) with the login-
session variant. Requires sockets; skipped where forbidden, runs hosted.
Uses the seeded synthetic store only.
"""
import pytest

from env_probe import CAN_SOCKETS

import app.config as config_mod
from app import auth as auth_mod
from app import ratelimit as rl

pytestmark = pytest.mark.skipif(
    not CAN_SOCKETS,
    reason="socket creation forbidden in this sandbox; runs hosted")

SECRET = "test-secret-e2e-journey-032-chars-ok"
RECORD = auth_mod.hash_password("demo-pass-1")
W = {"X-Requested-With": "TestClient"}


def _arm(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:investigator:%s,boss:admin:%s" % (RECORD, RECORD))
    monkeypatch.setattr(config_mod, "TRIAL_ENFORCEMENT", "0")
    monkeypatch.setattr(config_mod, "FOUNDER_USER", "")
    rl.reset()


def test_full_investigation_journey(client, monkeypatch):
    _arm(monkeypatch)
    assert client.get("/api/v1/health").json()["status"] == "healthy"
    anon = client.get("/api/v1/cases")
    assert anon.status_code == 401
    login = client.post("/api/v1/auth/login",
                        json={"username": "judge",
                              "password": "demo-pass-1"})
    assert login.status_code == 200
    assert login.json()["user"] == "judge"

    txns = client.get("/api/v1/transactions").json()
    rows = txns["transactions"] if isinstance(txns, dict) else txns
    assert len(rows) >= 1
    txn_id = rows[0]["transaction_id"]

    found = client.get("/api/v1/signals/search").json()
    assert found["total"] >= 1
    assert found["signals"][0]["transaction_id"]
    signal_id = found["signals"][0]["signal_id"]
    detail = client.get("/api/v1/signals/%s" % signal_id).json()
    assert detail["signal_id"] == signal_id

    case = client.post("/api/v1/cases", json={"title": "e2e probe",
                                             "priority": "HIGH"},
                       headers=W).json()["case"]
    assert case["status"] == "NEW"
    reread = client.get("/api/v1/cases/%s" % case["case_id"]).json()
    assert reread["title"] == "e2e probe"

    out = client.post("/api/v1/signals/%s/outcome" % signal_id,
                      json={"outcome": "DISMISSED",
                            "note": "e2e verified benign",
                            "actor_id": "judge"},
                      headers=W).json()
    assert out["outcome"] == "DISMISSED"

    done = client.post("/api/v1/cases/%s/decisions" % case["case_id"],
                       json={"decision": "Mark False Positive",
                             "target_status": "FALSE_POSITIVE",
                             "reason": "signal dismissed after review",
                             "actor_id": "judge"},
                       headers=W).json()
    assert done["case"]["status"] == "FALSE_POSITIVE"

    trail = client.get("/api/v1/cases/%s/audit"
                       % case["case_id"]).json()["audits"]
    actions = {a["action"] for a in trail}
    assert {"case.created", "case.decision"} <= actions
    assert client.get("/api/v1/transactions/%s" % txn_id).status_code == 200


def test_write_without_csrf_header_is_rejected(client, monkeypatch):
    _arm(monkeypatch)
    login = client.post("/api/v1/auth/login",
                        json={"username": "judge",
                              "password": "demo-pass-1"})
    assert login.status_code == 200
    denied = client.post("/api/v1/cases", json={"title": "no-csrf"})
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "CSRF_HEADER_REQUIRED"
