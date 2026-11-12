"""Energy & Utilities module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Metering and billing systems are declared BLOCKED — generic transfer/graph rules apply to collection flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "energy-utilities",
    "risk_taxonomy": [
        {"code": "EN-COL", "label": "Large collection sweep",
         "rules": ["R-001"]},
        {"code": "EN-BURST", "label": "Vendor burst velocity",
         "rules": ["R-002"]},
        {"code": "EN-RING", "label": "Linked vendor ring",
         "rules": ["R-003", "R-004"]},
        {"code": "EN-DISCO", "label": "Shared-collection funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "EN-FANIN", "label": "Tariff-collection fan-in",
         "rules": ["R-006"]},
        {"code": "EN-FANOUT", "label": "Contractor fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "EN-T1", "label": "Ghost-vendor billing ring",
         "rules": ["R-003", "R-007"]},
        {"id": "EN-T2", "label": "Collection funnel diversion",
         "rules": ["R-008", "R-007"]},
        {"id": "EN-T3", "label": "Large contracts to linked vendors",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "energy_note": note}
        for rid, note in [
            ("R-001", "Large-collection review queue"),
            ("R-002", "Vendor-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Vendor-link review"),
            ("R-006", "Tariff fan-in alert"),
            ("R-007", "Contractor fan-out alert"),
            ("R-008", "Collection-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "metering feed",
         "source": "ami-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "billing feed",
         "source": "cis-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "EN-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "EN-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "EN-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "EN-C1", "label": "Collection-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
