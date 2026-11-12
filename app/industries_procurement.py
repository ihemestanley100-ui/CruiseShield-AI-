"""Public Procurement & Infrastructure module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Tender and contract systems are declared BLOCKED — generic transfer/graph rules apply to award-scale flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "procurement-infra",
    "risk_taxonomy": [
        {"code": "PR-AWARD", "label": "Large contract award",
         "rules": ["R-001"]},
        {"code": "PR-BURST", "label": "Award burst velocity",
         "rules": ["R-002"]},
        {"code": "PR-RING", "label": "Linked bidder ring",
         "rules": ["R-003", "R-004"]},
        {"code": "PR-VENDOR", "label": "Shared-vendor award funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "PR-FANIN", "label": "Bid-bond collection fan-in",
         "rules": ["R-006"]},
        {"code": "PR-FANOUT", "label": "Progress-payment fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "PR-T1", "label": "Rotating awards within a bidder ring",
         "rules": ["R-003", "R-001"]},
        {"id": "PR-T2", "label": "Subcontract funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "PR-T3", "label": "Mobilisation then rapid drawdowns",
         "rules": ["R-006", "R-007"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "procurement_note": note}
        for rid, note in [
            ("R-001", "Large-award review queue"),
            ("R-002", "Award-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Beneficiary-link review"),
            ("R-006", "Collection fan-in alert"),
            ("R-007", "Drawdown fan-out alert"),
            ("R-008", "Bidder-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "tender feed",
         "source": "e-procurement connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "contract-ledger feed",
         "source": "works-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "PR-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "PR-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "PR-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "PR-C1", "label": "Award-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
