"""Tenant isolation across connector, governance, agent, transaction,
graph, risk, alert, notification, replay, ai-run, and simulation
surfaces.

Socket-free adversarial checks through the real handlers. The request
resolver seam is patched for beta requests because the D-014 user-map
is still owner-gated; this proves the enforcement wiring, not the map.
"""
import copy
import json

import pytest
from starlette.requests import Request

import app.main as main
from app import auth as auth_mod
from app import config as config_mod
from app import detection as det_mod
from app import governance as gov_mod
from app import tenancy as tenancy_mod
from app.tenancy import TenantContext

SECRET = "test-secret-not-a-real-credential"
RECORD = auth_mod.hash_password("demo-pass-1")
BETA = "org_beta"


@pytest.fixture(autouse=True)
def _beta():
    tenancy_mod.register_tenant(BETA)
    yield


def _users(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "")
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:investigator:%s,boss:admin:%s" % (RECORD, RECORD))


def _scope(path, method="GET", cookie=None, xrw=False):
    headers = [(b"host", b"t")]
    if cookie is not None:
        headers.append((b"cookie", ("csai_session=%s" % cookie).encode()))
    if xrw:
        headers.append((b"x-requested-with", b"XMLHttpRequest"))
    return {"type": "http", "method": method, "scheme": "http",
            "server": ("t", 80), "client": ("9.9.9.9", 1234),
            "path": path, "query_string": b"", "headers": headers}


def _sess(user, role):
    return auth_mod.create_session(user, role, SECRET)


def _ireq():
    return Request(_scope("/x", method="POST",
                          cookie=_sess("judge", "investigator"),
                          xrw=True))


def _areq():
    return Request(_scope("/x", method="POST",
                          cookie=_sess("boss", "admin"), xrw=True))


def _creq():
    return Request(_scope("/x", method="POST"))


def _pump(coro):
    try:
        coro.send(None)
    except StopIteration as exc:
        return exc.value
    raise AssertionError("coroutine suspended on real I/O")


def _body(resp):
    return json.loads(resp.body.decode())


def _as_beta(monkeypatch):
    monkeypatch.setattr(
        main, "_request_ctx",
        lambda request=None: TenantContext(tenant_id=BETA, actor="bob"))


def _beta_case(tmp_store):
    tmp_store.state["cases"].append(
        {"case_id": "case_beta", "investigation_id": "inv_84721",
         "status": "NEW", "tenant_id": BETA})


def test_legacy_connection_tenant_key_stays_owned():
    alpha = TenantContext(tenant_id=tenancy_mod.DEFAULT_TENANT,
                          actor="alice")
    beta = TenantContext(tenant_id=BETA, actor="bob")
    legacy = {"id": "conn_legacy", "tenant": BETA}
    assert tenancy_mod.tenant_of(legacy) == BETA
    assert tenancy_mod.enforce_read(legacy, alpha) is None
    assert tenancy_mod.enforce_read(legacy, beta) is legacy
    rows = [{"id": "a", "tenant": tenancy_mod.DEFAULT_TENANT}, legacy]
    assert [r["id"] for r in tenancy_mod.filter_visible(rows, beta)] == [
        "conn_legacy"]


def test_connections_are_tenant_scoped(tmp_store, monkeypatch):
    alpha = _body(main.connection_create(
        {"adapter": "loopback", "name": "alpha"}, _creq()))["id"]
    assert tmp_store.connection_get(alpha)["tenant_id"] == \
        tenancy_mod.DEFAULT_TENANT
    assert [c["id"] for c in main.connections_list()["connections"]] == [
        alpha]
    _as_beta(monkeypatch)
    beta = _body(main.connection_create(
        {"adapter": "loopback", "name": "beta"}, _creq()))["id"]
    assert tmp_store.connection_get(beta)["tenant_id"] == BETA
    assert [c["id"] for c in main.connections_list(_creq())[
        "connections"]] == [beta]
    assert [c["tenant"] for c in main.connections_list(_creq())[
        "connections"]] == [BETA]
    assert main.connection_detail(beta, _creq())["id"] == beta
    with pytest.raises(main.AppError) as exc:
        main.connection_detail(alpha, _creq())
    assert (exc.value.code, exc.value.status) == (
        "CONNECTION_NOT_FOUND", 404)
    with pytest.raises(main.AppError) as exc:
        main.connection_configure(alpha, {"params": {}}, _creq())
    assert exc.value.code == "CONNECTION_NOT_FOUND"


