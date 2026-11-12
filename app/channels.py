"""Canonical channel taxonomy (detection-intelligence §5).

Raw seed/connector channel codes map to 9 canonical channels. Unknown
codes map to UNMAPPED (never guessed) and surface an operational
alert. Integration status is honest: the only feed is the
deterministic seed — no live NIP/ATM/POS/banking connection exists.
"""
from __future__ import annotations

from typing import Any

CANONICAL = ("POS", "MOBILE_APP", "USSD", "NIP", "WEB", "ATM",
             "TRANSFER", "AGENT", "QR")

UNMAPPED = "UNMAPPED"

_RAW_MAP = {
    "POS": "POS",
    "MOBILE_APP": "MOBILE_APP",
    "USSD": "USSD",
    "TRANSFER_NIP": "NIP",
    "NIP": "NIP",
    "WEB": "WEB",
    "ATM": "ATM",
    "TRANSFER": "TRANSFER",
    "AGENT_AGENCY": "AGENT",
    "AGENT": "AGENT",
    "QR": "QR",
}


def classify(raw: str | None) -> str:
    """Map a raw channel code to canonical or UNMAPPED."""
    return _RAW_MAP.get((raw or "").strip().upper(), UNMAPPED)


def summarize(transactions: list[dict[str, Any]],
              signals: list[dict[str, Any]]) -> dict[str, Any]:
    """Per-channel volume + signal counts from real records.

    Signals join by transaction_id. Channels with no transactions
    report zeros with an explicit no-data note — never invented.
    """
    by_txn: dict[str, list[dict[str, Any]]] = {}
    for signal in signals:
        by_txn.setdefault(signal["transaction_id"], []).append(signal)
    rows: dict[str, dict[str, Any]] = {}
    unmapped_raw: set[str] = set()
    for txn in transactions:
        canonical = classify(txn.get("channel"))
        if canonical == UNMAPPED:
            unmapped_raw.add(str(txn.get("channel")))
        row = rows.setdefault(canonical, {
            "channel": canonical, "transactions": 0,
            "unique_transactions": 0, "signals": 0,
            "unique_flagged": 0, "last_seen": "",
            "integration": "SEED_FEED",
            "note": ("Deterministic seed feed; no live channel "
                     "integration.")})
        row["transactions"] += 1
        row["unique_transactions"] += 1
        hits = by_txn.get(txn.get("transaction_id", ""), [])
        row["signals"] += len(hits)
        if hits:
            row["unique_flagged"] += 1
        occurred = str(txn.get("occurred_at", ""))
        if occurred > row["last_seen"]:
            row["last_seen"] = occurred
    for canonical in CANONICAL:
        rows.setdefault(canonical, {
            "channel": canonical, "transactions": 0,
            "unique_transactions": 0, "signals": 0,
            "unique_flagged": 0, "last_seen": "",
            "integration": "SEED_FEED",
            "note": "No qualifying transactions recorded."})
    return {"channels": [rows[c] for c in CANONICAL]
            + ([rows[UNMAPPED]] if UNMAPPED in rows else []),
            "unmapped_raw_codes": sorted(unmapped_raw),
            "unmapped_alert": bool(unmapped_raw)}
