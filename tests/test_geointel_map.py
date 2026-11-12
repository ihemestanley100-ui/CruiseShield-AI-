"""Map payloads, relationships, summaries, metrics (derived only)."""
from app import intel_auth as authz_mod
from app import investigation_map as invmap
from app import location_obs as loc

PURPOSE = "AUTHORIZED_FRAUD_INVESTIGATION"


def _observe(store):
    authz = authz_mod.create_authorization(
        store, "org_primary", "inv_84721", "u", "SUBJ-MAP-1",
        PURPOSE, "court order CO-9", "NG", "map evidence")
    authz_mod.decide_authorization(store,
                                   authz["authorization_id"],
                                   "boss", True, "CO-9")
    return loc.record_observation(
        store, {"source_type": "terminal-data", "latitude": 6.5,
                "longitude": 3.4, "observed_at": "2026-11-01T00:00:00Z",
                "received_at": "2026-11-01T00:01:00Z"},
        "SUBJ-MAP-1", PURPOSE, "org_primary", "u", "org_primary",
        investigation_id="inv_84721", device_ref="dev_04")


def test_twelve_layers_present_with_reasons(tmp_store):
    body = invmap.investigation_map(tmp_store.state, "inv_84721",
                                    masked=False)
    assert len(body["layers"]) == 12
    assert set(body["layers"]) == set(invmap.LAYERS)
    for name, layer in body["layers"].items():
        assert layer["item_count"] == len(layer["items"])
        if not layer["items"]:
            assert layer["reason_if_empty"], name


def test_observations_surface_masked_and_full(tmp_store):
    _observe(tmp_store)
    full = invmap.investigation_map(tmp_store.state, "inv_84721",
                                    masked=False)
    hist = full["layers"]["historical_observations"]
    assert hist["item_count"] == 1
    assert hist["items"][0]["coordinates"]["latitude"] == 6.5
    masked = invmap.investigation_map(tmp_store.state, "inv_84721",
                                      masked=True)
    item = masked["layers"]["historical_observations"]["items"][0]
    assert item["coordinates"] is None
    assert item["masked"] is True


def test_locations_filters(tmp_store):
    _observe(tmp_store)
    rows = invmap.investigation_locations(tmp_store.state,
                                          "inv_84721", False)
    assert len(rows) == 1
    assert invmap.investigation_locations(
        tmp_store.state, "inv_84721", False,
        status="NOPE") == []
    assert invmap.investigation_locations(
        tmp_store.state, "inv_84721", False,
        provider="nope") == []


def test_relationships_cap_derived_at_observed(tmp_store):
    _observe(tmp_store)
    edges = invmap.investigation_relationships(tmp_store.state,
                                               "inv_84721")
    assert len(edges) > 30  # stored edges + 1 derived link
    derived = [e for e in edges
               if e["edge_id"].startswith("derived_")]
    assert len(derived) == 1
    assert derived[0]["strength"] == "OBSERVED"
    assert "DIRECTLY_VERIFIED" not in {e["strength"] for e in edges}


def test_summarize_evidence_grounded(tmp_store):
    record = _observe(tmp_store)
    summary = invmap.summarize_evidence({"records": [
        record,
        {"verification_id": "idv_1", "factors": [
            {"factor": "dob-plausible", "result": "fail"}],
         "limitations": ["unconfirmed"], "missing": ["provider"]}]})
    assert summary["records_reviewed"] == 2
    assert summary["discrepancies"][0]["factor"] == "dob-plausible"
    assert summary["uncertainties"]
    assert summary["missing_evidence"]
    assert summary["model_used"] is None
    assert "guilt" not in str(summary).lower()


def test_metrics_counts_no_history(tmp_store):
    _observe(tmp_store)
    body = invmap.metrics(tmp_store.state, "org_primary")
    assert body["counts"]["location_observations"]["total"] == 1
    assert body["counts"]["identity_verifications"]["total"] == 0
    assert body["history"].startswith("none")
    other = invmap.metrics(tmp_store.state, "org_other")
    assert other["counts"]["location_observations"]["total"] == 0