def test_sar_records_are_tenant_scoped(monkeypatch, tmp_store):
    _users(monkeypatch)
    alpha_case = tmp_store.state["cases"][0]["case_id"]
    alpha = _body(main.sar_create(
        {"case_id": alpha_case, "summary": "alpha trail"}, _ireq()))[
            "sar_id"]
    assert main.sar_list(_ireq())["count"] == 1
    _beta_case(tmp_store)
    _as_beta(monkeypatch)
    beta = _body(main.sar_create(
        {"case_id": "case_beta", "summary": "beta trail"}, _ireq()))[
            "sar_id"]
    assert tmp_store.sar_get(beta)["tenant_id"] == BETA
    assert [s["sar_id"] for s in main.sar_list(_ireq())["sars"]] == [beta]
    with pytest.raises(main.AppError) as exc:
        main.sar_transition(alpha, {"to": "IN_REVIEW"}, _ireq())
    assert (exc.value.code, exc.value.status) == ("SAR_NOT_FOUND", 404)
    with pytest.raises(main.AppError) as exc:
        main.sar_create({"case_id": alpha_case, "summary": "x"}, _ireq())
    assert exc.value.code == "CASE_NOT_FOUND"


def test_dsr_records_are_tenant_scoped(monkeypatch, tmp_store):
    _users(monkeypatch)
    alpha = _body(main.dsr_create(
        {"subject_ref": "ALPHA-1", "kind": "access", "details": ""},
        _ireq()))["dsr_id"]
    assert main.dsr_list(_ireq())["count"] == 1
    _as_beta(monkeypatch)
    beta = _body(main.dsr_create(
        {"subject_ref": "BETA-1", "kind": "access", "details": ""},
        _ireq()))["dsr_id"]
    assert tmp_store.dsr_get(beta)["tenant_id"] == BETA
    assert [d["dsr_id"] for d in main.dsr_list(_ireq())["dsrs"]] == [beta]
    with pytest.raises(main.AppError) as exc:
        main.dsr_transition(alpha, {"to": "VERIFYING"}, _ireq())
    assert (exc.value.code, exc.value.status) == ("DSR_NOT_FOUND", 404)


def test_holds_are_tenant_scoped(monkeypatch, tmp_store):
    _users(monkeypatch)
    alpha_case = tmp_store.state["cases"][0]["case_id"]
    alpha = _body(main.hold_place(
        {"resource_kind": "case", "resource_id": alpha_case,
         "reason": "alpha matter"}, _areq()))["hold_id"]
    assert main.hold_list(_areq())["count"] == 1
    _beta_case(tmp_store)
    _as_beta(monkeypatch)
    beta = _body(main.hold_place(
        {"resource_kind": "case", "resource_id": "case_beta",
         "reason": "beta matter"}, _areq()))["hold_id"]
    assert tmp_store.hold_get(beta)["tenant_id"] == BETA
    assert [h["hold_id"] for h in main.hold_list(_areq())[
        "holds"]] == [beta]
    with pytest.raises(main.AppError) as exc:
        main.hold_release(alpha, {"reason": "x"}, _areq())
    assert (exc.value.code, exc.value.status) == ("HOLD_NOT_FOUND", 404)
    assert gov_mod.is_held(tmp_store, "case", alpha_case,
                           tenancy_mod.DEFAULT_TENANT) is True
    assert gov_mod.is_held(tmp_store, "case", "case_beta", BETA) is True
    assert gov_mod.is_held(tmp_store, "case", alpha_case, BETA) is False


