"""UFI AI slice: governed intel tools + evidence-grounded reports."""
from __future__ import annotations

import json

import pytest
from starlette.requests import Request

import app.main as main
from app import agents as agents_mod
from app import auth as auth_mod
from app import config as config_mod
from app import tenancy as tenancy_mod

SECRET = "test-secret-not-a-real-credential"
RECORD = auth_mod.hash_password("demo-pass-1")


def _users(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "")
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:investigator:%s,boss:admin:%s" % (RECORD, RECORD))


def _req():
    cookie = auth_mod.create_session("judge", "investigator", SECRET)
    return Request({"type": "http", "method": "POST", "scheme": "http",
                    "server": ("t", 80), "client": ("9.9.9.9", 1234),
                    "path": "/x", "query_string": b"",
                    "headers": [(b"host", b"t"),
                                (b"cookie",
                                 ("csai_session=%s" % cookie).encode()),
                                (b"x-requested-with",
                                 b"XMLHttpRequest")]})


def _ctx(tenant="org_primary"):
    return tenancy_mod.TenantContext(tenant_id=tenant, actor="judge")


def _subject():
    return {"kind": "session", "user": "judge",
            "role": "investigator", "tenant": "org_primary"}


def test_tool_catalogue_lists_intel_tools():
    tools = agents_mod.tools()
    for name in ("trace.read", "typology.match", "monitoring.status",
                 "industry.coverage", "report.build"):
        assert name in tools


def test_typology_match_binds_real_signals(tmp_store):
    out = agents_mod._tool_typology_match(
        tmp_store, {"typology_id": "T-01"}, _ctx())
    assert out["typology_id"] == "T-01"
    assert out["matched_count"] == len(out["signals"])
    gap = agents_mod._tool_typology_match(
        tmp_store, {"typology_id": "T-25"}, _ctx())
    assert gap["detection_gap"] is True
    assert gap["matched_count"] == 0
    with pytest.raises(ValueError):
        agents_mod._tool_typology_match(
            tmp_store, {"typology_id": "T-99"}, _ctx())


def test_trace_read_tenant_checked(tmp_store):
    trace = {"trace_id": "trace_x", "origin_transaction": "t1",
             "movements": [], "visited_transactions": ["t1"],
             "limitations": [], "tenant_id": "org_primary"}
    tmp_store.trace_save(trace)
    hit = agents_mod._tool_trace_read(
        tmp_store, {"trace_id": "trace_x"}, _ctx())
    assert hit["found"] is True
    miss = agents_mod._tool_trace_read(
        tmp_store, {"trace_id": "trace_x"}, _ctx("org_other"))
    assert miss["found"] is False
    assert agents_mod._tool_trace_read(
        tmp_store, {"trace_id": "nope"}, _ctx())["found"] is False


def test_monitoring_status_tool(tmp_store):
    out = agents_mod._tool_monitoring_status(tmp_store, {}, _ctx())
    assert out["mode"] == "on-demand-evaluation"
    assert out["tenant_scope"] == "org_primary"
    other = agents_mod._tool_monitoring_status(
        tmp_store, {}, _ctx("org_other"))
    assert other["transactions_visible"] == 0


def test_industry_coverage_tool(tmp_store):
    out = agents_mod._tool_industry_coverage(
        tmp_store, {"module_id": "banking"}, _ctx())
    assert out["coverage"]["industry_id"] == "banking"
    assert out["readiness"]["overall"] in ("READY", "NOT_READY")
    with pytest.raises(ValueError):
        agents_mod._tool_industry_coverage(
            tmp_store, {"module_id": "nope"}, _ctx())


def test_report_build_from_investigation(tmp_store):
    inv = tmp_store.state["investigations"][0]
    out = agents_mod._tool_report_build(
        tmp_store, {"report_type": "fraud_pattern",
                    "investigation_id": inv["investigation_id"]},
        _ctx())
    assert out["report_type"] == "fraud_pattern"
    assert out["tenant_scope"] == "org_primary"
    assert "signals" in out["sections"]
    assert "typologies" in out["sections"]
    with pytest.raises(ValueError):
        agents_mod._tool_report_build(
            tmp_store, {"report_type": "nope",
                        "investigation_id": inv["investigation_id"]},
            _ctx())
    with pytest.raises(ValueError):
        agents_mod._tool_report_build(
            tmp_store, {"report_type": "tracing",
                        "investigation_id": "inv_nope"},
            _ctx())


def test_report_build_cross_tenant_denied(tmp_store):
    inv = tmp_store.state["investigations"][0]
    with pytest.raises(ValueError):
        agents_mod._tool_report_build(
            tmp_store, {"report_type": "tracing",
                        "investigation_id": inv["investigation_id"]},
            _ctx("org_other"))


def test_propose_grants_and_denials(tmp_store, monkeypatch):
    _users(monkeypatch)
    plan, run = agents_mod.propose(
        tmp_store, "txn-intel", "typology.match",
        {"typology_id": "T-01"}, _subject())
    assert plan["tool"] == "typology.match"
    assert run is not None, "auto-approved agent runs immediately"
    with pytest.raises(ValueError):
        agents_mod.propose(tmp_store, "data-quality", "trace.read",
                           {"trace_id": "x"}, _subject())


def test_route_end_to_end_report(monkeypatch, tmp_store):
    _users(monkeypatch)
    inv = tmp_store.state["investigations"][0]
    body = json.loads(main.agent_propose(
        "case-assistant",
        {"tool": "report.build",
         "args": {"report_type": "transaction",
                  "investigation_id": inv["investigation_id"]}},
        _req()).body.decode())
    assert body["run"]["status"] == "OK"
    assert body["run"]["output"]["report_type"] == "transaction"
