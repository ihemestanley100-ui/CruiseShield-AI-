"""Foreign Exchange & Remittance module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Corridor
pricing and FX-rate feeds are declared BLOCKED — generic
transfer/graph rules apply to corridor-scale flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "fx-remittance",
    "risk_taxonomy": [
        {"code": "FX-SPLIT", "label": "Split-threshold structuring",
         "rules": ["R-002"]},
        {"code": "FX-LARGE", "label": "Large corridor transfer",
         "rules": ["R-001"]},
        {"code": "FX-RING", "label": "Shared device/phone sender ring",
         "rules": ["R-003", "R-004"]},
        {"code": "FX-PAYOUT", "label": "Shared payout-beneficiary funnel",
         "rules": ["R-005", "R-008"]},
        {"code": "FX-CASCADE", "label": "Rapid onward distribution",
         "rules": ["R-007", "R-002"]},
        {"code": "FX-COLLECT", "label": "Collection fan-in",
         "rules": ["R-006", "R-003"]},
    ],
    "threat_scenarios": [
        {"id": "FX-T1", "label": "Smurfed sends from a linked ring to "
         "one payout point",
         "rules": ["R-003", "R-002", "R-005"]},
        {"id": "FX-T2", "label": "Collection then rapid corridor "
         "distribution",
         "rules": ["R-006", "R-007"]},
        {"id": "FX-T3", "label": "Repeated just-below-threshold sends "
         "to linked beneficiaries",
         "rules": ["R-002", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "fx_note": note}
        for rid, note in [
            ("R-001", "Large-transfer review queue"),
            ("R-002", "Structuring-velocity review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Payout-link review"),
            ("R-006", "Collection fan-in alert"),
            ("R-007", "Distribution fan-out alert"),
            ("R-008", "Corridor-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "corridor/FX-rate feed",
         "source": "FX-data connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "payout-agent registry",
         "source": "agent-network connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "FX-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "FX-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "FX-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "FX-C1", "label": "Corridor-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
