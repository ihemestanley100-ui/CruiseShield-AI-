"""Manufacturing & Industrial Production module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Production and supplier systems are declared BLOCKED — generic transfer/graph rules apply to payment flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "manufacturing",
    "risk_taxonomy": [
        {"code": "MF-PAY", "label": "Large supplier payment",
         "rules": ["R-001"]},
        {"code": "MF-BURST", "label": "Payment burst velocity",
         "rules": ["R-002"]},
        {"code": "MF-RING", "label": "Linked supplier ring",
         "rules": ["R-003", "R-004"]},
        {"code": "MF-PLANT", "label": "Shared-plant payment funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "MF-FANIN", "label": "Customer-receipt fan-in",
         "rules": ["R-006"]},
        {"code": "MF-FANOUT", "label": "Supplier fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "MF-T1", "label": "Phantom-supplier payment ring",
         "rules": ["R-003", "R-007"]},
        {"id": "MF-T2", "label": "Kickback funnel via one plant",
         "rules": ["R-008", "R-005"]},
        {"id": "MF-T3", "label": "Large payments to linked suppliers",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "manufacturing_note": note}
        for rid, note in [
            ("R-001", "Large-payment review queue"),
            ("R-002", "Payment-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Supplier-link review"),
            ("R-006", "Receipt fan-in alert"),
            ("R-007", "Supplier fan-out alert"),
            ("R-008", "Plant-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "production feed",
         "source": "mes-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "supplier-registry feed",
         "source": "erp-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "MF-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "MF-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "MF-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "MF-C1", "label": "Payment-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
