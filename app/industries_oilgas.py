"""Oil & Gas module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Lifting and terminal systems are declared BLOCKED — generic transfer/graph rules apply to cargo-scale payments only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "oil-gas",
    "risk_taxonomy": [
        {"code": "OG-CGO", "label": "Large cargo payment",
         "rules": ["R-001"]},
        {"code": "OG-BURST", "label": "Lifting burst velocity",
         "rules": ["R-002"]},
        {"code": "OG-RING", "label": "Linked lifter ring",
         "rules": ["R-003", "R-004"]},
        {"code": "OG-TERM", "label": "Shared-terminal funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "OG-FANIN", "label": "Sales-proceed fan-in",
         "rules": ["R-006"]},
        {"code": "OG-FANOUT", "label": "Service-contractor fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "OG-T1", "label": "Diverted liftings via linked lifters",
         "rules": ["R-003", "R-007"]},
        {"id": "OG-T2", "label": "Terminal funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "OG-T3", "label": "Large cargo payments to linked traders",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "oilgas_note": note}
        for rid, note in [
            ("R-001", "Large-cargo review queue"),
            ("R-002", "Lifting-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Lifter-link review"),
            ("R-006", "Proceeds fan-in alert"),
            ("R-007", "Contractor fan-out alert"),
            ("R-008", "Terminal-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "lifting feed",
         "source": "terminal-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "cargo-manifest feed",
         "source": "shipping-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "OG-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "OG-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "OG-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "OG-C1", "label": "Cargo-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
