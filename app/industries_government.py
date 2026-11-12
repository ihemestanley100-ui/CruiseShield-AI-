"""Government & Public Administration module (Level 14 §6): TESTING.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Treasury
and vendor systems are declared BLOCKED; classification/handling
controls are required before any operational use and are NOT
claimed here. Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "government",
    "risk_taxonomy": [
        {"code": "GV-DISB", "label": "Disbursement burst velocity",
         "rules": ["R-002"]},
        {"code": "GV-LARGE", "label": "Large single disbursement",
         "rules": ["R-001"]},
        {"code": "GV-RING", "label": "Linked payee ring",
         "rules": ["R-003", "R-004"]},
        {"code": "GV-VENDOR", "label": "Shared-vendor payment funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "GV-FANOUT", "label": "Rapid sub-disbursement fan-out",
         "rules": ["R-007", "R-002"]},
        {"code": "GV-FANIN", "label": "Revenue collection fan-in",
         "rules": ["R-006", "R-003"]},
    ],
    "threat_scenarios": [
        {"id": "GV-T1", "label": "Split disbursements to linked "
         "payees under review thresholds",
         "rules": ["R-002", "R-005"]},
        {"id": "GV-T2", "label": "Vendor funnel concentrating awards "
         "to one beneficiary network",
         "rules": ["R-008", "R-005"]},
        {"id": "GV-T3", "label": "Collection then rapid onward "
         "disbursement",
         "rules": ["R-006", "R-007"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "government_note": note}
        for rid, note in [
            ("R-001", "Large-disbursement review queue"),
            ("R-002", "Disbursement-velocity review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Payee-link review"),
            ("R-006", "Collection fan-in alert"),
            ("R-007", "Disbursement fan-out alert"),
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
        {"field": "treasury disbursement feed",
         "source": "treasury-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "vendor/award registry",
         "source": "procurement-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "GV-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "GV-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "GV-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "GV-C1", "label": "Disbursement-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
