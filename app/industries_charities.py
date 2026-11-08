"""Charities & Foundations module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Donation and endowment systems are declared BLOCKED — generic transfer/graph rules apply to grant flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "charities",
    "risk_taxonomy": [
        {"code": "CH-GRT", "label": "Large charitable grant",
         "rules": ["R-001"]},
        {"code": "CH-BURST", "label": "Appeal burst velocity",
         "rules": ["R-002"]},
        {"code": "CH-RING", "label": "Linked trustee ring",
         "rules": ["R-003", "R-004"]},
        {"code": "CH-FUND", "label": "Shared-fund funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "CH-FANIN", "label": "Donation fan-in",
         "rules": ["R-006"]},
        {"code": "CH-FANOUT", "label": "Grant fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "CH-T1", "label": "Round-tripped donations via linked parties",
         "rules": ["R-006", "R-007"]},
        {"id": "CH-T2", "label": "Fund funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "CH-T3", "label": "Large grants to linked entities",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "charities_note": note}
        for rid, note in [
            ("R-001", "Large-grant review queue"),
            ("R-002", "Appeal-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Trustee-link review"),
            ("R-006", "Donation fan-in alert"),
            ("R-007", "Grant fan-out alert"),
            ("R-008", "Fund-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "donation feed",
         "source": "crm-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "endowment feed",
         "source": "finance-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "CH-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "CH-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "CH-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "CH-C1", "label": "Grant-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
