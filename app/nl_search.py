"""Natural-language transaction search (deterministic).

Parses amounts, currencies, dates, channels, case/transaction/device
references, and beneficiary keywords into a validated structured
query, executes it through tenant-scoped transaction rows +
detection signals, and explains the query. Ambiguous or empty
parses return a clarification question instead of guessing. No
model calls; no generated SQL.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

from app import channels as _channels

_CURRENCY_SYMBOLS = {"\u20a6": "NGN", "$": "USD", "\u20ac": "EUR",
                     "\u00a3": "GBP"}
_CHANNEL_WORDS = {"pos": "POS", "atm": "ATM", "ussd": "USSD",
                  "qr": "QR",
                  "nip": "NIP", "web": "WEB", "online": "WEB",
                  "mobile": "MOBILE_APP", "app": "MOBILE_APP",
                  "transfer": "TRANSFER", "agent": "AGENT"}


def _today() -> datetime:
    return datetime.now(timezone.utc)


def parse(text: str) -> dict[str, Any]:
    """Parse NL text into a structured query (never raises)."""
    query: dict[str, Any] = {"filters": {}, "notes": []}
    lowered = (text or "").lower()

    amount = re.search(
        r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*(million|m\b|billion|b\b|"
        r"thousand|k\b)?", lowered)
    symbol = next((s for s in _CURRENCY_SYMBOLS if s in (text or "")),
                  None)
    if amount and ("above" in lowered or "over" in lowered
                   or "greater" in lowered or symbol
                   or "million" in lowered or amount.group(2)):
        raw = float(amount.group(1).replace(",", ""))
        magnitude = (amount.group(2) or "").strip()
        multiplier = {"million": 1_000_000, "m": 1_000_000,
                      "billion": 1_000_000_000, "b": 1_000_000_000,
                      "thousand": 1_000, "k": 1_000}.get(magnitude, 1)
        query["filters"]["min_amount_minor"] = int(raw * multiplier * 100)
        query["filters"]["currency"] = _CURRENCY_SYMBOLS.get(
            symbol or "", None) or None
        if query["filters"]["currency"] is None:
            del query["filters"]["currency"]
        query["notes"].append("amount threshold parsed")

    if "today" in lowered:
        start = _today().replace(hour=0, minute=0, second=0,
                                 microsecond=0)
        query["filters"]["start"] = start.isoformat().replace(
            "+00:00", "Z")
    match = re.search(r"within (\d+) minutes", lowered)
    if match:
        query["filters"]["within_minutes"] = int(match.group(1))
        query["notes"].append("relative window needs an anchor "
                              "transaction")
    match = re.search(r"last (\d+) days?", lowered)
    if match:
        start = _today() - timedelta(days=int(match.group(1)))
        query["filters"]["start"] = start.isoformat().replace(
            "+00:00", "Z")

    for word, channel in _CHANNEL_WORDS.items():
        if re.search(r"\b%s\b" % word, lowered):
            query["filters"]["channel"] = channel
            break

    case = re.search(r"\b(cs[-_ ]?\d+|case[-_ ]?\d+)\b", lowered)
    if case:
        query["filters"]["case_ref"] = case.group(1).upper().replace(
            " ", "")
    txn = re.search(r"\b(txn[-_][a-z0-9_]+)\b", lowered)
    if txn:
        query["filters"]["transaction_id"] = txn.group(1)
    device = re.search(r"\b(dev[-_][a-z0-9_]+)\b", lowered)
    if device:
        query["filters"]["device_id"] = device.group(1)
    beneficiary = re.search(r"beneficiary ([a-z0-9_ ]+?)(?:\.|$| and )",
                            lowered)
    if beneficiary:
        query["filters"]["beneficiary_text"] = beneficiary.group(1).strip()
    if "suspicious" in lowered or "unusual" in lowered:
        query["filters"]["flagged_only"] = True

    if not query["filters"]:
        query["needs_clarification"] = True
        query["question"] = ("Which transactions should I search? Give "
                             "an amount, date, channel, case, account, "
                             "device, or beneficiary reference.")
    return query


def execute(store: Any, txns: list[dict[str, Any]],
            signals: list[dict[str, Any]],
            query: dict[str, Any]) -> dict[str, Any]:
    """Run a parsed query over tenant-visible rows."""
    filters = query.get("filters", {})
    flagged = {s.get("transaction_id") for s in signals}
    rows = []
    for txn in txns:
        if not _matches(txn, filters, flagged):
            continue
        rows.append(txn)
    rows = rows[:100]
    return {
        "count": len(rows),
        "capped": len(rows) == 100,
        "transactions": [
            {"transaction_id": t.get("transaction_id"),
             "channel": t.get("channel"),
             "amount_minor": t.get("amount_minor"),
             "currency": t.get("currency"),
             "occurred_at": t.get("occurred_at"),
             "flagged": t.get("transaction_id") in flagged}
            for t in rows
        ],
        "explanation": explain(query),
        "filters": filters,
    }


def _matches(txn: dict, filters: dict, flagged: set) -> bool:
    threshold = filters.get("min_amount_minor")
    if threshold is not None and (txn.get("amount_minor") or 0) < threshold:
        return False
    if filters.get("currency") and txn.get("currency") != filters[
            "currency"]:
        return False
    if filters.get("channel"):
        want = _channels.classify(filters["channel"])
        if _channels.classify(txn.get("channel")) != want:
            return False
    if filters.get("start") and (txn.get("occurred_at") or "") < filters[
            "start"]:
        return False
    if filters.get("transaction_id") and txn.get(
            "transaction_id") != filters["transaction_id"]:
        return False
    if filters.get("device_id") and txn.get("device_id") != filters[
            "device_id"]:
        return False
    if filters.get("beneficiary_text"):
        haystack = " ".join(str(txn.get(k, "")) for k in
                            ("receiver_account_id", "sender_account_id",
                             "merchant_id")).lower()
        if filters["beneficiary_text"] not in haystack:
            return False
    if filters.get("flagged_only") and txn.get(
            "transaction_id") not in flagged:
        return False
    return True


def explain(query: dict[str, Any]) -> str:
    """Human-readable account of what the query does."""
    if query.get("needs_clarification"):
        return query.get("question", "clarification needed")
    parts = []
    filters = query.get("filters", {})
    if filters.get("min_amount_minor") is not None:
        parts.append("amount >= %d minor units" % filters[
            "min_amount_minor"])
    for key in ("currency", "channel", "start", "transaction_id",
                "device_id", "beneficiary_text", "case_ref"):
        if filters.get(key) is not None:
            parts.append("%s = %s" % (key, filters[key]))
    if filters.get("flagged_only"):
        parts.append("flagged by detection only")
    if filters.get("within_minutes") is not None:
        parts.append("relative %d-minute window (needs an anchor "
                     "transaction id)" % filters["within_minutes"])
    return "Matched " + "; ".join(parts) if parts else "No filters"
