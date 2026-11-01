# PHASE 15 — OPERATIONAL GOVERNANCE

## Responsibilities (RACI summary; institution staffs all roles)
| Decision | Investigator | Compliance officer | Admin | Model/risk owner | Auditor |
|---|---|---|---|---|---|
| Case decisions + rationale | R/A | I (escalations: A) | — | — | I |
| STR filing judgment | C | R/A | — | — | I |
| User/role changes | — | I | R/A | — | I |
| Risk-engine / prompt version release | C | I | C | R/A | I |
| Incident declaration | C | R | C | C | I |
| Audit sampling review | I | R/A | — | C | R |

## Standing policies
- Human decision authority: no AI output, however confident, constitutes a finding without a named human decision + rationale. Enforced in product (`requires_human_approval`) and in procedure (unsigned AI text is inadmissible in the case file).
- Escalation: investigator → compliance officer → MLRO/board committee, with clocks (define per institution; default propose 24h/72h).
- Appeals/review: subjects' complaints route via the institution's existing process; system records support but do not decide.
- Change management: risk-engine + prompt + threshold changes are versioned releases (pin, validate on golden cases incl. txn 35/MOD + net 84/HIGH invariants, canary, rollback plan). No Friday releases.
- SLOs (pilot proposal): API p95 < 500 ms (excl. model calls); UI interactive < 2 s; AI explanation p95 < 60 s with honest timeout states; availability 99.5% business-hours; RPO ≤ 1 h, RTO ≤ 4 h (backup execution D-008 is a precondition).
- Business continuity / DR: encrypted backups (tested restores quarterly — current drill pattern promoted), runbook + on-call rotation, annual tabletop exercise.

## Audit review
Weekly sampling of decisions + AI explanations (grounding spot-checks), monthly access review, quarterly control self-assessment. Findings feed the defect register (D-series continues).
