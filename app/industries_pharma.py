"""Pharmaceuticals & Biotechnology module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Trial and distribution systems are declared BLOCKED — generic transfer/graph rules apply to payment flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "pharma-biotech",
    "risk_taxonomy": [
        {"code": "PH-GRT", "label": "Large grant/trial payment",
         "rules": ["R-001"]},
        {"code": "PH-BURST", "label": "Site-payment burst velocity",
         "rules": ["R-002"]},
        {"code": "PH-RING", "label": "Linked site ring",
         "rules": ["R-003", "R-004"]},
        {"code": "PH-CRO", "label": "Shared-CRO payment funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "PH-FANIN", "label": "Funding fan-in",
         "rules": ["R-006"]},
        {"code": "PH-FANOUT", "label": "Site fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "PH-T1", "label": "Ghost-site payments within a ring",
         "rules": ["R-003", "R-007"]},
        {"id": "PH-T2", "label": "CRO funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "PH-T3", "label": "Large grants to linked entities",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "pharma_note": note}
        for rid, note in [
            ("R-001", "Large-grant review queue"),
            ("R-002", "Site-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Site-link review"),
            ("R-006", "Funding fan-in alert"),
            ("R-007", "Site fan-out alert"),
            ("R-008", "CRO-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "trial feed",
         "source": "ctms-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "distribution feed",
         "source": "distributor-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "PH-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "PH-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "PH-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "PH-C1", "label": "Grant-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
