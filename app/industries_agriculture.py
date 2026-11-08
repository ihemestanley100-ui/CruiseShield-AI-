"""Agriculture & Agribusiness module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Crop and cooperative systems are declared BLOCKED — generic transfer/graph rules apply to offtake payments only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "agriculture",
    "risk_taxonomy": [
        {"code": "AG-OFF", "label": "Large offtake payment",
         "rules": ["R-001"]},
        {"code": "AG-BURST", "label": "Delivery burst velocity",
         "rules": ["R-002"]},
        {"code": "AG-RING", "label": "Linked farmer ring",
         "rules": ["R-003", "R-004"]},
        {"code": "AG-COOP", "label": "Shared-cooperative funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "AG-FANIN", "label": "Input-credit fan-in",
         "rules": ["R-006"]},
        {"code": "AG-FANOUT", "label": "Offtaker fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "AG-T1", "label": "Ghost-delivery ring",
         "rules": ["R-003", "R-007"]},
        {"id": "AG-T2", "label": "Cooperative funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "AG-T3", "label": "Large subsidies to linked recipients",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "agriculture_note": note}
        for rid, note in [
            ("R-001", "Large-offtake review queue"),
            ("R-002", "Delivery-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Farmer-link review"),
            ("R-006", "Input-credit fan-in alert"),
            ("R-007", "Offtaker fan-out alert"),
            ("R-008", "Cooperative-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "crop feed",
         "source": "extension-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "cooperative-ledger feed",
         "source": "coop-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "AG-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "AG-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "AG-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "AG-C1", "label": "Offtake-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
