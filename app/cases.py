"""Case state machine, human decisions, and audit helpers."""
from __future__ import annotations

from datetime import datetime, timezone

TRANSITIONS: dict[str, list[str]] = {
    "NEW": ["TRIAGED", "FALSE_POSITIVE"],
    "TRIAGED": ["INVESTIGATING", "FALSE_POSITIVE"],
    "INVESTIGATING": ["AWAITING_REVIEW", "FALSE_POSITIVE", "ESCALATED"],
    "AWAITING_REVIEW": ["DECISIONED", "ESCALATED", "FALSE_POSITIVE"],
    "DECISIONED": ["ACTIONED", "NO_ACTION"],
    "ACTIONED": ["CLOSED"],
    "ESCALATED": ["INVESTIGATING", "CLOSED"],
    "FALSE_POSITIVE": [],
    "NO_ACTION": [],
    "CLOSED": [],
}

DECISION_LABELS = {"Escalate", "Request Verification", "Monitor",
                   "Mark False Positive", "Close Case"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def allowed_transitions(status: str) -> list[str]:
    return list(TRANSITIONS.get(status, []))


def record_decision(store, case_id: str, decision: str, target_status: str,
                    reason: str, actor_id: str,
                    evidence_viewed: list[str] | None = None,
                    recommendation: str = "",
                    trace_id: str = "") -> tuple[dict, dict]:
    """Validate and persist a human decision + case transition + audit event."""
    if decision not in DECISION_LABELS:
        raise ValueError(f"INVALID_DECISION: {decision}")
    if not reason or not reason.strip():
        raise ValueError("REASON_REQUIRED: a reason is required")
    case = store.get_case(case_id)
    if case is None:
        raise ValueError(f"CASE_NOT_FOUND: {case_id}")
    if target_status not in TRANSITIONS.get(case["status"], []):
        raise ValueError(f"INVALID_TRANSITION: {case['status']} -> {target_status}")
    decision_id = f"decision_{len(store.state['decisions']) + 1:04d}"
    record = {
        "decision_id": decision_id, "case_id": case_id, "actor_id": actor_id,
        "actor_role": "INVESTIGATOR", "decision": decision,
        "reason": reason.strip(),
        "evidence_viewed": evidence_viewed or [],
        "recommendation_at_decision": recommendation,
        "created_at": _now(), "authorization_scope": "demo",
        "trace_id": trace_id or store.state["trace_id"],
    }
    previous = case["status"]
    case["status"] = target_status
    case["updated_at"] = record["created_at"]
    store.state["decisions"].append(record)
    audit = store.append_audit(
        "human", actor_id, "case.decision", "case", case_id, previous,
        target_status, f"{decision}: {reason.strip()}", record["trace_id"],
        record["trace_id"])
    return record, audit
