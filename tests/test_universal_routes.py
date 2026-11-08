"""UFI route tests: taxonomy, parties, typologies, alerts, tracing,
alt-payments, reports. Socket-free direct handler invocation."""
from __future__ import annotations

import pytest
from starlette.requests import Request

import app.main as main


def _req():
    return Request({"type": "http", "method": "GET", "scheme": "http",
                    "server": ("t", 80), "client": ("9.9.9.9", 1234),
                    "path": "/x", "query_string": b"",
                    "headers": [(b"host", b"t")]})


def test_payment_method_routes(tmp_store):
    out = main.list_payment_methods()
    assert len(out["methods"]) >= 13
    one = main.get_payment_method("nip_instant")
    assert one["family"] == "A"
    with pytest.raises(main.AppError):
        main.get_payment_method("nope")


def test_network_routes(tmp_store):
    nets = main.list_payment_networks()
    assert len(nets["networks"]) >= 8
    inst = main.list_institutions()
    assert inst["institutions"] == nets["networks"]


def test_parties_route_masked(tmp_store):
    txns = main.store.state.get("transactions", [])
    assert txns, "seed transactions required"
    txn_id = txns[0]["transaction_id"]
    out = main.transaction_parties(txn_id, _req())
    assert out["transaction_id"] == txn_id
    assert out["parties"]
    assert out["classification"]["method_id"]
    with pytest.raises(main.AppError):
        main.transaction_parties("nope", _req())


def test_parties_reveal_audited(tmp_store):
    txn_id = main.store.state["transactions"][0]["transaction_id"]
    out = main.transaction_parties(txn_id, _req(), reveal=True)
    assert all("reference_full" in p for p in out["parties"])


def test_typology_routes(tmp_store):
    out = main.list_typologies(_req())
    assert len(out["typologies"]) == 40
    one = main.get_typology("T-01", _req())
    assert one["matched_count"] >= 0
    assert isinstance(one["matched_signal_ids"], list)
    with pytest.raises(main.AppError):
        main.get_typology("T-99", _req())


def test_industry_typologies(tmp_store):
    out = main.industry_typologies("banking")
    assert out["typologies"]
    with pytest.raises(main.AppError):
        main.industry_typologies("nope")


def _signal_id():
    _, result = main._tenant_signals(_req())
    assert result["signals"], "seed signals required"
    return result["signals"][0]["signal_id"]


def test_alert_routes(tmp_store):
    signal_id = _signal_id()
    opened = main.open_fraud_alert({"signal_id": signal_id}, _req())
    assert opened["status"] in ("opened", "duplicate")
    alert_id = opened["alert"]["id"]
    dup = main.open_fraud_alert({"signal_id": signal_id}, _req())
    assert dup["status"] == "duplicate"
    listed = main.list_fraud_alerts(_req())
    assert any(a["id"] == alert_id for a in listed["alerts"])
    one = main.get_fraud_alert(alert_id, _req())
    assert one["signal_id"] == signal_id
    if one["status"] == "NEW":
        moved = main.move_fraud_alert(alert_id, {"status": "TRIAGED"},
                                      _req())
        assert moved["status"] == "TRIAGED"
    with pytest.raises(main.AppError):
        main.move_fraud_alert(alert_id, {"status": "CLOSED"}, _req())
    with pytest.raises(main.AppError):
        main.get_fraud_alert("nope", _req())
    metrics = main.fraud_alert_metrics(_req())
    assert metrics["tenant_total"] >= 1


def test_trace_routes(tmp_store):
    txn_id = main.store.state["transactions"][0]["transaction_id"]
    trace = main.create_trace({"transaction_id": txn_id}, _req())
    assert trace["origin_transaction"] == txn_id
    got = main.get_trace(trace["trace_id"], _req())
    assert got["trace_id"] == trace["trace_id"]
    legs = main.get_trace_movements(trace["trace_id"], _req())
    assert isinstance(legs["movements"], list)
    with pytest.raises(main.AppError):
        main.get_trace("nope", _req())
    with pytest.raises(main.AppError):
        main.create_trace({"transaction_id": "nope"}, _req())


def test_altpayments_and_reports(tmp_store):
    caps = main.altpayment_capabilities()
    assert caps["crypto"]["chain_data"] == "PROVIDER_UNAVAILABLE"
    rep = main.create_report(
        {"report_type": "fraud_pattern",
         "bundle": {"signals": [{"id": "s1"}]}}, _req())
    assert rep["sections"]["signals"] == [{"id": "s1"}]
    assert "typologies" in rep["evidence_gaps"]
    with pytest.raises(main.AppError):
        main.create_report({"report_type": "nope"}, _req())
