"""T-001: reset determinism, expected counts, and pinned risk bands."""
import threading

import pytest

from app.store import Store


def test_missing_state_file_warns_before_reseed(tmp_path):
    with pytest.warns(RuntimeWarning, match="seeding fresh demo state"):
        Store(tmp_path / "missing.json")


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


def test_ambiguous_scenario_moderate_needs_judgment(tmp_path):
    store = Store(tmp_path / "state.json")
    store.reset("scn_ambiguous")
    counts = store.state["manifest"]["expected_graph_counts"]
    assert (counts["nodes"], counts["edges"], counts["transactions"],
            counts["events"]) == (4, 4, 2, 2)
    assert store.state["manifest"]["expected_risk_band"] == {
        "transaction": "LOW", "network": "MODERATE"}
    results = {r["rule_id"]: r["triggered"]
               for r in store.state["rule_results"]["txn_84740"]}
    assert results == {"R-001": False, "R-002": True, "R-003": True,
                       "R-004": False, "R-005": False, "R-006": False,
                       "R-007": True, "R-008": False}
    assert store.state["risk"]["txn_84740"]["transaction"]["score"] == 20
    assert store.state["risk"]["txn_84740"]["network"]["score"] == 38
    # Own investigation/case identities; switching scenarios is explicit.
    assert store.state["cases"][0]["case_id"] == "case_84740"
    assert store.state["investigations"][0]["investigation_id"] == "inv_84740"


def test_restart_reloads_decisions_and_audit(tmp_path):
    # G18: the JSON store survives a process restart (re-init from disk).
    from app import cases as cases_mod
    path = tmp_path / "state.json"
    store = Store(path)
    store.reset("scn_primary")
    cases_mod.record_decision(store, "case_84721", "Monitor", "TRIAGED",
                              "Triage.", "inv1")
    assert path.exists()
    revived = Store(path)
    assert revived.state["scenario_id"] == "scn_primary"
    assert revived.state["cases"][0]["status"] == "TRIAGED"
    assert len(revived.state["decisions"]) == 1
    assert revived.state["decisions"][0]["reason"] == "Triage."
    assert revived.state["audits"][-1]["action"] == "case.decision"
    assert revived.state["risk"]["txn_84721"]["network"]["score"] == 84


def test_concurrent_saves_do_not_collide(tmp_path):
    # Phase 11 (PERF-001): concurrent POST /api/v1/simulations returned
    # HTTP 500 — every _save() shared one fixed tmp path (WinError 32).
    store = Store(tmp_path / "state.json")
    errors: list = []

    def worker(n: int) -> None:
        try:
            for i in range(5):
                store.save_simulation({"simulation_id": f"race_{n}_{i}"})
        except Exception as exc:  # noqa: BLE001 — collected, asserted below
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    revived = Store(tmp_path / "state.json")
    assert len(revived.state["simulations"]) == 80
