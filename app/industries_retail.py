"""Retail & Supermarkets module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). POS item-level and loyalty systems are declared BLOCKED — generic transfer/graph rules apply to settlement flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "retail",
    "risk_taxonomy": [
        {"code": "RT-STL", "label": "Large settlement transfer",
         "rules": ["R-001"]},
        {"code": "RT-BURST", "label": "Refund burst velocity",
         "rules": ["R-002"]},
        {"code": "RT-RING", "label": "Shared device/phone refund ring",
         "rules": ["R-003", "R-004"]},
        {"code": "RT-STORE", "label": "Shared-store refund funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "RT-FANIN", "label": "Takings collection fan-in",
         "rules": ["R-006"]},
        {"code": "RT-FANOUT", "label": "Supplier payout fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "RT-T1", "label": "Coordinated refunds across stores",
         "rules": ["R-003", "R-002"]},
        {"id": "RT-T2", "label": "Supplier funnel to linked accounts",
         "rules": ["R-008", "R-005"]},
        {"id": "RT-T3", "label": "Large settlements to one beneficiary",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "retail_note": note}
        for rid, note in [
            ("R-001", "Large-settlement review queue"),
            ("R-002", "Refund-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Beneficiary-link review"),
            ("R-006", "Takings fan-in alert"),
            ("R-007", "Supplier fan-out alert"),
            ("R-008", "Store-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "POS item-level feed",
         "source": "pos-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "loyalty feed",
         "source": "loyalty-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "RT-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "RT-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "RT-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "RT-C1", "label": "Settlement-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
