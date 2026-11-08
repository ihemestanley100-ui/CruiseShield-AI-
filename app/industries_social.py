"""Social Media & Digital Platforms module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Creator-payout and ads systems are declared BLOCKED — generic transfer/graph rules apply to payout-scale flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "social-platforms",
    "risk_taxonomy": [
        {"code": "SO-PAY", "label": "Large creator payout",
         "rules": ["R-001"]},
        {"code": "SO-BURST", "label": "Account burst velocity",
         "rules": ["R-002"]},
        {"code": "SO-RING", "label": "Shared device/account ring",
         "rules": ["R-003", "R-004"]},
        {"code": "SO-VERT", "label": "Shared-vertical funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "SO-FANIN", "label": "Ad-spend fan-in",
         "rules": ["R-006"]},
        {"code": "SO-FANOUT", "label": "Creator fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "SO-T1", "label": "Engagement-fraud payout ring",
         "rules": ["R-003", "R-007"]},
        {"id": "SO-T2", "label": "Vertical funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "SO-T3", "label": "Large payouts to linked creators",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "social_note": note}
        for rid, note in [
            ("R-001", "Large-payout review queue"),
            ("R-002", "Account-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Account-ring investigation"),
            ("R-005", "Creator-link review"),
            ("R-006", "Ad-spend fan-in alert"),
            ("R-007", "Creator fan-out alert"),
            ("R-008", "Vertical-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "creator-payout feed",
         "source": "payout-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "ads feed",
         "source": "ads-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "SO-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "SO-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "SO-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "SO-C1", "label": "Payout-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
