"""Deterministic replay over the seeded event sequence."""
from __future__ import annotations


def ordered_events(state: dict) -> list[dict]:
    return sorted(state["events"], key=lambda e: (e["occurred_at"], e["event_id"]))


def state_at(state: dict, cursor: int) -> dict:
    events = ordered_events(state)
    total = len(events)
    cursor = max(0, min(cursor, total))
    seen = events[:cursor]
    seen_ids = {e["event_id"] for e in seen}
    txn_ids = sorted({e["transaction"]["transaction_id"] for e in seen})
    edge_ids = sorted(e["edge_id"] for e in state["edges"]
                      if e["source_event_ids"]
                      and e["source_event_ids"][0] in seen_ids)
    current = seen[-1] if seen else None
    return {
        "scenario_id": state["scenario_id"], "cursor": cursor, "total": total,
        "current_event": current,
        "cumulative_event_ids": sorted(seen_ids),
        "cumulative_transaction_ids": txn_ids,
        "cumulative_edge_ids": edge_ids,
        "counts": {"events": len(seen), "transactions": len(txn_ids),
                   "edges": len(edge_ids)},
    }
