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
- Interim risk CLOSED by A-1: verification FAIL now
  degrades the headline (proven by tamper/misconfigured
  tests).
- Evidence: `UNIT_D1_EVIDENCE.md`. Full-regression proof
  lands in the final battery.

## A-1 — Truthful system health (IMPLEMENTED, backend green)

- Severity: Medium. `health()` exempted AI/audit/PG yet
  returned `healthy`; frontend printed "All systems
  operational" on any `healthy`.
- Correction: `_qualified_status()` backend (unavailable
  / degraded / operational_with_gaps / healthy) +
  status-keyed frontend headlines (allOk / gapsOk / none).
- Tests: `tests/test_health_qualified.py` 6/6 backend;
  frontend tests authored, execution pending hosted CI
  (sandbox node EPERM; static verification recorded).
- Evidence: `UNIT_A1_EVIDENCE.md`. Full-regression proof
  lands in the final battery.

## C-1 — Storage reliability (IMPLEMENTED, docs-only)

- Severity: Medium. JSON bounds were uncontracted.
- Correction: `docs/JSON_STORAGE_OPERATIONS_RUNBOOK.md`
  (atomicity, concurrency, recovery, integrity, backup/
  export/restore, exhaustion, $0 notes, PG criteria).
  Owner review pending; O-05 approval NOT claimed.
- Executable proof: backup drill exit 0 + parity true;
  durability slice 34 passed; matrix 213 valid.
- Evidence: `UNIT_C1_EVIDENCE.md`. Full-regression proof
  lands in the final battery.

## E-1 — Detection completeness (OPEN)

- Severity: Low. Seed `txn_84731` uses channel `QR`, which
  classifies UNMAPPED. ML_ANOMALY honestly NOT_IMPLEMENTED
  (must stay so).
- Correction (specified): QR as 9th canonical channel +
  regression tests proving zero seed UNMAPPED.
