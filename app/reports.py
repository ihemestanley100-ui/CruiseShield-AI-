"""Deterministic investigation reports (UFI section 26).

One evidence-driven builder serves all 15 report types: each type selects
sections, each section renders only from the supplied evidence bundle, and
missing evidence renders as an explicit gap - never as invented content.
Every report separates verified facts, provider-reported facts,
observations, inferences, unverified information, and limitations.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

REPORT_TYPES = (
    "transaction", "payment_method", "party", "fraud_pattern",
    "tracing", "network_relationship", "crypto", "gift_card",
    "remittance", "identity", "telecom", "device", "geospatial",
    "industry", "comprehensive",
)

_SECTIONS: dict[str, tuple[str, ...]] = {
    "transaction": ("transactions", "lifecycle", "limitations"),
    "payment_method": ("payment_methods", "traceability", "limitations"),
    "party": ("parties", "resolution", "limitations"),
    "fraud_pattern": ("typologies", "signals", "outcomes", "limitations"),
    "tracing": ("trace", "limitations"),
    "network_relationship": ("graph", "limitations"),
    "crypto": ("crypto", "limitations"),
    "gift_card": ("gift_cards", "limitations"),
    "remittance": ("remittance", "limitations"),
    "identity": ("identity", "limitations"),
    "telecom": ("telecom", "limitations"),
    "device": ("devices", "limitations"),
    "geospatial": ("geospatial", "limitations"),
    "industry": ("industry", "typologies", "limitations"),
    "comprehensive": ("transactions", "payment_methods", "parties",
                      "typologies", "signals", "trace", "graph",
                      "identity", "telecom", "devices", "geospatial",
                      "outcomes", "limitations"),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build(report_type: str, bundle: dict[str, Any],
          investigation_id: str | None = None) -> dict[str, Any]:
    """Build a report from an evidence bundle. Unknown types raise."""
    if report_type not in REPORT_TYPES:
        raise ValueError("REPORT_TYPE_UNKNOWN: %s" % report_type)
    sections: dict[str, Any] = {}
    gaps: list[str] = []
    for section in _SECTIONS[report_type]:
        if section in bundle and bundle[section] is not None:
            sections[section] = bundle[section]
        else:
            sections[section] = {"status": "not_available",
                                 "note": "No evidence supplied."}
            gaps.append(section)
    return {
        "report_type": report_type,
        "investigation_id": investigation_id,
        "generated_at": _now(),
        "sections": sections,
        "evidence_gaps": gaps,
        "reading_guide": {
            "verified_facts": "sections whose source is a verified record",
            "provider_reported": "sections sourced from provider responses",
            "inferences": "labelled as inferred inside their section",
            "unverified": "labelled UNVERIFIED / UNKNOWN inside sections",
        },
    }
