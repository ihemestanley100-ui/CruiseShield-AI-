"""Candidate risk-intelligence layer (DI-08, additive assessment only).

Engine id ``risk-intelligence-v2-candidate``: deterministic,
explainable, read-only findings over DI-03..DI-07 observations. It
never touches risk-score-v1 (no weights, rules, scores, or decisions
are read for mutation or written anywhere), emits no numeric score,
makes no fraud determination, and authorizes nothing.

Gated by RISK_INTELLIGENCE_V2_ENABLED (default OFF). Flag OFF serves
a documented disabled response; flag ON exposes findings only.
Unknown stays UNKNOWN; missing stays INSUFFICIENT_EVIDENCE; stale is
never presented as current. No providers, no network, no collection.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from app import device_intel as device_mod
from app import geo_intel as geo_mod
from app import intel_link as link_mod
from app import ip_intel as ip_mod

ENGINE_ID = "risk-intelligence-v2-candidate"
FLAG_NAME = "RISK_INTELLIGENCE_V2_ENABLED"

STATUSES = {"PRESENT", "ABSENT_WITH_SUFFICIENT_COVERAGE", "UNKNOWN",
            "UNAVAILABLE", "STALE", "CONFLICTING", "INSUFFICIENT_EVIDENCE"}


class Finding(BaseModel):
    """One explainable candidate signal (never a verdict)."""

    signal_id: str
    category: str  # device | ip | geolocation | cross_signal
    status: str
    observation_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    observed_at: str = ""
    assessed_at: str = ""
    freshness: str = "unknown"
    confidence: str = "unknown"
    evidence_refs: list[str] = Field(default_factory=list)
    explanation: str = ""
    limitations: list[str] = Field(default_factory=list)
    human_review: str = "not_required"


def enabled() -> bool:
    """Feature flag, default OFF; only explicit "true" enables."""
    return os.environ.get(FLAG_NAME, "").strip().lower() == "true"


def _now_iso(now: Optional[datetime] = None) -> str:
    return (now or datetime.now(timezone.utc)).isoformat().replace(
        "+00:00", "Z")


def _finding(signal_id: str, category: str, status: str,
             explanation: str, now: Optional[datetime], **over: Any
             ) -> Finding:
    assert status in STATUSES, status
    return Finding(signal_id=signal_id, category=category, status=status,
                   assessed_at=_now_iso(now), explanation=explanation,
                   **over)


def _device_findings(state: dict[str, Any], txn_ids: set[str],
                     now: Optional[datetime],
                     account_id: Optional[str] = None) -> list[Finding]:
    out: list[Finding] = []

    def in_scope(o: Any) -> bool:
        if o.txn_id in txn_ids:
            return True
        if account_id is not None and o.account_id == account_id:
            return True  # graph-edge attribution for account subjects
        return not txn_ids and account_id is None

    obs = [o for o in device_mod.build_observations(state) if in_scope(o)]
    labels = sorted({o.device_id for o in obs})
    if not labels:
        return [_finding(
            "DEV-COVERAGE", "device", "INSUFFICIENT_EVIDENCE",
            "No device observations in scope; nothing can be assessed.",
            now, limitations=["No device data available."],
            human_review="required_if_decision_depends_on_device")]
    for label in labels:
        mine = [o for o in obs if o.device_id == label]
        profile = device_mod.get_profile(state, label)
        stamps = sorted(o.observed_at for o in mine if o.observed_at)
        fresh = geo_mod.classify_freshness(stamps[-1], now) if stamps \
            else "unknown"
        status = "PRESENT" if fresh in ("fresh", "unknown") else "STALE"
        accts = sorted({o.account_id for o in mine if o.account_id})
        out.append(_finding(
            f"DEV-KNOWN-{label}", "device", status,
            f"Device label {label} observed {len(mine)} time(s) on "
            f"{len(accts)} account(s); fixture label, not verified "
            f"identity. Shared infrastructure is not fraud evidence.",
            now, observation_refs=[o.obs_id for o in mine],
            source_refs=[o.source_ref for o in mine],
            observed_at=stamps[-1] if stamps else "",
            freshness=fresh, confidence="low",
            evidence_refs=(profile.evidence_refs.get("graph_edge_ids", [])
                           + profile.evidence_refs.get("event_ids", []))
            if profile else [],
            limitations=["Label only; no measured fingerprint.",
                         "Attributes are declared synthetic demo values."],
            human_review="required_before_any_action"))
        if profile is not None and profile.shared:
            out.append(_finding(
                f"DEV-SHARED-{label}", "device", status,
                f"Device label {label} is shared across accounts "
                f"{', '.join(profile.account_ids)}. Sharing alone "
                f"proves nothing about intent.",
                now, observation_refs=[o.obs_id for o in mine],
                freshness=fresh, confidence="low",
                evidence_refs=profile.evidence_refs.get(
                    "graph_edge_ids", []),
                limitations=["Coincidental sharing is common."],
                human_review="required_before_any_action"))
    out.append(_finding(
        "DEV-NEWNESS", "device", "INSUFFICIENT_EVIDENCE",
        "New-device assessment needs a first-seen baseline the fixtures "
        "do not provide; no newness claim is made.",
        now, limitations=["No temporal baseline available."]))
    return out


def _ip_findings(state: dict[str, Any], txn_ids: set[str],
                 now: Optional[datetime]) -> list[Finding]:
    out: list[Finding] = []
    obs = [o for o in ip_mod.build_observations(state)
           if o.txn_id in txn_ids or not txn_ids]
    labels = sorted({o.ip_label for o in obs})
    if not labels:
        return [_finding(
            "IP-COVERAGE", "ip", "INSUFFICIENT_EVIDENCE",
            "No IP observations in scope; nothing can be assessed.",
            now, human_review="required_if_decision_depends_on_ip")]
    for label in labels:
        mine = [o for o in obs if o.ip_label == label]
        stamps = sorted(o.observed_at for o in mine if o.observed_at)
        fresh = geo_mod.classify_freshness(stamps[-1], now) if stamps \
            else "unknown"
        out.append(_finding(
            f"IP-LABEL-{label}", "ip",
            "PRESENT" if fresh in ("fresh", "unknown") else "STALE",
            f"IP fixture label {label} observed without an address; no "
            f"classification, reputation, or VPN/proxy/Tor inference is "
            f"possible. Provider enrichment unavailable (NullProvider).",
            now, observation_refs=[o.obs_id for o in mine],
            source_refs=[o.source_ref for o in mine],
            observed_at=stamps[-1] if stamps else "",
            freshness=fresh, confidence="unknown",
            limitations=["Opaque label, not an address.",
                         "No provider source authorized."],
            human_review="required_before_any_action"))
    out.append(_finding(
        "IP-PROVIDER", "ip", "UNAVAILABLE",
        "No IP intelligence provider is configured; ASN/ISP/VPN/Tor/"
        "reputation are UNKNOWN, not safe and not malicious.",
        now, confidence="unknown",
        limitations=["NullProvider only."]))
    return out


def _geo_findings(state: dict[str, Any], txn_ids: set[str],
                  now: Optional[datetime]) -> list[Finding]:
    all_obs = geo_mod.build_label_observations(state)
    obs = [o for o in all_obs if o["txn_id"] in txn_ids or not txn_ids]
    labels = sorted({o["location_label"] for o in obs})
    if not labels:
        return [_finding(
            "GEO-COVERAGE", "geolocation", "INSUFFICIENT_EVIDENCE",
            "No location observations in scope; nothing can be assessed.",
            now, human_review="required_if_decision_depends_on_location")]
    out = []
    for label in labels:
        mine = [o for o in obs if o["location_label"] == label]
        stamps = sorted(o["observed_at"] for o in mine if o["observed_at"])
        fresh = geo_mod.classify_freshness(stamps[-1], now) if stamps \
            else "unknown"
        out.append(_finding(
            f"GEO-LABEL-{label}", "geolocation",
            "PRESENT" if fresh in ("fresh", "unknown") else "STALE",
            f"Location fixture label {label} observed without coordinates "
            f"or place data; no country/city, travel, or anomaly "
            f"statement is possible. IP-derived locations would be "
            f"approximate only.",
            now, observation_refs=[o["obs_id"] for o in mine],
            source_refs=[o["source_ref"] for o in mine],
            observed_at=stamps[-1] if stamps else "",
            freshness=fresh, confidence="unknown",
            limitations=["Label only; no coordinates or place data.",
                         "No GPS permission or collection exists."],
            human_review="required_before_any_action"))
    out.append(_finding(
        "GEO-TRAVEL", "geolocation", "INSUFFICIENT_EVIDENCE",
        "Impossible-travel analysis requires two coordinate-bearing "
        "timestamps; none exist, so no conclusion is drawn.",
        now, limitations=["No coordinates available."]))
    return out


def _cross_findings(state: dict[str, Any], subject: dict[str, str],
                    txn_ids: set[str],
                    now: Optional[datetime]) -> list[Finding]:
    def _linked(group: dict[str, Any]) -> bool:
        if txn_ids & set(group.get("txn_ids", [])):
            return True
        # Graph-edge-only attribution for account subjects (mirrors the
        # account_id branch of _device_findings).
        return (subject["type"] == "account"
                and subject["id"] in group.get("account_ids", []))

    shared_dev = [s for s in device_mod.shared_devices(state)
                  if _linked(s)]
    shared_ip = [s for s in ip_mod.shared_ips(state) if _linked(s)]
    if not (shared_dev or shared_ip):
        return [_finding(
            "XSHARE-SUMMARY", "cross_signal", "UNKNOWN",
            f"No shared-device or shared-IP groups linked to "
            f"{subject['type']} {subject['id']}; nothing in scope to "
            f"report. Sharing is reported, never judged.",
            now, confidence="unknown",
            limitations=["No linked sharing groups in scope."],
            human_review="required_before_any_action")]
    spacer = "none observed"
    return [_finding(
        "XSHARE-SUMMARY", "cross_signal", "PRESENT",
        f"Shared-device groups: "
        f"{', '.join(s['device_id'] for s in shared_dev) or spacer}; "
        f"shared-IP groups: "
        f"{', '.join(s['ip_label'] for s in shared_ip) or spacer}. "
        f"Scoped to {subject['type']} {subject['id']} linkage only; "
        f"sharing is reported, never judged.",
        now, confidence="low",
        limitations=["Fixture-derived sharing references."],
        human_review="required_before_any_action")]


def assess(state: dict[str, Any], subject_type: str, subject_id: str,
           now: Optional[datetime] = None) -> Optional[dict[str, Any]]:
    """Assess one subject; None when the subject is unknown.

    Findings only: no numeric score, no verdict, no mutation.
    """
    if subject_type == "transaction":
        linked = link_mod.transaction_intel(state, subject_id)
        txn_ids = {subject_id} if linked else set()
    elif subject_type == "account":
        linked = link_mod.account_intel(state, subject_id)
        txn_ids = set(linked["transaction_ids"]) if linked else set()
    elif subject_type == "investigation":
        linked = link_mod.investigation_intel(state, subject_id)
        txn_ids = {linked["transaction_id"]} if linked and linked[
            "transaction_id"] != "unknown" else set()
    else:
        return None
    if linked is None:
        return None
    findings: list[Finding] = []
    findings += _device_findings(
        state, txn_ids, now,
        account_id=subject_id if subject_type == "account" else None)
    findings += _ip_findings(state, txn_ids, now)
    findings += _geo_findings(state, txn_ids, now)
    subject = {"type": subject_type, "id": subject_id}
    findings += _cross_findings(state, subject, txn_ids, now)
    return {"engine": ENGINE_ID, "enabled": True, "subject": subject,
            "finding_count": len(findings),
            "findings": [f.model_dump() for f in findings],
            "numeric_score": None,
            "score_note": "No candidate numeric score: available evidence "
                          "does not justify one.",
            "authoritative_engine": "risk-score-v1 (unchanged; see the "
                                    "standard risk endpoints)",
            "synthetic": True}


def disabled_response() -> dict[str, Any]:
    """Documented flag-OFF response (no findings, no behavior change)."""
    return {"engine": ENGINE_ID, "enabled": False,
            "status": "disabled_by_flag",
            "detail": f"Set {FLAG_NAME}=true to expose candidate "
                      f"findings. risk-score-v1 remains authoritative.",
            "findings": []}


def to_ai_context(assessment: dict[str, Any]) -> dict[str, Any]:
    """Minimal grounded AI context: ids + statuses only, no new claims."""
    return {"engine": assessment["engine"],
            "subject": assessment["subject"],
            "signals": [{"signal_id": f["signal_id"],
                         "category": f["category"], "status": f["status"],
                         "evidence_refs": f["evidence_refs"],
                         "explanation": f["explanation"]}
                        for f in assessment.get("findings", [])],
            "grounding_rule": "Cite only these signal and evidence IDs; "
                              "preserve UNKNOWN/UNAVAILABLE; never invent "
                              "observations or alter risk-score-v1."}
