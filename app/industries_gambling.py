"""Gambling & Casinos module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Wagering and cage systems are declared BLOCKED — generic transfer/graph rules apply to redemption flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "gambling",
    "risk_taxonomy": [
        {"code": "GB-RED", "label": "Large chip redemption",
         "rules": ["R-001"]},
        {"code": "GB-BURST", "label": "Buy-in burst velocity",
         "rules": ["R-002"]},
        {"code": "GB-RING", "label": "Shared device/player ring",
         "rules": ["R-003", "R-004"]},
        {"code": "GB-PIT", "label": "Shared-pit funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "GB-FANIN", "label": "Buy-in fan-in",
         "rules": ["R-006"]},
        {"code": "GB-FANOUT", "label": "Payout fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "GB-T1", "label": "Chip-dumping ring cashing out",
         "rules": ["R-003", "R-007"]},
        {"id": "GB-T2", "label": "Junket funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "GB-T3", "label": "Large redemptions by linked players",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "gambling_note": note}
        for rid, note in [
            ("R-001", "Large-redemption review queue"),
            ("R-002", "Buy-in burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Player-ring investigation"),
            ("R-005", "Player-link review"),
            ("R-006", "Buy-in fan-in alert"),
            ("R-007", "Payout fan-out alert"),
            ("R-008", "Pit-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "wagering feed",
         "source": "casino-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "cage-ledger feed",
         "source": "cage-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "GB-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "GB-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "GB-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "GB-C1", "label": "Redemption-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
