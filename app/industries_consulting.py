"""Consulting & Professional Services module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Engagement and billing systems are declared BLOCKED — generic transfer/graph rules apply to fee flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "consulting",
    "risk_taxonomy": [
        {"code": "CS-FEE", "label": "Large fee payment",
         "rules": ["R-001"]},
        {"code": "CS-BURST", "label": "Invoice burst velocity",
         "rules": ["R-002"]},
        {"code": "CS-RING", "label": "Linked client ring",
         "rules": ["R-003", "R-004"]},
        {"code": "CS-PRAC", "label": "Shared-practice funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "CS-FANIN", "label": "Retainer fan-in",
         "rules": ["R-006"]},
        {"code": "CS-FANOUT", "label": "Subcontractor fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "CS-T1", "label": "Phantom-engagement billing ring",
         "rules": ["R-003", "R-007"]},
        {"id": "CS-T2", "label": "Practice funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "CS-T3", "label": "Large fees to linked entities",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "consulting_note": note}
        for rid, note in [
            ("R-001", "Large-fee review queue"),
            ("R-002", "Invoice-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Client-link review"),
            ("R-006", "Retainer fan-in alert"),
            ("R-007", "Subcontractor fan-out alert"),
            ("R-008", "Practice-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "engagement feed",
         "source": "psa-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "billing feed",
         "source": "billing-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "CS-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "CS-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "CS-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "CS-C1", "label": "Fee-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