def test_agent_case_read_respects_tenant(monkeypatch, tmp_store):
    _users(monkeypatch)
    case_id = tmp_store.state["cases"][0]["case_id"]
    tmp_store.state["cases"][0]["tenant_id"] = BETA
    pending = json.loads(main.agent_propose(
        "fraud-detection", {"tool": "case.read",
                            "args": {"case_id": case_id}},
        _ireq()).body.decode())
    foreign = json.loads(main.agent_approve(
        pending["plan"]["plan_id"], _areq()).body.decode())
    assert foreign["run"]["status"] == "OK"
    assert foreign["run"]["output"] == {"found": False,
                                       "case_id": case_id}
    _as_beta(monkeypatch)
    own_pending = json.loads(main.agent_propose(
        "fraud-detection", {"tool": "case.read",
                            "args": {"case_id": case_id}},
        _ireq()).body.decode())
    own = json.loads(main.agent_approve(
        own_pending["plan"]["plan_id"], _areq()).body.decode())
    assert own["run"]["output"]["found"] is True
    assert own["run"]["tenant_id"] == BETA


def test_agent_cross_tenant_approval_is_not_found(monkeypatch,
                                                 tmp_store):
    _users(monkeypatch)
    case_id = tmp_store.state["cases"][0]["case_id"]
    plan_id = json.loads(main.agent_propose(
        "fraud-detection", {"tool": "case.read",
                            "args": {"case_id": case_id}},
        _ireq()).body.decode())["plan"]["plan_id"]
    _as_beta(monkeypatch)
    with pytest.raises(main.AppError) as exc:
        main.agent_approve(plan_id, _areq())
    assert (exc.value.code, exc.value.status) == (
        "AGENT_PLAN_UNKNOWN", 404)


def test_agent_runs_are_tenant_scoped(monkeypatch, tmp_store):
    _users(monkeypatch)
    main.agent_propose("txn-intel", {"tool": "signal.search",
                                    "args": {"limit": 1}}, _ireq())
    assert main.agent_runs(_ireq())["count"] == 1
    _as_beta(monkeypatch)
    main.agent_propose("txn-intel", {"tool": "signal.search",
                                    "args": {"limit": 1}}, _ireq())
    beta = main.agent_runs(_ireq())
    assert beta["count"] == 1
    assert beta["runs"][0]["tenant_id"] == BETA


def test_agent_signal_search_respects_tenant(monkeypatch, tmp_store):
    _users(monkeypatch)
    foreign = copy.deepcopy(tmp_store.state["transactions"][0])
    foreign["transaction_id"] = "txn_beta"
    foreign["tenant_id"] = BETA
    tmp_store.state["transactions"].append(foreign)
    default = json.loads(main.agent_propose(
        "txn-intel", {"tool": "signal.search",
                     "args": {"limit": 200}}, _ireq()).body.decode())
    assert "txn_beta" not in {
        s["transaction_id"] for s in default["run"]["output"]["signals"]}
    _as_beta(monkeypatch)
    beta = json.loads(main.agent_propose(
        "txn-intel", {"tool": "signal.search",
                     "args": {"limit": 200}}, _ireq()).body.decode())
    expected = det_mod.evaluate_all([foreign],
                                    tmp_store.state["edges"])["signals"]
    assert beta["run"]["output"]["total"] == len(expected)
    assert {s["transaction_id"]
            for s in beta["run"]["output"]["signals"]} <= {"txn_beta"}


def test_agent_evidence_read_respects_tenant(monkeypatch, tmp_store):
    _users(monkeypatch)
    inv_id = tmp_store.state["investigations"][0]["investigation_id"]
    tmp_store.state["investigations"][0]["tenant_id"] = BETA
    foreign = json.loads(main.agent_propose(
        "evidence-analyst", {"tool": "evidence.read",
                             "args": {"package_id": inv_id}},
        _ireq()).body.decode())
    assert foreign["run"]["output"] == {"found": False,
                                       "package_id": inv_id}
    _as_beta(monkeypatch)
    own = json.loads(main.agent_propose(
        "evidence-analyst", {"tool": "evidence.read",
                             "args": {"package_id": inv_id}},
        _ireq()).body.decode())
    assert own["run"]["output"]["found"] is True


