"""Fintech & Digital Payments pilot (Level 14 §6): second module.

Same honest contract as banking: rule IDs asserted against the
engine, workflow steps asserted against live routes, missing feeds
declared BLOCKED_EXTERNAL, no certification claimed.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "fintech-payments",
    "risk_taxonomy": [
        {"code": "FNP-VEL", "label": "Wallet burst transfers",
         "rules": ["R-002"]},
        {"code": "FNP-P2P", "label": "P2P fan-out cash-out",
         "rules": ["R-007", "R-002"]},
        {"code": "FNP-FUNNEL", "label": "Shared-merchant funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "FNP-RING", "label": "Shared-device/phone ring",
         "rules": ["R-003", "R-004"]},
        {"code": "FNP-MULE", "label": "Mule fan-in collection",
         "rules": ["R-006", "R-003"]},
        {"code": "FNP-AMT", "label": "Large single transfer",
         "rules": ["R-001"]},
    ],
    "threat_scenarios": [
        {"id": "FNP-T1", "label": "New wallet fans out to 2+ "
         "receivers within minutes",
         "rules": ["R-007", "R-002"]},
        {"id": "FNP-T2", "label": "One device rotates 2+ wallets "
         "into one merchant",
         "rules": ["R-003", "R-008"]},
        {"id": "FNP-T3", "label": "Burst above the large-transfer "
         "threshold across wallets",
         "rules": ["R-001", "R-002"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "fintech_note": note}
        for rid, note in [
            ("R-001", "Large-transfer review queue"),
            ("R-002", "Velocity review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Beneficiary-link review"),
            ("R-006", "Mule fan-in alert"),
            ("R-007", "Cash-out fan-out alert"),
            ("R-008", "Merchant-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "wallet-ledger records", "source": "fintech connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "KYC identity records", "source": "fintech connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "FNP-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "FNP-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "FNP-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "FNP-C1", "label": "Suspicious-activity review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
