"""NGOs & Humanitarian Organisations module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Programme and beneficiary systems are declared BLOCKED — generic transfer/graph rules apply to grant flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "ngo",
    "risk_taxonomy": [
        {"code": "NG-GRT", "label": "Large programme grant",
         "rules": ["R-001"]},
        {"code": "NG-BURST", "label": "Disbursement burst velocity",
         "rules": ["R-002"]},
        {"code": "NG-RING", "label": "Linked sub-grantee ring",
         "rules": ["R-003", "R-004"]},
        {"code": "NG-PRG", "label": "Shared-programme funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "NG-FANIN", "label": "Donor-funding fan-in",
         "rules": ["R-006"]},
        {"code": "NG-FANOUT", "label": "Sub-grant fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "NG-T1", "label": "Ghost-beneficiary disbursement ring",
         "rules": ["R-003", "R-007"]},
        {"id": "NG-T2", "label": "Programme funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "NG-T3", "label": "Large grants to linked sub-grantees",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "ngo_note": note}
        for rid, note in [
            ("R-001", "Large-grant review queue"),
            ("R-002", "Disbursement-burst queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Grantee-link review"),
            ("R-006", "Donor fan-in alert"),
            ("R-007", "Sub-grant fan-out alert"),
            ("R-008", "Programme-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "programme feed",
         "source": "gms-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "beneficiary feed",
         "source": "registry-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "NG-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "NG-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "NG-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "NG-C1", "label": "Grant-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
