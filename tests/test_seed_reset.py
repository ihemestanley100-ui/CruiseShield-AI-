"""T-001: reset determinism, expected counts, and pinned risk bands."""
import pytest

from app.store import Store


def test_reset_twice_reproduces_seed(tmp_path):
    first = Store(tmp_path / "a.json")
    h1, m1 = first.state["seed_hash"], first.state["manifest"]
    second = Store(tmp_path / "b.json")
    assert second.state["seed_hash"] == h1
    assert second.state["manifest"]["expected_graph_counts"] == m1["expected_graph_counts"]
    assert second.state["manifest"]["expected_rule_results"] == m1["expected_rule_results"]
    assert second.state["manifest"]["expected_risk_band"] == m1["expected_risk_band"]
    assert second.state["manifest"]["expected_evidence_ids"] == m1["expected_evidence_ids"]
    # No duplicate records.
    for key, id_field in (("events", "event_id"), ("transactions", "transaction_id"),
                          ("nodes", "node_id"), ("edges", "edge_id")):
        ids = [r[id_field] for r in second.state[key]]
        assert len(ids) == len(set(ids)), key
    # Distinct run identity per reset.
    assert first.state["run_id"] != second.state["run_id"]


def test_primary_counts_and_bands_pinned(tmp_path):
    store = Store(tmp_path / "state.json")
    assert store.state["manifest"]["expected_graph_counts"] == {
        "nodes": 22, "edges": 30, "accounts": 12, "devices": 4, "phones": 3,
        "merchants": 2, "beneficiaries": 1, "transactions": 11, "events": 11,
    }
    assert store.state["manifest"]["expected_risk_band"] == {
        "transaction": "MODERATE", "network": "HIGH"}
    results = {r["rule_id"]: r["triggered"]
               for r in store.state["rule_results"]["txn_84721"]}
    assert results == {f"R-00{i}": True for i in range(1, 9)}
    assert store.state["risk"]["txn_84721"]["transaction"]["score"] == 35
    assert store.state["risk"]["txn_84721"]["network"]["score"] == 84


def test_false_positive_scenario_low_without_network(tmp_path):
    store = Store(tmp_path / "state.json")
    store.reset("scn_false_positive")
    assert store.state["manifest"]["expected_graph_counts"]["nodes"] == 2
    assert store.state["manifest"]["expected_graph_counts"]["edges"] == 1
    assert store.state["manifest"]["expected_risk_band"] == {
        "transaction": "LOW", "network": "LOW"}
    results = {r["rule_id"]: r["triggered"]
               for r in store.state["rule_results"]["txn_84730"]}
    assert results["R-001"] is True  # large amount still observed
    assert results["R-003"] is False  # but no network evidence


def test_unknown_scenario_rejected(tmp_path):
    store = Store(tmp_path / "state.json")
    with pytest.raises(ValueError, match="UNKNOWN_SCENARIO"):
        store.reset("scn_nope")
