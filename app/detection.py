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
from datetime import datetime, timedelta, timezone
from typing import Any

from app import channels as chan_mod
from app import config as config_mod
from app import graph as graph_mod
from app import payment_methods as paymethod_mod
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
          "GEOGRAPHIC_ANOMALY", "STRUCTURING_PATTERN",
          "DECLINE_REPETITION", "MULE_PASSTHROUGH")

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
    "STRUCTURING_PATTERN": "3+ sub-threshold sender transfers in "
                           "24h totalling 40,000,000+ kobo.",
    "DECLINE_REPETITION": "3+ DECLINED authorizations from one "
                          "sender in 24h.",
    "MULE_PASSTHROUGH": "Account receives from 3+ senders and "
                        "forwards 80%+ within 24h.",
    "ML_ANOMALY": "No model deployed; awaiting validated model.",
}

_SEVERITY = {r.rule_id: r.severity for r in rules_mod.RULES}

# MS-DETECT-001 aggregate-detector rule versions. These rules fire at
# the detector layer (multi-transaction windows), not in the
# per-transaction engine, so the engine score contracts stay stable.
RULE_VERSIONS = {"R-009": "1.0", "R-010": "1.0", "R-011": "1.1"}

# Family -> config kill-switch variable. Unmapped families (including
# the RULE_FAMILIES group) have no switch and always run.
_KILL_SWITCHES = {
    "STRUCTURING_PATTERN": "DETECTOR_STRUCTURING_ENABLED",
    "DECLINE_REPETITION": "DETECTOR_DECLINE_REPETITION_ENABLED",
    "MULE_PASSTHROUGH": "DETECTOR_MULE_ENABLED",
}


def family_enabled(family: str) -> bool:
    """True unless the family's kill switch is explicitly "0".

    Grammar is owned by config.detector_flag_enabled
    (availability-biased fail-open; RV-04).
    """
    var = _KILL_SWITCHES.get(family)
    if var is None:
        return True
    return config_mod.detector_flag_enabled(
        getattr(config_mod, var, None))


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
        "rule_version": (RULE_VERSIONS.get(detail, "1.0")
                         if detail.startswith("R-") else ""),
        "transaction_id": txn["transaction_id"],
        "channel": txn.get("channel", ""),
        "channel_canonical": chan_mod.classify(txn.get("channel")),
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


def _structuring_signals(txn: dict, transactions: list[dict],
                         edges: list[dict]) -> list[dict]:
    """R-009: 3+ sub-threshold transfers in 24h totalling 40M+ kobo.

    Fires on the target only when the target itself is part of the
    pattern. Grouping (tenant, sender, window, dedupe) is owned by
    graph.sender_window_peers.
    """
    peers = graph_mod.sender_window_peers(
        txn, transactions, graph_mod.STRUCTURING_WINDOW_MINUTES)
    qualifying = [p for p in peers
                  if isinstance(p.get("amount_minor"), int)
                  and p["amount_minor"] < graph_mod.STRUCTURING_AMOUNT_LINE]
    ids = sorted(p["transaction_id"] for p in qualifying)
    total = sum(p["amount_minor"] for p in qualifying)
    if (txn.get("transaction_id") not in ids
            or len(ids) < graph_mod.STRUCTURING_MIN_COUNT
            or total < graph_mod.STRUCTURING_MIN_TOTAL):
        return []
    return [_base(txn, "STRUCTURING_PATTERN", "R-009", "high",
                  f"{len(ids)} sub-threshold transfers totalling "
                  f"{total} kobo in "
                  f"{graph_mod.STRUCTURING_WINDOW_MINUTES}m window "
                  f"(line {graph_mod.STRUCTURING_AMOUNT_LINE}, "
                  f"threshold {graph_mod.STRUCTURING_MIN_COUNT})",
                  {"rule_id": "R-009",
                   "rule_version": RULE_VERSIONS["R-009"],
                   "count": len(ids), "total_minor": total,
                   "window_minutes":
                       graph_mod.STRUCTURING_WINDOW_MINUTES,
                   "amount_line_minor":
                       graph_mod.STRUCTURING_AMOUNT_LINE,
                   "transaction_ids": ids})]


