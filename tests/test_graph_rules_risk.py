"""T-004..T-008: provenance, rule boundaries, deterministic scoring."""
from app import graph as graph_mod
from app import rules as rules_mod
from app.store import Store


def _state(tmp_path):
    return Store(tmp_path / "state.json").state


def test_all_edges_have_provenance(tmp_path):
    assert graph_mod.validate_provenance(_state(tmp_path)["edges"]) == []


def test_provenance_checker_catches_missing():
    assert graph_mod.validate_provenance(
        [{"edge_id": "edge_bad", "source_event_ids": []}]) == ["edge_bad"]


def test_amount_rule_boundary(tmp_path):
    state = _state(tmp_path)
    txns = [dict(t, amount_minor=39999999) if t["transaction_id"] == "txn_84721" else t
            for t in state["transactions"]]
    below = rules_mod.evaluate("txn_84721", txns, state["edges"], "t")
    assert next(r for r in below if r.rule_id == "R-001").triggered is False
    txns = [dict(t, amount_minor=40000000) if t["transaction_id"] == "txn_84721" else t
            for t in state["transactions"]]
    at = rules_mod.evaluate("txn_84721", txns, state["edges"], "t")
    assert next(r for r in at if r.rule_id == "R-001").triggered is True


def test_score_matches_documented_formula(tmp_path):
    state = _state(tmp_path)
    results = rules_mod.evaluate("txn_84721", state["transactions"],
                                 state["edges"], "t")
    net = rules_mod.assess("txn_84721", "network", state["transactions"],
                           state["edges"], results, "t")
    weights = {r.rule_id: r.weight for r in rules_mod.RULES}
    expected = rules_mod.BASE_SCORE + sum(
        weights[r.rule_id] for r in results if r.triggered)
    assert net["score"] == min(100, expected)
    assert [c["rule_id"] for c in net["contributions"]] == [r.rule_id for r in results]


def test_neighborhood_is_deterministic_subset(tmp_path):
    state = _state(tmp_path)
    nodes, edges = graph_mod.neighborhood(
        state["nodes"], state["edges"], {"acct_A", "acct_B"}, depth=2)
    first = ([n["node_id"] for n in nodes], [e["edge_id"] for e in edges])
    nodes2, edges2 = graph_mod.neighborhood(
        state["nodes"], state["edges"], {"acct_B", "acct_A"}, depth=2)
    assert ([n["node_id"] for n in nodes2], [e["edge_id"] for e in edges2]) == first
    assert "acct_A" in first[0] and "dev_04" in first[0]


def test_rule_evaluation_deterministic_over_repeats(tmp_path):
    # G03: the synthetic benchmark — 200 evaluations, identical output.
    import json as jsonlib
    state = _state(tmp_path)
    first = jsonlib.dumps(
        [r.model_dump() for r in rules_mod.evaluate(
            "txn_84721", state["transactions"], state["edges"], "t")],
        sort_keys=True, default=str)
    for _ in range(200):
        again = jsonlib.dumps(
            [r.model_dump() for r in rules_mod.evaluate(
                "txn_84721", state["transactions"], state["edges"], "t")],
            sort_keys=True, default=str)
        assert again == first


def test_unknown_scope_rejected(tmp_path):
    state = _state(tmp_path)
    results = rules_mod.evaluate("txn_84721", state["transactions"],
                                 state["edges"], "t")
    try:
        rules_mod.assess("txn_84721", "bogus", state["transactions"],
                         state["edges"], results, "t")
    except ValueError as exc:
        assert "UNKNOWN_SCOPE" in str(exc)
    else:
        raise AssertionError("expected UNKNOWN_SCOPE")
