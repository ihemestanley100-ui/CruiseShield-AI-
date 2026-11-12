"""UFI integration: fleet readiness, report assembly, trace links."""
from __future__ import annotations

import pytest
from starlette.requests import Request

import app.main as main
from app import industry_adapters as adapters
from app import tracing


def _req():
    return Request({"type": "http", "method": "GET", "scheme": "http",
                    "server": ("t", 80), "client": ("9.9.9.9", 1234),
                    "path": "/x", "query_string": b"",
                    "headers": [(b"host", b"t")]})


def test_fleet_readiness_snapshot():
    snap = adapters.fleet_readiness()
    assert snap["total"] == 45
    assert snap["ready"] + snap["not_ready"] == 45
    assert all(set(r) >= {"industry_id", "overall", "checks"}
               for r in snap["industries"])
    measured = adapters.fleet_readiness({"T-01": 3})
    banking = next(r for r in measured["industries"]
                   if r["industry_id"] == "banking")
    assert banking["typologies_measured"] >= 1


def test_fleet_readiness_route(tmp_store):
    out = main.industries_fleet_readiness(_req())
    assert out["total"] == 45
    assert isinstance(out["ready"], int)


def test_report_assembles_from_investigation(tmp_store):
    inv = main.store.state["investigations"][0]
    out = main.create_report(
        {"report_type": "transaction",
         "investigation_id": inv["investigation_id"]}, _req())
    assert out["investigation_id"] == inv["investigation_id"]
    assert out["sections"]["transactions"]
    assert out["sections"]["lifecycle"]["status"] == "not_available"


def test_report_requires_bundle_or_investigation(tmp_store):
    with pytest.raises(main.AppError):
        main.create_report({"report_type": "tracing"}, _req())
    with pytest.raises(main.AppError):
        main.create_report({"report_type": "tracing",
                            "investigation_id": "inv_nope"}, _req())


def test_trace_carries_related_investigations(tmp_store):
    inv = main.store.state["investigations"][0]
    created = main.create_trace(
        {"transaction_id": inv["transaction_id"]}, _req())
    assert inv["investigation_id"] in created["related_investigation_ids"]
    fetched = main.get_trace(created["trace_id"], _req())
    assert fetched["related_investigation_ids"] == \
        created["related_investigation_ids"]


def test_related_investigations_pure():
    trace = {"visited_transactions": ["t1", "t2"]}
    invs = [{"investigation_id": "i1", "transaction_id": "t2"},
            {"investigation_id": "i2", "transaction_id": "t9"}]
    assert tracing.related_investigations(trace, invs) == ["i1"]
    assert tracing.related_investigations({}, invs) == []
