# CS-ERD-001 Technical Findings Matrix (living — updated per unit)

Scope: Stage 1 remediation D-1/A-1/C-1/E-1. No finding is PASS
without executable evidence on a named SHA. O-05 stays OPEN and is
not a development blocker; it remains a release gate.

## D-1 — Cryptographic audit-chain integrity (IMPLEMENTED, focused green)

- Severity: High. Baseline: `app/store.py:58` hardcoded
  `audit_chain_key = None`; zero tamper detection active.
- Correction: env-sourced `AUDIT_CHAIN_KEY*` (32-byte minimum,
  hex/base64/raw), key ids + previous-epoch rotation, Store
  arming before seed, fail-closed construction on invalid
  config, `audit_chain_verified` health check (counts/codes
  only, exempt until A-1), legacy entries counted never
  retro-sealed.
- Tests: `tests/test_audit_arming.py` 16/16 (predicates,
  rotation, arming, tamper, legacy, leak, health surfacing).
- Interim risk (carried to A-1): a verification FAIL is
  visible in checks but does not yet flip `status`.
- Evidence: `UNIT_D1_EVIDENCE.md`. Full-regression proof
  lands in the final battery.

## A-1 — Truthful system health (OPEN)

- Severity: Medium. `health()` exempts AI/audit/PG yet
  returns `healthy`; frontend prints "All systems
  operational" on any `healthy`.
- Correction (specified): qualified backend statuses
  (`healthy` / `operational_with_gaps` / `degraded` /
  `unavailable`) + headline logic both sides.

## C-1 — Storage reliability (OPEN)

- Severity: Medium. JSON bounds uncontracted (tmp+replace
  under a thread lock, no fsync, single-process; missing
  file reseeds with a warning; no exhaustion path).
- Correction (specified): docs-only operations runbook,
  owner-reviewed; no PG, no paid storage.

## E-1 — Detection completeness (OPEN)

- Severity: Low. Seed `txn_84731` uses channel `QR`, which
  classifies UNMAPPED. ML_ANOMALY honestly NOT_IMPLEMENTED
  (must stay so).
- Correction (specified): QR as 9th canonical channel +
  regression tests proving zero seed UNMAPPED.
