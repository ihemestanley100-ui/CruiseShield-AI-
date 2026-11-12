"""Real Estate & Property module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Title and listing systems are declared BLOCKED — generic transfer/graph rules apply to property payments only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "real-estate",
    "risk_taxonomy": [
        {"code": "RE-BUY", "label": "Large property payment",
         "rules": ["R-001"]},
        {"code": "RE-BURST", "label": "Transaction burst velocity",
         "rules": ["R-002"]},
        {"code": "RE-RING", "label": "Linked buyer/seller ring",
         "rules": ["R-003", "R-004"]},
        {"code": "RE-AGENT", "label": "Shared-agent deal funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "RE-FANIN", "label": "Deposit-collection fan-in",
         "rules": ["R-006"]},
        {"code": "RE-FANOUT", "label": "Completion fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "RE-T1", "label": "Back-to-back flipping within a ring",
         "rules": ["R-003", "R-002"]},
        {"id": "RE-T2", "label": "Agent funnel to one beneficiary network",
         "rules": ["R-008", "R-005"]},
        {"id": "RE-T3", "label": "Large cash-equivalent completions",
         "rules": ["R-001", "R-007"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "property_note": note}
        for rid, note in [
            ("R-001", "Large-payment review queue"),
            ("R-002", "Deal-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Party-link review"),
            ("R-006", "Deposit fan-in alert"),
            ("R-007", "Completion fan-out alert"),
            ("R-008", "Agent-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "title-registry feed",
         "source": "land-registry connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "listing feed",
         "source": "property-portal connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "RE-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "RE-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "RE-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "RE-C1", "label": "Conveyance-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
