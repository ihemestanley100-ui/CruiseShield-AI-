"""Media, Advertising & Entertainment module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Campaign and royalty systems are declared BLOCKED — generic transfer/graph rules apply to spend-scale flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "media",
    "risk_taxonomy": [
        {"code": "MD-SPN", "label": "Large campaign spend",
         "rules": ["R-001"]},
        {"code": "MD-BURST", "label": "Placement burst velocity",
         "rules": ["R-002"]},
        {"code": "MD-RING", "label": "Linked agency ring",
         "rules": ["R-003", "R-004"]},
        {"code": "MD-NETW", "label": "Shared-network funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "MD-FANIN", "label": "Advertiser-spend fan-in",
         "rules": ["R-006"]},
        {"code": "MD-FANOUT", "label": "Publisher fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "MD-T1", "label": "Rebate-kickback ring",
         "rules": ["R-003", "R-007"]},
        {"id": "MD-T2", "label": "Inventory-fraud funnel",
         "rules": ["R-008", "R-002"]},
        {"id": "MD-T3", "label": "Large spends to linked publishers",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "media_note": note}
        for rid, note in [
            ("R-001", "Large-spend review queue"),
            ("R-002", "Placement-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Agency-link review"),
            ("R-006", "Spend fan-in alert"),
            ("R-007", "Publisher fan-out alert"),
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
        {"field": "campaign feed",
         "source": "ad-server connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "royalty feed",
         "source": "rights-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "MD-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "MD-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "MD-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "MD-C1", "label": "Spend-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
