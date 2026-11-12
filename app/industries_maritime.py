"""Maritime & Shipping module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Voyage and port systems are declared BLOCKED — generic transfer/graph rules apply to freight payments only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "maritime",
    "risk_taxonomy": [
        {"code": "MA-FRT", "label": "Large freight payment",
         "rules": ["R-001"]},
        {"code": "MA-BURST", "label": "Fixture burst velocity",
         "rules": ["R-002"]},
        {"code": "MA-RING", "label": "Linked charterer ring",
         "rules": ["R-003", "R-004"]},
        {"code": "MA-PORT", "label": "Shared-port funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "MA-FANIN", "label": "Freight-revenue fan-in",
         "rules": ["R-006"]},
        {"code": "MA-FANOUT", "label": "Owner/agent fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "MA-T1", "label": "Phantom-voyage billing ring",
         "rules": ["R-003", "R-007"]},
        {"id": "MA-T2", "label": "Port funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "MA-T3", "label": "Large freight to linked owners",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "maritime_note": note}
        for rid, note in [
            ("R-001", "Large-freight review queue"),
            ("R-002", "Fixture-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Charterer-link review"),
            ("R-006", "Revenue fan-in alert"),
            ("R-007", "Owner fan-out alert"),
            ("R-008", "Port-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "voyage feed",
         "source": "vms-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "port feed",
         "source": "port-community connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "MA-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "MA-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "MA-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "MA-C1", "label": "Freight-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
