"""Mining & Natural Resources module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Assay and offtake systems are declared BLOCKED — generic transfer/graph rules apply to royalty-scale flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "mining-resources",
    "risk_taxonomy": [
        {"code": "MI-ROY", "label": "Large royalty payment",
         "rules": ["R-001"]},
        {"code": "MI-BURST", "label": "Shipment burst velocity",
         "rules": ["R-002"]},
        {"code": "MI-RING", "label": "Linked offtaker ring",
         "rules": ["R-003", "R-004"]},
        {"code": "MI-MINE", "label": "Shared-mine payment funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "MI-FANIN", "label": "Offtake-proceed fan-in",
         "rules": ["R-006"]},
        {"code": "MI-FANOUT", "label": "Contractor fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "MI-T1", "label": "Under-reported offtake via linked buyers",
         "rules": ["R-003", "R-006"]},
        {"id": "MI-T2", "label": "Mine funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "MI-T3", "label": "Large royalties to linked entities",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "mining_note": note}
        for rid, note in [
            ("R-001", "Large-royalty review queue"),
            ("R-002", "Shipment-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Offtaker-link review"),
            ("R-006", "Proceeds fan-in alert"),
            ("R-007", "Contractor fan-out alert"),
            ("R-008", "Mine-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "assay feed",
         "source": "lab-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "offtake feed",
         "source": "offtake-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "MI-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "MI-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "MI-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "MI-C1", "label": "Royalty-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
