"""DI-07 Graph intel overlay: derived nodes, edge gates, no persistence.

Uses tmp_store (scratch); live data/state.json untouched.
"""
import app.main as main
from app import graph_intel as gi


def _edge(**over):
    base = {"edge_id": "e1", "source_node_id": "acct_A",
            "relationship_type": "ACCOUNT_USES_DEVICE",
            "target_node_id": "dev_04", "source_obs_id": "o1",
            "source": "seed_event", "status": "derived",
            "evidence_refs": ["evidence_edge_1"]}
    base.update(over)
    return base


# B/C. Node builders + edge gates -------------------------------------------
def test_device_detail_enrichment(tmp_store):
    detail = gi.device_detail(tmp_store.state, "dev_04")
    assert detail["node_type"] == "device"
    assert detail["identity_status"] == "observed_only"
    assert detail["linked_accounts"] == 4
    assert detail["derived"] is True and detail["synthetic"] is True
    assert gi.device_detail(tmp_store.state, "dev_zz") is None


def test_ip_node_requires_real_address():
    node = gi.ip_node_for("8.8.8.8", [{"obs_id": "o1", "txn_id": "t",
                                       "account_id": "a"}])
    assert node["node_type"] == "ip"
    assert node["classification"] == "public"
    assert node["intel"] == "unavailable"
    assert gi.ip_node_for("ip_02", []) is None
    assert gi.ip_node_for("bogus", []) is None


def test_location_node_requires_resolved_geo():
    assert gi.location_node_for("loc_01", [], None) is None
    assert gi.location_node_for("loc_01", [],
                                {"status": "unavailable"}) is None
    node = gi.location_node_for(
        "loc_01", [{"obs_id": "o1"}],
        {"status": "resolved", "city": "Lagos", "country_code": "NG",
         "confidence": "medium", "observed_at": "2026-10-30T10:00:00Z"})
    assert node["node_type"] == "location"
    assert node["approximate_only"] is True


def test_edge_gates():
    nodes = {"acct_A", "dev_04"}
    assert gi.validate_derived_edge(_edge(), nodes) == (True, "ok")
    assert gi.validate_derived_edge(_edge(edge_id=""), nodes)[0] is False
    assert gi.validate_derived_edge(
        _edge(source_node_id="acct_X"), nodes)[1] == "unknown_source_node"
    assert gi.validate_derived_edge(
        _edge(target_node_id="dev_X"), nodes)[1] == "unknown_target_node"
    assert gi.validate_derived_edge(
        _edge(relationship_type="MADE_UP"), nodes)[1] \
        == "relationship_type_not_allowed"
    assert gi.validate_derived_edge(
        _edge(status="confirmed", evidence_refs=[]), nodes)[1] \
        == "confirmed_requires_evidence_refs"


# Overlay + endpoint --------------------------------------------------------------
def test_overlay_honest_empty_on_fixtures(tmp_store):
    overlay = gi.build_overlay(tmp_store.state, "txn_84721")
    assert overlay["nodes"] == []
    assert overlay["edges"] == []
    assert overlay["unavailable"]["ip"].startswith("labels_without_address")
    assert overlay["unavailable"]["location"].startswith("labels_without_geo")
    assert overlay["node_details"]["dev_04"]["linked_accounts"] == 4
    assert overlay["counts"]["base_nodes"] == 22
    assert overlay["counts"]["base_edges"] == 30
    assert overlay["derived"] is True
    assert gi.build_overlay(tmp_store.state, "txn_nope") is None


def test_overlay_endpoint_and_routes(tmp_store):
    body = main.get_graph_overlay("txn_84721")
    assert body["transaction_id"] == "txn_84721"
    assert body["counts"]["overlay_nodes"] == 0
    try:
        main.get_graph_overlay("txn_nope")
        raise AssertionError("expected 404")
    except main.AppError as exc:
        assert exc.status == 404
    paths = {route.path for route in main.app.routes}
    assert "/api/v1/graph/{txn_id}/overlay" in paths
    assert "/api/v1/graph/{txn_id}" in paths


def test_proposed_edges_fail_derived_gates_by_design(tmp_store):
    """DI-04 proposals are inert review input, not valid DI-07 edges.

    They use a different relationship vocabulary and carry no provenance
    gate fields, so the validator must reject every one. This pins the
    boundary: neither side may silently drift into misuse, and any future
    wiring must pass the gates explicitly.
    """
    from app import ip_intel as ip
    nodes = {n["node_id"] for n in tmp_store.state["nodes"]}
    proposed = ip.proposed_edges(tmp_store.state)
    assert proposed, "expected proposal fixtures"
    assert {e["relationship_type"]
            for e in proposed}.isdisjoint(gi.ALLOWED_RELATIONSHIPS)
    for edge in proposed:
        ok, reason = gi.validate_derived_edge(edge, nodes)
        assert ok is False
        assert reason in ("missing_source_obs_id", "missing_source",
                          "unknown_source_node", "unknown_target_node",
                          "relationship_type_not_allowed")


def test_overlay_changes_nothing(tmp_store):
    before_nodes = list(tmp_store.state["nodes"])
    before_edges = list(tmp_store.state["edges"])
    gi.build_overlay(tmp_store.state, "txn_84721")
    main.get_graph_overlay("txn_84721")
    assert tmp_store.state["nodes"] == before_nodes
    assert tmp_store.state["edges"] == before_edges


# F. Risk + evidence isolation --------------------------------------------------------
def test_risk_evidence_graph_pins(tmp_store):
    txn = main.get_transaction("txn_84721")
    assert txn["risk_transaction"]["score"] == 35
    assert txn["risk_network"]["score"] == 84
    graph = main.get_graph("txn_84721")
    assert graph["counts"] == {"nodes": 22, "edges": 30}
    inv = main.get_investigation("inv_84721")
    assert inv["evidence_count"] == 39
