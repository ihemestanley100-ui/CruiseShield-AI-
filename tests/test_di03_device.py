"""DI-03 Device Intelligence Foundation: validation, profiles, attribution.

Derived layer only: no store writes, no risk changes, no package changes.
All tests use tmp_store (scratch); the live data/state.json is untouched.
"""
import pytest

import app.main as main
from app import device_intel as di


def test_validate_device_id_accepts_seed_labels():
    for label in ("dev_01", "dev_04", "dev_09"):
        assert di.validate_device_id(label) == label


def test_validate_device_id_rejects_malformed():
    for bad in ("", "  ", "dev 04", "dev/04", "../x", "x" * 65, None, 42):
        with pytest.raises(ValueError):
            di.validate_device_id(bad)


def test_observations_derive_from_events_and_edges(tmp_store):
    obs = di.build_observations(tmp_store.state)
    assert obs, "seeded fixtures must yield observations"
    sources = {o.source for o in obs}
    assert sources == {"seed_event", "graph_edge"}
    assert all(o.synthetic for o in obs)
    assert all(o.device_id.startswith("dev_") for o in obs)


def test_profile_dev04_shared_across_four_accounts(tmp_store):
    profile = di.get_profile(tmp_store.state, "dev_04")
    assert profile is not None
    assert profile.device_id == "dev_04"
    assert profile.account_ids == ["acct_A", "acct_B", "acct_C", "acct_D"]
    assert profile.shared is True
    assert profile.first_seen <= profile.last_seen
    assert profile.txn_ids, "expected linked transactions"
    assert profile.evidence_refs["graph_edge_ids"], "needs edge attribution"
    assert profile.evidence_refs["event_ids"], "needs event attribution"


def test_profile_distinguishes_observation_from_identity(tmp_store):
    profile = di.get_profile(tmp_store.state, "dev_04")
    assert profile.identity_status == "observed_only"
    assert "not verified device identity" in profile.disclaimer


def test_profile_attributes_are_synthetic_and_declared(tmp_store):
    profile = di.get_profile(tmp_store.state, "dev_04")
    assert profile.attributes_source == "synthetic_demo_fixture"
    assert profile.attributes["device_type"] == "mobile"


def test_unknown_device_has_no_profile_or_attributes(tmp_store):
    assert di.get_profile(tmp_store.state, "dev_zz") is None


def test_shared_devices_attribution(tmp_store):
    shared = di.shared_devices(tmp_store.state)
    by_id = {s["device_id"]: s for s in shared}
    assert by_id["dev_04"]["account_ids"] == ["acct_A", "acct_B",
                                                "acct_C", "acct_D"]
    assert by_id["dev_02"]["account_ids"] == ["acct_F", "acct_G"]
    assert all(s["identity_status"] == "observed_only" for s in shared)
    assert all(s["synthetic"] for s in shared)


def test_device_endpoint_returns_profile(tmp_store):
    body = main.get_device("dev_04")
    assert body["device_id"] == "dev_04"
    assert body["shared"] is True
    assert body["attributes_source"] == "synthetic_demo_fixture"


def test_device_endpoint_404_unknown_400_malformed(tmp_store):
    with pytest.raises(main.AppError) as exc:
        main.get_device("dev_zz")
    assert exc.value.status == 404
    assert exc.value.code == "UNKNOWN_DEVICE"
    with pytest.raises(main.AppError) as exc2:
        main.get_device("../x")
    assert exc2.value.status == 400


def test_route_registered():
    paths = {route.path for route in main.app.routes}
    assert "/api/v1/devices/{device_id}" in paths
    assert "/api/v1/graph/{txn_id}" in paths  # neighbor route intact


def test_di03_changes_nothing_persisted(tmp_store):
    before = dict(tmp_store.state)
    di.build_observations(tmp_store.state)
    di.get_profile(tmp_store.state, "dev_04")
    di.shared_devices(tmp_store.state)
    main.get_device("dev_04")
    assert tmp_store.state == before


def test_risk_scores_unchanged(tmp_store):
    txn = main.get_transaction("txn_84721")
    assert txn["risk_transaction"]["score"] == 35
    assert txn["risk_network"]["score"] == 84


def test_graph_counts_unchanged(tmp_store):
    graph = main.get_graph("txn_84721")
    assert graph["counts"] == {"nodes": 22, "edges": 30}
    assert graph["provenance_errors"] == []
