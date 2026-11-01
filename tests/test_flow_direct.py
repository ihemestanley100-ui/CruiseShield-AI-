"""Socket-free end-to-end verification: direct handler calls + renders.

Runs everywhere, including sandboxes that forbid socket creation.
Transport-level coverage lives in test_api_flow.py (TestClient, gated).
"""
import pytest
from starlette.requests import Request

import app.main as main
from app import ai_adapter


def _req() -> Request:
    return Request({"type": "http", "method": "GET", "headers": [], "path": "/"})


def test_route_table_matches_contract():
    paths = {route.path for route in main.app.routes}
    for expected in [
        "/", "/investigations/{inv_id}", "/system-health",
        "/api/v1/health", "/api/v1/demo/scenarios", "/api/v1/demo/reset",
        "/api/v1/demo/scenarios/{scenario_id}/start",
        "/api/v1/demo/judge-start", "/api/v1/transactions/{txn_id}",
        "/api/v1/graph/{txn_id}", "/api/v1/risk/{txn_id}", "/api/v1/alerts",
        "/api/v1/investigations/{inv_id}",
        "/api/v1/investigations/{inv_id}/evidence-package",
        "/api/v1/investigations/{inv_id}/ai-analysis",
        "/api/v1/investigations/{inv_id}/ai-followup",
        "/api/v1/ai-runs/{run_id}", "/api/v1/replay/{scenario_id}",
        "/api/v1/simulations", "/api/v1/cases", "/api/v1/cases/{case_id}",
        "/api/v1/cases/{case_id}/decisions", "/api/v1/cases/{case_id}/audit",
        "/api/v1/events",
    ]:
        assert expected in paths, expected


def test_full_judge_flow_direct(tmp_store, monkeypatch):
    monkeypatch.setattr(ai_adapter, "MODEL_API_KEY", "")
    result = main.demo_reset(_req(), {"scenario_id": "scn_primary"})
    assert result["manifest"]["synthetic_notice"] == "Synthetic demo data."

    txn = main.get_transaction("txn_84721")
    assert txn["transaction"]["amount_minor"] == 48000000
    assert txn["risk_transaction"]["band"] == "MODERATE"
    assert txn["risk_network"]["band"] == "HIGH"

    graph = main.get_graph("txn_84721")
    assert graph["counts"] == {"nodes": 22, "edges": 30}
    assert graph["provenance_errors"] == []

    risk = main.get_risk("txn_84721", scope="network")
    assert risk["assessment"]["score"] == 84
    assert len(risk["rule_results"]) == 8

    inv = main.get_investigation("inv_84721")
    assert inv["evidence_count"] == 39
    package = main.build_evidence_package("inv_84721")
    assert package["package_id"].startswith("evidence_pkg_scn_primary")

    replay0 = main.get_replay("scn_primary", cursor=0)
    assert replay0["total"] == 11 and replay0["counts"]["edges"] == 0
    replay_full = main.get_replay("scn_primary", cursor=11)
    assert replay_full["counts"] == {"events": 11, "transactions": 11, "edges": 30}

    sim = main.post_simulation({
        "target_transaction_id": "txn_84721",
        "ignored_edge_ids": ["edge_0002", "edge_0004", "edge_0005",
                             "edge_0011", "edge_0012"],
        "assumption": "All device-sharing relationships treated as absent."},
        _req())
    assert sim["baseline_score"] == 84
    assert sim["simulated_score"] == 72  # R-003 (weight 12) drops out
    assert main.get_graph("txn_84721")["counts"]["edges"] == 30
    # §4.7: the simulation mutates neither case state nor case audit history.
    assert tmp_store.get_case("case_84721")["status"] == "NEW"
    assert tmp_store.state["decisions"] == []
    assert [a for a in tmp_store.state["audits"]
            if a["action"] == "case.decision"] == []

    with pytest.raises(main.AppError) as exc:
        main.post_decision("case_84721", {
            "decision": "Escalate", "target_status": "TRIAGED", "reason": "  "},
            _req())
    assert exc.value.code == "REASON_REQUIRED"

    with pytest.raises(main.AppError):
        main.post_decision("case_84721", {
            "decision": "Close Case", "target_status": "CLOSED", "reason": "x"},
            _req())

    good = main.post_decision("case_84721", {
        "decision": "Escalate", "target_status": "TRIAGED",
        "reason": "Network shows shared device across three accounts.",
        "actor_id": "investigator"}, _req())
    assert good["case"]["status"] == "TRIAGED"
    audits = main.case_audit("case_84721")["audits"]
    assert any(a["action"] == "case.decision" for a in audits)

    # Fail-fast AI path executes no awaits, so it runs without an event loop.
    with pytest.raises(main.AppError) as exc:
        main.ai_analysis("inv_84721", _req()).send(None)
    assert exc.value.code == "MODEL_NOT_CONFIGURED"


