"""Aviation & Aerospace module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Charter and maintenance systems are declared BLOCKED — generic transfer/graph rules apply to charter payments.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "aviation",
    "risk_taxonomy": [
        {"code": "AV-CHR", "label": "Large charter payment",
         "rules": ["R-001"]},
        {"code": "AV-BURST", "label": "Booking burst velocity",
         "rules": ["R-002"]},
        {"code": "AV-RING", "label": "Linked charterer ring",
         "rules": ["R-003", "R-004"]},
        {"code": "AV-FBO", "label": "Shared-FBO funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "AV-FANIN", "label": "Ticket/charter fan-in",
         "rules": ["R-006"]},
        {"code": "AV-FANOUT", "label": "Operator fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "AV-T1", "label": "Ghost-charter billing ring",
         "rules": ["R-003", "R-007"]},
        {"id": "AV-T2", "label": "FBO funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "AV-T3", "label": "Large charters for linked parties",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "aviation_note": note}
        for rid, note in [
            ("R-001", "Large-charter review queue"),
            ("R-002", "Booking-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Charterer-link review"),
            ("R-006", "Ticket fan-in alert"),
            ("R-007", "Operator fan-out alert"),
            ("R-008", "FBO-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "charter feed",
         "source": "ops-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "maintenance feed",
         "source": "mro-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "AV-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "AV-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "AV-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "AV-C1", "label": "Charter-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
