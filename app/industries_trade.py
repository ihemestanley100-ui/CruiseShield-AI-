"""Import & Export Businesses module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Trade-document and shipping systems are declared BLOCKED — generic transfer/graph rules apply to trade payments.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "import-export",
    "risk_taxonomy": [
        {"code": "IE-TRD", "label": "Large trade payment",
         "rules": ["R-001"]},
        {"code": "IE-BURST", "label": "Invoice burst velocity",
         "rules": ["R-002"]},
        {"code": "IE-RING", "label": "Linked trader ring",
         "rules": ["R-003", "R-004"]},
        {"code": "IE-CORR", "label": "Shared-corridor funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "IE-FANIN", "label": "Export-proceed fan-in",
         "rules": ["R-006"]},
        {"code": "IE-FANOUT", "label": "Import-payment fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "IE-T1", "label": "Over/under-invoicing ring",
         "rules": ["R-003", "R-001"]},
        {"id": "IE-T2", "label": "Corridor funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "IE-T3", "label": "Round-tripping proceeds via linked traders",
         "rules": ["R-006", "R-007"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "trade_note": note}
        for rid, note in [
            ("R-001", "Large-trade review queue"),
            ("R-002", "Invoice-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Trader-link review"),
            ("R-006", "Proceeds fan-in alert"),
            ("R-007", "Import fan-out alert"),
            ("R-008", "Corridor-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "trade-document feed",
         "source": "trade-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "shipping feed",
         "source": "shipping-line connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "IE-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "IE-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "IE-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "IE-C1", "label": "Trade-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