def test_agent_connector_read_respects_tenant(monkeypatch, tmp_store):
    _users(monkeypatch)
    alpha = _body(main.connection_create(
        {"adapter": "loopback", "name": "alpha"}, _creq()))["id"]
    foreign = json.loads(main.agent_propose(
        "data-quality", {"tool": "connector.read",
                         "args": {"connection_id": alpha}},
        _ireq()).body.decode())
    assert foreign["run"]["output"]["found"] is True
    _as_beta(monkeypatch)
    denied = json.loads(main.agent_propose(
        "data-quality", {"tool": "connector.read",
                         "args": {"connection_id": alpha}},
        _ireq()).body.decode())
    assert denied["run"]["output"] == {"found": False,
                                      "connection_id": alpha}
    beta = _body(main.connection_create(
        {"adapter": "loopback", "name": "beta"}, _creq()))["id"]
    own = json.loads(main.agent_propose(
        "data-quality", {"tool": "connector.read",
                         "args": {"connection_id": beta}},
        _ireq()).body.decode())
    assert own["run"]["output"]["found"] is True


def test_agent_graph_read_uses_visible_events(monkeypatch, tmp_store):
    _users(monkeypatch)
    foreign = copy.deepcopy(tmp_store.state["transactions"][0])
    foreign["transaction_id"] = "txn_beta"
    foreign["tenant_id"] = BETA
    tmp_store.state["transactions"].append(foreign)
    root = foreign["sender_account_id"]
    default = json.loads(main.agent_propose(
        "graph-investigator", {"tool": "graph.neighbors",
                               "args": {"node_id": root}},
        _ireq()).body.decode())["run"]["output"]
    assert default["edges"]
    _as_beta(monkeypatch)
    beta = json.loads(main.agent_propose(
        "graph-investigator", {"tool": "graph.neighbors",
                               "args": {"node_id": root}},
        _ireq()).body.decode())["run"]["output"]
    assert beta["edges"] == []
    assert "dev_04" not in {n["node_id"] for n in beta["nodes"]}


def _beta_txn(tmp_store):
    foreign = copy.deepcopy(tmp_store.state["transactions"][0])
    foreign.update(transaction_id="txn_beta", tenant_id=BETA,
                   amount_minor=1000000, receiver_account_id="acct_Z",
                   device_id=None, phone_id=None, ip_id=None,
                   location_id=None, merchant_id=None)
    tmp_store.state["transactions"].append(foreign)
    return foreign


def test_transaction_read_is_tenant_scoped(tmp_store, monkeypatch):
    alpha = tmp_store.state["transactions"][0]["transaction_id"]
    assert main.get_transaction(alpha)["transaction"][
        "transaction_id"] == alpha
    _beta_txn(tmp_store)
    _as_beta(monkeypatch)
    with pytest.raises(main.AppError) as exc:
        main.get_transaction(alpha)
    assert (exc.value.code, exc.value.status) == (
        "UNKNOWN_TRANSACTION", 404)
    assert main.get_transaction("txn_beta")["transaction"][
        "transaction_id"] == "txn_beta"


def test_risk_assessment_uses_visible_inputs(tmp_store, monkeypatch):
    alpha = tmp_store.state["transactions"][0]["transaction_id"]
    _beta_txn(tmp_store)
    _as_beta(monkeypatch)
    with pytest.raises(main.AppError) as exc:
        main.get_risk(alpha, scope="transaction")
    assert exc.value.code == "UNKNOWN_TRANSACTION"
    beta = main.get_risk("txn_beta", scope="transaction")
    rules = {r["rule_id"]: r for r in beta["rule_results"]}
    assert rules["R-002"]["triggered"] is False
    assert rules["R-002"]["observed_values"][
        "sender_outgoing_120m"] == 1


def test_graph_read_is_tenant_scoped(tmp_store, monkeypatch):
    alpha = tmp_store.state["transactions"][0]["transaction_id"]
    default = main.get_graph(alpha)
    assert default["counts"] == {"nodes": 22, "edges": 30}
    assert default["provenance_errors"] == []
    _beta_txn(tmp_store)
    _as_beta(monkeypatch)
    with pytest.raises(main.AppError) as exc:
        main.get_graph(alpha)
    assert (exc.value.code, exc.value.status) == (
        "UNKNOWN_TRANSACTION", 404)
    beta = main.get_graph("txn_beta")
    assert beta["transaction_id"] == "txn_beta"
    assert beta["edges"] == []
    assert beta["provenance_errors"] == []
    assert "dev_04" not in {n["node_id"] for n in beta["nodes"]}


