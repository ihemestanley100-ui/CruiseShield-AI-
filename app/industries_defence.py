"""Defence & National Security module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Classified and procurement systems are declared BLOCKED; classification/handling controls are NOT claimed here.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "defence-security",
    "risk_taxonomy": [
        {"code": "DF-DISB", "label": "Large programme disbursement",
         "rules": ["R-001"]},
        {"code": "DF-BURST", "label": "Disbursement burst velocity",
         "rules": ["R-002"]},
        {"code": "DF-RING", "label": "Linked payee ring",
         "rules": ["R-003", "R-004"]},
        {"code": "DF-VENDOR", "label": "Shared-vendor payment funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "DF-FANIN", "label": "Funding fan-in",
         "rules": ["R-006"]},
        {"code": "DF-FANOUT", "label": "Sub-award fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "DF-T1", "label": "Split awards to linked payees",
         "rules": ["R-002", "R-005"]},
        {"id": "DF-T2", "label": "Vendor funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "DF-T3", "label": "Funding then rapid sub-awards",
         "rules": ["R-006", "R-007"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "defence_note": note}
        for rid, note in [
            ("R-001", "Large-award review queue"),
            ("R-002", "Award-velocity review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Payee-link review"),
            ("R-006", "Funding fan-in alert"),
            ("R-007", "Sub-award fan-out alert"),
            ("R-008", "Vendor-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "programme-ledger feed",
         "source": "finance-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "award registry feed",
         "source": "contracts-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "DF-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "DF-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "DF-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "DF-C1", "label": "Disbursement-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
