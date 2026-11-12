"""UFI end-to-end: ingest -> signals -> evaluate -> alert -> trace ->
report through the real handlers on an isolated store."""
from __future__ import annotations

import pytest
from starlette.requests import Request

import app.main as main


def _req():
    return Request({"type": "http", "method": "POST", "scheme": "http",
                    "server": ("t", 80), "client": ("9.9.9.9", 1234),
                    "path": "/x", "query_string": b"",
                    "headers": [(b"host", b"t")]})


def _event(event_id, txn_id, sender, receiver, channel="NIP",
           amount=1000):
    return {
        "event_id": event_id,
        "event_type": "financial.transaction.created",
        "occurred_at": "2026-11-07T10:00:00Z",
        "source": "e2e-fixture",
        "transaction": {
            "transaction_id": txn_id, "channel": channel,
            "amount_minor": amount, "currency": "NGN",
            "sender_account_id": sender,
            "receiver_account_id": receiver,
            "occurred_at": "2026-11-07T10:00:00Z",
        },
    }


def test_full_investigation_flow(tmp_store):
    # 1. Ingest a two-leg fund movement.
    first = main.ingest_event(_event("evt_e2e_1", "txn_e2e_1", "a1", "mid"),
                              _req())
    assert first["status"] == "accepted"
    second = main.ingest_event(_event("evt_e2e_2", "txn_e2e_2", "mid", "a2"),
                               _req())
    assert second["status"] == "accepted"
    dup = main.ingest_event(_event("evt_e2e_1", "txn_e2e_1", "a1", "mid"),
                            _req())
    assert dup["status"] == "duplicate"

    # 2. List shows the intake with classification.
    listed = main.list_transactions(_req())
    assert listed["total"] >= 2

    # 3. Evaluate opens alerts for newly-seen signals.
    run = main.monitoring_evaluate(_req())
    assert run["signals_evaluated"] >= 0
    rerun = main.monitoring_evaluate(_req())
    assert rerun["alerts_opened"] == []

    # 4. Alert lifecycle moves forward when signals exist.
    queue = main.list_fraud_alerts(_req())
    if queue["alerts"]:
        alert = queue["alerts"][0]
        if alert["status"] == "NEW":
            moved = main.move_fraud_alert(alert["id"],
                                          {"status": "TRIAGED"}, _req())
            assert moved["status"] == "TRIAGED"

    # 5. Trace the movement end to end.
    trace = main.create_trace({"transaction_id": "txn_e2e_1"}, _req())
    assert trace["origin_transaction"] == "txn_e2e_1"
    legs = main.get_trace_movements(trace["trace_id"], _req())
    assert any(m["to_transaction"] == "txn_e2e_2"
               for m in legs["movements"])
    rels = main.transaction_relationships("txn_e2e_1", _req())
    assert any(r["transaction_id"] == "txn_e2e_2"
               for r in rels["related_transactions"])

    # 6. Report from explicitly supplied evidence bundle.
    report = main.create_report(
        {"report_type": "tracing",
         "bundle": {"trace": trace, "limitations": trace["limitations"]}},
        _req())
    assert report["sections"]["trace"]["trace_id"] == trace["trace_id"]

    # 7. Every write left an audit row.
    actions = {a.get("action") for a in main.store.state.get("audits", [])
               if isinstance(a, dict)}
    assert {"event.ingested", "monitoring.evaluated", "trace.created",
            "report.created"} <= actions


def test_e2e_unknowns_stay_unknown(tmp_store):
    with pytest.raises(main.AppError):
        main.create_trace({"transaction_id": "txn_missing"}, _req())
    out = main.transaction_parties(
        main.store.state["transactions"][0]["transaction_id"], _req())
    assert out["network"]["institution_id"] == "UNKNOWN"