def _second_alert(tmp_store):
    tmp_store.state["alerts"].append(
        {"alert_id": "alert_84722", "transaction_id": "txn_84722",
         "status": "OPEN", "title": "second",
         "created_at": "2026-10-27T11:00:00Z"})


def test_alerts_are_tenant_scoped(tmp_store, monkeypatch):
    assert len(main.list_alerts()["alerts"]) == 1
    _second_alert(tmp_store)
    assert len(main.list_alerts()["alerts"]) == 2
    tmp_store.get_transaction("txn_84721")["tenant_id"] = BETA
    assert [a["alert_id"]
            for a in main.list_alerts()["alerts"]] == ["alert_84722"]
    _as_beta(monkeypatch)
    beta = main.list_alerts(_creq())["alerts"]
    assert [a["alert_id"] for a in beta] == ["alert_84721"]


def test_notifications_are_tenant_scoped(tmp_store, monkeypatch):
    _second_alert(tmp_store)
    assert main.list_notifications(_creq())["unread_count"] == 2
    tmp_store.get_transaction("txn_84721")["tenant_id"] = BETA
    assert main.list_notifications(_creq())["unread_count"] == 1
    _as_beta(monkeypatch)
    beta = main.list_notifications(_creq())
    assert beta["unread_count"] == 1
    assert [n["notification_id"]
            for n in beta["notifications"]] == ["alert_84721"]


def test_mark_all_read_ignores_foreign_alerts(tmp_store, monkeypatch):
    _second_alert(tmp_store)
    tmp_store.get_transaction("txn_84721")["tenant_id"] = BETA
    _as_beta(monkeypatch)
    body = main.mark_notifications_read({"all": True}, _creq())
    assert body["marked"] == ["alert_84721"]


def _all_txns_beta(tmp_store):
    for txn in tmp_store.state["transactions"]:
        txn["tenant_id"] = BETA


def test_device_ip_geo_intel_are_tenant_scoped(tmp_store, monkeypatch):
    assert main.get_device("dev_04")["device_id"] == "dev_04"
    assert main.get_ip_observations("ip_02")["ip_label"] == "ip_02"
    assert main.get_geo_observations("loc_01")["kind"] == "fixture_label"
    _all_txns_beta(tmp_store)
    with pytest.raises(main.AppError) as exc:
        main.get_device("dev_04")
    assert exc.value.code == "UNKNOWN_DEVICE"
    with pytest.raises(main.AppError) as exc:
        main.get_ip_observations("ip_02")
    assert exc.value.code == "UNKNOWN_IP_LABEL"
    with pytest.raises(main.AppError) as exc:
        main.get_geo_observations("loc_01")
    assert exc.value.code == "UNKNOWN_GEO_IDENTIFIER"
    _as_beta(monkeypatch)
    assert main.get_device("dev_04", _creq())["device_id"] == "dev_04"
    assert main.get_ip_observations("ip_02", _creq())[
        "ip_label"] == "ip_02"
    assert main.get_geo_observations("loc_01", _creq())[
        "kind"] == "fixture_label"


def test_link_intel_is_tenant_scoped(tmp_store, monkeypatch):
    assert main.get_transaction_intel(
        "txn_84721")["transaction_id"] == "txn_84721"
    tmp_store.get_transaction("txn_84721")["tenant_id"] = BETA
    with pytest.raises(main.AppError) as exc:
        main.get_transaction_intel("txn_84721")
    assert exc.value.code == "UNKNOWN_TRANSACTION"
    _as_beta(monkeypatch)
    with pytest.raises(main.AppError) as exc:
        main.get_transaction_intel("txn_84722", _creq())
    assert exc.value.code == "UNKNOWN_TRANSACTION"
    own = main.get_transaction_intel("txn_84721", _creq())
    assert own["transaction_id"] == "txn_84721"
    acct = main.get_account_intel("acct_A", _creq())
    assert acct["transaction_ids"] == ["txn_84721"]
    with pytest.raises(main.AppError) as exc:
        main.get_investigation_intel("inv_84721", _creq())
    assert exc.value.code == "UNKNOWN_INVESTIGATION"
    tmp_store.get_investigation("inv_84721")["tenant_id"] = BETA
    mine = main.get_investigation_intel("inv_84721", _creq())
    assert mine["investigation_id"] == "inv_84721"
    assert mine["transaction_intel"]["transaction_id"] == "txn_84721"


