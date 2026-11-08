"""Telecommunications module (Level 14 §6): TESTING candidate.

Same honesty contract as the banking pilot: every mapped rule is a
real versioned engine rule (R-001..R-008 asserted); every workflow
step is a real API route (asserted against the live app). CDR and airtime systems are declared BLOCKED — generic transfer/graph rules apply to settlement flows only.
Compliance entries are configuration placeholders.
"""
from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "id": "telecom",
    "risk_taxonomy": [
        {"code": "TL-STL", "label": "Large interconnect settlement",
         "rules": ["R-001"]},
        {"code": "TL-BURST", "label": "Top-up burst velocity",
         "rules": ["R-002"]},
        {"code": "TL-RING", "label": "Shared device/SIM ring",
         "rules": ["R-003", "R-004"]},
        {"code": "TL-AGENT", "label": "Shared-agent float funnel",
         "rules": ["R-008", "R-005"]},
        {"code": "TL-FANIN", "label": "Airtime-revenue fan-in",
         "rules": ["R-006"]},
        {"code": "TL-FANOUT", "label": "Dealer-commission fan-out",
         "rules": ["R-007"]},
    ],
    "threat_scenarios": [
        {"id": "TL-T1", "label": "SIM-box float cycling ring",
         "rules": ["R-003", "R-002"]},
        {"id": "TL-T2", "label": "Agent funnel to one network",
         "rules": ["R-008", "R-007"]},
        {"id": "TL-T3", "label": "Large settlements to linked dealers",
         "rules": ["R-001", "R-005"]},
    ],
    "detection_rules": [
        {"rule_id": rid, "engine": "risk-score-v1",
         "telecom_note": note}
        for rid, note in [
            ("R-001", "Large-settlement review queue"),
            ("R-002", "Top-up burst review queue"),
            ("R-003", "Device-ring investigation"),
            ("R-004", "SIM-ring investigation"),
            ("R-005", "Dealer-link review"),
            ("R-006", "Revenue fan-in alert"),
            ("R-007", "Commission fan-out alert"),
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
        {"field": "CDR feed",
         "source": "mediation-system connector",
         "status": "BLOCKED_EXTERNAL"},
        {"field": "airtime-ledger feed",
         "source": "in-system connector",
         "status": "BLOCKED_EXTERNAL"},
    ],
    "workflows": [
        {"id": "TL-W1", "label": "Alert triage to case decision",
         "steps": [
             "GET /api/v1/alerts",
             "GET /api/v1/cases/{case_id}",
             "POST /api/v1/cases/{case_id}/decisions",
             "GET /api/v1/cases/{case_id}/audit",
         ]},
    ],
    "reports": [
        {"id": "TL-R1", "label": "Alert queue by severity",
         "source": "GET /api/v1/alerts"},
        {"id": "TL-R2", "label": "Case audit trail",
         "source": "GET /api/v1/cases/{case_id}/audit"},
    ],
    "permissions": {
        "triage": ["investigator", "admin"],
        "decide": ["investigator", "admin"],
        "audit_read": ["investigator", "admin", "auditor"],
    },
    "compliance": [
        {"id": "TL-C1", "label": "Settlement-review trail",
         "mechanism": "case.decision audit events",
         "certification": "NOT_CLAIMED"},
    ],
}
