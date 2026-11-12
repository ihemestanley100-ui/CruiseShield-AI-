"""Luxury Goods & Precious Metals module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Provenance and vault systems are declared BLOCKED — generic transfer/graph rules apply to high-value payments only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "luxury-goods",
    "risk_taxonomy": [
        {"code": "LX-HV", "label": "Large high-value payment",
         "rules": ["R-001"]},
        {"code": "LX-BURST", "label": "Consignment burst velocity",
         "rules": ["R-002"]},
        {"code": "LX-RING", "label": "Linked buyer ring",
         "rules": ["R-003", "R-004"]},
        {"code": "LX-HOUSE", "label": "Shared-auction-house funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "LX-FANIN", "label": "Consignment fan-in",
         "rules": ["R-006"]},
        {"code": "LX-FANOUT", "label": "Settlement fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "LX-T1", "label": "Shill-bidding ring cashing out",
         "rules": ["R-003", "R-007"]},
        {"id": "LX-T2", "label": "House funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "LX-T3", "label": "Large private sales to linked buyers",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "luxury_note": note}
        for rid, note in [
            ("R-001", "Large-payment review queue"),
            ("R-002", "Consignment-burst queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Buyer-link review"),
            ("R-006", "Consignment fan-in alert"),
            ("R-007", "Settlement fan-out alert"),
            ("R-008", "House-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "provenance feed",
         "source": "registry-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "vault feed",
         "source": "vault-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "LX-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "LX-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "LX-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "LX-C1", "label": "Provenance-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
