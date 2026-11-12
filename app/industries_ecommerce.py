"""E-commerce & Online Marketplaces module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Order and seller systems are declared BLOCKED — generic transfer/graph rules apply to payout-scale flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "ecommerce",
    "risk_taxonomy": [
        {"code": "EC-PAY", "label": "Large seller payout",
         "rules": ["R-001"]},
        {"code": "EC-BURST", "label": "Order/refund burst velocity",
         "rules": ["R-002"]},
        {"code": "EC-RING", "label": "Shared device/phone seller ring",
         "rules": ["R-003", "R-004"]},
        {"code": "EC-MKT", "label": "Shared-marketplace payout funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "EC-FANIN", "label": "Buyer-payment fan-in",
         "rules": ["R-006"]},
        {"code": "EC-FANOUT", "label": "Seller fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "EC-T1", "label": "Fake-order ring cashing out",
         "rules": ["R-003", "R-007"]},
        {"id": "EC-T2", "label": "Refund-abuse burst across accounts",
         "rules": ["R-002", "R-008"]},
        {"id": "EC-T3", "label": "Large payouts to linked sellers",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "ecommerce_note": note}
        for rid, note in [
            ("R-001", "Large-payout review queue"),
            ("R-002", "Burst-velocity review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Seller-link review"),
            ("R-006", "Buyer fan-in alert"),
            ("R-007", "Payout fan-out alert"),
            ("R-008", "Marketplace-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "order feed",
         "source": "marketplace connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "seller-registry feed",
         "source": "seller-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "EC-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "EC-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "EC-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "EC-C1", "label": "Payout-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
