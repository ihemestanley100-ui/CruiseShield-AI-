"""Accounting & Auditing module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Ledger and audit-workpaper systems are declared BLOCKED — generic transfer/graph rules apply to client flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "accounting",
    "risk_taxonomy": [
        {"code": "AC-CLT", "label": "Large client transfer",
         "rules": ["R-001"]},
        {"code": "AC-BURST", "label": "Journal burst velocity",
         "rules": ["R-002"]},
        {"code": "AC-RING", "label": "Linked client ring",
         "rules": ["R-003", "R-004"]},
        {"code": "AC-PRAC", "label": "Shared-practice funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "AC-FANIN", "label": "Fee/receipt fan-in",
         "rules": ["R-006"]},
        {"code": "AC-FANOUT", "label": "Disbursement fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "AC-T1", "label": "Round-tripping via linked clients",
         "rules": ["R-006", "R-007"]},
        {"id": "AC-T2", "label": "Practice funnel to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "AC-T3", "label": "Large transfers to linked clients",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "accounting_note": note}
        for rid, note in [
            ("R-001", "Large-transfer review queue"),
            ("R-002", "Journal-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Client-link review"),
            ("R-006", "Receipt fan-in alert"),
            ("R-007", "Disbursement fan-out alert"),
            ("R-008", "Practice-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "ledger feed",
         "source": "erp-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "workpaper feed",
         "source": "audit-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "AC-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "AC-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "AC-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "AC-C1", "label": "Client-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
