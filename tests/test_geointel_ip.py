"""IP geolocation extension: ESTIMATED-only, masked persistence."""
from app import geo_intel as geo_mod
from app import intel_common as common
from app import ip_intel as ip_mod

PURPOSE = "TRANSACTION_RISK_ASSESSMENT"


class ScriptedGeo:
    name = "scripted-test"

    def __init__(self, record):
        self._record = record

    def lookup(self, ip):
        return dict(self._record)


def test_invalid_and_non_public_never_geolocated():
    bad = ip_mod.lookup_geolocation("bogus", "inv_84721", PURPOSE)
    assert bad["status"] == "INVALID"
    for ip in ("10.1.2.3", "127.0.0.1", "169.254.1.1", "224.0.0.1",
               "203.0.113.10", "::1"):
        result = ip_mod.lookup_geolocation(ip, "inv_84721", PURPOSE)
        assert result["status"] == "NOT_APPLICABLE", ip


def test_public_ip_estimated_null_shape():
    result = ip_mod.lookup_geolocation("8.8.8.8", "inv_84721", PURPOSE)
    assert result["status"] == "ESTIMATED"
    assert set(result["location"]) == {"country_code", "region",
                                       "city", "latitude",
                                       "longitude", "accuracy_km"}
    assert all(v is None for v in result["location"].values())
    assert result["network"]["vpn_indicator"] == "unknown"
    assert result["source"]["provider"] == "null_provider"
    assert any("residential address" in line
               for line in result["limitations"])
    assert result["purpose"] == PURPOSE


def test_provider_record_mapped_not_invented():
    backend = ScriptedGeo({"country_code": "NG", "city": "Lagos",
                           "latitude": 6.5, "longitude": 3.4,
                           "accuracy_radius_km": 50,
                           "asn": "AS29465",
                           "organization": "TestNet",
                           "observed_at": "2026-11-01T00:00:00Z",
                           "retrieved_at": "2026-11-07T00:00:00Z"})
    result = ip_mod.lookup_geolocation("197.210.29.1", "inv_84721",
                                       PURPOSE, provider=backend)
    assert result["location"]["country_code"] == "NG"
    assert result["location"]["region"] is None
    assert result["network"]["asn"] == "AS29465"
    assert result["source"]["provider"] == "scripted-test"


def test_mask_ip():
    assert ip_mod.mask_ip("8.8.8.8") == "8.***"
    assert ip_mod.mask_ip("2001:db8::1").startswith("2001:")
    assert ip_mod.mask_ip("bogus") == "invalid"


def test_record_persists_masked_only(tmp_store):
    result = ip_mod.lookup_geolocation("8.8.8.8", "inv_84721", PURPOSE)
    record = ip_mod.record_network_observation(
        tmp_store, "8.8.8.8", result, "org_primary", "inv_84721",
        PURPOSE, "org_primary", "investigator-1")
    assert record["observation_id"].startswith("net_")
    assert record["ip_masked"] == "8.***"
    assert "8.8.8.8" not in str(record)
    import time as _time

    assert record["expires_at"] > _time.time()
    assert common.check_integrity(record) is True
