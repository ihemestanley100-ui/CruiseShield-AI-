"""Detector families + derived signal evaluation (detection §1-4).

Signals are DERIVED deterministically from transactions + edges on
every call — never persisted — so replaying an event yields identical
signal IDs (idempotent by construction) and rule changes cannot
overwrite history (each signal pins its detector + rule version).
No canonical state keys are added.
"""
from __future__ import annotations

import hashlib
import time
from typing import Any

from app import graph as graph_mod
from app import rules as rules_mod

VERSION = "1.0"

# Family -> engine rule IDs. Empty tuple = custom logic below.
RULE_MAPPED: dict[str, tuple[str, ...]] = {
    "RULE_MATCH": tuple(r.rule_id for r in rules_mod.RULES),
    "VELOCITY": ("R-002",),
    "DEVICE_REUSE": ("R-003",),
    "PHONE_REUSE": ("R-004",),
    "BENEFICIARY_CLUSTER": ("R-005",),
    "SHARED_MERCHANT": ("R-008",),
    "GRAPH_PATTERN": ("R-006", "R-007"),
}

CUSTOM = ("NETWORK_PROXIMITY", "CROSS_CHANNEL_PATTERN",
          "GEOGRAPHIC_ANOMALY")

# ML_ANOMALY has no deployed model: listed, never firing, honestly
# flagged NOT_IMPLEMENTED in the registry and matrix.
FAMILIES = tuple(RULE_MAPPED) + CUSTOM + ("ML_ANOMALY",)

DESCRIPTIONS = {
    "RULE_MATCH": "Any versioned engine rule fired.",
    "VELOCITY": "2+ sender transfers in a 120-minute window.",
    "DEVICE_REUSE": "One device shared by 2+ accounts.",
    "PHONE_REUSE": "One phone shared by 2+ accounts.",
    "BENEFICIARY_CLUSTER": "One beneficiary linked to 2+ accounts.",
    "SHARED_MERCHANT": "One merchant paid by 2+ accounts.",
    "GRAPH_PATTERN": "Fan-in (3+ senders) or fan-out (2+ receivers).",
    "NETWORK_PROXIMITY": "Counterparty shares a device, phone, "
                          "merchant, or beneficiary link.",
    "CROSS_CHANNEL_PATTERN": "Sender transacts on 2+ channels.",
    "GEOGRAPHIC_ANOMALY": "Sender seen in 2+ known locations.",
    "ML_ANOMALY": "No model deployed; awaiting validated model.",
}

_SEVERITY = {r.rule_id: r.severity for r in rules_mod.RULES}


def _signal_id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


def _base(txn: dict, family: str, detail: str, severity: str,
          reason: str, evidence: dict) -> dict[str, Any]:
    return {
        "signal_id": _signal_id(txn["transaction_id"], family,
                                VERSION, detail),
        "detector_family": family,
        "detector_version": VERSION,
        "rule_id": detail if detail.startswith("R-") else "",
        "rule_version": "1.0" if detail.startswith("R-") else "",
        "transaction_id": txn["transaction_id"],
        "channel": txn.get("channel", ""),
        "severity": severity,
        "occurred_at": txn.get("occurred_at", ""),
        "tenant_id": txn.get("tenant_id", "org_primary"),
        "entities": {"sender": txn.get("sender_account_id"),
                     "receiver": txn.get("receiver_account_id")},
        "reason": reason,
        "evidence": evidence,
        "outcome": "PENDING",
    }


def _rule_signals(txn: dict, transactions: list[dict],
                  edges: list[dict]) -> list[dict]:
    results = rules_mod.evaluate(txn["transaction_id"], transactions,
                                 edges, "detection")
    fired = {r.rule_id: r for r in results if r.triggered}
    signals = []
    for family, rule_ids in RULE_MAPPED.items():
        for rid in rule_ids:
            if rid in fired:
                result = fired[rid]
                signals.append(_base(
                    txn, family, rid, _SEVERITY[rid],
                    f"{rid} fired: {result.threshold}",
                    {"rule_id": rid, "threshold": result.threshold}))
    return signals


def _proximity_signals(txn: dict, transactions: list[dict],
                       edges: list[dict]) -> list[dict]:
    feats = graph_mod.features_for_transaction(txn, transactions, edges)
    parties = {txn.get("sender_account_id"),
               txn.get("receiver_account_id")}
    hits = []
    for kind in ("device_sharing", "phone_sharing", "merchant_sharing",
                 "beneficiary_links"):
        for ident, accounts in feats[kind].items():
            shared = parties & set(accounts)
            if shared and len(accounts) >= 2:
                hits.append(f"{kind}:{ident}x{len(accounts)}")
    if not hits:
        return []
    return [_base(txn, "NETWORK_PROXIMITY", "proximity", "medium",
                  "Counterparty shares identifiers: " +
                  ", ".join(sorted(hits)[:4]),
                  {"shared": sorted(hits)})]


def _cross_channel_signals(txn: dict,
                           by_sender: dict[str, set[str]]
                           ) -> list[dict]:
    channels = sorted(by_sender.get(txn.get("sender_account_id", ""), ()))
    if len(channels) < 2:
        return []
    return [_base(txn, "CROSS_CHANNEL_PATTERN", "xchannel", "medium",
                  f"Sender active on {len(channels)} channels: " +
                  ", ".join(channels),
                  {"channels": channels})]


def _geo_signals(txn: dict, by_sender: dict[str, set[str]]) -> list[dict]:
    locs = sorted(by_sender.get(txn.get("sender_account_id", ""), ()))
    if len(locs) < 2:
        return []
    return [_base(txn, "GEOGRAPHIC_ANOMALY", "geo", "low",
                  f"Sender seen in {len(locs)} locations: " +
                  ", ".join(locs),
                  {"locations": locs})]


def evaluate_all(transactions: list[dict],
                 edges: list[dict]) -> dict[str, Any]:
    """Evaluate every operational family over the transactions."""
    started = time.perf_counter()
    by_sender_ch: dict[str, set[str]] = {}
    by_sender_loc: dict[str, set[str]] = {}
    unknown_loc = 0
    for txn in transactions:
        sender = txn.get("sender_account_id", "")
        if txn.get("channel"):
            by_sender_ch.setdefault(sender, set()).add(txn["channel"])
        if txn.get("location_id"):
            by_sender_loc.setdefault(sender, set()).add(
                txn["location_id"])
        else:
            unknown_loc += 1
    signals: list[dict] = []
    for txn in transactions:
        signals.extend(_rule_signals(txn, transactions, edges))
        signals.extend(_proximity_signals(txn, transactions, edges))
        signals.extend(_cross_channel_signals(txn, by_sender_ch))
        signals.extend(_geo_signals(txn, by_sender_loc))
    signals.sort(key=lambda s: (s["occurred_at"], s["signal_id"]))
    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    return {"signals": signals, "meta": {
        "transactions_evaluated": len(transactions),
        "detector_version": VERSION,
        "latency_ms": latency_ms,
        "unknown_location_txns": unknown_loc,
        "note": ("Derived on demand from stored transactions; no "
                 "historical signals are overwritten.")}}