def _decline_signals(txn: dict, transactions: list[dict],
                     edges: list[dict]) -> list[dict]:
    """R-010: 3+ DECLINED authorizations from one sender in 24h.

    Canonical lifecycle comes from payment_methods.map_lifecycle;
    original provider statuses are preserved in evidence. Fires on
    the target only when the target itself is a DECLINED event.
    """
    peers = graph_mod.sender_window_peers(
        txn, transactions, graph_mod.DECLINE_WINDOW_MINUTES)
    declined = [p for p in peers
                if paymethod_mod.map_lifecycle(
                    p.get("provider"), p.get("provider_status")
                )["canonical"] == "DECLINED"]
    ids = sorted(p["transaction_id"] for p in declined)
    if (txn.get("transaction_id") not in ids
            or len(ids) < graph_mod.DECLINE_MIN_COUNT):
        return []
    statuses = sorted({str(p.get("provider_status")) for p in declined})
    return [_base(txn, "DECLINE_REPETITION", "R-010", "medium",
                  f"{len(ids)} DECLINED authorizations in "
                  f"{graph_mod.DECLINE_WINDOW_MINUTES}m window "
                  f"(threshold {graph_mod.DECLINE_MIN_COUNT})",
                  {"rule_id": "R-010",
                   "rule_version": RULE_VERSIONS["R-010"],
                   "count": len(ids),
                   "window_minutes": graph_mod.DECLINE_WINDOW_MINUTES,
                   "transaction_ids": ids,
                   "provider_statuses": statuses})]


_MULE_WARNING = ("Activity consistent with pass-through "
                 "behavior; does not establish that specific funds "
                 "are criminal proceeds. Possible legitimate "
                 "explanations include escrow, payroll, marketplace "
                 "settlement and payment-processor activity. "
                 "Investigator review required before any action; "
                 "no automated adverse consequences.")


def _mule_valid_amount(value: object) -> bool:
    """Detector-boundary amount check: genuine non-negative int kobo.

    RV-03: bools, floats, strings, None, and negatives are malformed
    and excluded; a valid zero amount counts as a leg.
    """
    return (isinstance(value, int) and not isinstance(value, bool)
            and value >= 0)


def _mule_moment(txn: dict) -> datetime | None:
    """Aware-UTC instant of a leg; None when naive/unparseable (RV-01)."""
    try:
        return parse_ts(txn.get("occurred_at", ""))
    except ValueError:
        return None


def _mule_leg_status(txn: dict) -> str:
    """R-011 leg eligibility: SETTLED, LEGACY, or '' (excluded).

    LEGACY = no provider information at all (recorded transfer,
    lifecycle unattested). Unmapped provider/status pairs and all
    non-SETTLED canonical states are excluded.
    """
    provider, status = txn.get("provider"), txn.get("provider_status")
    if provider is None and status is None:
        return "LEGACY"
    if paymethod_mod.map_lifecycle(provider, status)["canonical"] \
            == "SETTLED":
        return "SETTLED"
    return ""


