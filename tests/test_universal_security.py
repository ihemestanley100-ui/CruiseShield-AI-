"""UFI security verification: tenancy, write gates, audit, validation,
masking. Socket-free direct handler invocation."""
from __future__ import annotations

import pytest
from starlette.requests import Request

import app.config as config_mod
import app.main as main
from app import tenancy as tenancy_mod


def _req():
    return Request({"type": "http", "method": "GET", "scheme": "http",
                    "server": ("t", 80), "client": ("9.9.9.9", 1234),
                    "path": "/x", "query_string": b"",
                    "headers": [(b"host", b"t")]})


def _other_tenant(monkeypatch):
    monkeypatch.setattr(
        main, "_request_ctx",
        lambda req: tenancy_mod.TenantContext(tenant_id="org_other",
                                              actor="intruder"))


def _signal_id():
    _, result = main._tenant_signals(_req())
    assert result["signals"], "seed signals required"
    return result["signals"][0]["signal_id"]


def _audits(action):
    return [a for a in main.store.state.get("audits", [])
            if isinstance(a, dict) and a.get("action") == action]


# -- tenant isolation -------------------------------------------------------
def test_cross_tenant_alerts_hidden(tmp_store, monkeypatch):
    opened = main.open_fraud_alert({"signal_id": _signal_id()}, _req())
    alert_id = opened["alert"]["id"]
    assert main.get_fraud_alert(alert_id, _req())["id"] == alert_id
    _other_tenant(monkeypatch)
    with pytest.raises(main.AppError):
        main.get_fraud_alert(alert_id, _req())
    assert main.list_fraud_alerts(_req())["alerts"] == []
    assert main.fraud_alert_metrics(_req())["tenant_total"] == 0
    with pytest.raises(main.AppError):
        main.move_fraud_alert(alert_id, {"status": "TRIAGED"}, _req())


def test_cross_tenant_traces_hidden(tmp_store, monkeypatch):
    txn_id = main.store.state["transactions"][0]["transaction_id"]
    trace = main.create_trace({"transaction_id": txn_id}, _req())
    _other_tenant(monkeypatch)
    with pytest.raises(main.AppError):
        main.get_trace(trace["trace_id"], _req())
    with pytest.raises(main.AppError):
        main.get_trace_movements(trace["trace_id"], _req())
    with pytest.raises(main.AppError):
        main.trace_relationships(trace["trace_id"], _req())


def test_cross_tenant_transactions_hidden(tmp_store, monkeypatch):
    txn_id = main.store.state["transactions"][0]["transaction_id"]
    _other_tenant(monkeypatch)
    assert main.list_transactions(_req())["total"] == 0
    with pytest.raises(main.AppError):
        main.transaction_parties(txn_id, _req())
    with pytest.raises(main.AppError):
        main.transaction_events(txn_id, _req())
    status = main.monitoring_status(_req())
    assert status["transactions_visible"] == 0
    assert status["alerts_open"] == 0


def test_unstamped_rows_default_tenant(tmp_store, monkeypatch):
    main.store.fraud_alert_save({"id": "legacy_row", "status": "NEW"})
    assert main.get_fraud_alert("legacy_row", _req())["id"] == "legacy_row"
    _other_tenant(monkeypatch)
    with pytest.raises(main.AppError):
        main.get_fraud_alert("legacy_row", _req())


# -- write gates --------------------------------------------------------------
def test_armed_writes_reject_anonymous(tmp_store, monkeypatch):
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "secret-token")
    with pytest.raises(main.AppError):
        main.open_fraud_alert({"signal_id": "s1"}, _req())
    with pytest.raises(main.AppError):
        main.create_trace({"transaction_id": "t1"}, _req())
    with pytest.raises(main.AppError):
        main.monitoring_evaluate(_req())
    with pytest.raises(main.AppError):
        main.create_report({"report_type": "tracing"}, _req())
    txn_id = main.store.state["transactions"][0]["transaction_id"]
    with pytest.raises(main.AppError):
        main.transaction_parties(txn_id, _req(), reveal=True)
    out = main.transaction_parties(txn_id, _req())
    assert all("reference_full" not in p for p in out["parties"])


# -- audit ----------------------------------------------------------------------
def test_sensitive_actions_audited(tmp_store):
    signal_id = _signal_id()
    opened = main.open_fraud_alert({"signal_id": signal_id}, _req())
    alert_id = opened["alert"]["id"]
    if opened["alert"]["status"] == "NEW":
        main.move_fraud_alert(alert_id, {"status": "TRIAGED"}, _req())
    txn_id = main.store.state["transactions"][0]["transaction_id"]
    main.create_trace({"transaction_id": txn_id}, _req())
    main.monitoring_evaluate(_req())
    main.create_report({"report_type": "tracing", "bundle": {}}, _req())
    main.transaction_parties(txn_id, _req(), reveal=True)
    assert _audits("fraud.alert.opened")
    assert _audits("trace.created")
    assert _audits("monitoring.evaluated")
    assert _audits("report.created")
    assert _audits("party.reveal")


# -- input validation -------------------------------------------------------------
def test_input_validation(tmp_store):
    with pytest.raises(main.AppError):
        main.create_trace({"transaction_id": "t1", "max_hops": "x"},
                          _req())
    big = {"k%d" % i: i for i in range(41)}
    with pytest.raises(main.AppError):
        main.create_report({"report_type": "tracing", "bundle": big},
                           _req())
    with pytest.raises(main.AppError):
        main.create_report({"report_type": "tracing", "bundle": []},
                           _req())
    with pytest.raises(main.AppError):
        main.open_fraud_alert({"signal_id": ""}, _req())
    with pytest.raises(main.AppError):
        main.move_fraud_alert("nope", {}, _req())
    out = main.list_transactions(_req(), limit=9999, offset=-5)
    assert out["limit"] == 200 and out["offset"] == 0


# -- masking / minimization ----------------------------------------------------------
def test_masked_by_default_no_secrets(tmp_store):
    txn_id = main.store.state["transactions"][0]["transaction_id"]
    out = main.transaction_parties(txn_id, _req())
    blob = repr(out).lower()
    for secret in ("cvv", "pin", "password", "private_key",
                   "recovery_phrase", "secret"):
        assert secret not in blob
    sender = next(p for p in out["parties"] if p["role"] == "SENDER")
    assert sender["reference_masked"] != "a1"
    txn = main.store.state["transactions"][0]
    assert "cvv" not in {k.lower() for k in txn}
