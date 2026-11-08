"""UFI slice 2: monitoring, industry adapters, edge-aware tracing."""
from __future__ import annotations

import pytest
from starlette.requests import Request

import app.main as main  # noqa: F401  (store fixture binding)
from app import industry_adapters as adapters
from app import monitoring, tracing


def _req():
    return Request({"type": "http", "method": "GET", "scheme": "http",
                    "server": ("t", 80), "client": ("9.9.9.9", 1234),
                    "path": "/x", "query_string": b"",
                    "headers": [(b"host", b"t")]})


def _txn(**kw):
    base = {"transaction_id": "t1", "channel": "NIP",
            "amount_minor": 1000, "currency": "NGN",
            "sender_account_id": "a1", "receiver_account_id": "mid",
            "occurred_at": "2026-11-01T10:00:00Z"}
    base.update(kw)
    return base


# -- monitoring ------------------------------------------------------------
def test_status_honest_mode(tmp_store):
    txns = [_txn(), _txn(transaction_id="t2")]
    out = monitoring.status(tmp_store, txns, [], "org_primary")
    assert out["mode"] == "on-demand-evaluation"
    assert "streaming" in out["mode_note"]
    assert out["transactions_visible"] == 2
    assert out["data_window"]["start"] == "2026-11-01T10:00:00Z"
    assert out["computed_at"]


def test_evaluate_opens_and_dedupes(tmp_store):
    txns = tmp_store.state.get("transactions", [])
    assert txns, "seed transactions required"
    first = monitoring.evaluate(tmp_store, txns,
                                tmp_store.state.get("edges", []),
                                "org_primary", "analyst")
    assert first["signals_evaluated"] >= 0
    assert first["evaluated_at"]
    second = monitoring.evaluate(tmp_store, txns,
                                 tmp_store.state.get("edges", []),
                                 "org_primary", "analyst")
    assert second["alerts_opened"] == []
    assert (len(second["alerts_duplicate"])
            == len(first["alerts_opened"]) + len(first["alerts_duplicate"]))


# -- industry adapters ------------------------------------------------------
def test_build_config_banking():
    config = adapters.build_config("banking")
    assert config["name"]
    assert config["profile_present"] is True
    assert config["risk_taxonomy"]
    assert config["typology_count"] > 0
    assert config["registry_status"]


def test_build_config_unknown():
    with pytest.raises(ValueError):
        adapters.build_config("nope")


def test_readiness_never_promotes():
    before = adapters.build_config("retail")["registry_status"]
    ready = adapters.readiness("retail")
    assert ready["overall"] in ("READY", "NOT_READY")
    assert set(ready["checks"]) == {"profile_present", "tests_present",
                                    "typologies_mapped",
                                    "typologies_measured",
                                    "status_gate"}
    after = adapters.build_config("retail")["registry_status"]
    assert before == after, "readiness must not mutate registry status"


def test_coverage_shape():
    cov = adapters.coverage("crypto-assets")
    assert cov["industry_id"] == "crypto-assets"
    assert isinstance(cov["risk_taxonomy_codes"], list)
    assert isinstance(cov["typologies"], list)


def test_all_registry_ids_have_configs():
    from app import industries as ind
    missing = []
    for entry in ind.registry():
        try:
            adapters.build_config(entry["id"])
        except ValueError:
            missing.append(entry["id"])
    assert missing == []
    assert len(ind.registry()) == 45


# -- edge-aware tracing -------------------------------------------------------
def test_account_edge_upgrades_link():
    legs = [_txn(transaction_id="t1", receiver_account_id="mid"),
            _txn(transaction_id="t2", sender_account_id="mid",
                 receiver_account_id="end")]
    plain = tracing.build_trace(legs, [], "t1")
    assert plain["movements"][0]["status"] == "STRONGLY_SUPPORTED_LINK"
    edges = [{"edge_id": "e1", "source_node_id": "mid",
              "target_node_id": "mid", "source_event_ids": ["evt1"]}]
    assert legs[0]["receiver_account_id"] == "mid"
    upgraded = tracing.build_trace(legs, edges, "t1")
    assert (upgraded["movements"][0]["status"]
            == "PROVIDER_REPORTED_LINK")


def test_unprovenanced_edges_withheld():
    legs = [_txn(transaction_id="t1", receiver_account_id="mid"),
            _txn(transaction_id="t2", sender_account_id="mid",
                 receiver_account_id="end")]
    bad = [{"edge_id": "e9", "source_node_id": "mid",
            "target_node_id": "mid"}]
    out = tracing.build_trace(legs, bad, "t1")
    assert out["movements"][0]["status"] == "STRONGLY_SUPPORTED_LINK"
    assert any("provenance" in lim for lim in out["limitations"])


# -- slice-2 routes ---------------------------------------------------------
def test_list_transactions(tmp_store):
    out = main.list_transactions(_req())
    assert out["total"] >= 1
    assert out["transactions"][0]["classification"]["method_id"]
    filtered = main.list_transactions(_req(), channel="ZZZ_NOPE")
    assert filtered["total"] == 0
    paged = main.list_transactions(_req(), limit=1, offset=0)
    assert len(paged["transactions"]) == 1


def test_transaction_events_route(tmp_store):
    txn_id = main.store.state["transactions"][0]["transaction_id"]
    out = main.transaction_events(txn_id, _req())
    assert out["transaction_id"] == txn_id
    assert isinstance(out["events"], list)
    if out["events"]:
        assert "lifecycle" in out["events"][0]
    with pytest.raises(main.AppError):
        main.transaction_events("nope", _req())


def test_transaction_relationships_route(tmp_store):
    txn_id = main.store.state["transactions"][0]["transaction_id"]
    out = main.transaction_relationships(txn_id, _req())
    assert isinstance(out["related_transactions"], list)
    assert isinstance(out["graph_nodes"], list)
    with pytest.raises(main.AppError):
        main.transaction_relationships("nope", _req())


def test_trace_relationships_route(tmp_store):
    txn_id = main.store.state["transactions"][0]["transaction_id"]
    trace = main.create_trace({"transaction_id": txn_id}, _req())
    out = main.trace_relationships(trace["trace_id"], _req())
    assert isinstance(out["accounts"], list)
    assert isinstance(out["account_edges"], list)


def test_monitoring_routes(tmp_store):
    status = main.monitoring_status(_req())
    assert status["mode"] == "on-demand-evaluation"
    assert status["transactions_visible"] >= 1
    run = main.monitoring_evaluate(_req())
    assert run["signals_evaluated"] >= 0
    assert run["tenant_scope"]
    rerun = main.monitoring_evaluate(_req())
    assert rerun["alerts_opened"] == []


def test_industry_adapter_routes(tmp_store):
    cov = main.industry_coverage("banking")
    assert cov["registry_status"]
    assert cov["typologies"]
    ready = main.industry_readiness("banking", _req())
    assert ready["overall"] in ("READY", "NOT_READY")
    with pytest.raises(main.AppError):
        main.industry_coverage("nope")
    with pytest.raises(main.AppError):
        main.industry_readiness("nope", _req())
