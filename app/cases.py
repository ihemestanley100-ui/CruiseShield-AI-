"""Case state machine, human decisions, and audit helpers."""
from __future__ import annotations

from datetime import datetime, timezone

from app import tenancy as tenancy_mod

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

# GAP-017: server-side role vocabulary for decision attribution (matches
# app.auth.ROLES, uppercased). Never taken from client input.
ACTOR_ROLES = {"INVESTIGATOR", "ADMIN", "AUDITOR", "DEMO_VIEWER"}
DEFAULT_ACTOR_ROLE = "INVESTIGATOR"

# Phase 10 (SEC-001): bound free-text decision inputs. A 2 MB reason was
# accepted and persisted (4 MB file: reason + audit echo). 10 000 chars
# is generous for a rationale; actor ids stay short by construction.
MAX_REASON_CHARS = 10000
MAX_ACTOR_ID_CHARS = 256
MAX_RECOMMENDATION_CHARS = 10000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def allowed_transitions(status: str) -> list[str]:
    return list(TRANSITIONS.get(status, []))


def record_decision(store, case_id: str, decision: str, target_status: str,
                    reason: str, actor_id: str,
                    evidence_viewed: list[str] | None = None,
                    recommendation: str = "",
                    trace_id: str = "",
                    actor_role: str = DEFAULT_ACTOR_ROLE,
                    tenant=None
                    ) -> tuple[dict, dict]:
    """Validate and persist a human decision + case transition + audit event.

    ``tenant`` (TenantContext, default tenant) enforces isolation:
    foreign-tenant cases read as NOT FOUND (reads and writes alike —
    no existence oracle); new decision records are stamped
    server-side.
    """
    if decision not in DECISION_LABELS:
        raise ValueError(f"INVALID_DECISION: {decision}")
    if actor_role not in ACTOR_ROLES:
        raise ValueError(f"ACTOR_ROLE_UNKNOWN: {actor_role}")
    if not reason or not reason.strip():
        raise ValueError("REASON_REQUIRED: a reason is required")
    if len(reason.strip()) > MAX_REASON_CHARS:
        raise ValueError(
            f"REASON_TOO_LONG: {len(reason.strip())} > {MAX_REASON_CHARS}")
    if len((actor_id or "").strip()) > MAX_ACTOR_ID_CHARS:
        raise ValueError("ACTOR_ID_TOO_LONG: actor_id exceeds 256 chars")
    if len(recommendation or "") > MAX_RECOMMENDATION_CHARS:
        raise ValueError("RECOMMENDATION_TOO_LONG: recommendation too long")
    ctx = tenant or tenancy_mod.TenantContext()
    case = tenancy_mod.enforce_read(store.get_case(case_id), ctx)
    if case is None:
        raise ValueError(f"CASE_NOT_FOUND: {case_id}")
    if target_status not in TRANSITIONS.get(case["status"], []):
        raise ValueError(f"INVALID_TRANSITION: {case['status']} -> {target_status}")
    decision_id = f"decision_{len(store.state['decisions']) + 1:04d}"
    record = {
        "decision_id": decision_id, "case_id": case_id, "actor_id": actor_id,
        "actor_role": actor_role, "decision": decision,
        "reason": reason.strip(),
        "evidence_viewed": evidence_viewed or [],
        "recommendation_at_decision": recommendation,
        "created_at": _now(), "authorization_scope": "synthetic",
        "trace_id": trace_id or store.state["trace_id"],
    }
    previous = case["status"]
    case["status"] = target_status
    case["updated_at"] = record["created_at"]
    tenancy_mod.stamp(record, ctx)
    store.state["decisions"].append(record)
    audit = store.append_audit(
        "human", actor_id, "case.decision", "case", case_id, previous,
        target_status, f"{decision}: {reason.strip()}", record["trace_id"],
        record["trace_id"])
    return record, audit


CASE_PRIORITIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
MAX_TITLE_CHARS = 200
MAX_NOTES_CHARS = 10000


def _valid_due_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def create_case(store, title: str, description: str = "",
                priority: str = "MEDIUM", assignee: str = "",
                due_date: str = "", notes: str = "",
                investigation_id: str = "", actor_id: str = "anonymous",
                trace_id: str = "", tenant=None) -> tuple[dict, dict]:
    """D-036: open a case (was seed-only). Validates, stamps, audits.

    ``tenant`` (TenantContext) stamps the record; a linked
    investigation must be tenant-visible (else NOT_FOUND, no
    oracle). Persists via the audit write.
    """
    title = (title or "").strip()
    if not title:
        raise ValueError("TITLE_REQUIRED: a title is required")
    if len(title) > MAX_TITLE_CHARS:
        raise ValueError(
            f"TITLE_TOO_LONG: {len(title)} > {MAX_TITLE_CHARS}")
    if priority not in CASE_PRIORITIES:
        raise ValueError(f"PRIORITY_UNKNOWN: {priority}")
    if len(assignee or "") > MAX_ACTOR_ID_CHARS:
        raise ValueError("ASSIGNEE_TOO_LONG: assignee exceeds 256 chars")
    if len(description or "") > MAX_REASON_CHARS:
        raise ValueError("DESCRIPTION_TOO_LONG: description too long")
    if len(notes or "") > MAX_NOTES_CHARS:
        raise ValueError("NOTES_TOO_LONG: notes too long")
    if due_date and not _valid_due_date(due_date):
        raise ValueError("DUE_DATE_INVALID: use YYYY-MM-DD")
    ctx = tenant or tenancy_mod.TenantContext()
    if investigation_id:
        inv = tenancy_mod.enforce_read(
            store.get_investigation(investigation_id), ctx)
        if inv is None:
            raise ValueError(
                f"INVESTIGATION_NOT_FOUND: {investigation_id}")
    store.state["case_seq"] = int(store.state.get("case_seq", 0)) + 1
    case_id = "case_%04d" % store.state["case_seq"]
    now = _now()
    case = {
        "case_id": case_id, "investigation_id": investigation_id or "",
        "title": title, "description": description or "",
        "priority": priority, "assignee": (assignee or "").strip(),
        "due_date": due_date or "", "notes": notes or "",
        "status": "NEW", "created_at": now, "updated_at": now,
        "trace_id": trace_id or store.state["trace_id"],
    }
    tenancy_mod.stamp(case, ctx)
    store.state["cases"].append(case)
    audit = store.append_audit(
        "human", actor_id, "case.opened", "case", case_id, "", "NEW",
        "Case created: %s" % title[:200], case["trace_id"],
        case["trace_id"])
    return case, audit
