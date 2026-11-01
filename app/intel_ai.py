"""Muse Spark DI context + response validation (DI-09, additive).

Builds minimized, grounded AI context from FindingRecords and
validates model responses against known finding/evidence IDs. Pure
functions only: no adapter changes, no secret handling changes, no
network calls, no writes. Deterministic findings remain fully
available when AI is absent or fails.
"""
from __future__ import annotations

from typing import Any

BANNED_SCORE_FIELDS = {"risk_score", "fraud_probability",
                       "fraud_score", "risk_probability"}

ENFORCEMENT_PHRASES = ("freeze the account", "block the transaction",
                       "account is fraudulent", "is guilty of fraud",
                       "confirmed fraudster", "must be blocked")

INSTRUCTION = (
    "Use only the supplied intelligence findings. Cite finding IDs and "
    "evidence references for material claims. Distinguish observations "
    "from interpretations. Disclose missing, stale, or conflicting "
    "evidence and all uncertainty. Never invent devices, IPs, locations, "
    "findings, or evidence. Never claim IP geolocation proves physical "
    "location. Never present an anomaly as proof of fraud. Never invent "
    "ISP, ASN, VPN, proxy, Tor, or reputation results. Never change "
    "deterministic risk scores. Never authorize freezes, blocks, or "
    "enforcement. Recommend human review when evidence is insufficient "
    "or consequential."
)


def build_di_context(findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Minimized grounded context: ids, statuses, refs, prose bounds."""
    return {
        "instruction": INSTRUCTION,
        "findings": [{
            "finding_id": f["finding_id"],
            "signal_id": f["signal_id"],
            "category": f["category"],
            "status": f["status"],
            "evidence_refs": f["evidence_refs"],
            "provenance": f["provenance"],
            "confidence": f["confidence"],
            "freshness": f["freshness"],
            "explanation": f["explanation"],
            "limitations": f["limitations"],
        } for f in findings],
        "grounding_rule": "Cite only these finding and evidence IDs.",
    }


def validate_di_response(data: Any,
                         known: dict[str, Any]) -> tuple[str, list[str]]:
    """Validate a model response; return (status, problems).

    Statuses: VALIDATED | INVALID | UNVERIFIED. Unknown IDs, invented
    scores, and enforcement language fail closed.
    """
    problems: list[str] = []
    if not isinstance(data, dict):
        return "INVALID", ["response must be an object"]
    findings = data.get("key_findings", [])
    if not isinstance(findings, list):
        return "INVALID", ["key_findings must be a list"]
    known_findings = set(known.get("finding_ids", set()))
    known_evidence = set(known.get("evidence_ids", set()))
    for i, finding in enumerate(findings):
        if not isinstance(finding, dict):
            return "INVALID", [f"key_findings[{i}] must be an object"]
        fid = finding.get("finding_id", "")
        if fid and fid not in known_findings:
            problems.append(f"unknown finding ID cited: {fid}")
            return "INVALID", problems
        for eid in finding.get("evidence_ids", []):
            if eid not in known_evidence:
                problems.append(f"unknown evidence ID cited: {eid}")
                return "INVALID", problems
        for field in BANNED_SCORE_FIELDS:
            if field in finding:
                problems.append(f"invented numeric score field: {field}")
                return "INVALID", problems
        text = str(finding.get("finding", "")).lower()
        for phrase in ENFORCEMENT_PHRASES:
            if phrase in text:
                problems.append(f"enforcement language: {phrase}")
                return "INVALID", problems
    if data.get("conclusion", "") not in ("insufficient_evidence",
                                          "requires_review",
                                          "evidence_supports_escalation"):
        problems.append(f"bad conclusion: {data.get('conclusion')}")
        return "INVALID", problems
    if not data.get("human_review_status"):
        problems.append("missing human_review_status")
        return "UNVERIFIED", problems
    return "VALIDATED", problems
