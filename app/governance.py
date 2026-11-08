"""Governance workflows: SAR drafts, DSR tracker, legal holds (§13).

Technical workflow controls only — this module makes NO legal or
regulatory compliance claim. In particular, SAR "FILED" means the
internal handoff package was prepared and its handoff recorded; any
actual regulator submission happens outside this system through
counsel-approved channels and is recorded as an external reference.
"""
from __future__ import annotations

import time
import uuid
from typing import Any

SAR_FLOW = {"DRAFT": ("IN_REVIEW",), "IN_REVIEW": ("READY", "DRAFT"),
            "READY": ("FILED",), "FILED": ("ACKNOWLEDGED",),
            "ACKNOWLEDGED": ()}
DSR_FLOW = {"RECEIVED": ("VERIFYING",), "VERIFYING": ("IN_PROGRESS",
            "REJECTED"), "IN_PROGRESS": ("FULFILLED", "REJECTED"),
            "FULFILLED": (), "REJECTED": ()}
DSR_KINDS = ("access", "erasure", "rectification", "portability")


def _new_id(prefix: str) -> str:
    return "%s_%s" % (prefix, uuid.uuid4().hex[:12])


def create_sar(case_id: str, summary: str, created_by: str) -> dict:
    """Draft a SAR handoff package for a case (DRAFT)."""
    if not (case_id or "").strip():
        raise ValueError("GOV_CASE_REQUIRED: sar needs a case_id")
    if not (summary or "").strip():
        raise ValueError("GOV_SUMMARY_REQUIRED: sar needs a summary")
    now = time.time()
    return {"sar_id": _new_id("sar"), "case_id": case_id.strip(),
            "summary": summary.strip()[:2000], "status": "DRAFT",
            "created_by": created_by, "created_at": now,
            "updated_at": now, "history": [{"to": "DRAFT", "by": created_by,
                                            "at": now, "note": ""}]}


def transition_sar(sar: dict, to: str, actor: str, note: str = "",
                   role: str = "") -> dict:
    """Move a SAR along SAR_FLOW with separation-of-duties checks."""
    current = sar["status"]
    if to not in SAR_FLOW.get(current, ()):
        raise ValueError("GOV_TRANSITION: sar %s -> %s illegal"
                         % (current, to))
    if to in ("READY", "FILED") and role != "admin":
        raise ValueError("GOV_APPROVER: %s needs the admin role" % to)
    if to == "READY" and actor == sar.get("created_by"):
        raise ValueError("GOV_SEPARATION: approver must differ from "
                         "drafter")
    if to == "FILED" and not (note or "").strip():
        raise ValueError("GOV_HANDOFF_REF: filing needs an external "
                         "handoff reference")
    now = time.time()
    sar["status"] = to
    sar["updated_at"] = now
    sar["history"].append({"to": to, "by": actor, "at": now,
                           "note": (note or "")[:500]})
    return sar


def create_dsr(subject_ref: str, kind: str, details: str,
               received_by: str) -> dict:
    """Open a data-subject request (RECEIVED)."""
    if not (subject_ref or "").strip():
        raise ValueError("GOV_SUBJECT_REQUIRED: dsr needs a subject ref")
    if kind not in DSR_KINDS:
        raise ValueError("GOV_KIND: unknown dsr kind %r" % (kind,))
    now = time.time()
    return {"dsr_id": _new_id("dsr"), "subject_ref": subject_ref.strip(),
            "kind": kind, "details": (details or "")[:2000],
            "status": "RECEIVED", "received_by": received_by,
            "created_at": now, "updated_at": now,
            "history": [{"to": "RECEIVED", "by": received_by, "at": now,
                         "note": ""}]}


def transition_dsr(dsr: dict, to: str, actor: str, note: str = "",
                   role: str = "") -> dict:
    """Move a DSR along DSR_FLOW (fulfil/reject need admin + note)."""
    current = dsr["status"]
    if to not in DSR_FLOW.get(current, ()):
        raise ValueError("GOV_TRANSITION: dsr %s -> %s illegal"
                         % (current, to))
    if to in ("FULFILLED", "REJECTED"):
        if role != "admin":
            raise ValueError("GOV_APPROVER: %s needs the admin role"
                             % to)
        if not (note or "").strip():
            raise ValueError("GOV_OUTCOME: %s needs an outcome note"
                             % to)
    now = time.time()
    dsr["status"] = to
    dsr["updated_at"] = now
    dsr["history"].append({"to": to, "by": actor, "at": now,
                           "note": (note or "")[:500]})
    return dsr


def place_hold(resource_kind: str, resource_id: str, reason: str,
               placed_by: str) -> dict:
    """Place an active legal hold (reason required)."""
    if not (resource_kind or "").strip() or not (resource_id or ""):
        raise ValueError("GOV_TARGET: hold needs kind + resource id")
    if not (reason or "").strip():
        raise ValueError("GOV_REASON: hold needs a reason")
    now = time.time()
    return {"hold_id": _new_id("hold"),
            "resource_kind": resource_kind.strip(),
            "resource_id": str(resource_id),
            "reason": reason.strip()[:500], "active": True,
            "placed_by": placed_by, "placed_at": now,
            "released_by": "", "released_at": 0.0,
            "release_reason": ""}


def release_hold(hold: dict, reason: str, actor: str) -> dict:
    """Release an active hold (reason required)."""
    if not hold.get("active"):
        raise ValueError("GOV_HOLD_STATE: hold already released")
    if not (reason or "").strip():
        raise ValueError("GOV_REASON: release needs a reason")
    hold["active"] = False
    hold["released_by"] = actor
    hold["released_at"] = time.time()
    hold["release_reason"] = reason.strip()[:500]
    return hold


def is_held(store: Any, resource_kind: str,
            resource_id: str, tenant: str | None = None) -> bool:
    """True when an ACTIVE hold covers kind+id (optionally one tenant)."""
    from app import tenancy as tenancy_mod

    holds = store.state.get("holds", [])
    if isinstance(holds, dict):
        holds = list(holds.values())
    for hold in holds:
        if not isinstance(hold, dict) or not hold.get("active"):
            continue
        if (hold.get("resource_kind") != resource_kind
                or str(hold.get("resource_id")) != str(resource_id)):
            continue
        if (tenant is not None
                and tenancy_mod.tenant_of(hold) != tenant):
            continue
        return True
    return False
