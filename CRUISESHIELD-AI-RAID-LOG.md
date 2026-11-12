# CRUISESHIELD-AI-RAID-LOG.md

Risks, Assumptions, Issues, Dependencies. Severity: CRITICAL /
HIGH / MEDIUM / LOW. Status: OPEN / MITIGATED / CLOSED / BLOCKED.

## Risks

### RSK-001 — Uncapped bandwidth overage with card on file
- Severity HIGH. Likelihood MEDIUM. Status OPEN. Owner: owner.
- Detail: $0.30/GB overage documented; no verified hard cap.
  Current usage ~0, but a traffic spike bills without approval.
- Mitigation: keep free-tier usage minimal; pursue dashboard
  spend evidence (R11/R12 readouts); no mitigation in code can
  cap provider billing.
- Due: before any public launch.

### RSK-002 — Single-tenant data model
- Severity HIGH. Likelihood HIGH if multi-org attempted.
  Status OPEN. Owner: owner (D-014).
- Detail: dev tenant boundary is implemented (core, key APIs,
  connector/governance/agent surfaces) with adversarial tests,
  but the D-014 user→tenant map is pending, so all current
  users resolve to the default tenant. A second live org would
  still share records.
- Mitigation: single-org operation only until D-014 decided and
  mapped. Due: before any second tenant.

### RSK-003 — Backup never operated
- Severity MEDIUM. Status OPEN. Owner: owner (D-018).
- Detail: 94 backup tests pass locally; ceremony keys and live
  drill outstanding (GAP-003).
- Mitigation: run authorized drill; record evidence.
- Due: with first production data.

### RSK-004 — PostCSS transitive advisories deferred
- Severity LOW. Status MITIGATED (accepted). Owner: agent.
- Detail: 2 npm advisories need breaking next@16 upgrade;
  build-stage only, no runtime secret path.
- Mitigation: revisit at Next major upgrade; recorded risk.

### RSK-005 — Live runs older commit than branch
- Severity MEDIUM. Status OPEN. Owner: owner (D-017).
- Detail: live backend = ff7052b; branch adds unreleased
  foundations + Batch 1.1. Live proof gates shut until deploy.
- Mitigation: release manifest + authorized push/deploy.

### RSK-006 — Public frontend URL serves Netlify 404
- Severity MEDIUM. Status OPEN. Owner: owner (deploy approval).
- Detail: static `.next` deploy, 0 functions, adapter missing.
- Mitigation: D-009 adapter fix + authorized redeploy.

### RSK-007 — No software license
- Severity LOW. Status OPEN. Owner: owner (D-015).
- Detail: public repo without license = unclear reuse rights.

## Assumptions

| ID | Assumption | Risk if wrong | Status |
|---|---|---|---|
| ASM-001 | Synthetic data only; no real PII or funds | Legal/data breach | OPEN — enforced by seed-only design |
| ASM-002 | CI installs locked deps | Phantom green/drift | OPEN — pip-audit timed out; lock-match FAIL on shared interpreter |
| ASM-003 | Win sandbox failures (node EPERM, socket denial) absent on Linux CI | CI red | OPEN — needs hosted run |
| ASM-004 | Free tiers suffice for demo scale | Forced paid tier | OPEN — usage near zero so far |

## Issues

| ID | Issue | Severity | Status |
|---|---|---|---|
| ISS-001 | Netlify live 404 (no OpenNext adapter) | MEDIUM | OPEN |
| ISS-002 | Backend suite: 1 failed + 2 errors on Win sandbox (proven environmental) | LOW | OPEN — needs Linux CI confirm |
| ISS-003 | 162 uncommitted entries; no release manifest yet | MEDIUM | OPEN |

## Dependencies

| ID | Dependency | Type | Status |
|---|---|---|---|
| DEP-001 | Owner: Meta key + live-call approval | External | BLOCKED (GAP-014) |
| DEP-002 | Owner: tenancy scope (D-014) | Decision | BLOCKED |
| DEP-003 | Owner: license choice (D-015) | Decision | BLOCKED |
| DEP-004 | Owner: push/deploy approvals (D-017) | Approval | BLOCKED |
| DEP-005 | Owner: Render dashboard readouts R1/R2/R11/R12 | Evidence | BLOCKED |
| DEP-006 | Owner: backup keys/ceremony (D-018) | Approval | BLOCKED |
| DEP-007 | Hosted Linux CI run for green proof | External | BLOCKED (needs DEP-004) |