def test_followup_validates_before_any_model_call(tmp_store):
    # Unknown investigation rejected without touching the provider.
    with pytest.raises(main.AppError) as exc:
        main.ai_followup("inv_nope", {"question": "Why?"}, _req()).send(None)
    assert exc.value.code == "UNKNOWN_INVESTIGATION"
    # Empty question rejected without touching the provider.
    with pytest.raises(main.AppError) as exc:
        main.ai_followup("inv_84721", {"question": "  "}, _req()).send(None)
    assert exc.value.code == "QUESTION_REQUIRED"
    # Overlong question rejected without touching the provider.
    with pytest.raises(main.AppError) as exc:
        main.ai_followup(
            "inv_84721", {"question": "x" * 2001}, _req()).send(None)
    assert exc.value.code == "QUESTION_TOO_LONG"
    assert tmp_store.state["ai_runs"] == []


def test_malformed_bodies_rejected_with_400_not_500(tmp_store):
    with pytest.raises(main.AppError) as exc:
        main.post_simulation(["not", "a", "dict"], _req())
    assert exc.value.code == "INVALID_BODY"
    with pytest.raises(main.AppError) as exc:
        main.post_simulation(
            {"target_transaction_id": "txn_84721",
             "ignored_edge_ids": "edge_0002"}, _req())
    assert exc.value.code == "INVALID_EDGE_LIST"
    with pytest.raises(main.AppError) as exc:
        main.post_simulation(
            {"target_transaction_id": "txn_84721",
             "ignored_edge_ids": ["edge_0002", 7]}, _req())
    assert exc.value.code == "INVALID_EDGE_LIST"
    with pytest.raises(main.AppError) as exc:
        main.ai_followup("inv_84721", ["nope"], _req()).send(None)
    assert exc.value.code == "INVALID_BODY"


def test_pages_render_with_live_state(tmp_store):
    for response in (main.command_center(_req()),
                     main.investigation_page(_req(), "inv_84721"),
                     main.system_health_page(_req())):
        html = response.body.decode("utf-8")
        assert response.status_code == 200
        assert "Synthetic demo data" in html
    health = main.health()
    assert health["status"] == "healthy"
    assert health["checks"]["graph_provenance"] == "PASS"


def test_investigation_renders_when_model_configured(tmp_store, monkeypatch):
    # Regression: with MODEL_API_KEY set, the configured-AI branch rendered
    # `package.items|length`, which resolved to the dict method and 500'd.
    # The suite never caught it because the key is absent in tests.
    monkeypatch.setattr(ai_adapter, "MODEL_API_KEY", "test-key")
    response = main.investigation_page(_req(), "inv_84721")
    html = response.body.decode("utf-8")
    assert response.status_code == 200
    assert "Run AI analysis" in html
    assert "39-item evidence package" in html
    assert "test-key" not in html


def test_simulation_input_caps_reject_abuse(tmp_store):
    before = (len(tmp_store.state["simulations"]),
              len(tmp_store.state["audits"]))
    with pytest.raises(main.AppError) as exc:
        main.post_simulation(
            {"target_transaction_id": "txn_84721",
             "ignored_edge_ids": [], "assumption": "a" * 10001}, _req())
    assert exc.value.code == "ASSUMPTION_TOO_LONG"
    with pytest.raises(main.AppError) as exc:
        main.post_simulation(
            {"target_transaction_id": "txn_84721",
             "ignored_edge_ids": ["edge_0002"] * 10001,
             "assumption": "fine"}, _req())
    assert exc.value.code == "TOO_MANY_IGNORED_EDGES"
    after = (len(tmp_store.state["simulations"]),
             len(tmp_store.state["audits"]))
    assert before == after
