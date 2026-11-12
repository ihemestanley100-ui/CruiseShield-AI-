"""Deterministic graph queries, provenance checks, and network features."""
from __future__ import annotations

from datetime import datetime, timedelta


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


# MS-DETECT-001 aggregate-detector windows/thresholds (rule v1.0).
# Structuring (R-009): repeated sub-threshold transfers whose combined
# value reaches the R-001 large-transfer line. Decline repetition
# (R-010): repeated DECLINED authorizations from one sender.
STRUCTURING_WINDOW_MINUTES = 1440
STRUCTURING_MIN_COUNT = 3
STRUCTURING_AMOUNT_LINE = 40000000
STRUCTURING_MIN_TOTAL = 40000000
DECLINE_WINDOW_MINUTES = 1440
DECLINE_MIN_COUNT = 3


def _safe_ts(value: object) -> datetime | None:
    """Parse an ISO timestamp; unparseable values read as None."""
    if not isinstance(value, str) or not value:
        return None
    try:
        return _parse_ts(value)
    except ValueError:
        return None


def sender_window_peers(txn: dict, transactions: list[dict],
                        window_minutes: int = 1440) -> list[dict]:
    """Same-tenant same-sender txns within ±window of txn (target incl).

    Deduplicated by transaction_id so repeated deliveries of one event
    never inflate a count. Rows with unparseable timestamps are
    excluded; an unparseable target timestamp yields no peers.
    Deterministic order: (occurred_at, transaction_id).
    """
    sender = txn.get("sender_account_id")
    if not sender:
        return []
    tenant = txn.get("tenant_id", "org_primary")
    center = _safe_ts(txn.get("occurred_at"))
    if center is None:
        return []
    window = timedelta(minutes=window_minutes)
    seen: set[str] = set()
    peers: list[dict] = []
    for other in transactions:
        if not isinstance(other, dict):
            continue
        oid = other.get("transaction_id")
        if not oid or oid in seen:
            continue
        if other.get("tenant_id", "org_primary") != tenant:
            continue
        if other.get("sender_account_id") != sender:
            continue
        moment = _safe_ts(other.get("occurred_at"))
        if moment is None or abs(moment - center) > window:
            continue
        seen.add(oid)
        peers.append(other)
    peers.sort(key=lambda t: (t.get("occurred_at", ""),
                              t.get("transaction_id", "")))
    return peers


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
