"""Education & Universities module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Enrolment and grant systems are declared BLOCKED — generic transfer/graph rules apply to bursary-scale flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "education",
    "risk_taxonomy": [
        {"code": "ED-BRS", "label": "Large bursary/grant payment",
         "rules": ["R-001"]},
        {"code": "ED-BURST", "label": "Enrolment burst velocity",
         "rules": ["R-002"]},
        {"code": "ED-RING", "label": "Linked applicant ring",
         "rules": ["R-003", "R-004"]},
        {"code": "ED-INST", "label": "Shared-institution funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "ED-FANIN", "label": "Fee/grant fan-in",
         "rules": ["R-006"]},
        {"code": "ED-FANOUT", "label": "Disbursement fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "ED-T1", "label": "Ghost-student aid ring",
         "rules": ["R-003", "R-007"]},
        {"id": "ED-T2", "label": "Institution funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "ED-T3", "label": "Large grants to linked recipients",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "education_note": note}
        for rid, note in [
            ("R-001", "Large-grant review queue"),
            ("R-002", "Enrolment-burst queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Applicant-link review"),
            ("R-006", "Fee fan-in alert"),
            ("R-007", "Disbursement fan-out alert"),
            ("R-008", "Institution-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "enrolment feed",
         "source": "sis-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "grant feed",
         "source": "grants-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "ED-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "ED-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "ED-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "ED-C1", "label": "Bursary-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
