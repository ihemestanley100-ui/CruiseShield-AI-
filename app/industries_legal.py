"""Legal Services module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Matter and trust-account systems are declared BLOCKED — generic transfer/graph rules apply to escrow flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "legal",
    "risk_taxonomy": [
        {"code": "LG-ESC", "label": "Large escrow movement",
         "rules": ["R-001"]},
        {"code": "LG-BURST", "label": "Matter burst velocity",
         "rules": ["R-002"]},
        {"code": "LG-RING", "label": "Linked client ring",
         "rules": ["R-003", "R-004"]},
        {"code": "LG-FIRM", "label": "Shared-firm escrow funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "LG-FANIN", "label": "Client-funds fan-in",
         "rules": ["R-006"]},
        {"code": "LG-FANOUT", "label": "Settlement fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "LG-T1", "label": "Pass-through escrow ring",
         "rules": ["R-003", "R-007"]},
        {"id": "LG-T2", "label": "Firm funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "LG-T3", "label": "Large settlements to linked parties",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "legal_note": note}
        for rid, note in [
            ("R-001", "Large-escrow review queue"),
            ("R-002", "Matter-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Client-link review"),
            ("R-006", "Client-funds fan-in alert"),
            ("R-007", "Settlement fan-out alert"),
            ("R-008", "Firm-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "matter feed",
         "source": "pms-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "trust-ledger feed",
         "source": "accounts-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "LG-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "LG-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "LG-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "LG-C1", "label": "Escrow-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
