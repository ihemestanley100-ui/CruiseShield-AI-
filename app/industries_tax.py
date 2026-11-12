"""Tax & Revenue Authorities module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Filing
and assessment systems are declared BLOCKED — generic
transfer/graph rules apply to revenue-scale flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "tax-revenue",
    "risk_taxonomy": [
        {"code": "TX-BURST", "label": "Refund/payout burst velocity",
         "rules": ["R-002"]},
        {"code": "TX-LARGE", "label": "Large single refund",
         "rules": ["R-001"]},
        {"code": "TX-RING", "label": "Shared device/phone filer ring",
         "rules": ["R-003", "R-004"]},
        {"code": "TX-AGENT", "label": "Shared-agent filing funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "TX-FANOUT", "label": "Rapid refund fan-out",
         "rules": ["R-007", "R-002"]},
        {"code": "TX-FANIN", "label": "Revenue collection fan-in",
         "rules": ["R-006", "R-003"]},
    ],
    "threat_scenarios": [
        {"id": "TX-T1", "label": "Ring-filed refunds to linked "
         "beneficiaries",
         "rules": ["R-003", "R-002", "R-005"]},
        {"id": "TX-T2", "label": "Agent funnel concentrating refunds "
         "to one network",
         "rules": ["R-008", "R-005"]},
        {"id": "TX-T3", "label": "Collection then rapid refund "
         "distribution",
         "rules": ["R-006", "R-007"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "tax_note": note}
        for rid, note in [
            ("R-001", "Large-refund review queue"),
            ("R-002", "Refund-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Beneficiary-link review"),
            ("R-006", "Revenue fan-in alert"),
            ("R-007", "Refund fan-out alert"),
            ("R-008", "Agent-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "filing-system feed",
         "source": "tax-filing connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "assessment/ledger feed",
         "source": "revenue-ledger connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "TX-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "TX-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "TX-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "TX-C1", "label": "Refund-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
