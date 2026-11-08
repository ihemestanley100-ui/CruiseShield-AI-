"""Gaming & Esports module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). In-game economy systems are declared BLOCKED — generic transfer/graph rules apply to cash-out flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "gaming-esports",
    "risk_taxonomy": [
        {"code": "GM-OUT", "label": "Large cash-out",
         "rules": ["R-001"]},
        {"code": "GM-BURST", "label": "Tournament burst velocity",
         "rules": ["R-002"]},
        {"code": "GM-RING", "label": "Shared device/player ring",
         "rules": ["R-003", "R-004"]},
        {"code": "GM-TITLE", "label": "Shared-title funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "GM-FANIN", "label": "Entry-fee fan-in",
         "rules": ["R-006"]},
        {"code": "GM-FANOUT", "label": "Prize fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "GM-T1", "label": "Match-fixing payout ring",
         "rules": ["R-003", "R-007"]},
        {"id": "GM-T2", "label": "Gold-farming funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "GM-T3", "label": "Large prizes to linked players",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "gaming_note": note}
        for rid, note in [
            ("R-001", "Large-cashout review queue"),
            ("R-002", "Tournament-burst queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Player-ring investigation"),
            ("R-005", "Player-link review"),
            ("R-006", "Entry-fee fan-in alert"),
            ("R-007", "Prize fan-out alert"),
            ("R-008", "Title-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "game-economy feed",
         "source": "game-server connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "tournament feed",
         "source": "tournament-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "GM-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "GM-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "GM-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "GM-C1", "label": "Cashout-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
