"""M3 fraud validation matrix: labeled synthetic cases over R-001..R-008.

Every case is constructed so its expected triggered-set is known; the
suite asserts per-rule precision/recall of 1.0 on this labeled set,
exact score arithmetic, and band boundaries. Synthetic-data validation
only — not real-world performance evidence.
"""
import pytest

from app import detection as detection_mod
from app import rules as rules_mod

T0 = "2026-01-01T10:00:00Z"
T1 = "2026-01-01T10:30:00Z"  # within the 120-minute window of T0


def _txn(tid, sender, receiver, amount=1000, at=T0):
    return {"transaction_id": tid, "sender_account_id": sender,
            "receiver_account_id": receiver, "amount_minor": amount,
            "occurred_at": at}


def _edge(eid, rel, src, tgt):
    return {"edge_id": eid, "relationship_type": rel,
            "source_node_id": src, "target_node_id": tgt,
            "source_event_ids": ["seed"]}


def _triggered(txn_id, txns, edges):
    return {r.rule_id for r in rules_mod.evaluate(txn_id, txns, edges, "t")
            if r.triggered}


def test_negative_control_triggers_nothing():
    txns = [_txn("txn_1", "A", "B")]
    assert _triggered("txn_1", txns, []) == set()
    results = rules_mod.evaluate("txn_1", txns, [], "t")
    net = rules_mod.assess("txn_1", "network", txns, [], results, "t")
    assert net["score"] == rules_mod.BASE_SCORE == 12
    assert rules_mod.band_for(net["score"]) == "LOW"


def test_amount_rule_positive():
    txns = [_txn("txn_1", "A", "B", amount=40000000)]
    assert _triggered("txn_1", txns, []) == {"R-001"}


def test_velocity_pair_triggers():
    txns = [_txn("txn_1", "A", "B", at=T0), _txn("txn_2", "A", "C", at=T1)]
    assert _triggered("txn_1", txns, []) == {"R-002", "R-007"}


def test_device_phone_beneficiary_merchant_sharing():
    txns = [_txn("txn_1", "A", "B")]
    edges = [_edge("e1", "USES_DEVICE", "A", "dev_1"),
             _edge("e2", "USES_DEVICE", "Q", "dev_1"),
             _edge("e3", "USES_PHONE", "A", "ph_1"),
             _edge("e4", "USES_PHONE", "Q", "ph_1"),
             _edge("e5", "BENEFICIARY_OF", "A", "ben_1"),
             _edge("e6", "BENEFICIARY_OF", "Q", "ben_1"),
             _edge("e7", "PAID_MERCHANT", "A", "m_1"),
             _edge("e8", "PAID_MERCHANT", "Q", "m_1")]
    assert _triggered("txn_1", txns, edges) == {"R-003", "R-004", "R-005",
                                               "R-008"}


def test_fan_in_and_fan_out():
    txns = [_txn("txn_1", "S1", "R"), _txn("txn_2", "S2", "R"),
            _txn("txn_3", "S3", "R"), _txn("txn_4", "S1", "R2")]
    assert "R-006" in _triggered("txn_1", txns, [])
    assert _triggered("txn_4", txns, []) >= {"R-007"}


def test_all_rules_fire_exact_score_and_band():
    txns = [_txn("txn_1", "S", "R1", amount=40000000, at=T0),
            _txn("txn_2", "S", "R2", at=T1),
            _txn("txn_3", "X", "R1", at=T0),
            _txn("txn_4", "Y", "R1", at=T0)]
    edges = [_edge("e1", "USES_DEVICE", "S", "dev_1"),
             _edge("e2", "USES_DEVICE", "Q", "dev_1"),
             _edge("e3", "USES_PHONE", "S", "ph_1"),
             _edge("e4", "USES_PHONE", "Q", "ph_1"),
             _edge("e5", "BENEFICIARY_OF", "S", "ben_1"),
             _edge("e6", "BENEFICIARY_OF", "Q", "ben_1"),
             _edge("e7", "PAID_MERCHANT", "S", "m_1"),
             _edge("e8", "PAID_MERCHANT", "Q", "m_1")]
    assert _triggered("txn_1", txns, edges) == {
        "R-001", "R-002", "R-003", "R-004",
        "R-005", "R-006", "R-007", "R-008"}
    results = rules_mod.evaluate("txn_1", txns, edges, "t")
    net = rules_mod.assess("txn_1", "network", txns, edges, results, "t")
    assert net["score"] == 12 + 15 + 8 + 12 + 10 + 8 + 8 + 6 + 5 == 84
    assert rules_mod.band_for(84) == "HIGH"
    txn_scope = rules_mod.assess("txn_1", "transaction", txns, edges,
                                results, "t")
    assert txn_scope["score"] == 12 + 15 + 8 == 35


def test_band_boundaries_and_scope_errors():
    assert [rules_mod.band_for(s) for s in (0, 29)] == ["LOW", "LOW"]
    assert [rules_mod.band_for(s) for s in (30, 59)] == ["MODERATE",
                                                        "MODERATE"]
    assert [rules_mod.band_for(s) for s in (60, 84)] == ["HIGH", "HIGH"]
    assert [rules_mod.band_for(s) for s in (85, 100, 500)] == ["CRITICAL"] * 3
    with pytest.raises(ValueError, match="UNKNOWN_SCOPE"):
        rules_mod.assess("txn_1", "nope", [], [], [], "t")
    with pytest.raises(ValueError, match="UNKNOWN_TXN"):
        rules_mod.evaluate("txn_zz", [_txn("txn_1", "A", "B")], [], "t")


def test_labeled_matrix_precision_recall():
    cases = [
        ([_txn("txn_1", "A", "B")], [], "txn_1", set()),
        ([_txn("txn_1", "A", "B", amount=50000000)], [], "txn_1", {"R-001"}),
        ([_txn("txn_1", "A", "B", at=T0), _txn("txn_2", "A", "C", at=T1)],
         [], "txn_1", {"R-002", "R-007"}),
    ]
    for rule in rules_mod.RULES:
        tp = fp = fn = 0
        for txns, edges, tid, expected in cases:
            got = _triggered(tid, txns, edges)
            tp += rule.rule_id in got and rule.rule_id in expected
            fp += rule.rule_id in got and rule.rule_id not in expected
            fn += rule.rule_id not in got and rule.rule_id in expected
        precision = tp / (tp + fp) if (tp + fp) else 1.0
        recall = tp / (tp + fn) if (tp + fn) else 1.0
        assert (precision, recall) == (1.0, 1.0), rule.rule_id


def test_detection_evaluate_all_pins_versions_and_skips_bad_rows():
    txns = [_txn("txn_1", "A", "B", amount=40000000), "corrupt-row",
            _txn("txn_2", "A", "C", at=T1)]
    out = detection_mod.evaluate_all(txns, [])
    assert any(e.get("family") == "INPUT"
               for e in out["meta"]["family_errors"])
    assert out["meta"]["transactions_evaluated"] == 2
    fams = {s["detector_family"] for s in out["signals"]}
    assert {"RULE_MATCH", "VELOCITY"} <= fams
    assert all(s.get("detector_version") for s in out["signals"])
    assert all(s.get("execution_id") for s in out["signals"])
