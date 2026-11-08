"""Unified provider registry + country coverage honesty."""
import pytest

from app import intel_providers as prov


def test_unified_registry_all_discovered_none_live(tmp_store):
    rows = prov.unified_registry(tmp_store, "org_primary")
    assert len(rows) == 33
    for row in rows:
        assert row["integration_status"] == "DISCOVERED", row
        assert row["live"] is False
        assert "secret" not in str(row).lower() or \
            "secret_refs" in str(row)


def test_intel_adapters_present(tmp_store):
    ids = {r["provider_id"] for r in
           prov.unified_registry(tmp_store, "org_primary")}
    for adapter in prov.INTEL_ADAPTERS:
        assert adapter in ids


def test_lifecycle_mapping_documented():
    assert prov.LIFECYCLE["DRAFT"] == "DISCOVERED"
    assert prov.LIFECYCLE["CONNECTED"] == "ACTIVE"
    assert prov.LIFECYCLE["REVOKED"] == "RETIRED"


def test_provider_health_no_connection(tmp_store):
    body = prov.provider_health(tmp_store, "org_primary",
                                "identity-document")
    assert body["status"] == "NO_CONNECTION"
    assert body["live"] is False
    assert prov.provider_health(tmp_store, "org_primary",
                                "nope") is None


def test_country_coverage_honest():
    rows = prov.country_coverage()
    assert len(rows) == 7
    for row in rows:
        assert row["overall"] == "PROVIDER_UNAVAILABLE"
        assert row["legal_review"] == "NOT_ASSESSED"
        assert "not coverage" in row["note"]


def test_map_provider_env(monkeypatch):
    monkeypatch.setenv("MAP_PROVIDER", "leaflet-osm")
    assert prov.map_provider() == "leaflet-osm"
    monkeypatch.setenv("MAP_PROVIDER", "google-billable")
    assert prov.map_provider() == "none"
    monkeypatch.delenv("MAP_PROVIDER", raising=False)
    assert prov.map_provider() == "none"