def test_graph_overlay_is_tenant_scoped(tmp_store, monkeypatch):
    assert main.get_graph_overlay(
        "txn_84721")["transaction_id"] == "txn_84721"
    tmp_store.get_transaction("txn_84721")["tenant_id"] = BETA
    with pytest.raises(main.AppError) as exc:
        main.get_graph_overlay("txn_84721")
    assert exc.value.code == "UNKNOWN_TRANSACTION"
    _as_beta(monkeypatch)
    assert main.get_graph_overlay("txn_84721", _creq())[
        "transaction_id"] == "txn_84721"


def test_risk_intel_is_tenant_scoped(tmp_store, monkeypatch):
    monkeypatch.setenv("RISK_INTELLIGENCE_V2_ENABLED", "true")
    assert main.get_risk_intelligence(
        "txn_84721")["subject"]["id"] == "txn_84721"
    tmp_store.get_transaction("txn_84721")["tenant_id"] = BETA
    with pytest.raises(main.AppError) as exc:
        main.get_risk_intelligence("txn_84721")
    assert exc.value.code == "UNKNOWN_RISK_INTEL_SUBJECT"
    _as_beta(monkeypatch)
    assert main.get_risk_intelligence("txn_84721", _creq())[
        "subject"]["id"] == "txn_84721"


def test_intel_evidence_is_tenant_scoped(tmp_store, monkeypatch):
    monkeypatch.setenv("RISK_INTELLIGENCE_V2_ENABLED", "true")
    assert main.get_intel_evidence(
        "inv_84721")["investigation_id"] == "inv_84721"
    tmp_store.get_investigation("inv_84721")["tenant_id"] = BETA
    with pytest.raises(main.AppError) as exc:
        main.get_intel_evidence("inv_84721")
    assert exc.value.code == "UNKNOWN_INVESTIGATION"
    _as_beta(monkeypatch)
    assert main.get_intel_evidence("inv_84721", _creq())[
        "investigation_id"] == "inv_84721"


def _ai_run_dict(run_id, package_id, tenant=None):
    run = {"agent_run_id": run_id, "evidence_package_id": package_id,
           "status": "SUCCEEDED", "model_id": "meta-test",
           "prompt_version": "v1", "schema_validation_status": "VALIDATED",
           "evidence_reference_validation_status": "VALIDATED",
           "latency_ms": 5, "completed_at": "2026-11-06T00:00:00Z",
           "result": {"summary": "s", "conclusion": "requires_review",
                      "key_findings": []}}
    if tenant is not None:
        run["tenant_id"] = tenant
    return run


def _seed_ai_runs(tmp_store):
    pkg_id = tmp_store.state["evidence_packages"]["inv_84721"][
        "package_id"]
    tmp_store.state["ai_runs"].append(_ai_run_dict("agentrun_0001", pkg_id))
    tmp_store.state["ai_runs"].append(
        _ai_run_dict("agentrun_0002", pkg_id, BETA))
    return pkg_id


def test_replay_is_tenant_scoped(tmp_store, monkeypatch):
    full = main.get_replay("scn_primary", cursor=11)
    assert full["total"] == 11
    assert full["counts"]["events"] == 11
    assert "txn_84721" in full["cumulative_transaction_ids"]
    tmp_store.get_transaction("txn_84721")["tenant_id"] = BETA
    default = main.get_replay("scn_primary", cursor=11)
    assert default["total"] == 10
    assert "txn_84721" not in default["cumulative_transaction_ids"]
    _as_beta(monkeypatch)
    beta = main.get_replay("scn_primary", cursor=11, request=_creq())
    assert beta["total"] == 1
    assert beta["cumulative_transaction_ids"] == ["txn_84721"]
    with pytest.raises(main.AppError) as exc:
        main.get_replay("scn_nope", cursor=0, request=_creq())
    assert (exc.value.code, exc.value.status) == (
        "UNKNOWN_SCENARIO", 404)


