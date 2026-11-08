"""Tracing scenarios (H.7 evidence): multi-hop, fan-in/out, currency
breaks, cash legs, hop caps, and provenance upgrades on synthetic
fixtures. Fixtures exercise the engine only; they assert engine
behavior, never production facts."""
from __future__ import annotations

from app import tracing


def _txn(tid, sender, receiver, currency="NGN", **kw):
    base = {"transaction_id": tid, "channel": "TRANSFER",
            "amount_minor": 5000, "currency": currency,
            "sender_account_id": sender,
            "receiver_account_id": receiver}
    base.update(kw)
    return base


def _chain(n=4, currency="NGN"):
    legs = []
    for i in range(n):
        legs.append(_txn("c%d" % i, "acct_%d" % i, "acct_%d" % (i + 1),
                         currency))
    return legs


def test_multihop_chain_all_strong():
    legs = _chain(4)
    trace = tracing.build_trace(legs, [], "c0")
    assert len(trace["movements"]) == 3
    assert all(m["status"] == "STRONGLY_SUPPORTED_LINK"
               for m in trace["movements"])
    assert [m["hop"] for m in trace["movements"]] == [1, 2, 3]
    assert trace["visited_transactions"] == ["c0", "c1", "c2", "c3"]


def test_fanin_collection():
    legs = [_txn("f%d" % i, "sender_%d" % i, "mule")
            for i in range(3)]
    legs.append(_txn("sink", "other", "elsewhere", "USD"))
    trace = tracing.build_trace(legs, [], "f0")
    assert trace["movements"] == []
    assert any("downstream" in lim or "off-ledger" in lim
               for lim in trace["limitations"])


def test_fanout_distribution():
    legs = [_txn("root", "origin", "hub"),
            _txn("o1", "hub", "b1"), _txn("o2", "hub", "b2")]
    trace = tracing.build_trace(legs, [], "root")
    assert len(trace["movements"]) == 2
    assert {m["to_transaction"] for m in trace["movements"]} == {"o1", "o2"}


def test_currency_break_downgrades_to_possible():
    legs = [_txn("a", "x", "mid", "NGN"),
            _txn("b", "mid", "y", "USD")]
    out = tracing.link_strength(legs[0], legs[1])
    assert out["status"] == "POSSIBLE_LINK"
    assert "USD" in out["evidence"] or "NGN" in out["evidence"]
    trace = tracing.build_trace(legs, [], "a")
    assert trace["movements"][0]["status"] == "POSSIBLE_LINK"


def test_cash_leg_breaks_determinism():
    legs = [_txn("a", "x", "mid", "NGN"),
            _txn("b", "mid", "y", None)]
    trace = tracing.build_trace(legs, [], "a")
    assert trace["movements"][0]["status"] == "POSSIBLE_LINK"
    assert trace["limitations"], "currency gap must surface a limit"


def test_hop_cap_marks_unknown_downstream():
    legs = _chain(5)
    trace = tracing.build_trace(legs, [], "c0", max_hops=2)
    assert len(trace["movements"]) == 2
    assert any("Hop limit" in lim for lim in trace["limitations"])


def test_provider_reference_confirms():
    legs = [_txn("a", "x", "mid", provider_reference="prov-1"),
            _txn("b", "mid", "y", provider_reference="prov-1")]
    assert tracing.link_strength(legs[0], legs[1])["status"] == \
        "CONFIRMED_LINK"


def test_provenanced_edge_upgrades():
    legs = [_txn("a", "x", "mid"), _txn("b", "mid", "y")]
    edges = [{"edge_id": "e1", "source_node_id": "mid",
              "target_node_id": "mid", "source_event_ids": ["ev1"]}]
    trace = tracing.build_trace(legs, edges, "a")
    assert trace["movements"][0]["status"] == "PROVIDER_REPORTED_LINK"


def test_unprovenanced_edge_withheld_with_limit():
    legs = [_txn("a", "x", "mid"), _txn("b", "mid", "y")]
    edges = [{"edge_id": "e2", "source_node_id": "mid",
              "target_node_id": "mid"}]
    trace = tracing.build_trace(legs, edges, "a")
    assert trace["movements"][0]["status"] == "STRONGLY_SUPPORTED_LINK"
    assert any("provenance" in lim for lim in trace["limitations"])


def test_no_match_isolated():
    legs = [_txn("a", "x", "y"), _txn("b", "p", "q", "USD")]
    assert tracing.link_strength(legs[0], legs[1])["status"] == "NO_MATCH"
    trace = tracing.build_trace(legs, [], "a")
    assert trace["movements"] == []
