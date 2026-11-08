"""Recovery connector capability matrix (recovery directive
section 7).

Every connector starts with every recovery capability UNSUPPORTED.
A capability flips to VERIFIED only through an admin declaration
carrying verification evidence (doc reference + verified date);
there is no other path. Live submission requires a VERIFIED
capability; everything else routes to the controlled manual
workflow. No provider is represented as capable without proof.
"""
from __future__ import annotations

from typing import Any

CAPABILITIES = (
    "transaction_lookup", "transaction_status", "cancellation",
    "reversal", "recall", "dispute_submission", "refund",
    "beneficiary_info_request", "funds_availability",
    "restriction_request", "request_status", "recovery_confirmation",
)


def matrix(store: Any) -> list[dict[str, Any]]:
    """Full connector x capability matrix (declared = verified)."""
    from app import connectors as conn_mod

    declared = {}
    for row in store.state.get("recovery_caps", []):
        if isinstance(row, dict) and row.get("connector_id"):
            declared[row["connector_id"]] = row
    rows = []
    for spec in conn_mod.registry():
        ident = spec.get("adapter") or spec.get("id") or spec.get(
            "name")
        entry = declared.get(ident, {})
        caps = {}
        for cap in CAPABILITIES:
            claimed = (entry.get("capabilities") or {}).get(cap)
            caps[cap] = claimed if isinstance(claimed, dict) else {
                "status": "UNSUPPORTED", "evidence": None,
                "verified_at": None}
        rows.append({"connector_id": ident,
                     "category": spec.get("category"),
                     "capabilities": caps})
    return rows


def declare(store: Any, connector_id: str, capability: str,
            evidence: str, actor: str) -> dict[str, Any]:
    """Admin declaration of one VERIFIED capability with evidence."""
    from app import connectors as conn_mod

    if capability not in CAPABILITIES:
        raise ValueError("RECOVERY_CAP_UNKNOWN: %s" % capability)
    known = {(s.get("adapter") or s.get("id") or s.get("name"))
             for s in conn_mod.registry()}
    if connector_id not in known:
        raise ValueError("CONNECTOR_UNKNOWN: %s" % connector_id)
    if not (evidence or "").strip():
        raise ValueError("RECOVERY_CAP_NEEDS_EVIDENCE")
    rows = store.state.setdefault("recovery_caps", [])
    entry = next((r for r in rows
                  if isinstance(r, dict)
                  and r.get("connector_id") == connector_id), None)
    if entry is None:
        entry = {"connector_id": connector_id, "capabilities": {}}
        rows.append(entry)
    from datetime import datetime, timezone
    entry.setdefault("capabilities", {})[capability] = {
        "status": "VERIFIED", "evidence": evidence.strip(),
        "verified_at": datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"),
        "declared_by": actor}
    store._save()
    return dict(entry)


def verified(store: Any, connector_id: str,
             capability: str) -> bool:
    """True only for a VERIFIED declared capability."""
    for row in store.state.get("recovery_caps", []):
        if isinstance(row, dict) and row.get(
                "connector_id") == connector_id:
            cap = (row.get("capabilities") or {}).get(capability, {})
            return cap.get("status") == "VERIFIED"
    return False
