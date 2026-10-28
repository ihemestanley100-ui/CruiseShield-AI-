"""T-009: every evidence item maps to real source records."""
from app.models import EvidencePackage
from app.store import Store


def test_evidence_package_maps_to_real_records(tmp_path):
    store = Store(tmp_path / "state.json")
    package = EvidencePackage.model_validate(
        store.state["evidence_packages"]["inv_84721"])
    assert len(package.items) == 1 + 8 + 30  # txn + rules + edges
    event_ids = {e["event_id"] for e in store.state["events"]}
    edge_ids = {e["edge_id"] for e in store.state["edges"]}
    node_ids = {n["node_id"] for n in store.state["nodes"]}
    rule_ids = {r["rule_result_id"]
                for r in store.state["rule_results"]["txn_84721"]}
    for item in package.items:
        assert set(item.event_ids) <= event_ids, item.evidence_id
        assert set(item.graph_edge_ids) <= edge_ids, item.evidence_id
        assert set(item.graph_node_ids) <= node_ids, item.evidence_id
        assert set(item.rule_result_ids) <= rule_ids, item.evidence_id
    assert [i.evidence_id for i in package.items] == sorted(
        i.evidence_id for i in package.items)
    assert package.package_hash
