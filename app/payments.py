"""Payment intents + provider abstraction (Phase 5, D-041).

Live charging: DISABLED. No adapter performs network I/O. The stub
provider records manual-reconciliation intents only. live_charge()
always raises: charging is impossible by construction until a named
provider plus credentials plus owner approval exist.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

PROVIDERS = (
    {"id": "stub-manual", "name": "Manual reconciliation stub",
     "live_capable": False, "interface": 1,
     "webhook": "hmac-sha256", "idempotency": "reference"},
)

# Provider interface v1: every adapter declares these capability keys.
# Webhook endpoints arrive with the first named provider (URL shape and
# header names are vendor-specific and must not be guessed).
PROVIDER_INTERFACE_VERSION = 1
PROVIDER_INTERFACE_KEYS = ("id", "name", "live_capable", "interface",
                           "webhook", "idempotency")
WEBHOOK_TOLERANCE_SECONDS = 300

INTENT_TRANSITIONS = {
    "pending": ("succeeded", "failed", "cancelled"),
    "succeeded": ("refunded",),
    "failed": ("pending",),
    "cancelled": (),
    "refunded": (),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def provider_ids() -> tuple[str, ...]:
    """Known provider identifiers."""
    return tuple(p["id"] for p in PROVIDERS)


def live_capable(provider_id: str) -> bool:
    """True only for providers able to move money (none today)."""
    return next((bool(p["live_capable"]) for p in PROVIDERS
                 if p["id"] == provider_id), False)


def create_intent(store, username: str, amount: int, currency: str,
                  provider_id: str, reference: str = "") -> dict[str, Any]:
    """Record a payment intent (minor units; no money moves)."""
    if provider_id not in provider_ids():
        raise ValueError("PROVIDER_UNKNOWN: %s" % (provider_id,))
    if not isinstance(amount, int) or isinstance(amount, bool) \
            or amount <= 0:
        raise ValueError("AMOUNT_INVALID: positive integer minor units")
    code = (currency or "").strip().upper()
    if len(code) != 3 or not code.isalpha():
        raise ValueError("CURRENCY_INVALID: 3-letter code")
    if len(reference or "") > 200:
        raise ValueError("REFERENCE_TOO_LONG: 200 chars max")
    store.state["payment_seq"] = int(store.state.get("payment_seq", 0)) + 1
    rec = {"payment_id": "pay_%04d" % store.state["payment_seq"],
           "kind": "fiat", "user": username, "amount": amount,
           "currency": code, "provider": provider_id,
           "status": "pending", "reference": reference or "",
           "created_at": _now()}
    store.save_payment(rec)
    return rec


def transition(store, payment_id: str, to: str) -> dict[str, Any]:
    """Move an intent along the state machine (terminal states hold)."""
    rec = store.payment(payment_id)
    if rec is None:
        raise ValueError("PAYMENT_NOT_FOUND: %s" % payment_id)
    allowed = INTENT_TRANSITIONS.get(rec.get("status", ""), ())
    if to not in allowed:
        raise ValueError("PAYMENT_TRANSITION_ILLEGAL: %s -> %s"
                         % (rec.get("status"), to))
    rec["status"] = to
    store._save()
    return rec


def live_charge(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """The seam a future live provider implements. Always raises today."""
    raise ValueError("LIVE_CHARGING_DISABLED: no live provider configured")


def provider_conformance(provider_id: str) -> list[str]:
    """Missing interface keys for one provider ([] = conformant)."""
    entry = next((p for p in PROVIDERS if p["id"] == provider_id), None)
    if entry is None:
        return ["PROVIDER_UNKNOWN: %s" % (provider_id,)]
    missing = [key for key in PROVIDER_INTERFACE_KEYS
               if key not in entry]
    if entry.get("interface") != PROVIDER_INTERFACE_VERSION:
        missing.append("interface")
    return missing


def webhook_verify(secret: str, body: bytes, signature_b64: str,
                   timestamp: int,
                   now: float | None = None) -> bool:
    """HMAC-SHA256 webhook check over timestamp.body (never raises).

    Rejects missing secrets, bad signatures, and timestamps outside
    the tolerance window (replay resistance).
    """
    import base64
    import hashlib
    import hmac
    import time

    try:
        if not secret:
            return False
        moment = time.time() if now is None else now
        if abs(float(moment) - int(timestamp)) > WEBHOOK_TOLERANCE_SECONDS:
            return False
        expect = hmac.new(secret.encode(), b"%d." % int(timestamp) + body,
                          hashlib.sha256).digest()
        given = base64.b64decode(signature_b64)
        return hmac.compare_digest(expect, given)
    except (ValueError, TypeError):
        return False


def find_intent_by_reference(store, reference: str) -> dict[str, Any] | None:
    """Idempotency lookup: the intent carrying one merchant reference."""
    if not reference:
        return None
    return next((p for p in store.state.get("payments", [])
                 if isinstance(p, dict)
                 and p.get("reference") == reference), None)