def _mule_signals(txn: dict, transactions: list[dict],
                  edges: list[dict]) -> list[dict]:
    """R-011: 3+ senders in, 80%+ value out within 24h (HIGH).

    Both ends of the target (sender, receiver) are evaluated as
    candidate mule accounts. Timestamps normalize to aware UTC
    before window evaluation, sorting, and comparison; naive or
    unparseable timestamps are excluded (no timezone assumed).
    Chronological guard: OUT legs count only at/after the earliest
    eligible IN leg (UTC comparison, same ordering as the window
    sort). Ratio is uncapped; values above 1.0 are flagged
    OVER_FORWARD / BALANCE_CONFOUNDED.
    """
    tenant = txn.get("tenant_id", "org_primary")
    center = txn.get("occurred_at", "")
    target_id = txn.get("transaction_id")
    accounts = sorted({a for a in (txn.get("sender_account_id"),
                                   txn.get("receiver_account_id"))
                       if a})
    signals = []
    for account in accounts:
        ins, outs = graph_mod.account_window_legs(
            account, tenant, center, transactions,
            graph_mod.MULE_WINDOW_MINUTES)
        elig_in = [t for t in ins
                   if _mule_leg_status(t)
                   and _mule_valid_amount(t.get("amount_minor"))
                   and _mule_moment(t) is not None]
        if not elig_in:
            continue
        earliest = elig_in[0]["occurred_at"]
        earliest_dt = _mule_moment(elig_in[0])
        elig_out = [t for t in outs
                    if _mule_leg_status(t)
                    and _mule_valid_amount(t.get("amount_minor"))
                    and _mule_moment(t) is not None]
        out_moments = {t["transaction_id"]: _mule_moment(t)
                       for t in elig_out}
        chrono_out = [t for t in elig_out
                      if out_moments[t["transaction_id"]] >= earliest_dt]
        senders = sorted({t.get("sender_account_id")
                          for t in elig_in
                          if t.get("sender_account_id")})
        total_in = sum(t["amount_minor"] for t in elig_in)
        total_out = sum(t["amount_minor"] for t in chrono_out)
        if total_in <= 0:
            continue
        ratio = total_out / total_in
        in_ids = sorted(t["transaction_id"] for t in elig_in)
        out_ids = sorted(t["transaction_id"] for t in chrono_out)
        if (target_id not in in_ids + out_ids
                or len(senders) < graph_mod.MULE_MIN_SENDERS
                or total_in < graph_mod.MULE_MIN_INCOMING
                or ratio < graph_mod.MULE_MIN_RATIO):
            continue
        over = ratio > 1.0
        unattested = sum(1 for t in elig_in + chrono_out
                         if _mule_leg_status(t) == "LEGACY")
        lifecycle_excluded = (len(ins) - len(elig_in)
                                + len(outs) - len(elig_out))
        chronology_excluded = len(elig_out) - len(chrono_out)
        ineligible = lifecycle_excluded + chronology_excluded
        try:
            midpoint = parse_ts(center)
            delta = timedelta(minutes=graph_mod.MULE_WINDOW_MINUTES)
            start = (midpoint - delta).strftime("%Y-%m-%dT%H:%M:%SZ")
            end = (midpoint + delta).strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            start, end = "", ""
        reason = (f"Mule pass-through: {len(senders)} senders, "
                  f"{total_in}->{total_out} kobo "
                  f"(ratio {ratio:.2f}) in "
                  f"{graph_mod.MULE_WINDOW_MINUTES}m window" +
                  (" [OVER_FORWARD / BALANCE_CONFOUNDED]"
                   if over else "") + "; " + _MULE_WARNING)
        signals.append(_base(
            txn, "MULE_PASSTHROUGH", "R-011", "high", reason,
            {"rule_id": "R-011",
             "rule_version": RULE_VERSIONS["R-011"],
             "account": account, "distinct_senders": len(senders),
             "sender_ids": senders, "in_ids": in_ids,
             "out_ids": out_ids, "total_in": total_in,
             "total_out": total_out, "forwarded_ratio": ratio,
             "window_start": start, "window_end": end,
             "window_minutes": graph_mod.MULE_WINDOW_MINUTES,
             "earliest_incoming_at": earliest,
             "unattested_count": unattested,
             "ineligible_excluded": ineligible,
             "lifecycle_excluded": lifecycle_excluded,
             "chronology_excluded": chronology_excluded,
             "over_forward": over,
             "thresholds": {
                 "min_senders": graph_mod.MULE_MIN_SENDERS,
                 "min_incoming": graph_mod.MULE_MIN_INCOMING,
                 "min_ratio": graph_mod.MULE_MIN_RATIO},
             "warning": _MULE_WARNING}))
    return signals


def parse_ts(value: str) -> datetime:
    """Strict ISO-8601 to aware UTC datetime. Raises ValueError."""
    text = (value or "").strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        raise ValueError(f"FILTER_INVALID: bad timestamp {value!r}")
    if parsed.tzinfo is None:
        raise ValueError(f"FILTER_INVALID: naive timestamp {value!r}")
    return parsed.astimezone(timezone.utc)


def _bucket_key(moment: datetime, granularity: str) -> str:
    if granularity == "hour":
        return moment.strftime("%Y-%m-%dT%H:00:00Z")
    if granularity == "day":
        return moment.strftime("%Y-%m-%d")
    if granularity == "week":
        iso_year, iso_week, _ = moment.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"
    if granularity == "month":
        return moment.strftime("%Y-%m")
    raise ValueError(f"FILTER_INVALID: granularity {granularity!r}")


def bucketize(signals: list[dict[str, Any]],
              granularity: str) -> list[dict[str, Any]]:
    """Bucket signals by occurred_at (UTC). Empty input -> []."""
    buckets: dict[str, dict[str, Any]] = {}
    for sig in signals:
        key = _bucket_key(parse_ts(sig.get("occurred_at", "")), granularity)
        row = buckets.setdefault(key, {"bucket": key, "signals": 0,
                                       "unique_txns": set()})
        row["signals"] += 1
        row["unique_txns"].add(sig.get("transaction_id"))
    ordered = [buckets[k] for k in sorted(buckets)]
    for row in ordered:
        row["unique_txns"] = len(row["unique_txns"])
    return ordered


