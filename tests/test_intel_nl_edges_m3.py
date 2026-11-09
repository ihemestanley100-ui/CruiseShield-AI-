"""M3 provider-registry + NL-search edges (offline, synthetic inputs).

Covers the branches the full suite misses: connection lifecycle
mapping, telecom fallback rows, health best-status selection, NL
parse variants (relative windows, txn/beneficiary refs), execute
filter predicates, and explanation parts.
"""
from app import intel_providers as providers
from app import nl_search


def _conn(cid, adapter, tenant, status, observed=True):
    rec = {"id": cid, "adapter": adapter, "tenant_id": tenant,
           "status": status}
    if observed:
        rec["last_success_at"] = "2026-01-01T00:00:00Z"
        rec["last_health_at"] = "2026-01-02T00:00:00Z"
    return rec


def _row(rows, provider_id):
    return next(r for r in rows if r["provider_id"] == provider_id)


def test_registry_live_connected_is_active(tmp_store):
    tmp_store.connection_save(_conn("c1", "mapping-tiles",
                                    "org_primary", "CONFIGURED"))
    tmp_store.connection_save(_conn("c2", "mapping-tiles",
                                    "org_primary", "CONNECTED"))
    row = _row(providers.unified_registry(tmp_store, "org_primary"),
               "mapping-tiles")
    assert row["integration_status"] == "ACTIVE"
    assert row["live"] is True


def test_registry_connected_unobserved_is_tested(tmp_store):
    tmp_store.connection_save(_conn("c1", "mapping-tiles",
                                    "org_primary", "CONNECTED",
                                    observed=False))
    row = _row(providers.unified_registry(tmp_store, "org_primary"),
               "mapping-tiles")
    assert row["integration_status"] == "CONNECTIVITY_TESTED"
    assert row["live"] is False


def test_registry_ignores_bad_and_foreign_rows(tmp_store):
    tmp_store.state.setdefault("connections", {})["junk"] = "junk-row"
    tmp_store.connection_save(_conn("c9", "mapping-tiles",
                                    "org_other", "CONNECTED"))
    row = _row(providers.unified_registry(tmp_store, "org_primary"),
               "mapping-tiles")
    assert row["integration_status"] == "DISCOVERED"
    assert row["live"] is False


def test_telecom_fallback_rows_declared_not_live(tmp_store,
                                                 monkeypatch):
    from app import telecom_providers as telecom_prov
    monkeypatch.setattr(telecom_prov, "TELECOM_ADAPTERS",
                        telecom_prov.TELECOM_ADAPTERS + ("zz-future",))
    rows = providers.unified_registry(tmp_store, "org_primary")
    future = _row(rows, "zz-future")
    assert future["category"] == "telecom"
    assert future["integration_status"] == "DISCOVERED"
    assert future["live"] is False


def test_provider_health_unknown_and_declared(tmp_store):
    assert providers.provider_health(tmp_store, "org_primary",
                                     "no-such") is None
    declared = providers.provider_health(tmp_store, "org_primary",
                                         "camara-sim-swap")
    assert declared["status"] == "NO_CONNECTION"
    assert declared["live"] is False


def test_provider_health_best_status_mapping(tmp_store):
    tmp_store.connection_save(_conn("c1", "mapping-tiles",
                                    "org_primary", "FAILED"))
    tmp_store.connection_save(_conn("c2", "mapping-tiles",
                                    "org_primary", "SUSPENDED"))
    health = providers.provider_health(tmp_store, "org_primary",
                                       "mapping-tiles")
    assert health["status"] == "FAILED"
    assert health["integration_status"] == "DEGRADED"
    assert health["live"] is False
    tmp_store.connection_save(_conn("c3", "mapping-tiles",
                                    "org_primary", "CONNECTED"))
    health = providers.provider_health(tmp_store, "org_primary",
                                       "mapping-tiles")
    assert health["status"] == "CONNECTED"
    assert health["integration_status"] == "ACTIVE"
    assert health["live"] is True
    assert health["last_check"] == "2026-01-02T00:00:00Z"


def test_parse_relative_and_reference_variants():
    assert nl_search.parse("above 5 million")["filters"] == {
        "min_amount_minor": 500000000}
    window = nl_search.parse("show transfers within 30 minutes")
    assert window["filters"]["within_minutes"] == 30
    assert "needs_clarification" not in window
    assert nl_search.parse("show transfers last 7 days")[
        "filters"]["start"].endswith("Z")
    assert nl_search.parse("find txn_ab12")["filters"] == {
        "transaction_id": "txn_ab12"}
    assert nl_search.parse("show beneficiary acme stores")[
        "filters"]["beneficiary_text"] == "acme stores"


def _txn(**over):
    base = {"transaction_id": "txn_1", "amount_minor": 100,
            "currency": "NGN", "occurred_at": "2026-06-01T00:00:00Z",
            "device_id": "dev_1", "receiver_account_id": "ACME",
            "sender_account_id": "B", "merchant_id": "M"}
    base.update(over)
    return base


def test_execute_filter_predicates():
    assert nl_search.execute(None, [_txn()], [],
                             {"filters": {}})["count"] == 1
    assert nl_search.execute(
        None, [_txn()], [],
        {"filters": {"min_amount_minor": 200}})["count"] == 0
    assert nl_search.execute(
        None, [_txn()], [],
        {"filters": {"min_amount_minor": 100}})["count"] == 1
    assert nl_search.execute(
        None, [_txn()], [],
        {"filters": {"currency": "USD"}})["count"] == 0
    assert nl_search.execute(
        None, [_txn()], [],
        {"filters": {"start": "2026-07-01T00:00:00Z"}})["count"] == 0
    assert nl_search.execute(
        None, [_txn()], [],
        {"filters": {"transaction_id": "txn_zz"}})["count"] == 0
    assert nl_search.execute(
        None, [_txn()], [],
        {"filters": {"device_id": "dev_zz"}})["count"] == 0
    assert nl_search.execute(
        None, [_txn()], [],
        {"filters": {"beneficiary_text": "zzz"}})["count"] == 0
    assert nl_search.execute(
        None, [_txn()], [],
        {"filters": {"beneficiary_text": "acme"}})["count"] == 1
    assert nl_search.execute(
        None, [_txn()], [],
        {"filters": {"flagged_only": True}})["count"] == 0
    flagged = [{"transaction_id": "txn_1"}]
    assert nl_search.execute(
        None, [_txn()], flagged,
        {"filters": {"flagged_only": True}})["count"] == 1


def test_explain_parts():
    assert nl_search.explain({"needs_clarification": True,
                              "question": "q?"}) == "q?"
    assert nl_search.explain({}) == "No filters"
    text = nl_search.explain({"filters": {
        "min_amount_minor": 500, "flagged_only": True,
        "within_minutes": 30}})
    assert "amount >= 500 minor units" in text
    assert "flagged by detection only" in text
    assert "relative 30-minute window" in text
