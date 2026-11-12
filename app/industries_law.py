"""Law Enforcement & Financial Intelligence module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Case-management and watchlist systems are declared BLOCKED; evidentiary handling controls are NOT claimed here.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "law-enforcement",
    "risk_taxonomy": [
        {"code": "LE-INTEL", "label": "Large intelligence-linked fund move",
         "rules": ["R-001"]},
        {"code": "LE-BURST", "label": "Burst transfer velocity",
         "rules": ["R-002"]},
        {"code": "LE-RING", "label": "Shared device/phone subject ring",
         "rules": ["R-003", "R-004"]},
        {"code": "LE-NET", "label": "Shared-beneficiary network",
         "rules": ["R-005", "R-008"]},
        {"code": "LE-FANIN", "label": "Consolidation fan-in",
         "rules": ["R-006"]},
        {"code": "LE-FANOUT", "label": "Distribution fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "LE-T1", "label": "Ring consolidation to one account",
         "rules": ["R-003", "R-006"]},
        {"id": "LE-T2", "label": "Burst distribution after funding",
         "rules": ["R-002", "R-007"]},
        {"id": "LE-T3", "label": "Large moves to linked beneficiaries",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "law_note": note}
        for rid, note in [
            ("R-001", "Large-move review queue"),
            ("R-002", "Burst-velocity review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Beneficiary-link review"),
            ("R-006", "Consolidation fan-in alert"),
            ("R-007", "Distribution fan-out alert"),
            ("R-008", "Network-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "case-management feed",
         "source": "records-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "watchlist feed",
         "source": "sanctions-list provider",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "LE-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "LE-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "LE-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "LE-C1", "label": "Intelligence-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
