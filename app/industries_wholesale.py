"""Wholesale & Distribution module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Inventory and distributor systems are declared BLOCKED — generic transfer/graph rules apply to invoice flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "wholesale",
    "risk_taxonomy": [
        {"code": "WH-INV", "label": "Large invoice settlement",
         "rules": ["R-001"]},
        {"code": "WH-BURST", "label": "Invoice burst velocity",
         "rules": ["R-002"]},
        {"code": "WH-RING", "label": "Linked buyer ring",
         "rules": ["R-003", "R-004"]},
        {"code": "WH-DIST", "label": "Shared-distributor funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "WH-FANIN", "label": "Receipt fan-in",
         "rules": ["R-006"]},
        {"code": "WH-FANOUT", "label": "Supplier fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "WH-T1", "label": "Circular invoicing within a ring",
         "rules": ["R-003", "R-002"]},
        {"id": "WH-T2", "label": "Distributor funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "WH-T3", "label": "Large invoices to linked buyers",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "wholesale_note": note}
        for rid, note in [
            ("R-001", "Large-invoice review queue"),
            ("R-002", "Invoice-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Buyer-link review"),
            ("R-006", "Receipt fan-in alert"),
            ("R-007", "Supplier fan-out alert"),
            ("R-008", "Distributor-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "inventory feed",
         "source": "warehouse-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "distributor-registry feed",
         "source": "trade-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "WH-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "WH-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "WH-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "WH-C1", "label": "Invoice-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
