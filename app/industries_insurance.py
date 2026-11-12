"""Insurance & Pensions module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). Claim
line-items and provider registries are declared BLOCKED —
generic transfer/graph rules apply to payout-scale flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "insurance-pensions",
    "risk_taxonomy": [
        {"code": "IN-BURST", "label": "Claim/payout burst velocity",
         "rules": ["R-002"]},
        {"code": "IN-LARGE", "label": "Large single payout",
         "rules": ["R-001"]},
        {"code": "IN-RING", "label": "Shared device/phone claimants",
         "rules": ["R-003", "R-004"]},
        {"code": "IN-PROV", "label": "Shared-provider billing funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "IN-DISB", "label": "Rapid disbursement fan-out",
         "rules": ["R-007", "R-002"]},
        {"code": "IN-PREM", "label": "Premium collection fan-in",
         "rules": ["R-006", "R-003"]},
    ],
    "threat_scenarios": [
        {"id": "IN-T1", "label": "Staged claims from a linked "
         "claimant ring",
         "rules": ["R-003", "R-002"]},
        {"id": "IN-T2", "label": "Provider billing burst across "
         "policies",
         "rules": ["R-008", "R-002"]},
        {"id": "IN-T3", "label": "Large payouts to linked "
         "beneficiaries",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "insurance_note": note}
        for rid, note in [
            ("R-001", "Large-payout review queue"),
            ("R-002", "Claim-burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "Phone-ring investigation"),
            ("R-005", "Beneficiary-link review"),
            ("R-006", "Premium fan-in alert"),
            ("R-007", "Disbursement fan-out alert"),
            ("R-008", "Provider-funnel review"),
        ]
    ],
    "data_requirements": [
        {"field": "transactions", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "accounts", "source": "seed/connector",
         "status": "AVAILABLE"},
        {"field": "devices/phones/merchants/beneficiaries",
         "source": "seed/connector", "status": "AVAILABLE"},
        {"field": "claim line-item feed",
         "source": "claims-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "provider registry feed",
         "source": "provider-registry connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "IN-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "IN-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "IN-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "IN-C1", "label": "Claim-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
