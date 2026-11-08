"""Socket-free end-to-end verification: direct handler calls + renders.

Runs everywhere, including sandboxes that forbid socket creation.
Transport-level coverage lives in test_api_flow.py (TestClient, gated).
"""
import json

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
        "/api/v1/health", "/api/v1/platform/scenarios", "/api/v1/demo/scenarios", "/api/v1/platform/reset", "/api/v1/demo/reset",
        "/api/v1/platform/scenarios/{scenario_id}/start", "/api/v1/demo/scenarios/{scenario_id}/start",
        "/api/v1/platform/judge-start", "/api/v1/demo/judge-start", "/api/v1/transactions/{txn_id}",
        "/api/v1/graph/{txn_id}", "/api/v1/risk/{txn_id}", "/api/v1/alerts",
        "/api/v1/investigations/{inv_id}",
        "/api/v1/investigations/{inv_id}/evidence-package",
        "/api/v1/investigations/{inv_id}/ai-analysis",
        "/api/v1/investigations/{inv_id}/ai-followup",
        "/api/v1/ai-runs/{run_id}", "/api/v1/auth/logout-all",
        "/api/v1/replay/{scenario_id}",
        "/api/v1/simulations", "/api/v1/cases", "/api/v1/cases/{case_id}",
        "/api/v1/cases/{case_id}/decisions", "/api/v1/cases/{case_id}/audit",
        "/api/v1/events",
    ]:
        assert expected in paths, expected


def test_full_judge_flow_direct(tmp_store, monkeypatch):
    monkeypatch.setattr(ai_adapter, "MODEL_API_KEY", "")
    result = main.platform_reset(_req(), {"scenario_id": "scn_primary"})
    assert result["manifest"]["synthetic_notice"] == "Synthetic data."

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
    package = main.build_evidence_package("inv_84721", _req())
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
        assert "Synthetic data" in html
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


def _pump(coro):
    try:
        coro.send(None)
    except StopIteration as exc:
        return exc.value
    raise AssertionError("coroutine suspended on real I/O")


def test_unknown_ids_404_direct(tmp_store):
    """J3-P9: every unknown-identifier read fails closed with its code."""
    cases = [
        (main.get_investigation, ("inv_nope",), "UNKNOWN_INVESTIGATION"),
        (main.build_evidence_package, ("inv_nope", _req()),
         "UNKNOWN_INVESTIGATION"),
        (main.get_case, ("case_nope",), "CASE_NOT_FOUND"),
        (main.case_audit, ("case_nope",), "CASE_NOT_FOUND"),
        (main.get_transaction, ("txn_nope",), "UNKNOWN_TRANSACTION"),
        (main.get_graph, ("txn_nope",), "UNKNOWN_TRANSACTION"),
        (main.get_risk, ("txn_nope",), "UNKNOWN_TRANSACTION"),
        (main.get_replay, ("scn_nope",), "UNKNOWN_SCENARIO"),
        (main.get_ai_run, ("agentrun_9999",), "UNKNOWN_RUN"),
    ]
    for fn, args, code in cases:
        with pytest.raises(main.AppError) as exc:
            fn(*args)
        assert (exc.value.code, exc.value.status) == (code, 404), fn.__name__


def test_risk_bogus_scope_400_direct(tmp_store):
    with pytest.raises(main.AppError) as exc:
        main.get_risk("txn_84721", scope="bogus")
    assert (exc.value.code, exc.value.status) == ("UNKNOWN_SCOPE", 400)


def test_ai_endpoints_validate_before_model_call(tmp_store, monkeypatch):
    """J3-P9: unknown-inv + bad followup bodies 404/400 pre-provider."""
    from app import ai_adapter

    monkeypatch.setattr(ai_adapter, "MODEL_API_KEY", "")
    with pytest.raises(main.AppError) as exc:
        _pump(main.ai_analysis("inv_nope", _req()))
    assert exc.value.code == "UNKNOWN_INVESTIGATION"
    with pytest.raises(main.AppError) as exc:
        _pump(main.ai_followup("inv_nope", {"question": "q?"}, _req()))
    assert exc.value.code == "UNKNOWN_INVESTIGATION"
    with pytest.raises(main.AppError) as exc:
        _pump(main.ai_followup("inv_84721", {"question": "  "}, _req()))
    assert (exc.value.code, exc.value.status) == ("QUESTION_REQUIRED", 400)
    with pytest.raises(main.AppError) as exc:
        _pump(main.ai_followup(
            "inv_84721", {"question": "q" * 2001}, _req()))
    assert (exc.value.code, exc.value.status) == ("QUESTION_TOO_LONG", 400)


def test_simulation_and_decision_domain_errors_direct(tmp_store):
    with pytest.raises(main.AppError) as exc:
        main.post_simulation({"target_transaction_id": "txn_nope",
                              "ignored_edge_ids": [], "assumption": "a"},
                             _req())
    assert exc.value.status == 404
    with pytest.raises(main.AppError) as exc:
        main.post_simulation({"target_transaction_id": "txn_84721",
                              "ignored_edge_ids": ["edge_nope"],
                              "assumption": "a"}, _req())
    assert (exc.value.code, exc.value.status) == ("UNKNOWN_EDGE", 404)
    with pytest.raises(main.AppError) as exc:
        main.post_decision("case_nope", {"decision": "Escalate",
                                         "reason": "r"}, _req())
    assert (exc.value.code, exc.value.status) == ("CASE_NOT_FOUND", 404)
    with pytest.raises(main.AppError) as exc:
        main.post_decision("case_84721", {"decision": "CONFIRM",
                                          "reason": "r"}, _req())
    assert (exc.value.code, exc.value.status) == ("INVALID_DECISION", 400)


def test_platform_reset_unknown_scenario_404_direct(tmp_store):
    # J3 closeout (backend EV2): reset payload errors fail closed.
    with pytest.raises(main.AppError) as exc:
        main.platform_reset(_req(), {"scenario_id": "scn_nope"})
    assert (exc.value.code, exc.value.status) == ("UNKNOWN_SCENARIO", 404)
    with pytest.raises(main.AppError) as exc:
        main.platform_start("scn_nope", _req())
    assert (exc.value.code, exc.value.status) == ("UNKNOWN_SCENARIO", 404)


def test_ai_run_read_roundtrip_direct(tmp_store):
    # J3 closeout (AI EV21): a persisted run reads back by ID.
    tmp_store.save_ai_run({"agent_run_id": "agentrun_42",
                           "status": "SUCCEEDED"})
    run = main.get_ai_run("agentrun_42")
    assert run["status"] == "SUCCEEDED"


def test_ready_envelope_direct(tmp_store):
    # J3 closeout (backend EV0): readiness contract without sockets.
    response = main.ready()
    assert response.status_code == 200
    body = json.loads(response.body.decode("utf-8"))
    assert body["ready"] is True
    assert body["store"] is True
    assert body["backend"] == "json"
