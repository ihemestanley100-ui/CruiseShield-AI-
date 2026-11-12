"""Cryptocurrency & Digital Assets module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). On-chain
data and VASP attribution are declared BLOCKED — generic
transfer/graph rules apply to off-chain-recorded flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "crypto-assets",
    "risk_taxonomy": [
        {"code": "CX-PEEL", "label": "Peel-chain distribution fan-out",
         "rules": ["R-007", "R-002"]},
        {"code": "CX-CONSOL", "label": "Consolidation fan-in",
         "rules": ["R-006"]},
        {"code": "CX-HOP", "label": "Rapid multi-hop velocity",
         "rules": ["R-002"]},
        {"code": "CX-CLUSTER", "label": "Shared-identifier cluster",
         "rules": ["R-003", "R-004"]},
        {"code": "CX-FUNNEL", "label": "Shared-address/service funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "CX-LARGE", "label": "Large single transfer",
         "rules": ["R-001"]},
    ],
    "threat_scenarios": [
        {"id": "CX-T1", "label": "Consolidation then peel-chain "
         "distribution",
         "rules": ["R-006", "R-007"]},
        {"id": "CX-T2", "label": "Rapid hops across linked "
         "addresses",
         "rules": ["R-002"]},
        {"id": "CX-T3", "label": "Cluster cash-out to one "
         "beneficiary",
         "rules": ["R-003", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "crypto_note": note}
        for rid, note in [
            ("R-001", "Large-transfer review queue"),
            ("R-002", "Hop-velocity review queue"),
            ("R-003", "Cluster-ring investigation"),
            ("R-004", "Identifier-ring investigation"),
            ("R-005", "Beneficiary-link review"),
            ("R-006", "Consolidation fan-in alert"),
            ("R-007", "Peel-chain fan-out alert"),
            ("R-008", "Service-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "chain-data connector feed",
         "source": "chain-data connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "VASP attribution feed",
         "source": "attribution provider",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "CX-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "CX-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "CX-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "CX-C1", "label": "Transfer-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
