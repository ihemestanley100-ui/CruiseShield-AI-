"""Capital Markets & Investment module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Market
microstructure data (order book, quotes) is declared BLOCKED —
generic transfer/graph rules apply to settlement-scale flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "capital-markets",
    "risk_taxonomy": [
        {"code": "CM-WASH", "label": "Wash-pattern velocity bursts",
         "rules": ["R-002"]},
        {"code": "CM-BLOCK", "label": "Large block-size transfer",
         "rules": ["R-001"]},
        {"code": "CM-RING", "label": "Coordinated account ring",
         "rules": ["R-003", "R-004"]},
        {"code": "CM-SETTLE", "label": "Shared-beneficiary settlement",
         "rules": ["R-005", "R-008"]},
        {"code": "CM-CASCADE", "label": "Rapid distribution cascade",
         "rules": ["R-007", "R-002"]},
        {"code": "CM-ACCUM", "label": "Quiet accumulation fan-in",
         "rules": ["R-006", "R-003"]},
    ],
    "threat_scenarios": [
        {"id": "CM-T1", "label": "Coordinated burst across 2+ linked "
         "accounts",
         "rules": ["R-002", "R-003"]},
        {"id": "CM-T2", "label": "Accumulation then rapid "
         "distribution",
         "rules": ["R-006", "R-007"]},
        {"id": "CM-T3", "label": "Repeated large blocks to one "
         "beneficiary",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "capital_note": note}
        for rid, note in [
            ("R-001", "Block-trade review queue"),
            ("R-002", "Burst-velocity review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Settlement-link review"),
            ("R-006", "Accumulation fan-in alert"),
            ("R-007", "Distribution fan-out alert"),
            ("R-008", "Venue-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "order-book/market-data feed",
         "source": "market-data connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "beneficial-ownership registry",
         "source": "registry connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "CM-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "CM-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "CM-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "CM-C1", "label": "Trade-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
