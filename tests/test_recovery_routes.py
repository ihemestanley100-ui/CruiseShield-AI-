"""Recovery OS routes + agent tools. Socket-free direct handlers."""
from __future__ import annotations

import pytest
from starlette.requests import Request

import app.main as main
from app import auth as auth_mod
from app import config as config_mod
from app import recovery_rules

SECRET = "test-secret-not-a-real-credential"
RECORD = auth_mod.hash_password("demo-pass-1")


def _users(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "")
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:investigator:%s,boss:admin:%s" % (RECORD, RECORD))


def _req(cookie=None):
    headers = [(b"host", b"t")]
    if cookie is not None:
        headers.append((b"cookie", ("csai_session=%s" % cookie).encode()))
    return Request({"type": "http", "method": "POST", "scheme": "http",
                    "server": ("t", 80), "client": ("9.9.9.9", 1234),
                    "path": "/x", "query_string": b"", "headers": headers})


def _inv():
    return auth_mod.create_session("judge", "investigator", SECRET)


def _adm():
    return auth_mod.create_session("boss", "admin", SECRET)


def _rule():
    base = {f: None for f in recovery_rules.FIELDS}
    base.update({"rule_id": "BANK-NG-001", "version": "2.0",
                 "scheme": "bank-rail", "transaction_type":
                 "nip_instant", "reason": "erroneous",
                 "verification_status": "VERIFIED",
                 "rule_source": "counsel memo 2026-11",
                 "effective_at": "2026-01-01", "window_days": 30,
                 "evidence_required": ["transaction-record"]})
    return base


def test_rules_routes(tmp_store, monkeypatch):
    _users(monkeypatch)
    out = main.list_recovery_rules(_req(_inv()))
    assert len(out["rules"]) == 10
    one = main.get_recovery_rule("TMPL-BANK-002", _req(_inv()))
    assert one["verification_status"] == "NOT_VERIFIED"
    with pytest.raises(main.AppError):
        main.get_recovery_rule("nope", _req(_inv()))
    created = main.register_recovery_rule(_rule(), _req(_adm()))
    assert created["rule_id"] == "BANK-NG-001"
    with pytest.raises(main.AppError):
        main.register_recovery_rule(_rule(), _req(_inv()))


def test_assess_route(tmp_store, monkeypatch):
    _users(monkeypatch)
    txn_id = main.store.state["transactions"][0]["transaction_id"]
    out = main.assess_recovery({"transaction_id": txn_id,
                                "reason": "erroneous"}, _req(_inv()))
    assert out["status"] in ("RULES_NOT_VERIFIED",
                             "UNSUPPORTED_PAYMENT_RAIL",
                             "NOT_ELIGIBLE")
    with pytest.raises(main.AppError):
        main.assess_recovery({"transaction_id": "nope",
                              "reason": "fraud"}, _req(_inv()))


def _drive_to_approval(tmp_store, monkeypatch):
    _users(monkeypatch)
    txn_id = main.store.state["transactions"][0]["transaction_id"]
    opened = main.open_recovery_case({"transaction_id": txn_id,
                                      "reason": "fraud"},
                                     _req(_inv()))
    rid = opened["case"]["recovery_id"]
    for state in ("TRANSACTION_VERIFIED", "ELIGIBILITY_ASSESSED",
                  "EVIDENCE_VALIDATED", "REQUEST_PREPARED",
                  "APPROVAL_PENDING"):
        main.move_recovery_case(rid, {"state": state}, _req(_inv()))
    return rid


def test_case_lifecycle_routes(tmp_store, monkeypatch):
    rid = _drive_to_approval(tmp_store, monkeypatch)
    with pytest.raises(main.AppError):
        main.move_recovery_case(rid, {"state": "APPROVED"},
                                _req(_inv()))
    row = main.move_recovery_case(rid, {"state": "APPROVED"},
                                  _req(_adm()))
    assert row["state"] == "APPROVED"
    ev = main.add_recovery_evidence(
        rid, {"kind": "transaction-record", "reference": "t1"},
        _req(_inv()))
    assert ev["evidence"]
    listed = main.list_recovery_cases(_req(_inv()))
    assert any(c["recovery_id"] == rid for c in listed["cases"])
    fetched = main.get_recovery_case(rid, _req(_inv()))
    assert fetched["recovery_id"] == rid


