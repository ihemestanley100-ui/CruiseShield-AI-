# LIVE EVIDENCE INDEX — CruiseShield AI™ (current line)

Date: 2026-11-06. Branch: feat/phasezero-foundations @ d82627d.
Canonical per D-033. Every entry quotes an observed result;
absence of an entry means absence of evidence.

## Test execution (this line, measured)

- LEB-01 backend full suite 2026-11-06: 1074 passed / 141
  skipped / 1 failed + 2 errors — all three sandbox-only
  (node EPERM lstat on test_static_escaping; CORS-setup
  PermissionErrors), each re-verified individually.
  Covers Phase 5 (+45: accounts/verify/billing/payments;
  +41: passkeys/orgs/notify/webhooks/session-fix),
  Phase 6 (+13: AI gateway), Phase 7 (+1: backup-root
  regression). Skips never counted as passes.
- LEB-02 quality gates 2026-11-06: 3/3 green —
  0 duplicate source groups; 81/81 /api routes referenced;
  11/11 decision codes logged.
- LEB-03 D-029 slice (prior turn, same line): focused 10
  passed / 7 socket-skipped; full 958/141/same 1F+2E.
- LEB-04 frontend: NO current-tree green run exists
  (AC-12/FE-01). Historical 366/366 local run stands only.
- LEB-05 Phase 5 batches 2026-11-06, focused runs green:
  test_passkeys 15/15, test_orgs 8/8, test_notify 11/11,
  test_provider_webhooks 5/5, test_account_security 7/7
  (flaky rotation test 5/5 after D-046 nonce fix),
  test_auth + test_revocation green incl 2 new
  same-second regression tests.
- LEB-06 AI gateway 2026-11-06: test_ai_gateway 13/13;
  AI suites (cost/validation/eval/agents) + quality gates
  + deploy manifests green; MODEL_API_KEY presence check
  UNSET (no live call made or claimed).
- LEB-07 phases 7–8 batches 2026-11-06: security 151/15
  exit 0; tenancy 52/52; perf smoke exit 0 (local
  in-process latencies only); load scratch 5/5; backup
  drill exit 0 (scratch parity true); rollback
  REHEARSED; rehearsal files 5 passed / 2 skipped.
- LEB-08 phase 7 negative results (recorded, not
  passed): security gate FAIL — cryptography absent
  from lock, ambient-env drift, pip_check conflict,
  OSV unreachable; secret_scan + lockfile_hashes PASS.
  tsc still node-EPERM; docker unreachable in sandbox.

## Read-only probes (2026-11-06)

- LEP-01 matrix parse: 90 rows / 90 unique IDs (pre-extension
  count; generator now writes 115 rows, validator exit 0).
- LEP-02 detection: NETWORK_PROXIMITY fires 11 of 136 seed
  signals; 9 families fire; zero family errors.
- LEP-03 fault path: malformed-dict input degrades silently;
  non-dict input raises uncaught AttributeError; no
  family_errors entry was produced by any probe (DET-16).

## State integrity

- LES-01 data/state.json BA1D4DB4…3790FE, 101417 B,
  unchanged across all sessions (re-verified 2026-11-06).

## Registers (this line)

- LER-01 matrix: scripts/zero_gap_matrix.py ROWS →
  docs/ZERO_GAP_MATRIX.json, 115 rows
  (89 closed / 4 in-progress / 4 blocked / 10 awaiting /
  7 not-started / 1 testing), validator exit 0.
- LER-02 decisions D-001…D-048 in the canonical log
  (CRUISESHIELD-AI-DECISION-LOG.md + execution state).
- LER-03 manifest: docs/CANONICAL_FILE_MANIFEST.md.

## Explicitly NOT evidenced (do not claim)

No hosted CI run, no deploy, no live AI call, no live PG
run, no live backup/restore/rollback drill, no customer
acceptance, no commercial/billing run, no production URL.

## Frozen history (consult, never extend)

FINAL_EVIDENCE_INDEX.md (J3–J10) ·
CRUISESHIELD_MASTER_EVIDENCE_REGISTER.md (ff7052b) ·
EVIDENCE_PROVENANCE_REGISTER.md (ff7052b) · phase/audit docs.

## Telecom Identity backend evidence (2026-11-07, hermetic)

pytest tests/test_telecom_registry.py tests/test_telecom_verify.py
tests/test_telecom_providers.py tests/test_telecom_contract.py
tests/test_telecom_security.py tests/test_connectors.py
tests/test_quality_gates.py tests/test_di03_device.py ->
88 passed. Frontend telecom-section.tsx + 6 vitest cases written,
unexecuted (sandbox node EPERM; hosted CI per D-017). Live
provider evidence: none (TEL-08 BLOCKED_EXTERNAL).

## Geointel backend evidence (2026-11-07, hermetic)

56/56 geointel tests green + full-suite regression (see
PROJECT_EXECUTION_STATE). Frontend: 3 components + 8 vitest
cases written, unexecuted (sandbox node EPERM; D-017). Live
provider evidence: none (LIVE-GEO BLOCKED_EXTERNAL).

## Universal intel backend evidence (2026-11-07, hermetic)

39/39 UFI tests green (30 core + 9 routes) + full-suite
regression: 1242 passed / 141 skipped / same sandbox-only
1F+2E (node EPERM + 2x WinError 10013). Frontend: 1
component + 5 vitest cases written, unexecuted (sandbox
node EPERM; D-017). Live provider evidence: none
(UFI-LIVE BLOCKED_EXTERNAL).

UFI slice 2: 23/23 new tests green (15 slice2 + 8 security); frontend +7 vitest unexecuted (EPERM); live none.

UFI slice 3: 17/17 new tests green (9 AI + 6 integration + 2 contract); fleet snapshot 0 READY / 7 measured (evidence); vitest+build reconfirmed EPERM; live none.

SEC slice: 13/13 new tests green (6 cred + 3 rot + 4 dev); no live changes.

UFI closeout: 20/20 new tests green + 1 explicit hosted skip; full suite 1315 passed / same sandbox-only 1F+2E.

Agent OS: 24/24 new tests green (18 + 6 routes); vitest reconfirmed EPERM; contract parity green; no model live.

Recovery OS: 20/20 new tests green (11 + 9 routes); vitest reconfirmed EPERM; contract parity green; no live submissions possible (0 VERIFIED caps).

Acceptance + closure arc 2026-11-07: D-014 map + strict unmapped-deny (403) + fallback audit, 16 map tests green; CS_ENV production guard, 6 tests green; SITE-01 4 static pages + 4 tests (TESTING); locale parity via node stdin (545 en keys; 17 detection keys x11 locales missing, en fallback covers); NO-LIVE settled AI-01/TEL-08/LIVE-GEO/UFI-LIVE; evidence manifest tripwire green; full suite 1377 passed / 142 skipped / same sandbox-only 1F+2E; matrix 190 rows valid.
