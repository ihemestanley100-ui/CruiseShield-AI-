"""Deterministic graph queries, provenance checks, and network features."""
from __future__ import annotations

from datetime import datetime, timedelta


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_provenance(edges: list[dict]) -> list[str]:
    """Return edge IDs that lack usable provenance (must be empty)."""
    bad: list[str] = []
    for edge in edges:
        if not edge.get("source_event_ids"):
            bad.append(edge.get("edge_id", "?"))
    return bad


def neighborhood(nodes: list[dict], edges: list[dict], seeds: set[str],
                 depth: int = 2) -> tuple[list[dict], list[dict]]:
    """BFS node/edge neighborhood around seed node IDs (deterministic order)."""
    seen = set(seeds)
    frontier = set(seeds)
    picked_edges: list[dict] = []
    for _ in range(depth):
        nxt: set[str] = set()
        for edge in sorted(edges, key=lambda e: e["edge_id"]):
            src, tgt = edge["source_node_id"], edge["target_node_id"]
            if src in frontier or tgt in frontier:
                picked_edges.append(edge)
                for node_id in (src, tgt):
                    if node_id not in seen:
                        seen.add(node_id)
                        nxt.add(node_id)
        frontier = nxt
    picked_nodes = [n for n in sorted(nodes, key=lambda n: n["node_id"])
                    if n["node_id"] in seen]
    return picked_nodes, picked_edges


def _sharing(edges: list[dict], relationship: str) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for edge in edges:
        if edge["relationship_type"] == relationship:
            grouped.setdefault(edge["target_node_id"], []).append(edge["source_node_id"])
    return {key: sorted(set(val)) for key, val in grouped.items()}


def features_for_transaction(txn: dict, transactions: list[dict],
                             edges: list[dict]) -> dict:
    """Compute deterministic graph/event features for rule evaluation."""
    sender = txn["sender_account_id"]
    receiver = txn["receiver_account_id"]
    center = _parse_ts(txn["occurred_at"])
    window = timedelta(minutes=120)
    sender_txns = [t for t in transactions
                   if t["sender_account_id"] == sender
                   and abs(_parse_ts(t["occurred_at"]) - center) <= window]
    senders_to_receiver = sorted({t["sender_account_id"] for t in transactions
                                  if t["receiver_account_id"] == receiver})
    receivers_of_sender = sorted({t["receiver_account_id"] for t in transactions
                                  if t["sender_account_id"] == sender})
    devices = _sharing(edges, "USES_DEVICE")
    phones = _sharing(edges, "USES_PHONE")
    merchants = _sharing(edges, "PAID_MERCHANT")
    beneficiaries = _sharing(edges, "BENEFICIARY_OF")
    return {
        "amount_minor": txn["amount_minor"],
        "sender_outgoing_120m": len(sender_txns),
        "fan_in_distinct_senders": len(senders_to_receiver),
        "fan_in_senders": senders_to_receiver,
        "fan_out_distinct_receivers": len(receivers_of_sender),
        "fan_out_receivers": receivers_of_sender,
        "device_sharing_max": max([len(v) for v in devices.values()] or [0]),
        "device_sharing": devices,
        "phone_sharing_max": max([len(v) for v in phones.values()] or [0]),
        "phone_sharing": phones,
        "merchant_sharing_max": max([len(v) for v in merchants.values()] or [0]),
        "merchant_sharing": merchants,
        "beneficiary_links_max": max([len(v) for v in beneficiaries.values()] or [0]),
        "beneficiary_links": beneficiaries,
    }
