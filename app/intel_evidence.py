"""Intelligence evidence records + provenance (DI-09, additive layer).

Translates DI-08 candidate findings into traceable FindingRecords with
explicit provenance classification. Nothing here mutates the historical
39-record evidence package, appends audits, or persists anything: all
outputs are derived at request time. Audit metadata is provided as a
descriptor builders' output for existing flows to record through
their own authorized paths — never auto-appended.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from app import intel_link as link_mod
from app import risk_intel as rintel_mod

CATEGORIES = {"DEVICE", "IP", "GEOLOCATION", "SHARED_DEVICE", "SHARED_IP",
              "LOCATION_COMPARISON", "DEVICE_HISTORY", "NETWORK_CONTEXT"}

PROVENANCE = {"SYNTHETIC_FIXTURE", "DERIVED_FROM_SYNTHETIC", "USER_SUPPLIED",
              "EXTERNAL_PROVIDER_VERIFIED", "UNKNOWN_SOURCE"}


class FindingRecord(BaseModel):
    """One traceable intelligence finding (derived, non-persisted)."""

    finding_id: str
    category: str
    signal_id: str
    status: str
    subject_type: str = "unknown"
    subject_ref: str = "unknown"
    transaction_ref: str = "unknown"
    account_ref: str = "unknown"
    investigation_ref: str = "unknown"
    source_observation_ids: list[str] = Field(default_factory=list)
    source_event_ids: list[str] = Field(default_factory=list)
    source_edge_ids: list[str] = Field(default_factory=list)
    observed_at: str = ""
    processed_at: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    provenance: str = "UNKNOWN_SOURCE"
    confidence: str = "unknown"
    freshness: str = "unknown"
    synthetic: bool = True
    derivation_method: str = ""
    explanation: str = ""
    limitations: list[str] = Field(default_factory=list)
    human_review: str = "not_required"


def _category_for(signal_id: str, category: str) -> str:
    if signal_id.startswith("DEV-SHARED"):
        return "SHARED_DEVICE"
    if signal_id.startswith("DEV-"):
        return "DEVICE"
    if "SHARED" in signal_id and category == "ip":
        return "SHARED_IP"
    if category == "ip":
        return "IP"
    if signal_id == "GEO-TRAVEL":
        return "LOCATION_COMPARISON"
    if category == "geolocation":
        return "GEOLOCATION"
    if category == "cross_signal":
        return "NETWORK_CONTEXT"
    return "DEVICE"


def _provenance_for(finding: dict[str, Any]) -> str:
    if finding.get("observation_refs"):
        return "DERIVED_FROM_SYNTHETIC"
    return "UNKNOWN_SOURCE"


def build_findings(state: dict[str, Any], subject_type: str,
                   subject_id: str,
                   now: Optional[datetime] = None) -> Optional[list[dict[str, Any]]]:
    """Translate DI-08 findings into FindingRecords (None if unknown)."""
    assessment = rintel_mod.assess(state, subject_type, subject_id, now)
    if assessment is None:
        return None
    processed = (now or datetime.now(timezone.utc)).isoformat().replace(
        "+00:00", "Z")
    refs = {"transaction_ref": "unknown", "account_ref": "unknown",
            "investigation_ref": "unknown"}
    if subject_type == "transaction":
        refs["transaction_ref"] = subject_id
    elif subject_type == "account":
        refs["account_ref"] = subject_id
    elif subject_type == "investigation":
        refs["investigation_ref"] = subject_id
        linked = link_mod.investigation_intel(state, subject_id)
        if linked and linked["transaction_id"] != "unknown":
            refs["transaction_ref"] = linked["transaction_id"]
    records = []
    for index, finding in enumerate(assessment["findings"]):
        record = FindingRecord(
            finding_id=f"DIF-{finding['signal_id']}-{index:03d}",
            category=_category_for(finding["signal_id"],
                                   finding["category"]),
            signal_id=finding["signal_id"], status=finding["status"],
            subject_type=subject_type, subject_ref=subject_id,
            transaction_ref=refs["transaction_ref"],
            account_ref=refs["account_ref"],
            investigation_ref=refs["investigation_ref"],
            source_observation_ids=list(finding["observation_refs"]),
            source_event_ids=[
                r for r in finding["source_refs"] if r.startswith("evt_")],
            source_edge_ids=[
                r for r in finding["source_refs"] if r.startswith("edge_")],
            observed_at=finding.get("observed_at", ""),
            processed_at=processed,
            evidence_refs=list(finding["evidence_refs"]),
            provenance=_provenance_for(finding),
            confidence=finding.get("confidence", "unknown"),
            freshness=finding.get("freshness", "unknown"),
            synthetic=True,
            derivation_method="di08_signal_translation_v1",
            explanation=finding["explanation"],
            limitations=list(finding["limitations"]),
            human_review=finding.get("human_review", "not_required"))
        records.append(record.model_dump())
    return records


def trace_chain(state: dict[str, Any],
                investigation_id: str) -> Optional[dict[str, Any]]:
    """Transaction → account → investigation → findings → obs → evidence."""
    linked = link_mod.investigation_intel(state, investigation_id)
    if linked is None:
        return None
    findings = build_findings(state, "investigation", investigation_id) or []
    return {
        "investigation_id": investigation_id,
        "transaction_id": linked["transaction_id"],
        "findings": [{"finding_id": f["finding_id"],
                      "signal_id": f["signal_id"],
                      "source_observation_ids": f["source_observation_ids"],
                      "evidence_refs": f["evidence_refs"],
                      "provenance": f["provenance"]} for f in findings],
        "synthetic": True,
    }


def audit_descriptor(operation: str, finding_ids: list[str],
                     ai_run_id: Optional[str] = None,
                     validation_status: str = "unknown",
                     human_review: str = "not_required") -> dict[str, Any]:
    """Metadata for existing audit flows (describes; never appends)."""
    return {
        "operation": operation,
        "finding_refs": list(finding_ids),
        "ai_run_ref": ai_run_id or "none",
        "occurred_at": datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"),
        "outcome": "described_not_recorded",
        "validation_status": validation_status,
        "human_review": human_review,
        "note": "Record through authorized audit paths only; this "
                "descriptor appends nothing by itself.",
    }
