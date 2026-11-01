# 10. PRODUCTION RELEASE GATE MATRIX

DATE: 2026-11-01 | STAGING vs PRODUCTION are different gates. Staging hosts the DEMO (synthetic); production would serve REAL institutions — nothing here approves production.

| Gate | Staging | Production |
|---|---|---|
| Config complete (2 services, order, env) | OPEN (docs 5–7) | OPEN (same docs) |
| Image built + container-smoked | OPEN (184 MB, health/risk 200) | OPEN |
| Suites green (300/68/0 + 234/234 + build) | OPEN | OPEN (re-run at release) |
| Body cap + secure headers | OPEN (live-verified) | OPEN (needs CSP design) |
| AuthN/authZ + roles | WAIVED (demo; URL-secrecy accepted by owner) | CLOSED (D-002; workstream required) |
| Rate limiting | WAIVED (demo) | CLOSED (D-001; workstream required) |
| Live red-team | WAIVED | CLOSED (D-005) |
| Multi-user store | WAIVED (single instance) | CLOSED (D-012; Option B workstream) |
| Backup executed + rollback drilled | CONDITIONAL (D-008 approval) | CLOSED |
| Independent validation + DPIA + agreements | N/A (synthetic) | CLOSED (Phase 15 G-P4/G-P5) |
| Paid plan + domain approval | CONDITIONAL (owner) | CONDITIONAL (owner) |

## Verdicts
- STAGING: READY_FOR_OWNER_APPROVAL — all technical blockers resolved; remaining gates are owner approvals (backup, plan, demo-limits acceptance) + first-deploy unknowns (Render-side build, hosted-origin combo) handled by runbook branches.
- PRODUCTION: NOT_READY (unchanged) — auth, rate limiting, CSP, red-team, Option B store, backup/rollback proof, and institutional gates all outstanding by design.
