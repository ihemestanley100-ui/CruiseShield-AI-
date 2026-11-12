"""Recovery eligibility + case lifecycle (recovery directive
sections 5-6, 8, 10, 12).

Eligibility evaluates 11 honest statuses against the scheme rules
registry: VERIFIED rules decide windows; NOT_VERIFIED templates
force RULES_NOT_VERIFIED; structural rules decide irreversibility.
Case lifecycle (17 states) enforces legal transitions, idempotent
creation (transaction + reason), evidence gating, and audited
history. Submission distinguishes LIVE_CONNECTOR (verified
capability only) from MANUAL_WORKFLOW (controlled packet +
external reference tracking). Nothing here moves money.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app import payment_methods as _paymethods
from app import recovery_rules as _rules

STATUSES = (
    "ELIGIBLE_CONFIRMED", "POTENTIALLY_ELIGIBLE",
    "OUT_OF_SCHEME_WINDOW", "LEGAL_REVIEW_REQUIRED",
    "PROVIDER_CONFIRMATION_REQUIRED", "EVIDENCE_REQUIRED",
    "FUNDS_AVAILABILITY_UNKNOWN", "NOT_ELIGIBLE",
    "UNSUPPORTED_PAYMENT_RAIL", "PROVIDER_UNAVAILABLE",
    "RULES_NOT_VERIFIED",
)

STATES = (
    "CASE_CREATED", "TRANSACTION_VERIFIED", "ELIGIBILITY_ASSESSED",
    "EVIDENCE_VALIDATED", "REQUEST_PREPARED", "APPROVAL_PENDING",
    "APPROVED", "SUBMITTED_TO_PROVIDER", "PROVIDER_ACKNOWLEDGED",
    "UNDER_REVIEW", "FUNDS_RESTRICTION_CONFIRMED", "PARTIAL_RECOVERY",
    "FULL_RECOVERY", "REJECTED", "EXPIRED", "ESCALATED", "CLOSED",
)

_TRANSITIONS = {
    "CASE_CREATED": ("TRANSACTION_VERIFIED", "CLOSED"),
    "TRANSACTION_VERIFIED": ("ELIGIBILITY_ASSESSED", "CLOSED"),
    "ELIGIBILITY_ASSESSED": ("EVIDENCE_VALIDATED", "ESCALATED",
                              "CLOSED"),
    "EVIDENCE_VALIDATED": ("REQUEST_PREPARED", "ESCALATED", "CLOSED"),
    "REQUEST_PREPARED": ("APPROVAL_PENDING", "CLOSED"),
    "APPROVAL_PENDING": ("APPROVED", "REJECTED", "EXPIRED"),
    "APPROVED": ("SUBMITTED_TO_PROVIDER", "UNDER_REVIEW", "EXPIRED",
                 "CLOSED"),
    "SUBMITTED_TO_PROVIDER": ("PROVIDER_ACKNOWLEDGED", "EXPIRED",
                               "CLOSED"),
    "PROVIDER_ACKNOWLEDGED": ("UNDER_REVIEW", "EXPIRED", "CLOSED"),
    "UNDER_REVIEW": ("FUNDS_RESTRICTION_CONFIRMED", "PARTIAL_RECOVERY",
                     "FULL_RECOVERY", "REJECTED", "ESCALATED",
                     "EXPIRED"),
    "FUNDS_RESTRICTION_CONFIRMED": ("PARTIAL_RECOVERY",
                                    "FULL_RECOVERY", "REJECTED",
                                    "ESCALATED", "EXPIRED"),
    "PARTIAL_RECOVERY": ("FULL_RECOVERY", "ESCALATED", "CLOSED"),
    "FULL_RECOVERY": ("CLOSED",),
    "REJECTED": ("ESCALATED", "CLOSED"),
    "EXPIRED": ("ESCALATED", "CLOSED"),
    "ESCALATED": ("UNDER_REVIEW", "CLOSED"),
    "CLOSED": (),
}

REASONS = ("unauthorized", "erroneous", "fraud", "duplicate",
           "service-not-rendered")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _age_days(occurred_at: str | None) -> int | None:
    if not occurred_at:
        return None
    try:
        then = datetime.fromisoformat(
            occurred_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    return max(0, (datetime.now(timezone.utc) - then).days)


def assess(store: Any, txn: dict[str, Any], reason: str,
           evidence: list[dict[str, Any]] | None = None,
           provider_available: bool = False,
           funds_record: dict[str, Any] | None = None
           ) -> dict[str, Any]:
    """Eligibility decision with the precise rule + reason."""
    evidence = evidence or []
    if reason not in REASONS:
        return {"status": "LEGAL_REVIEW_REQUIRED", "rule_id": None,
                "reason": "reason '%s' is outside the coded set; "
                          "counsel must classify it" % reason,
                "missing": [], "alternatives": []}
    classified = _paymethods.classify(txn)
    method_id = classified["method_id"]
    if method_id == "UNKNOWN":
        return {"status": "UNSUPPORTED_PAYMENT_RAIL", "rule_id": None,
                "reason": "payment method unclassified: %s" %
                          classified["explanation"],
                "missing": ["payment-method evidence"],
                "alternatives": ["historical-investigation"]}
    candidates = _rules.match(store, method_id, reason)
    if not candidates:
        return {"status": "UNSUPPORTED_PAYMENT_RAIL", "rule_id": None,
                "reason": "no rule covers %s / %s" % (method_id,
                                                      reason),
                "missing": [], "alternatives":
                ["historical-investigation"]}
    structural = [r for r in candidates
                  if r["rule_id"].startswith("STRUCT-")]
    if structural and method_id in ("crypto_onchain", "stablecoin",
                                    "cash"):
        return {"status": "NOT_ELIGIBLE",
                "rule_id": structural[0]["rule_id"],
                "reason": "%s: %s" % (
                    structural[0]["rule_id"],
                    structural[0]["rule_source"]),
                "missing": [],
                "alternatives": ["historical-investigation",
                                 "civil-restitution",
                                 "law-enforcement-referral"]}
    verified = [r for r in candidates
                if r["verification_status"] == "VERIFIED"]
    if not verified:
        return {"status": "RULES_NOT_VERIFIED",
                "rule_id": candidates[0]["rule_id"],
                "reason": "only NOT_VERIFIED templates cover %s / "
                          "%s; legal verification (D-058) required" % (
                              method_id, reason),
                "missing": ["verified-scheme-rule"],
                "alternatives": ["historical-investigation"]}
    rule = verified[0]
    window = rule.get("window_days")
    age = _age_days(txn.get("occurred_at"))
    if window is not None and age is not None and age > window:
        return {"status": "OUT_OF_SCHEME_WINDOW",
                "rule_id": rule["rule_id"],
                "reason": "age %d days exceeds %d-day window "
                          "(rule %s v%s)" % (
                              age, window, rule["rule_id"],
                              rule["version"]),
                "missing": [],
                "alternatives": ["provider-refund-request",
                                 "historical-investigation",
                                 "civil-restitution",
                                 "law-enforcement-referral"]}
    provided = {e.get("kind") for e in evidence
                if isinstance(e, dict)}
    missing = [k for k in rule.get("evidence_required", [])
               if k not in provided]
    if missing:
        return {"status": "EVIDENCE_REQUIRED", "rule_id": rule[
            "rule_id"], "reason": "missing: %s" % ", ".join(missing),
                "missing": missing, "alternatives": []}
    if not provider_available:
        return {"status": "PROVIDER_CONFIRMATION_REQUIRED",
                "rule_id": rule["rule_id"],
                "reason": "no live connector confirmed for this "
                          "provider; manual workflow or confirmation "
                          "required",
                "missing": ["provider-confirmation"],
                "alternatives": ["manual-workflow"]}
    if funds_record is None:
        return {"status": "FUNDS_AVAILABILITY_UNKNOWN",
                "rule_id": rule["rule_id"],
                "reason": "no lawful funds-availability record "
                          "supplied",
                "missing": ["funds-availability-record"],
                "alternatives": []}
    if not funds_record.get("available"):
        return {"status": "POTENTIALLY_ELIGIBLE",
                "rule_id": rule["rule_id"],
                "reason": "rule satisfied but funds reported "
                          "unavailable; restriction workflow may apply",
                "missing": [],
                "alternatives": ["restriction-request"]}
    return {"status": "ELIGIBLE_CONFIRMED", "rule_id": rule["rule_id"],
            "reason": "rule %s v%s satisfied with evidence + "
                      "funds" % (rule["rule_id"], rule["version"]),
            "missing": [], "alternatives": []}


def case_key(transaction_id: str, reason: str) -> str:
    return "%s|%s" % (transaction_id, reason)


def open_case(store: Any, transaction_id: str, reason: str,
              tenant_id: str, actor: str) -> dict[str, Any]:
    """Idempotent open: an open case for the key returns as-is."""
    for row in store.recovery_cases():
        if row.get("case_key") == case_key(transaction_id, reason) \
                and row.get("state") != "CLOSED" \
                and row.get("tenant_id") == tenant_id:
            return {"status": "duplicate", "case": row}
    record = {
        "recovery_id": "recv_%s" % _now().replace(
            "-", "").replace(":", "").replace(".", "")[:17],
        "case_key": case_key(transaction_id, reason),
        "transaction_id": transaction_id, "reason": reason,
        "tenant_id": tenant_id, "state": "CASE_CREATED",
        "eligibility": None, "evidence": [],
        "channel": None, "external_reference": None,
        "history": [{"state": "CASE_CREATED", "at": _now(),
                     "actor": actor}],
        "created_at": _now(),
    }
    store.recovery_case_save(record)
    return {"status": "opened", "case": record}


def transition(store: Any, recovery_id: str, to_state: str,
               actor: str, note: str = "") -> dict[str, Any]:
    """Legal lifecycle transition; raises on violation."""
    if to_state not in STATES:
        raise ValueError("RECOVERY_STATE_UNKNOWN: %s" % to_state)
    record = next((r for r in store.recovery_cases()
                   if r.get("recovery_id") == recovery_id), None)
    if record is None:
        raise ValueError("RECOVERY_UNKNOWN: %s" % recovery_id)
    if to_state not in _TRANSITIONS[record["state"]]:
        raise ValueError("RECOVERY_TRANSITION_ILLEGAL: %s -> %s" % (
            record["state"], to_state))
    record["state"] = to_state
    record.setdefault("history", []).append(
        {"state": to_state, "at": _now(), "actor": actor,
         "note": note[:300]})
    store.recovery_case_save(record)
    return record


def metrics(store: Any, tenant_id: str) -> dict[str, Any]:
    """Outcome dashboard from stored tenant rows only."""
    rows = [r for r in store.recovery_cases()
            if r.get("tenant_id") == tenant_id]
    by_state: dict[str, int] = {}
    by_reason: dict[str, int] = {}
    for row in rows:
        state = row.get("state", "?")
        by_state[state] = by_state.get(state, 0) + 1
        reason = row.get("reason", "?")
        by_reason[reason] = by_reason.get(reason, 0) + 1
    return {"total": len(rows), "by_state": by_state,
            "by_reason": by_reason, "tenant_scope": tenant_id,
            "window": "stored recovery cases for this tenant"}
