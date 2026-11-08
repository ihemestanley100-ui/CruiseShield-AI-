"""R1-R4 token remediation (DEMO_TOKEN_SECURITY_AUDIT.md).

4-way access matrix over the real middleware stack (socket-gated
TestClient) plus socket-free unit tests for the new helpers.
"""
import json

import pytest
from env_probe import CAN_SOCKETS
from starlette.requests import Request

import app.main as main
import app.config as config_mod
from app import auth as auth_mod
from app import ratelimit as rl

needs_sockets = pytest.mark.skipif(
    not CAN_SOCKETS,
    reason="socket creation forbidden in this sandbox; runs in CI/user envs")

SECRET = "test-secret-r1r4-remediation-32ch!!"
TOKEN = "test-platform-token-r1r4-not-a-secret"
RECORD = auth_mod.hash_password("pw-r1r4")
XRW = {"X-Requested-With": "XMLHttpRequest"}
DECISION = {"decision": "Escalate", "target_status": "TRIAGED",
            "reason": "r1r4 probe", "actor_id": "judge"}


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


def _login(client, username):
    resp = client.post("/api/v1/auth/login",
                       json={"username": username, "password": "pw-r1r4"})
    assert resp.status_code == 200, username
    return {"csai_session": resp.cookies["csai_session"]}


def _tok():
    return {"Authorization": "Bearer " + TOKEN}


# -- R1: token must not reach admin-only demo paths ----------------------

@needs_sockets
def test_r1_token_denied_platform_reset(client, tmp_store, armed):
    resp = client.post("/api/v1/platform/reset", headers=_tok())
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "ADMIN_REQUIRED"


@needs_sockets
def test_r1_token_denied_judge_start(client, tmp_store, armed):
    resp = client.post("/api/v1/platform/judge-start", headers=_tok())
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "ADMIN_REQUIRED"


@needs_sockets
def test_r1_token_denied_platform_scenarios_get(client, tmp_store, armed):
    resp = client.get("/api/v1/platform/scenarios", headers=_tok())
    assert resp.status_code == 403


@needs_sockets
def test_r1_admin_session_allowed_platform_reset(client, tmp_store, armed):
    cookies = _login(client, "boss")
    resp = client.post("/api/v1/platform/reset", headers=XRW, cookies=cookies)
    assert resp.status_code == 200


@needs_sockets
def test_r1_nonadmin_session_still_denied(client, tmp_store, armed):
    cookies = _login(client, "judge")
    resp = client.post("/api/v1/platform/reset", headers=XRW, cookies=cookies)
    assert resp.status_code == 403


@needs_sockets
def test_r1_anonymous_denied_platform_reset(client, tmp_store, armed):
    resp = client.post("/api/v1/platform/reset")
    assert resp.status_code == 401


# -- R2: token actor forced to platform-token --------------------------------

@needs_sockets
def test_r2_token_actor_forced(client, tmp_store, armed):
    case_id = tmp_store.state["cases"][0]["case_id"]
    resp = client.post("/api/v1/cases/%s/decisions" % case_id,
                       json=DECISION, headers=_tok())
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"]["actor_id"] == "platform-token"
    assert "platform-token" in json.dumps(body["audit"])
    assert "judge" not in json.dumps(body["audit"])


@needs_sockets
def test_r2_session_actor_preserved(client, tmp_store, armed):
    cookies = _login(client, "judge")
    case_id = tmp_store.state["cases"][0]["case_id"]
    resp = client.post("/api/v1/cases/%s/decisions" % case_id,
                       json=DECISION, headers=XRW, cookies=cookies)
    assert resp.status_code == 200
    assert resp.json()["decision"]["actor_id"] == "judge"


def test_r2_helper_token_forced(monkeypatch):
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", TOKEN)
    req = Request({"type": "http", "method": "POST", "path": "/x",
                   "headers": [(b"host", b"t"),
                               (b"authorization",
                                ("Bearer " + TOKEN).encode())]})
    assert main._decision_actor(req, "judge") == "platform-token"


def test_r2_helper_no_credential_passthrough(monkeypatch):
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", TOKEN)
    req = Request({"type": "http", "method": "POST", "path": "/x",
                   "headers": [(b"host", b"t")]})
    assert main._decision_actor(req, "judge") == "judge"


# -- R3: AI requires an authenticated login session ----------------------

@needs_sockets
def test_r3_token_denied_ai_analysis(client, tmp_store, armed):
    inv_id = tmp_store.state["investigations"][0]["investigation_id"]
    resp = client.post(
        "/api/v1/investigations/%s/ai-analysis" % inv_id, headers=_tok())
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "AI_LOGIN_REQUIRED"


@needs_sockets
def test_r3_token_denied_ai_followup(client, tmp_store, armed):
    inv_id = tmp_store.state["investigations"][0]["investigation_id"]
    resp = client.post(
        "/api/v1/investigations/%s/ai-followup" % inv_id,
        json={"question": "probe"}, headers=_tok())
    assert resp.status_code == 403


@needs_sockets
def test_r3_session_allowed_ai_analysis(client, tmp_store, armed,
                                        monkeypatch):
    async def fake_run(*args, **kwargs):
        return {"ok": True}

    monkeypatch.setattr(main, "_run_ai", fake_run)
    cookies = _login(client, "judge")
    inv_id = tmp_store.state["investigations"][0]["investigation_id"]
    resp = client.post(
        "/api/v1/investigations/%s/ai-analysis" % inv_id,
        headers=XRW, cookies=cookies)
    assert resp.status_code == 200


@needs_sockets
def test_r3_unarmed_local_dev_unaffected(client, tmp_store, monkeypatch):
    """Local open-demo default keeps working: no login needed unarmed."""
    async def fake_run(*args, **kwargs):
        return {"ok": True}

    monkeypatch.setattr(main, "_run_ai", fake_run)
    monkeypatch.setattr(config_mod, "SESSION_SECRET", "")
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "")
    inv_id = tmp_store.state["investigations"][0]["investigation_id"]
    resp = client.post(
        "/api/v1/investigations/%s/ai-analysis" % inv_id)
    assert resp.status_code == 200


# -- R4: evidence-package POST gated -------------------------------------

@needs_sockets
def test_r4_token_reads_evidence_post(client, tmp_store, armed):
    inv_id = tmp_store.state["investigations"][0]["investigation_id"]
    resp = client.post(
        "/api/v1/investigations/%s/evidence-package" % inv_id,
        headers=_tok())
    assert resp.status_code == 200
    assert "package_id" in resp.json() or "evidence" in json.dumps(
        resp.json())


@needs_sockets
def test_r4_anonymous_denied_evidence_post(client, tmp_store, armed):
    inv_id = tmp_store.state["investigations"][0]["investigation_id"]
    resp = client.post(
        "/api/v1/investigations/%s/evidence-package" % inv_id)
    assert resp.status_code == 401


def test_r4_route_gate_unit(monkeypatch):
    """Route-level gate exists independent of middleware."""
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", TOKEN)
    req = Request({"type": "http", "method": "POST", "path": "/x",
                   "headers": [(b"host", b"t")]})
    with pytest.raises(main.AppError) as exc:
        main.build_evidence_package("inv_84721", req)
    assert exc.value.status == 401
    assert exc.value.code == "WRITE_TOKEN_REQUIRED"