def filter_signals(signals: list[dict[str, Any]], *,
                   start: str = "", end: str = "",
                   family: str = "", channel: str = "",
                   severity: str = "") -> list[dict[str, Any]]:
    """Filter by UTC range + exact family/channel/severity matches."""
    start_dt = parse_ts(start) if start else None
    end_dt = parse_ts(end) if end else None
    if start_dt and end_dt and start_dt > end_dt:
        raise ValueError("FILTER_INVALID: start after end")
    out = []
    for sig in signals:
        moment = parse_ts(sig.get("occurred_at", ""))
        if start_dt and moment < start_dt:
            continue
        if end_dt and moment > end_dt:
            continue
        if family and sig.get("detector_family") != family:
            continue
        if channel and sig.get("channel_canonical") != channel:
            continue
        if severity and sig.get("severity") != severity:
            continue
        out.append(sig)
    return out


def evaluate_all(transactions: list[dict],
                 edges: list[dict]) -> dict[str, Any]:
    """Evaluate every operational family over the transactions."""
    started = time.perf_counter()
    by_sender_ch: dict[str, set[str]] = {}
    by_sender_loc: dict[str, set[str]] = {}
    unknown_loc = 0
    # D-035: non-dict rows are skipped and surfaced (fail-closed
    # per-row). Previously such a row raised AttributeError past
    # every handler; valid rows were lost with it.
    valid = [t for t in transactions if isinstance(t, dict)]
    skipped_non_dict = len(transactions) - len(valid)
    transactions = valid
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
    family_errors: list[dict[str, str]] = []
    if skipped_non_dict:
        family_errors.append({"family": "INPUT",
                              "error": "NON_DICT_ROWS_SKIPPED: %d"
                              % skipped_non_dict})
    family_runs: dict[str, int] = {}
    family_latency_ms: dict[str, float] = {}
    groups = [("RULE_FAMILIES", _rule_signals, True),
              ("NETWORK_PROXIMITY", _proximity_signals, True),
              ("CROSS_CHANNEL_PATTERN", _cross_channel_signals, False),
              ("GEOGRAPHIC_ANOMALY", _geo_signals, False),
              ("STRUCTURING_PATTERN", _structuring_signals, True),
              ("DECLINE_REPETITION", _decline_signals, True),
              ("MULE_PASSTHROUGH", _mule_signals, True)]
    for name, func, needs_edges in groups:
        group_started = time.perf_counter()
        if not family_enabled(name):
            family_runs[name] = 0
            family_latency_ms[name] = 0.0
            continue
        try:
            for txn in transactions:
                if needs_edges:
                    signals.extend(func(txn, transactions, edges))
                elif name == "CROSS_CHANNEL_PATTERN":
                    signals.extend(func(txn, by_sender_ch))
                else:
                    signals.extend(func(txn, by_sender_loc))
            family_runs[name] = len(transactions)
        except Exception as exc:  # noqa: BLE001 - counted, surfaced
            family_errors.append({"family": name,
                                  "error": f"{type(exc).__name__}"})
        finally:
            family_latency_ms[name] = round(
                (time.perf_counter() - group_started) * 1000, 2)
    signals.sort(key=lambda s: (s["occurred_at"], s["signal_id"]))
    for sig in signals:
        sig["execution_id"] = _signal_id(
            ",".join(sorted(t.get("transaction_id", "")
                            for t in transactions)), VERSION, "run")
    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    meta = {
        "transactions_evaluated": len(transactions),
        "detector_version": VERSION,
        "latency_ms": latency_ms,
        "unknown_location_txns": unknown_loc,
        "family_runs": family_runs,
        "family_latency_ms": family_latency_ms,
        "family_errors": family_errors,
        "execution_id": signals[0]["execution_id"] if signals else _signal_id(
            ",".join(sorted(t.get("transaction_id", "")
                            for t in transactions)), VERSION, "run"),
        "note": ("Derived on demand from stored transactions; no "
                 "historical signals are overwritten.")}
    return {"signals": signals, "meta": meta}
