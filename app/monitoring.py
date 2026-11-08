"""Transaction monitoring wiring (UFI section 09).

Honest modes: detection evaluates on demand over stored tenant
transactions (never claimed as streaming real-time); freshness derives
from event timestamps. evaluate() runs the real Detection Engine and
opens fraud alerts for signals that lack one - the monitoring ->
detection -> alert wire. Every count comes from stored rows.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app import alerts as _alerts
from app import detection as _detection
from app import tenancy as _tenancy

MODES = ("on-demand-evaluation", "scheduled-batch", "historical-search")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def status(store: Any, txns: list[dict[str, Any]],
           signals: list[dict[str, Any]],
           tenant_id: str) -> dict[str, Any]:
    """Monitoring status from real rows. No invented liveness."""
    stamps = sorted(t.get("occurred_at", "") for t in txns
                    if t.get("occurred_at"))
    tenant_alerts = [r for r in store.fraud_alerts()
                     if r.get("tenant_id", _tenancy.DEFAULT_TENANT)
                     == tenant_id]
    by_status: dict[str, int] = {}
    for row in tenant_alerts:
        key = row.get("status", "?")
        by_status[key] = by_status.get(key, 0) + 1
    unalerted = 0
    alerted_signals = {r.get("signal_id") for r in tenant_alerts}
    for sig in signals:
        if sig.get("signal_id") not in alerted_signals:
            unalerted += 1
    return {
        "mode": "on-demand-evaluation",
        "mode_note": "Detection evaluates when requested over stored "
                     "records; this is not a streaming real-time feed.",
        "tenant_scope": tenant_id,
        "transactions_visible": len(txns),
        "signals_visible": len(signals),
        "alerts_open": sum(1 for r in tenant_alerts
                           if r.get("status") not in ("RESOLVED",
                                                     "FALSE_POSITIVE",
                                                     "CLOSED")),
        "alerts_by_status": by_status,
        "signals_without_alerts": unalerted,
        "data_window": {"start": stamps[0] if stamps else None,
                        "end": stamps[-1] if stamps else None},
        "computed_at": _now(),
    }


def evaluate(store: Any, txns: list[dict[str, Any]],
             edges: list[dict[str, Any]], tenant_id: str,
             actor: str) -> dict[str, Any]:
    """Run detection and open alerts for newly-seen signals.

    Idempotent: signals that already have a tenant alert are reported
    as duplicates, never double-opened. Returns the run summary.
    """
    result = _detection.evaluate_all(txns, edges)
    signals = result.get("signals", [])
    opened: list[str] = []
    duplicates: list[str] = []
    for sig in signals:
        out = _alerts.open_from_signal(store, sig, actor)
        alert = out["alert"]
        if out["status"] == "opened":
            alert["tenant_id"] = tenant_id
            store.fraud_alert_save(alert)
            opened.append(alert["id"])
        else:
            duplicates.append(alert["id"])
    return {
        "tenant_scope": tenant_id,
        "signals_evaluated": len(signals),
        "alerts_opened": opened,
        "alerts_duplicate": duplicates,
        "family_runs": result.get("family_runs", {}),
        "family_errors": result.get("family_errors", []),
        "evaluated_at": _now(),
    }
