"""DI-05 Geolocation Foundation: validation, providers, comparison, API.

Derived layer only: no store writes, no risk/graph/evidence changes.
Uses tmp_store (scratch); live data/state.json untouched.
"""
from datetime import datetime, timedelta, timezone

import pytest

import app.main as main
from app import geo_intel as geo


class StubProvider:
    name = "stub"

    def __init__(self, record=None, fail=False):
        self.record = record
        self.fail = fail
        self.calls = 0

    def lookup(self, ip):
        self.calls += 1
        if self.fail:
            raise TimeoutError("stub outage")
        return self.record


def _obs(**over):
    base = {"obs_id": "o1", "pathway": "ip_derived", "label": "loc_01",
            "latitude": 6.45, "longitude": 3.39,
            "observed_at": "2026-10-30T10:00:00Z",
            "confidence": "medium", "source": "stub"}
    base.update(over)
    return geo.LocationObservation(**base)


# A. IP geolocation behavior -------------------------------------------
def test_null_public_ipv4_and_ipv6_unavailable():
    for ip in ("8.8.8.8", "2001:4860:4860::8888"):
        out = geo.resolve_ip(ip)
        assert out.status == "unavailable"
        assert out.source == "none"
        assert out.country == "unknown"
        assert out.latitude is None and out.longitude is None
        assert out.confidence == "unknown"
        assert out.provider == "null_provider"
        assert out.external_lookup_performed is False
        assert out.approximate_only is True


def test_non_public_ips_never_resolved():
    for ip, category in (("10.0.0.1", "private"), ("fd00::1", "private"),
                         ("127.0.0.1", "loopback"), ("::1", "loopback"),
                         ("169.254.1.1", "link_local"),
                         ("240.0.0.1", "reserved"),
                         ("224.0.0.1", "multicast")):
        out = geo.resolve_ip(ip)
        assert out.status == "unavailable"
        assert out.reason == f"unsupported_category:{category}"


def test_invalid_and_missing_ip():
    assert geo.resolve_ip("bogus").reason == "invalid_ip"
    assert geo.resolve_ip("").reason == "invalid_ip"


def test_stub_provider_resolved_and_malformed():
    record = {"country_code": "NG", "country": "Nigeria",
              "region": "Lagos", "city": "Lagos",
              "latitude": 6.45, "longitude": 3.39, "timezone": "Africa/Lagos",
              "accuracy_radius_km": 10, "dataset_version": "stub-1",
              "observed_at": "2026-10-30T10:00:00Z"}
    out = geo.resolve_ip("8.8.8.8", StubProvider(record))
    assert out.status == "resolved"
    assert out.country_code == "NG" and out.city == "Lagos"
    assert out.confidence == "high"
    assert out.approximate_only is True
    bad = geo.resolve_ip("8.8.8.8", StubProvider({"latitude": 999.0,
                                                 "longitude": 0.0}))
    assert bad.status == "unavailable"
    assert bad.reason == "provider_malformed_coordinates"


def test_provider_failure_is_unavailable_not_fatal():
    out = geo.resolve_ip("8.8.8.8", StubProvider(fail=True))
    assert out.status == "unavailable"
    assert out.reason == "provider_error"


def test_zero_external_calls_by_construction():
    import inspect
    src = inspect.getsource(geo)
    for banned in ("httpx", "requests", "urlopen", "socket."):
        assert banned not in src


# B. Coordinate validation ---------------------------------------------
def test_coordinates_valid_and_bounds():
    assert geo.validate_coordinates(6.45, 3.39) == (True, "ok")
    assert geo.validate_coordinates(-90, -180) == (True, "ok")
    assert geo.validate_coordinates(90, 180) == (True, "ok")
    assert geo.validate_coordinates(-90.1, 0)[0] is False
    assert geo.validate_coordinates(90.1, 0)[0] is False
    assert geo.validate_coordinates(0, -180.1)[0] is False
    assert geo.validate_coordinates(0, 180.1)[0] is False


def test_coordinates_reject_nan_inf_types_missing():
    nan, inf = float("nan"), float("inf")
    for lat, lon in ((nan, 0.0), (0.0, nan), (inf, 0.0), (0.0, inf),
                     ("6.45", 3.39), (None, 3.39), (6.45, None),
                     (True, 0.0)):
        assert geo.validate_coordinates(lat, lon)[0] is False, (lat, lon)


# C. Metadata validation -------------------------------------------------
def test_country_accuracy_timezone_metadata():
    assert geo.validate_country_code("NG") is True
    assert geo.validate_country_code("ng") is False
    assert geo.validate_country_code("NIG") is False
    assert geo.validate_country_code(None) is False
    assert geo.validate_accuracy_radius(10.5) is True
    assert geo.validate_accuracy_radius(None) is True
    assert geo.validate_accuracy_radius(-1) is False
    assert geo.validate_accuracy_radius(float("inf")) is False
    assert geo.validate_accuracy_radius("10") is False


