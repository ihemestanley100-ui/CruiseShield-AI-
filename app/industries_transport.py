"""Transportation & Mobility module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Fleet and ticketing systems are declared BLOCKED — generic transfer/graph rules apply to fare-scale flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "transport",
    "risk_taxonomy": [
        {"code": "TR-FAR", "label": "Large fleet payment",
         "rules": ["R-001"]},
        {"code": "TR-BURST", "label": "Trip burst velocity",
         "rules": ["R-002"]},
        {"code": "TR-RING", "label": "Shared device/driver ring",
         "rules": ["R-003", "R-004"]},
        {"code": "TR-DEPOT", "label": "Shared-depot funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "TR-FANIN", "label": "Fare-collection fan-in",
         "rules": ["R-006"]},
        {"code": "TR-FANOUT", "label": "Operator fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "TR-T1", "label": "Ghost-trip incentive ring",
         "rules": ["R-003", "R-007"]},
        {"id": "TR-T2", "label": "Depot funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "TR-T3", "label": "Large fleet deals to linked operators",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "transport_note": note}
        for rid, note in [
            ("R-001", "Large-fleet review queue"),
            ("R-002", "Trip-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Driver-ring investigation"),
            ("R-005", "Operator-link review"),
            ("R-006", "Fare fan-in alert"),
            ("R-007", "Operator fan-out alert"),
            ("R-008", "Depot-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "fleet feed",
         "source": "fleet-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "ticketing feed",
         "source": "ticketing-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "TR-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "TR-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "TR-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "TR-C1", "label": "Fare-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
