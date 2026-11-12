"""Fraud alert lifecycle over detection signals (UFI section 09).

Alerts are opened from real signals only (deduplicated by signal id) and
move through NEW -> TRIAGED -> UNDER_REVIEW -> ESCALATED ->
INVESTIGATION_OPENED -> RESOLVED | FALSE_POSITIVE -> CLOSED. Notifications
reuse app/notify.dispatch with identifier-only context (no PII in the
payload); when no actor is known the alert records notified:false instead
of sending.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app import notify as _notify

STATUSES = (
    "NEW", "TRIAGED", "UNDER_REVIEW", "ESCALATED",
    "INVESTIGATION_OPENED", "RESOLVED", "FALSE_POSITIVE", "CLOSED",
)

_TRANSITIONS = {
    "NEW": ("TRIAGED", "UNDER_REVIEW"),
    "TRIAGED": ("UNDER_REVIEW", "FALSE_POSITIVE"),
    "UNDER_REVIEW": ("ESCALATED", "INVESTIGATION_OPENED", "RESOLVED",
                     "FALSE_POSITIVE"),
    "ESCALATED": ("INVESTIGATION_OPENED", "UNDER_REVIEW"),
    "INVESTIGATION_OPENED": ("RESOLVED", "FALSE_POSITIVE"),
    "RESOLVED": ("CLOSED",),
    "FALSE_POSITIVE": ("CLOSED",),
    "CLOSED": (),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _alert_id(signal_id: str) -> str:
    return "fraud_" + signal_id


def open_from_signal(store: Any, signal: dict[str, Any],
                     actor: str | None = None,
                     channel: str = "email") -> dict[str, Any]:
    """Open an alert for a signal, or return the existing one (idempotent)."""
    signal_id = signal.get("signal_id")
    if not signal_id:
        raise ValueError("SIGNAL_ID_REQUIRED")
    for row in store.fraud_alerts():
        if row.get("signal_id") == signal_id:
            return {"status": "duplicate", "alert": row}
    alert = {
        "id": _alert_id(signal_id),
        "signal_id": signal_id,
        "transaction_id": signal.get("transaction_id"),
        "detector_family": (signal.get("detector_family")
                             or signal.get("family")),
        "severity": signal.get("severity"),
        "status": "NEW",
        "opened_at": _now(),
        "history": [{"status": "NEW", "at": _now(),
                     "actor": actor or "system"}],
        "notified": False,
    }
    if actor:
        try:
            _notify.dispatch(store, "fraud.alert.opened", actor,
                             {"alert_id": alert["id"],
                              "signal_id": signal_id}, channel)
            alert["notified"] = True
        except Exception:
            alert["notified"] = False
    store.fraud_alert_save(alert)
    return {"status": "opened", "alert": alert}


def transition(store: Any, alert_id: str, to_status: str,
               actor: str) -> dict[str, Any]:
    """Move an alert along a legal transition; raises on violation."""
    if to_status not in STATUSES:
        raise ValueError("ALERT_STATUS_UNKNOWN: %s" % to_status)
    current = next((r for r in store.fraud_alerts()
                    if r.get("id") == alert_id), None)
    if current is None:
        raise ValueError("ALERT_NOT_FOUND: %s" % alert_id)
    if to_status not in _TRANSITIONS[current["status"]]:
        raise ValueError("ALERT_TRANSITION_ILLEGAL: %s -> %s"
                         % (current["status"], to_status))
    current["status"] = to_status
    current.setdefault("history", []).append(
        {"status": to_status, "at": _now(), "actor": actor})
    if to_status == "ESCALATED":
        try:
            _notify.dispatch(store, "fraud.alert.escalated", actor,
                             {"alert_id": alert_id})
            current["notified"] = True
        except Exception:
            pass
    store.fraud_alert_save(current)
    return current


def get_alert(store: Any, alert_id: str) -> dict[str, Any] | None:
    return next((r for r in store.fraud_alerts()
                 if r.get("id") == alert_id), None)


def list_alerts(store: Any, status: str | None = None) -> list[dict]:
    rows = store.fraud_alerts()
    if status:
        rows = [r for r in rows if r.get("status") == status]
    return rows


def metrics(store: Any) -> dict[str, Any]:
    """Alert metrics from real rows only, with a documented window."""
    rows = store.fraud_alerts()
    by_status: dict[str, int] = {}
    by_family: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for row in rows:
        by_status[row.get("status", "?")] = \
            by_status.get(row.get("status", "?"), 0) + 1
        fam = row.get("detector_family") or "?"
        by_family[fam] = by_family.get(fam, 0) + 1
        sev = row.get("severity") or "?"
        by_severity[sev] = by_severity.get(sev, 0) + 1
    return {
        "total": len(rows), "by_status": by_status,
        "by_detector_family": by_family, "by_severity": by_severity,
        "window": "all stored fraud alerts",
        "calculated_at": _now(),
    }
