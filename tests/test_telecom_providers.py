"""Telecom providers: honest status, harness discipline, never-live rule."""
import pytest

from app import connectors as conn_mod
from app import telecom_providers as prov_mod


def test_telecom_adapters_registered():
    for adapter in prov_mod.TELECOM_ADAPTERS:
        assert conn_mod.get_adapter(adapter) is not None, adapter
    assert len(prov_mod.TELECOM_ADAPTERS) == 8


def test_every_verify_type_maps_to_adapters():
    from app import telecom_verify as tv

    assert set(prov_mod.TYPE_ADAPTERS) == set(tv.TYPES)
    for adapters in prov_mod.TYPE_ADAPTERS.values():
        assert adapters


def test_provider_status_all_not_connected(tmp_store):
    rows = prov_mod.provider_status(tmp_store, "org_primary")
    assert len(rows) == 8
    for row in rows:
        assert row["status"] == "NOT_CONNECTED"
        assert row["live"] is False
        assert row["secret_refs"]
        assert all(v is False for v in
                   row["secret_present"].values())


def test_no_live_connection_without_evidence(tmp_store):
    for adapter in prov_mod.TELECOM_ADAPTERS:
        assert prov_mod.live_connection(tmp_store, adapter,
                                        "org_primary") is None


def test_loopback_never_counts_as_live(tmp_store):
    record = conn_mod.create_connection("loopback", "t", "org_primary")
    conn_mod.begin_verify(record)
    record, ok = conn_mod.complete_verify(record)
    assert ok
    tmp_store.connection_save(record)
    for adapter in prov_mod.TELECOM_ADAPTERS:
        assert prov_mod.live_connection(tmp_store, adapter,
                                        "org_primary") is None


def test_harness_answers_only_with_loopback(tmp_store):
    harness = prov_mod.TelecomHarness()
    with pytest.raises(prov_mod.ProviderOutage):
        harness.answer(tmp_store, "org_primary", "sim_swap")
    record = conn_mod.create_connection("loopback", "t", "org_primary")
    conn_mod.begin_verify(record)
    record, _ = conn_mod.complete_verify(record)
    tmp_store.connection_save(record)
    response = harness.answer(tmp_store, "org_primary", "sim_swap",
                              {"result": "VERIFIED"})
    assert response["synthetic"] is True
    assert response["provider"] == "harness-loopback"


def test_harness_fault_injection(tmp_store):
    record = conn_mod.create_connection("loopback", "t", "org_primary")
    conn_mod.begin_verify(record)
    record, _ = conn_mod.complete_verify(record)
    tmp_store.connection_save(record)
    harness = prov_mod.TelecomHarness()
    harness.fail_next(2)
    with pytest.raises(prov_mod.ProviderOutage):
        harness.answer(tmp_store, "org_primary", "sim_swap")
    with pytest.raises(prov_mod.ProviderOutage):
        harness.answer(tmp_store, "org_primary", "sim_swap")
    assert harness.answer(tmp_store, "org_primary",
                          "sim_swap")["synthetic"] is True


def test_harness_is_tenant_scoped(tmp_store):
    from app import tenancy as tenancy_mod

    tenancy_mod.register_tenant("org_other")
    record = conn_mod.create_connection("loopback", "t", "org_primary")
    conn_mod.begin_verify(record)
    record, _ = conn_mod.complete_verify(record)
    tmp_store.connection_save(record)
    harness = prov_mod.TelecomHarness()
    with pytest.raises(prov_mod.ProviderOutage):
        harness.answer(tmp_store, "org_other", "sim_swap")
