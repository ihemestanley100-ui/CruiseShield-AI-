"""End-to-end API flow over real HTTP transport (TestClient).

Requires socket creation; skipped in sandboxes that forbid it. The same flow
is verified socket-free in test_flow_direct.py.
"""
import pytest

from env_probe import CAN_SOCKETS

pytestmark = pytest.mark.skipif(
    not CAN_SOCKETS,
    reason="socket creation forbidden in this sandbox; runs in CI/user envs")


def test_full_judge_flow(client):
    reset = client.post("/api/v1/demo/reset", json={"scenario_id": "scn_primary"})
    assert reset.status_code == 200, reset.text
    assert reset.json()["manifest"]["synthetic_notice"] == "Synthetic demo data."

    txn = client.get("/api/v1/transactions/txn_84721").json()
    assert txn["transaction"]["amount_minor"] == 48000000
    assert txn["risk_transaction"]["band"] == "MODERATE"
    assert txn["risk_network"]["band"] == "HIGH"

    graph = client.get("/api/v1/graph/txn_84721").json()
    assert graph["counts"] == {"nodes": 22, "edges": 30}
    assert graph["provenance_errors"] == []

    risk = client.get("/api/v1/risk/txn_84721?scope=network").json()
    assert risk["assessment"]["score"] == 84
    assert len(risk["rule_results"]) == 8

    inv = client.get("/api/v1/investigations/inv_84721").json()
    assert inv["evidence_count"] == 39
    package = client.post(
        "/api/v1/investigations/inv_84721/evidence-package").json()
    assert package["package_id"].startswith("evidence_pkg_scn_primary")

    replay0 = client.get("/api/v1/replay/scn_primary?cursor=0").json()
    assert replay0["total"] == 11 and replay0["counts"]["edges"] == 0
    replay_full = client.get("/api/v1/replay/scn_primary?cursor=11").json()
    assert replay_full["counts"] == {"events": 11, "transactions": 11, "edges": 30}
    replay_clamped = client.get("/api/v1/replay/scn_primary?cursor=99").json()
    assert replay_clamped["cursor"] == 11

    sim = client.post("/api/v1/simulations", json={
        "target_transaction_id": "txn_84721",
        "ignored_edge_ids": ["edge_0002", "edge_0004", "edge_0005",
                             "edge_0011", "edge_0012"],
        "assumption": "All device-sharing relationships treated as absent."}).json()
    assert sim["baseline_score"] == 84
    assert sim["simulated_score"] == 72  # R-003 (weight 12) drops out
    after = client.get("/api/v1/graph/txn_84721").json()
    assert after["counts"]["edges"] == 30  # baseline untouched

    bad_decision = client.post("/api/v1/cases/case_84721/decisions", json={
        "decision": "Escalate", "target_status": "TRIAGED", "reason": "  "})
    assert bad_decision.status_code == 400
    assert bad_decision.json()["error"]["code"] == "REASON_REQUIRED"

    bad_transition = client.post("/api/v1/cases/case_84721/decisions", json={
        "decision": "Close Case", "target_status": "CLOSED", "reason": "x"})
    assert bad_transition.status_code == 400

    good = client.post("/api/v1/cases/case_84721/decisions", json={
        "decision": "Escalate", "target_status": "TRIAGED",
        "reason": "Network shows shared device across three accounts.",
        "actor_id": "investigator"}).json()
    assert good["case"]["status"] == "TRIAGED"
    assert good["audit"]["audit_event_id"].startswith("audit_")
    audits = client.get("/api/v1/cases/case_84721/audit").json()["audits"]
    assert any(a["action"] == "case.decision" for a in audits)


def test_pages_and_health_render(client):
    for path in ("/", "/investigations/inv_84721", "/system-health"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert "Synthetic demo data" in response.text
    health = client.get("/api/v1/health").json()
    assert health["status"] == "healthy"
    assert health["checks"]["graph_provenance"] == "PASS"


def test_stable_error_format(client):
    response = client.get("/api/v1/transactions/txn_nope")
    assert response.status_code == 404
    body = response.json()["error"]
    assert set(body) == {"code", "message", "trace_id"}
    assert body["code"] == "UNKNOWN_TRANSACTION"
    dup = client.post("/api/v1/events", json={"event_id": "x"})
    assert dup.status_code == 422
    assert dup.json()["error"]["code"] == "SCHEMA_INVALID"
