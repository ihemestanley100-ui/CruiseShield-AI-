"""Environmental & Waste Management module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Permit and weighbridge systems are declared BLOCKED — generic transfer/graph rules apply to contract flows.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "environmental",
    "risk_taxonomy": [
        {"code": "EV-CNT", "label": "Large services contract",
         "rules": ["R-001"]},
        {"code": "EV-BURST", "label": "Tipping burst velocity",
         "rules": ["R-002"]},
        {"code": "EV-RING", "label": "Linked haulier ring",
         "rules": ["R-003", "R-004"]},
        {"code": "EV-SITE", "label": "Shared-site funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "EV-FANIN", "label": "Levy-collection fan-in",
         "rules": ["R-006"]},
        {"code": "EV-FANOUT", "label": "Haulier fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "EV-T1", "label": "Ghost-load billing ring",
         "rules": ["R-003", "R-007"]},
        {"id": "EV-T2", "label": "Site funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "EV-T3", "label": "Large contracts to linked hauliers",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "environment_note": note}
        for rid, note in [
            ("R-001", "Large-contract review queue"),
            ("R-002", "Tipping-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Haulier-link review"),
            ("R-006", "Levy fan-in alert"),
            ("R-007", "Haulier fan-out alert"),
            ("R-008", "Site-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "permit feed",
         "source": "permit-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "weighbridge feed",
         "source": "site-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "EV-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "EV-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "EV-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "EV-C1", "label": "Contract-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
