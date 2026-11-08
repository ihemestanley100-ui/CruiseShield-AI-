"""Supply Chain & Logistics module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Shipment and carrier systems are declared BLOCKED — generic transfer/graph rules apply to freight payments.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "supply-chain",
    "risk_taxonomy": [
        {"code": "SC-FRT", "label": "Large freight payment",
         "rules": ["R-001"]},
        {"code": "SC-BURST", "label": "Consignment burst velocity",
         "rules": ["R-002"]},
        {"code": "SC-RING", "label": "Linked consignee ring",
         "rules": ["R-003", "R-004"]},
        {"code": "SC-LANE", "label": "Shared-lane payment funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "SC-FANIN", "label": "Customer-receipt fan-in",
         "rules": ["R-006"]},
        {"code": "SC-FANOUT", "label": "Carrier fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "SC-T1", "label": "Ghost-consignment billing ring",
         "rules": ["R-003", "R-002"]},
        {"id": "SC-T2", "label": "Lane funnel to one carrier network",
         "rules": ["R-008", "R-007"]},
        {"id": "SC-T3", "label": "Large freight payments to linked carriers",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "supply_note": note}
        for rid, note in [
            ("R-001", "Large-freight review queue"),
            ("R-002", "Consignment-burst queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Consignee-link review"),
            ("R-006", "Receipt fan-in alert"),
            ("R-007", "Carrier fan-out alert"),
            ("R-008", "Lane-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "shipment feed",
         "source": "tms-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "carrier-registry feed",
         "source": "carrier-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "SC-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "SC-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "SC-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "SC-C1", "label": "Freight-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
