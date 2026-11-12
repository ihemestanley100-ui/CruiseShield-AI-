"""Customs & Border Administration module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Declaration and cargo systems are declared BLOCKED — generic transfer/graph rules apply to duty-scale flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "customs-border",
    "risk_taxonomy": [
        {"code": "CU-DUTY", "label": "Large duty-related transfer",
         "rules": ["R-001"]},
        {"code": "CU-BURST", "label": "Declaration burst velocity",
         "rules": ["R-002"]},
        {"code": "CU-RING", "label": "Shared device/phone declarant ring",
         "rules": ["R-003", "R-004"]},
        {"code": "CU-BROKER", "label": "Shared-broker filing funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "CU-FANIN", "label": "Collection fan-in",
         "rules": ["R-006"]},
        {"code": "CU-FANOUT", "label": "Refund/drawback fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "CU-T1", "label": "Ring-filed declarations to one beneficiary",
         "rules": ["R-003", "R-005"]},
        {"id": "CU-T2", "label": "Broker funnel concentrating refunds",
         "rules": ["R-008", "R-007"]},
        {"id": "CU-T3", "label": "Large duty flows via linked accounts",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "customs_note": note}
        for rid, note in [
            ("R-001", "Large-transfer review queue"),
            ("R-002", "Filing-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Beneficiary-link review"),
            ("R-006", "Collection fan-in alert"),
            ("R-007", "Drawback fan-out alert"),
            ("R-008", "Broker-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "declaration feed",
         "source": "customs-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "cargo-manifest feed",
         "source": "port-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "CU-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "CU-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "CU-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "CU-C1", "label": "Declaration-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