def test_ai_runs_are_tenant_scoped(tmp_store, monkeypatch):
    _seed_ai_runs(tmp_store)
    assert main.get_ai_run("agentrun_0001")[
        "agent_run_id"] == "agentrun_0001"
    with pytest.raises(main.AppError) as exc:
        main.get_ai_run("agentrun_0002")
    assert (exc.value.code, exc.value.status) == ("UNKNOWN_RUN", 404)
    _as_beta(monkeypatch)
    assert main.get_ai_run("agentrun_0002", _creq())[
        "agent_run_id"] == "agentrun_0002"
    with pytest.raises(main.AppError) as exc:
        main.get_ai_run("agentrun_0001", _creq())
    assert exc.value.code == "UNKNOWN_RUN"
    with pytest.raises(main.AppError) as exc:
        main.get_ai_run("agentrun_9999", _creq())
    assert exc.value.code == "UNKNOWN_RUN"


def test_ai_analysis_rejects_foreign_investigation(tmp_store, monkeypatch):
    with pytest.raises(main.AppError) as exc:
        _pump(main.ai_analysis("inv_84721", _creq()))
    assert exc.value.code == "MODEL_NOT_CONFIGURED"
    _as_beta(monkeypatch)
    with pytest.raises(main.AppError) as exc:
        _pump(main.ai_analysis("inv_84721", _creq()))
    assert (exc.value.code, exc.value.status) == (
        "UNKNOWN_INVESTIGATION", 404)
    with pytest.raises(main.AppError) as exc:
        _pump(main.ai_followup("inv_84721", {"question": "probe"},
                               _creq()))
    assert exc.value.code == "UNKNOWN_INVESTIGATION"
    tmp_store.get_investigation("inv_84721")["tenant_id"] = BETA
    tmp_store.get_transaction("txn_84721")["tenant_id"] = BETA
    with pytest.raises(main.AppError) as exc:
        _pump(main.ai_analysis("inv_84721", _creq()))
    assert exc.value.code == "MODEL_NOT_CONFIGURED"
    del tmp_store.get_transaction("txn_84721")["tenant_id"]
    with pytest.raises(main.AppError) as exc:
        _pump(main.ai_analysis("inv_84721", _creq()))
    assert exc.value.code == "UNKNOWN_INVESTIGATION"


def test_ai_run_stamping_on_success_and_failure(tmp_store, monkeypatch):
    from app import ai_adapter
    from app.models import EvidencePackage

    package = EvidencePackage.model_validate(
        tmp_store.state["evidence_packages"]["inv_84721"])

    async def stub_ok(package, summary, trace_id, run_id, **kwargs):
        return {"agent_run_id": run_id, "model_id": "stub",
                "status": "SUCCEEDED",
                "schema_validation_status": "VALIDATED",
                "evidence_reference_validation_status": "VALIDATED"}

    monkeypatch.setattr(ai_adapter, "analyze", stub_ok)
    beta_ctx = TenantContext(tenant_id=BETA, actor="bob")
    run = _pump(main._run_ai(package, "summary", "agentrun_0001",
                             "trace_stamp", ctx=beta_ctx))
    assert run["tenant_id"] == BETA
    assert tmp_store.state["ai_runs"][-1]["tenant_id"] == BETA
    run2 = _pump(main._run_ai(package, "summary", "agentrun_0002",
                              "trace_compat"))
    assert "tenant_id" not in run2
    assert main.get_ai_run("agentrun_0002")[
        "agent_run_id"] == "agentrun_0002"

    async def stub_fail(*args, **kwargs):
        raise ai_adapter.AIError("MODEL_NOT_CONFIGURED", "no key")

    monkeypatch.setattr(ai_adapter, "analyze", stub_fail)
    with pytest.raises(main.AppError):
        _pump(main._run_ai(package, "summary", "agentrun_0003",
                           "trace_fail", ctx=beta_ctx))
    assert tmp_store.state["ai_runs"][-1]["tenant_id"] == BETA
    assert tmp_store.state["ai_runs"][-1]["status"] == "FAILED"


def _sim_body(txn="txn_84721", ignored=None):
    return {"target_transaction_id": txn,
            "ignored_edge_ids": [] if ignored is None else ignored,
            "assumption": "test what-if"}


def _greq():
    return Request({"type": "http", "method": "GET", "headers": [],
                    "path": "/"})


