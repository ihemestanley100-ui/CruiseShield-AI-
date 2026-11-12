"""Technology & Software Companies module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Subscription and payout systems are declared BLOCKED — generic transfer/graph rules apply to billing flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "technology",
    "risk_taxonomy": [
        {"code": "TC-BIL", "label": "Large contract payment",
         "rules": ["R-001"]},
        {"code": "TC-BURST", "label": "Subscription burst velocity",
         "rules": ["R-002"]},
        {"code": "TC-RING", "label": "Linked account ring",
         "rules": ["R-003", "R-004"]},
        {"code": "TC-PLAT", "label": "Shared-platform payout funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "TC-FANIN", "label": "Subscription fan-in",
         "rules": ["R-006"]},
        {"code": "TC-FANOUT", "label": "Vendor/affiliate fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "TC-T1", "label": "Trial-abuse ring cashing out",
         "rules": ["R-003", "R-007"]},
        {"id": "TC-T2", "label": "Affiliate funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "TC-T3", "label": "Large contracts to linked vendors",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "technology_note": note}
        for rid, note in [
            ("R-001", "Large-contract review queue"),
            ("R-002", "Subscription-burst queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Account-link review"),
            ("R-006", "Subscription fan-in alert"),
            ("R-007", "Affiliate fan-out alert"),
            ("R-008", "Platform-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "subscription feed",
         "source": "billing-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "affiliate feed",
         "source": "partner-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "TC-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "TC-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "TC-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "TC-C1", "label": "Billing-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
