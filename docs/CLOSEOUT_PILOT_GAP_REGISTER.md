# CLOSEOUT — STAGED PILOT-READINESS GAP REGISTER

PROGRAMME: CSAI-MASTER-RELEASE-001 CLOSEOUT | DATE: 2026-11-01
METHOD: the 8 Phase 15 docs reconciled against the current implementation (code greps + test/evidence review 2026-11-01). Planning documents ≠ operational capabilities — separated below.

## Verified present (carry into pilot as strengths)
- Deterministic risk engine + golden-case invariants (35/MOD, 84/HIGH) with regression tests.
- Evidence grounding + advisory-only AI boundaries (validators tested; 7 live runs demonstrated).
- Human-decision + audit chain (browser write now verified end-to-end, L2).
- Input caps, locked saves, secret hygiene, dependency gate PASS, licence scan (only psycopg LGPL note).
- Atomic writes, restart/restore drills, demo runbooks.

## Gaps by pilot stage
| Stage | Gap | Evidence of absence | Closes |
|---|---|---|---|
| STAGE 0 — Security baseline | G-P1 authN/authZ + roles | No auth code (grep 11-01) | Build + test |
| STAGE 0 | G-P2 edge rate limiting + body limits | No limiter (grep 11-01) | Build + test |
| STAGE 0 | G-P3 backup executed + restore tested (prod-grade) | Plan ready, unexecuted (D-008) | Owner approval + run |
| STAGE 1 — Governance | G-P4 DPIA + signed data agreements | Framework only; LQ-01…04/08 open | Institution + counsel |
| STAGE 1 | G-P5 independent validation on pilot-like data | Not performed | Third party |
| STAGE 1 | G-P6 screen-reader pass or scope exclusion | D-003, no AT | AT run or waiver |
| STAGE 1 | G-P7 live AI red-team or AI-off pilot | D-005 NOT_RUN | Approved call or flag-off |
| STAGE 2 — Operations | G-P8 runbook + on-call + dashboards | Documented, not staffed/built | Institution staffing |
| STAGE 2 | Multi-user store (D-012) | Per-process lock only | External store / workers design |
| STAGE 2 | Integration connectors (core/KYC/STR) | Design only | Authorised build |
| STAGE 2 | Monitoring (drift, bias, override rate) | Not built | Build pre-go-live |

## Decision
**INSTITUTIONAL_PILOT_NOT_READY** — plan complete (Phase 15), Stage 0–2 gates all open. No pilot activity may start; no real data; no connections. Re-assess gate-by-gate as each closes with evidence.
