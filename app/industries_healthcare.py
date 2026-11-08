"""Healthcare & Hospitals module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Clinical and claims systems are declared BLOCKED — generic transfer/graph rules apply to payout-scale flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "healthcare",
    "risk_taxonomy": [
        {"code": "HC-PAY", "label": "Large provider payout",
         "rules": ["R-001"]},
        {"code": "HC-BURST", "label": "Claim burst velocity",
         "rules": ["R-002"]},
        {"code": "HC-RING", "label": "Shared device/phone claimant ring",
         "rules": ["R-003", "R-004"]},
        {"code": "HC-FAC", "label": "Shared-facility billing funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "HC-FANIN", "label": "Premium/grant fan-in",
         "rules": ["R-006"]},
        {"code": "HC-FANOUT", "label": "Provider fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "HC-T1", "label": "Phantom-billing ring",
         "rules": ["R-003", "R-007"]},
        {"id": "HC-T2", "label": "Facility funnel upcoding burst",
         "rules": ["R-008", "R-002"]},
        {"id": "HC-T3", "label": "Large payouts to linked providers",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "healthcare_note": note}
        for rid, note in [
            ("R-001", "Large-payout review queue"),
            ("R-002", "Claim-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Provider-link review"),
            ("R-006", "Premium fan-in alert"),
            ("R-007", "Provider fan-out alert"),
            ("R-008", "Facility-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "claims feed",
         "source": "claims-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "provider-registry feed",
         "source": "provider-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "HC-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "HC-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "HC-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "HC-C1", "label": "Payout-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