# D. Confidence and freshness ---------------------------------------------
def test_confidence_derived_from_metadata():
    assert geo.classify_confidence({}) == "unknown"
    assert geo.classify_confidence({"latitude": 1.0, "longitude": 1.0}) \
        == "low"  # coords alone never high
    assert geo.classify_confidence({"provider": "stub",
                                    "accuracy_radius_km": 10}) == "high"
    assert geo.classify_confidence({"provider": "stub",
                                    "accuracy_radius_km": 500}) == "medium"
    assert geo.classify_confidence({"confidence_override": "low"}) == "low"


def test_freshness_policy():
    now = datetime(2026, 10, 30, 12, 0, 0, tzinfo=timezone.utc)
    hour_ago = (now - timedelta(hours=1)).isoformat()
    assert geo.classify_freshness(hour_ago, now) == "fresh"
    week_ago = (now - timedelta(days=7)).isoformat()
    assert geo.classify_freshness(week_ago, now) == "stale"
    year_ago = (now - timedelta(days=400)).isoformat()
    assert geo.classify_freshness(year_ago, now) == "expired"
    assert geo.classify_freshness("", now) == "unknown"
    assert geo.classify_freshness("bogus", now) == "unknown"
    future = (now + timedelta(hours=1)).isoformat()
    assert geo.classify_freshness(future, now) == "unknown"


# E. Device permission contracts -------------------------------------------
def test_permission_and_consent_states():
    assert geo.PERMISSION_STATES == {"granted", "denied", "prompt",
                                     "unsupported", "revoked", "unknown"}
    assert geo.CONSENT_STATES == {"granted", "denied", "withdrawn",
                                  "not_requested", "unknown"}
    loc = geo.DeviceLocation(permission="denied", consent="not_requested")
    assert loc.latitude is None and loc.longitude is None
    assert loc.synthetic is True


def test_no_collection_code_paths():
    import inspect
    src = inspect.getsource(geo)
    for banned in ("geolocation.getCurrentPosition", "watchPosition",
                   "navigator.geolocation"):
        assert banned not in src


# F. Location comparison ----------------------------------------------------
def test_compare_same_different_conflicting():
    same = geo.compare_observations(_obs(), _obs(obs_id="o2"))
    assert same["outcome"] == "same_location"
    assert same["fraud_determination"] == "none"
    far = geo.compare_observations(_obs(), _obs(obs_id="o2", latitude=51.5,
                                                longitude=-0.12))
    assert far["outcome"] == "different_location"
    assert far["distance_km"] > 100
    conflict = geo.compare_observations(
        _obs(), _obs(obs_id="o2", pathway="device", latitude=51.5,
                     longitude=-0.12))
    assert conflict["outcome"] == "conflicting"


def test_compare_fails_safe():
    assert geo.compare_observations(_obs(latitude=None),
                                    _obs())["outcome"] \
        == "insufficient_evidence"
    assert geo.compare_observations(_obs(observed_at=""),
                                    _obs())["outcome"] \
        == "insufficient_evidence"
    assert geo.compare_observations(_obs(confidence="low"),
                                    _obs())["outcome"] \
        == "insufficient_evidence"
    old = (datetime.now(timezone.utc) - timedelta(days=400)).isoformat()
    assert geo.compare_observations(_obs(observed_at=old),
                                    _obs())["outcome"] == "stale_input"


# G. API behavior --------------------------------------------------------------
def test_geo_endpoint_fixture_label(tmp_store):
    body = main.get_geo_observations("loc_01")
    assert body["kind"] == "fixture_label"
    assert len(body["observations"]) == 1
    assert body["observations"][0]["geo_status"] == "unavailable"


def test_geo_endpoint_ip_literal_and_errors(tmp_store):
    body = main.get_geo_observations("8.8.8.8")
    assert body["kind"] == "ip_literal"
    assert body["lookup"]["status"] == "unavailable"
    with pytest.raises(main.AppError) as exc:
        main.get_geo_observations("loc_zz")
    assert (exc.value.code, exc.value.status) == ("UNKNOWN_GEO_IDENTIFIER",
                                                  404)
    with pytest.raises(main.AppError) as exc2:
        main.get_geo_observations("../x")
    assert exc2.value.status == 400


def test_geo_endpoint_read_only(tmp_store):
    before = dict(tmp_store.state)
    main.get_geo_observations("loc_01")
    main.get_geo_observations("8.8.8.8")
    assert tmp_store.state == before
    paths = {route.path for route in main.app.routes}
    assert "/api/v1/geo-observations/{identifier}" in paths


# H. Regression and preservation -------------------------------------------------
def test_baseline_pins(tmp_store):
    txn = main.get_transaction("txn_84721")
    assert txn["risk_transaction"]["score"] == 35
    assert txn["risk_network"]["score"] == 84
    graph = main.get_graph("txn_84721")
    assert graph["counts"] == {"nodes": 22, "edges": 30}
    inv = main.get_investigation("inv_84721")
    assert inv["evidence_count"] == 39
