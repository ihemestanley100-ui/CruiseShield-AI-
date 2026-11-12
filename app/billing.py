"""Trials, subscriptions, founder entitlement (Phase 5, D-040).

Directive defaults (L13 §11.1): 14-day trial, no card, two
investigation credits. Enforcement is OFF by default and only
constrains session-authenticated callers when armed; open local
mode is never affected.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

TRIAL_DAYS = 14
TRIAL_CREDITS = 2


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


def ensure_trial(store, username: str,
                 now: datetime | None = None) -> dict[str, Any]:
    """Fetch the user's trial, creating it on first use (idempotent)."""
    trials = store.state.setdefault("trials", {})
    rec = trials.get(username)
    if isinstance(rec, dict):
        return rec
    start = now or _now()
    rec = {"user": username, "status": "active", "plan": "trial",
           "started_at": _iso(start),
           "ends_at": _iso(start + timedelta(days=TRIAL_DAYS)),
           "credits": TRIAL_CREDITS}
    trials[username] = rec
    store._save()
    return rec


def trial_state(trial: dict[str, Any],
                now: datetime | None = None) -> str:
    """active | expired | exhausted for one trial record."""
    moment = now or _now()
    try:
        ends = datetime.fromisoformat(
            str(trial.get("ends_at", "")).replace("Z", "+00:00"))
    except ValueError:
        return "expired"
    if moment > ends:
        return "expired"
    if int(trial.get("credits", 0)) <= 0:
        return "exhausted"
    return "active"


def consume_trial_credit(store, username: str,
                         now: datetime | None = None) -> dict[str, Any]:
    """Spend one credit or raise TRIAL_EXPIRED / TRIAL_EXHAUSTED."""
    trial = ensure_trial(store, username, now)
    state = trial_state(trial, now)
    if state == "expired":
        raise ValueError("TRIAL_EXPIRED: trial ended %s"
                         % trial.get("ends_at", ""))
    if state == "exhausted":
        raise ValueError("TRIAL_EXHAUSTED: no credits left")
    trial["credits"] = int(trial.get("credits", 0)) - 1
    store._save()
    return trial


# Plan catalogue: entitlements only. Prices are intentionally unset
# (None = owner quote) — the directive forbids invented pricing.
# Limits of None mean "owner-configured before enforcement".
PLANS = (
    {"id": "trial", "name": "Trial", "case_credits": TRIAL_CREDITS,
     "days": TRIAL_DAYS, "price": None, "currency": None},
    {"id": "starter", "name": "Starter", "case_credits": None,
     "days": None, "price": None, "currency": None},
    {"id": "professional", "name": "Professional", "case_credits": None,
     "days": None, "price": None, "currency": None},
    {"id": "business", "name": "Business", "case_credits": None,
     "days": None, "price": None, "currency": None},
    {"id": "enterprise", "name": "Enterprise", "case_credits": None,
     "days": None, "price": None, "currency": None},
    {"id": "government", "name": "Government / Institutional",
     "case_credits": None, "days": None, "price": None,
     "currency": None},
)


def plan_ids() -> tuple[str, ...]:
    """Catalogue plan identifiers."""
    return tuple(plan["id"] for plan in PLANS)


def start_subscription(store, username: str, plan_id: str,
                       evidence: str = "") -> dict[str, Any]:
    """Activate a plan (references only; no charging happens here)."""
    if plan_id not in plan_ids():
        raise ValueError("PLAN_UNKNOWN: %s" % (plan_id,))
    if not (evidence or "").strip():
        raise ValueError("SUBSCRIPTION_EVIDENCE_REQUIRED: cite the order")
    rec = {"user": username, "plan": plan_id, "status": "active",
           "started_at": _iso(_now()), "renews_at": None,
           "evidence": evidence.strip()}
    store.save_subscription(username, rec)
    return rec


def cancel_subscription(store, username: str) -> dict[str, Any]:
    """Cancel the user's subscription (missing subscription → error)."""
    rec = store.subscription_for(username)
    if rec is None:
        raise ValueError("SUBSCRIPTION_NOT_FOUND: %s" % username)
    rec["status"] = "cancelled"
    rec["cancelled_at"] = _iso(_now())
    store.save_subscription(username, rec)
    return rec


def record_payment_event(store, username: str, reference: str,
                         ok: bool = True) -> dict[str, Any] | None:
    """Record a provider-reported payment outcome (reference only).

    No money moves here: the reference names an external reconciliation
    artifact. Failed outcomes park the subscription as past_due.
    """
    rec = store.subscription_for(username)
    if rec is None:
        return None
    rec["status"] = "active" if ok else "past_due"
    rec["last_payment"] = {"reference": reference, "ok": bool(ok),
                           "at": _iso(_now())}
    store.save_subscription(username, rec)
    return rec


def founder_active(store, username: str, founder_user: str) -> bool:
    """True when the named founder entitlement covers the user."""
    founder = (founder_user or "").strip()
    return bool(founder) and username == founder


def ensure_founder(store, username: str) -> dict[str, Any]:
    """Fetch the founder record, creating it on first use."""
    rec = store.founder_record()
    if isinstance(rec, dict):
        return rec
    rec = {"user": username, "granted_at": _iso(_now()),
           "basis": "FOUNDER_USER env (owner entitlement)"}
    store.save_founder(rec)
    return rec


def metered_action(store, username: str, founder_user: str,
                   enforcement_on: bool,
                   now: datetime | None = None) -> dict[str, Any] | None:
    """Enforce trial metering for one metered write.

    Returns the charged trial, or None when unenforced (metering
    off, founder, or active paid subscription). Paid-plan numeric
    limits stay unset until the owner configures them.
    """
    if not enforcement_on:
        return None
    if founder_active(store, username, founder_user):
        return None
    sub = store.subscription_for(username)
    if sub is not None and sub.get("status") == "active":
        return None
    return consume_trial_credit(store, username, now)
