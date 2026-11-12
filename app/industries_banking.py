"""Banking industry pilot (Level 14 §6): first TESTING module.

Every detection rule maps to a real versioned engine rule
(app/rules.py R-001..R-008 IDs are asserted, not assumed); every
workflow step maps to a real API route (asserted against the live
app). Data gaps (KYC, sanctions feeds) are declared BLOCKED
external dependencies, not silently filled. Compliance entries are
configuration placeholders — no certification is claimed.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "banking",
    "risk_taxonomy": [
        {"code": "BNK-VEL", "label": "Rapid successive transfers",
         "rules": ["R-002"]},
        {"code": "BNK-AMT", "label": "Large single transfer",
         "rules": ["R-001"]},
        {"code": "BNK-MULE", "label": "Mule fan-in collection",
         "rules": ["R-006", "R-003"]},
        {"code": "BNK-RING", "label": "Shared-device/phone ring",
         "rules": ["R-003", "R-004"]},
        {"code": "BNK-CASHOUT", "label": "Rapid fan-out cash-out",
         "rules": ["R-007", "R-002"]},
        {"code": "BNK-MERCH", "label": "Shared-merchant funnel",
         "rules": ["R-008", "R-005"]},
    ],
    "threat_scenarios": [
        {"id": "BNK-T1", "label": "Mule account receives from 3+ "
         "senders then cashes out",
         "rules": ["R-006", "R-007", "R-002"]},
        {"id": "BNK-T2", "label": "One device operates 2+ accounts "
         "feeding one beneficiary",
         "rules": ["R-003", "R-005"]},
        {"id": "BNK-T3", "label": "Burst of transfers above the "
         "large-transfer threshold",
         "rules": ["R-001", "R-002"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "banking_note": note}
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
        {"field": "KYC identity records", "source": "bank connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "sanctions/watchlist feed", "source": "provider feed",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "BNK-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "BNK-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "BNK-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "BNK-C1", "label": "Suspicious-activity review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