def test_submit_live_and_manual(tmp_store, monkeypatch):
    rid = _drive_to_approval(tmp_store, monkeypatch)
    main.move_recovery_case(rid, {"state": "APPROVED"}, _req(_adm()))
    with pytest.raises(main.AppError):
        main.submit_recovery_case(
            rid, {"channel": "live", "connector_id": "nip-transfer"},
            _req(_inv()))
    row = main.submit_recovery_case(rid, {"channel": "manual"},
                                    _req(_inv()))
    assert row["state"] == "UNDER_REVIEW"
    assert row["channel"] == "manual"
    main.declare_recovery_capability(
        {"connector_id": "nip-transfer", "capability": "recall",
         "evidence": "provider doc v3"}, _req(_adm()))
    rid2 = main.open_recovery_case(
        {"transaction_id": main.store.state["transactions"][0][
            "transaction_id"], "reason": "erroneous"},
        _req(_inv()))["case"]["recovery_id"]
    for state in ("TRANSACTION_VERIFIED", "ELIGIBILITY_ASSESSED",
                  "EVIDENCE_VALIDATED", "REQUEST_PREPARED",
                  "APPROVAL_PENDING"):
        main.move_recovery_case(rid2, {"state": state}, _req(_inv()))
    main.move_recovery_case(rid2, {"state": "APPROVED"}, _req(_adm()))
    live = main.submit_recovery_case(
        rid2, {"channel": "live", "connector_id": "nip-transfer"},
        _req(_inv()))
    assert live["state"] == "SUBMITTED_TO_PROVIDER"


def test_caps_and_metrics(tmp_store, monkeypatch):
    _users(monkeypatch)
    matrix = main.recovery_capability_matrix(_req(_inv()))
    assert len(matrix["matrix"]) == 33
    metrics = main.recovery_metrics(_req(_inv()))
    assert metrics["tenant_scope"] == "org_primary"
    with pytest.raises(main.AppError):
        main.declare_recovery_capability(
            {"connector_id": "x", "capability": "y",
             "evidence": "z"}, _req(_inv()))


def test_industry_recovery_route(tmp_store):
    out = main.industry_recovery_config("banking")
    assert len(out["workflows"]) == 6
    assert out["live_recovery_connectors"] == 0
    with pytest.raises(main.AppError):
        main.industry_recovery_config("nope")


def test_recovery_agent_tools(tmp_store, monkeypatch):
    _users(monkeypatch)
    from app import agents as agents_mod
    from app import tenancy as tenancy_mod
    ctx = tenancy_mod.TenantContext(tenant_id="org_primary",
                                    actor="judge")
    txn_id = tmp_store.state["transactions"][0]["transaction_id"]
    out = agents_mod._tool_recovery_eligibility(
        tmp_store, {"transaction_id": txn_id, "reason": "fraud"},
        ctx)
    assert out["status"]
    rules = agents_mod._tool_recovery_rules(tmp_store, {}, ctx)
    assert rules["count"] == 10
    one = agents_mod._tool_recovery_rules(
        tmp_store, {"rule_id": "TMPL-BANK-002"}, ctx)
    assert one["found"] is True
    track = agents_mod._tool_recovery_track(
        tmp_store, {"recovery_id": "recv_nope"}, ctx)
    assert track["found"] is False
    assert "recovery.eligibility" in agents_mod.get_manifest(
        "fund-recovery")["tools"]


def test_orchestrator_recovery_intent(tmp_store, monkeypatch):
    _users(monkeypatch)
    from app import orchestration as orch
    assert orch.classify("can this transfer be recalled?")[
        "intent"] == "RECOVERY"
    txn_id = tmp_store.state["transactions"][0]["transaction_id"]
    out = orch.start(tmp_store, "recover transaction " + txn_id,
                     {"kind": "session", "user": "judge",
                      "role": "investigator",
                      "tenant": "org_primary"},
                     args={"transaction_id": txn_id,
                           "reason": "fraud"})
    assert out["state"] == "COMPLETED"
    assert out["steps"][0]["tool"] == "recovery.eligibility"
