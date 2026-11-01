"""DI-06 Intelligence association: txn/account/investigation linkage.

Derived layer only: references, no copies, no writes. Uses tmp_store;
live data/state.json untouched.
"""
import pytest

import app.main as main
from app import intel_link as link


def _inv_id(tmp_store):
    return tmp_store.state["investigations"][0]["investigation_id"]


# A. Transaction association --------------------------------------------
def test_txn_intel_full_linkage(tmp_store):
    out = link.transaction_intel(tmp_store.state, "txn_84721")
    assert out["transaction_id"] == "txn_84721"
    assert out["source_account_id"] == "acct_A"
    assert out["destination_account_id"] == "acct_B"
    assert out["transaction_time"] == "2026-10-27T10:00:00Z"
    assert {o["device_id"] for o in out["device_observations"]} == {"dev_04"}
    assert {o["ip_label"] for o in out["ip_observations"]} == {"ip_02"}
    assert {o["location_label"] for o in out["geolocation_observations"]} \
        == {"loc_01"}
    assert out["device_graph_refs"]["dev_04"], "graph refs expected"
    assert out["provenance"]["event_ids"], "provenance expected"
    assert out["synthetic"] is True


def test_txn_time_distinct_from_observation_time(tmp_store):
    out = link.transaction_intel(tmp_store.state, "txn_84721")
    assert out["transaction_time"]
    assert out["observation_first_seen"]


def test_txn_without_observations_valid(tmp_store):
    out = link.transaction_intel(tmp_store.state, "txn_84725")
    assert out is not None
    assert out["observation_first_seen"] == "not_available"


def test_txn_unknown_and_no_duplicates(tmp_store):
    assert link.transaction_intel(tmp_store.state, "txn_nope") is None
    out = link.transaction_intel(tmp_store.state, "txn_84721")
    ids = [o["obs_id"] for o in out["device_observations"]]
    assert len(ids) == len(set(ids))


# B. Account association --------------------------------------------------
def test_account_intel_summary(tmp_store):
    out = link.account_intel(tmp_store.state, "acct_A")
    assert out["account_id"] == "acct_A"
    assert "dev_04" in out["known_devices"]
    assert "ip_02" in out["known_ip_labels"]
    assert "loc_01" in out["known_geo_labels"]
    assert out["transaction_count"] >= 1
    assert out["first_seen"] <= out["last_seen"]
    assert out["synthetic"] is True


def test_account_shared_relationships_no_verdict(tmp_store):
    out = link.account_intel(tmp_store.state, "acct_B")
    assert any(s["device_id"] == "dev_04"
               for s in out["shared_devices"])
    blob = str(out).lower()
    assert "fraud" not in blob or "not proof of fraud" in blob
    assert "malicious" not in blob


def test_account_unknown_and_isolation(tmp_store):
    assert link.account_intel(tmp_store.state, "acct_nope") is None
    mine = link.account_intel(tmp_store.state, "acct_K")
    assert mine["known_devices"] == ["dev_01"]
    assert "dev_04" not in mine["known_devices"]


# C. Investigation association -----------------------------------------------
def test_investigation_intel_links_only_own_txn(tmp_store):
    inv_id = _inv_id(tmp_store)
    out = link.investigation_intel(tmp_store.state, inv_id)
    assert out["investigation_id"] == inv_id
    linked = out["transaction_intel"]
    assert linked["transaction_id"] == "txn_84721"
    assert {o["device_id"] for o in linked["device_observations"]} \
        == {"dev_04"}


def test_investigation_unknown(tmp_store):
    assert link.investigation_intel(tmp_store.state, "inv_nope") is None


# D. Geolocation comparison -----------------------------------------------------
def test_compare_pair_outcomes():
    base = {"obs_id": "o1", "pathway": "ip_derived", "label": "loc_01",
            "latitude": 6.45, "longitude": 3.39,
            "observed_at": "2026-10-30T10:00:00Z",
            "confidence": "medium", "source": "stub"}
    other = dict(base, obs_id="o2")
    same = link.compare_pair(base, other)
    assert same["outcome"] == "SAME_LOCATION"
    far_in = dict(base, obs_id="o2", latitude=51.5, longitude=-0.12)
    far = link.compare_pair(base, far_in)
    assert far["outcome"] == "DIFFERENT_LOCATION"
    cross_in = dict(far_in, pathway="device")
    conflict = link.compare_pair(base, cross_in)
    assert conflict["outcome"] == "CONFLICTING_LOCATION"
    for result in (same, far, conflict):
        assert result["fraud_determination"] == "none"


def test_compare_pair_fails_safe_and_unknown():
    base = {"obs_id": "o1", "pathway": "ip_derived", "label": "loc_01",
            "latitude": 6.45, "longitude": 3.39,
            "observed_at": "2026-10-30T10:00:00Z",
            "confidence": "medium", "source": "stub"}
    no_coords = dict(base, obs_id="o2", latitude=None, longitude=None)
    assert link.compare_pair(base, no_coords)["outcome"] \
        == "INSUFFICIENT_EVIDENCE"
    assert link.compare_pair("bogus", base)["outcome"] == "UNKNOWN"
    for result in (link.compare_pair(base, no_coords),
                   link.compare_pair("bogus", base)):
        assert result["fraud_determination"] == "none"


def test_compare_account_geo_insufficient_on_fixtures(tmp_store):
    out = link.compare_account_geo(tmp_store.state, "acct_A")
    assert out["outcome"] == "INSUFFICIENT_EVIDENCE"
    assert out["fraud_determination"] == "none"


# E/F. Provenance + API --------------------------------------------------------------
def test_provenance_and_synthetic_flags(tmp_store):
    out = link.transaction_intel(tmp_store.state, "txn_84721")
    assert out["provenance"]["event_ids"]
    assert all(o["synthetic"] for o in out["device_observations"])


def test_endpoints_valid_unknown(tmp_store):
    assert main.get_transaction_intel("txn_84721")["transaction_id"] \
        == "txn_84721"
    assert main.get_account_intel("acct_A")["account_id"] == "acct_A"
    inv_id = _inv_id(tmp_store)
    assert main.get_investigation_intel(inv_id)["investigation_id"] == inv_id
    with pytest.raises(main.AppError) as exc:
        main.get_transaction_intel("txn_nope")
    assert exc.value.status == 404
    with pytest.raises(main.AppError) as exc2:
        main.get_account_intel("acct_nope")
    assert exc2.value.code == "UNKNOWN_ACCOUNT"
    with pytest.raises(main.AppError) as exc3:
        main.get_investigation_intel("inv_nope")
    assert exc3.value.status == 404


def test_routes_registered_and_read_only(tmp_store):
    paths = {route.path for route in main.app.routes}
    assert "/api/v1/transactions/{txn_id}/intel" in paths
    assert "/api/v1/accounts/{account_id}/intel" in paths
    assert "/api/v1/investigations/{inv_id}/intel" in paths
    before = dict(tmp_store.state)
    main.get_transaction_intel("txn_84721")
    main.get_account_intel("acct_A")
    main.get_investigation_intel(_inv_id(tmp_store))
    assert tmp_store.state == before
    post_paths = {r.path for r in main.app.routes
                  if "POST" in getattr(r, "methods", set())
                  and r.path.endswith("/intel")}
    assert post_paths == set()
