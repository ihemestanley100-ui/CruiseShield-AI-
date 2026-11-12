"""Construction & Engineering module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Project and subcontractor systems are declared BLOCKED — generic transfer/graph rules apply to project payments.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "construction",
    "risk_taxonomy": [
        {"code": "CN-PRJ", "label": "Large project payment",
         "rules": ["R-001"]},
        {"code": "CN-BURST", "label": "Drawdown burst velocity",
         "rules": ["R-002"]},
        {"code": "CN-RING", "label": "Linked subcontractor ring",
         "rules": ["R-003", "R-004"]},
        {"code": "CN-SITE", "label": "Shared-site payment funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "CN-FANIN", "label": "Client-funding fan-in",
         "rules": ["R-006"]},
        {"code": "CN-FANOUT", "label": "Subcontractor fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "CN-T1", "label": "Inflated-variation ring",
         "rules": ["R-003", "R-001"]},
        {"id": "CN-T2", "label": "Site funnel to one network",
         "rules": ["R-008", "R-007"]},
        {"id": "CN-T3", "label": "Front-loaded drawdowns then stall",
         "rules": ["R-006", "R-007"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "construction_note": note}
        for rid, note in [
            ("R-001", "Large-payment review queue"),
            ("R-002", "Drawdown-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Subcontractor-link review"),
            ("R-006", "Funding fan-in alert"),
            ("R-007", "Drawdown fan-out alert"),
            ("R-008", "Site-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "project-ledger feed",
         "source": "pm-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "subcontractor feed",
         "source": "vendor-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "CN-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "CN-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "CN-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "CN-C1", "label": "Project-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
