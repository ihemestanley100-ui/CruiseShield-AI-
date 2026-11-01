# PHASE 15 — INSTITUTIONAL REQUIREMENTS

PROGRAMME: CSAI-MASTER-RELEASE-001 | PHASE: 15 | DATE: 2026-11-01
SCOPE: readiness documentation ONLY. No integrations built, no real data touched, no pilot started. All operational steps need separate owner + institutional + legal approvals.

## Candidate institutional users
| User type | Use case | Notes |
|---|---|---|
| Commercial / microfinance banks | Triage of mobile-money/card alerts; investigator workbench | Highest regulatory bar (CBN direct supervision) |
| Fintechs / PSPs | Real-time transaction screening queues | Needs low-latency API + reconciliation |
| Compliance teams | STR preparation support; audit trail | Read-mostly; strongest fit for current strengths (evidence+provenance+audit) |
| Fraud investigation teams | Link/network analysis across entities | Graph + replay modules map directly |
| Financial intelligence teams | Pattern review, scenario replay | Simulation + AI explanation assist |

## Roles (to be staffed by the institution, not the demo)
- Investigator: works cases, records decisions + rationale (maps to current `actor_id`, self-asserted in demo → must become authenticated identity).
- Compliance officer: reviews/escalates, owns STR decisions (human authority stays here — never the model).
- Administrator: user/role management, configuration, key custody (does not exist yet — D-002).
- Model/risk owner: approves risk-engine versions + AI prompt versions; signs off monitoring (see Model Risk Framework).
- Auditor (read-only): inspects immutable audit history (maps to current audit route + append-only log).

## Operating procedures (minimum viable set for pilot)
1. Alert intake → case opening (authenticated, deduplicated).
2. Evidence review → AI explanation request (grounded, logged with prompt+model version).
3. Human decision with mandatory rationale + second-eyes rule for escalations.
4. Audit review sampling (weekly) + incident escalation path.
5. Model/risk-engine change control (version pin, validation, rollback).

## Current-product gaps vs these requirements (cross-refs, not new findings)
AuthN/authZ + roles (D-002), rate limiting (D-001), multi-user store (D-012), encrypted backup execution (D-008), screen-reader pass (D-003), live red-team (D-005). The pilot MUST NOT start until its gate items (see Controlled Pilot Plan) close.
