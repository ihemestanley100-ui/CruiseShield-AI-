"""Hotels & Hospitality module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Property-management and booking systems are declared BLOCKED — generic transfer rules apply to folio flows.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "hospitality",
    "risk_taxonomy": [
        {"code": "HO-FOL", "label": "Large folio settlement",
         "rules": ["R-001"]},
        {"code": "HO-BURST", "label": "Booking burst velocity",
         "rules": ["R-002"]},
        {"code": "HO-RING", "label": "Linked guest/agent ring",
         "rules": ["R-003", "R-004"]},
        {"code": "HO-PROP", "label": "Shared-property funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "HO-FANIN", "label": "Room-revenue fan-in",
         "rules": ["R-006"]},
        {"code": "HO-FANOUT", "label": "Supplier fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "HO-T1", "label": "No-show billing ring",
         "rules": ["R-003", "R-007"]},
        {"id": "HO-T2", "label": "Property funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "HO-T3", "label": "Large events to linked organizers",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "hospitality_note": note}
        for rid, note in [
            ("R-001", "Large-folio review queue"),
            ("R-002", "Booking-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Guest-link review"),
            ("R-006", "Revenue fan-in alert"),
            ("R-007", "Supplier fan-out alert"),
            ("R-008", "Property-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "pms feed",
         "source": "pms-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "booking feed",
         "source": "booking-engine connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "HO-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "HO-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "HO-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "HO-C1", "label": "Folio-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
