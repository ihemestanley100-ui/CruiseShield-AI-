"""DI-04 IP Intelligence Foundation: parsing, extraction, attribution.

Derived layer only: no store writes, no risk changes, no providers.
All tests use tmp_store (scratch) or synthetic dicts; live state untouched.
"""
import pytest

import app.main as main
from app import ip_intel as ip


def test_parse_ipv4_and_ipv6():
    assert str(ip.parse_ip("8.8.8.8")) == "8.8.8.8"
    assert ip.parse_ip("2001:db8::1").version == 6
    assert ip.parse_ip("  1.1.1.1  ").compressed == "1.1.1.1"


def test_parse_rejects_garbage():
    for bad in ("", "999.1.1.1", "not-an-ip", "1.2.3.4/32", None, 12345):
        assert ip.parse_ip(bad) is None


def test_classification_table():
    assert ip.classify_ip("8.8.8.8")["category"] == "public"
    assert ip.classify_ip("192.168.0.1")["category"] == "private"
    assert ip.classify_ip("10.0.0.9")["category"] == "private"
    assert ip.classify_ip("127.0.0.1")["category"] == "loopback"
    assert ip.classify_ip("::1")["category"] == "loopback"
    assert ip.classify_ip("169.254.1.1")["category"] == "link_local"
    assert ip.classify_ip("224.0.0.1")["category"] == "multicast"
    assert ip.classify_ip("240.0.0.1")["category"] == "reserved"
    assert ip.classify_ip("0.0.0.0")["category"] == "reserved"
    assert ip.classify_ip("2001:db8::1")["category"] == "private"
    bad = ip.classify_ip("bogus")
    assert bad["valid"] is False and bad["status"] == "unknown"


def test_extraction_ignores_headers_from_untrusted_peer():
    out = ip.extract_client_ip({"x-forwarded-for": "9.9.9.9"},
                               "203.0.113.7", trusted=[])
    assert out["ip"] == "203.0.113.7"
    assert out["source"] == "direct_peer"
    assert out["status"] == "peer_untrusted_headers_ignored"


def test_extraction_walks_trusted_chain():
    out = ip.extract_client_ip(
        {"x-forwarded-for": "198.51.100.9, 10.0.0.1"}, "10.0.0.2",
        trusted=["10.0.0.0/8"])
    assert out["ip"] == "198.51.100.9"
    assert out["trusted_path"] is True


def test_extraction_skips_spoofed_and_invalid_hops():
    out = ip.extract_client_ip(
        {"x-forwarded-for": "bogus, 198.51.100.9, 10.0.0.1"}, "10.0.0.2",
        trusted=["10.0.0.0/8"])
    assert out["ip"] == "198.51.100.9"


def test_extraction_defaults_to_no_trusted_proxies(monkeypatch):
    monkeypatch.delenv("TRUSTED_PROXIES", raising=False)
    out = ip.extract_client_ip({"x-forwarded-for": "9.9.9.9"}, "203.0.113.7")
    assert out["source"] == "direct_peer"


def test_null_provider_reports_unknown_only():
    provider = ip.NullProvider()
    intel = provider.enrich_ip("8.8.8.8")
    assert intel.network_type == "unknown"
    assert intel.vpn_indicator == "unknown"
    assert intel.proxy_indicator == "unknown"
    assert intel.tor_indicator == "unknown"
    assert intel.reputation == "unknown"
    assert "safe" not in intel.model_dump_json().lower()
    assert "malicious" not in intel.model_dump_json().lower()
    assert provider.enrich_ip("bogus") is None


def test_label_observations_from_seed(tmp_store):
    obs = ip.build_observations(tmp_store.state)
    assert len(obs) == 1
    first = obs[0]
    assert first.ip_label == "ip_02"
    assert first.address is None
    assert first.address_status == "unknown"
    assert first.txn_id == "txn_84721"
    assert first.synthetic is True


def test_shared_ips_empty_on_fixtures_but_logic_sound(tmp_store):
    assert ip.shared_ips(tmp_store.state) == []
    state = {"events": [
        {"event_id": "e1", "occurred_at": "2026-10-27T10:00:00Z",
         "entities": {"ip_id": "ip_9"},
         "transaction": {"transaction_id": "t1", "sender_account_id": "a1"}},
        {"event_id": "e2", "occurred_at": "2026-10-27T10:05:00Z",
         "entities": {"ip_id": "ip_9"},
         "transaction": {"transaction_id": "t2", "sender_account_id": "a2"}},
    ]}
    shared = ip.shared_ips(state)
    assert len(shared) == 1
    assert shared[0]["account_ids"] == ["a1", "a2"]
    assert shared[0]["address_status"] == "unknown"


def test_proposed_edges_never_inserted(tmp_store):
    before_edges = list(tmp_store.state["edges"])
    proposed = ip.proposed_edges(tmp_store.state)
    assert proposed, "expected proposed edges for ip_02"
    assert all(e["status"] == "proposed_not_inserted" for e in proposed)
    rels = {e["relationship_type"] for e in proposed}
    assert rels == {"CONNECTED_FROM_IP", "ASSOCIATED_WITH_IP"}
    assert tmp_store.state["edges"] == before_edges


def test_ip_endpoint_returns_observations(tmp_store):
    body = main.get_ip_observations("ip_02")
    assert body["ip_label"] == "ip_02"
    assert body["address_status"] == "unknown"
    assert len(body["observations"]) == 1


def test_ip_endpoint_404_unknown_400_malformed(tmp_store):
    with pytest.raises(main.AppError) as exc:
        main.get_ip_observations("ip_zz")
    assert (exc.value.code, exc.value.status) == ("UNKNOWN_IP_LABEL", 404)
    with pytest.raises(main.AppError) as exc2:
        main.get_ip_observations("../x")
    assert exc2.value.status == 400


def test_routes_registered():
    paths = {route.path for route in main.app.routes}
    assert "/api/v1/ip-observations/{label}" in paths
    assert "/api/v1/devices/{device_id}" in paths  # DI-03 intact
    assert "/api/v1/graph/{txn_id}" in paths


def test_di04_changes_nothing_persisted(tmp_store):
    before = dict(tmp_store.state)
    ip.build_observations(tmp_store.state)
    ip.shared_ips(tmp_store.state)
    ip.proposed_edges(tmp_store.state)
    main.get_ip_observations("ip_02")
    assert tmp_store.state == before
