"""Automotive & Vehicle Trade module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Registration and dealership systems are declared BLOCKED — generic transfer/graph rules apply to vehicle payments.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "automotive",
    "risk_taxonomy": [
        {"code": "AU-VEH", "label": "Large vehicle payment",
         "rules": ["R-001"]},
        {"code": "AU-BURST", "label": "Title-transfer burst velocity",
         "rules": ["R-002"]},
        {"code": "AU-RING", "label": "Linked dealer ring",
         "rules": ["R-003", "R-004"]},
        {"code": "AU-DLR", "label": "Shared-dealership funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "AU-FANIN", "label": "Floorplan-funding fan-in",
         "rules": ["R-006"]},
        {"code": "AU-FANOUT", "label": "Wholesale fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "AU-T1", "label": "Title-washing within a dealer ring",
         "rules": ["R-003", "R-002"]},
        {"id": "AU-T2", "label": "Dealership funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "AU-T3", "label": "Large fleet payments to linked dealers",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "automotive_note": note}
        for rid, note in [
            ("R-001", "Large-payment review queue"),
            ("R-002", "Title-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Dealer-link review"),
            ("R-006", "Floorplan fan-in alert"),
            ("R-007", "Wholesale fan-out alert"),
            ("R-008", "Dealership-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "registration feed",
         "source": "vehicle-registry connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "dealership feed",
         "source": "dealer-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "AU-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "AU-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "AU-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "AU-C1", "label": "Vehicle-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