def test_latest_ai_run_respects_tenant(tmp_store, monkeypatch):
    _seed_ai_runs(tmp_store)
    case = tmp_store.state["cases"][0]
    assert main.latest_ai_run_for_case(case)[
        "agent_run_id"] == "agentrun_0002"
    default_ctx = TenantContext(
        tenant_id=tenancy_mod.DEFAULT_TENANT, actor="alice")
    assert main.latest_ai_run_for_case(case, default_ctx)[
        "agent_run_id"] == "agentrun_0001"
    beta_ctx = TenantContext(tenant_id=BETA, actor="bob")
    assert main.latest_ai_run_for_case(case, beta_ctx)[
        "agent_run_id"] == "agentrun_0002"
    assert main.get_case("case_84721")["latest_ai_run"][
        "agent_run_id"] == "agentrun_0001"
    _as_beta(monkeypatch)
    with pytest.raises(main.AppError) as exc:
        main.get_case("case_84721", _creq())
    assert exc.value.code == "CASE_NOT_FOUND"
    tmp_store.state["cases"][0]["tenant_id"] = BETA
    tmp_store.get_investigation("inv_84721")["tenant_id"] = BETA
    mine = main.get_case("case_84721", _creq())
    assert mine["latest_ai_run"]["agent_run_id"] == "agentrun_0002"


def test_simulations_are_tenant_scoped(tmp_store, monkeypatch):
    sim = main.post_simulation(_sim_body(), _creq())
    assert sim["simulation_id"] == "sim_0001"
    assert tmp_store.state["simulations"][-1]["tenant_id"] == \
        tenancy_mod.DEFAULT_TENANT
    tmp_store.get_transaction("txn_84721")["tenant_id"] = BETA
    with pytest.raises(main.AppError) as exc:
        main.post_simulation(_sim_body(), _creq())
    assert (exc.value.code, exc.value.status) == (
        "UNKNOWN_TRANSACTION", 404)
    _as_beta(monkeypatch)
    mine = main.post_simulation(_sim_body(), _creq())
    assert mine["simulation_id"] == "sim_0002"
    assert mine["tenant_id"] == BETA
    with pytest.raises(main.AppError) as exc:
        main.post_simulation(_sim_body("txn_84722"), _creq())
    assert exc.value.code == "UNKNOWN_TRANSACTION"
    with pytest.raises(main.AppError) as exc:
        main.post_simulation(_sim_body("txn_nope"), _creq())
    assert exc.value.code == "UNKNOWN_TRANSACTION"


def test_simulation_inputs_are_view_scoped(tmp_store, monkeypatch):
    base = main.post_simulation(_sim_body(ignored=["edge_0001"]), _creq())
    assert base["ignored_edge_ids"] == ["edge_0001"]
    tmp_store.get_transaction("txn_84721")["tenant_id"] = BETA
    _as_beta(monkeypatch)
    mine = main.post_simulation(_sim_body(ignored=["edge_0001"]), _creq())
    assert mine["tenant_id"] == BETA
    assert mine["ignored_edge_ids"] == ["edge_0001"]
    with pytest.raises(main.AppError) as exc:
        main.post_simulation(_sim_body(ignored=["edge_0004"]), _creq())
    assert (exc.value.code, exc.value.status) == ("UNKNOWN_EDGE", 404)


def test_investigation_page_simulations_respect_tenant(tmp_store,
                                                       monkeypatch):
    main.post_simulation(_sim_body(), _creq())
    tmp_store.get_transaction("txn_84721")["tenant_id"] = BETA
    tmp_store.get_investigation("inv_84721")["tenant_id"] = BETA
    with pytest.raises(main.AppError) as exc:
        main.investigation_page(_greq(), "inv_84721")
    assert exc.value.code == "UNKNOWN_INVESTIGATION"
    _as_beta(monkeypatch)
    main.post_simulation(_sim_body(), _creq())
    sims = tmp_store.state["simulations"]
    assert [s["simulation_id"] for s in sims] == ["sim_0001", "sim_0002"]
    beta_ctx = TenantContext(tenant_id=BETA, actor="bob")
    assert [s["simulation_id"]
            for s in tenancy_mod.filter_visible(sims, beta_ctx)] == [
                "sim_0002"]
    page = main.investigation_page(_greq(), "inv_84721")
    assert page.status_code == 200
