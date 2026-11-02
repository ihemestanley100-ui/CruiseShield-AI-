# J6 — RESTORE TEST REPORT

**Date:** 2026-11-01. **Scope:** disposable drill only. No owner
backup exists; none claimed (D-008 still open).

## Drill: scratch-PG snapshot → seal → restore (green)

`tests/test_j6_drill.py::test_j6_disposable_roundtrip_drill` —
PASSED (live scratch PG, ephemeral keys, in-memory targets):

1. Seeded scratch PG from live-shape bytes via `run_migration`
   (`passed:true`).
2. `PostgresSnapshotter.capture()` → schema 5.1.0 + canonical dump.
3. `produce_backup` → 2 targets, `promoted:true`,
   `cross_copy_ok:true`, minisign manifest.
4. `verify_backup_set` → `verified:true` (both targets, both
   signatures).
5. `plan_restore` → decrypt → plaintext == snapshot dump bytes,
   manifest id matches.

## Suite backing (fresh, sandboxed)

94 passed across `test_p1_*` (crypto, shamir, signing incl.
minisign-CLI interop, targets, integrity), `test_p2_*` (produce,
restore, resilience, integration, log redaction),
`test_backup_manifest`.

## Not demonstrated

Real B2/C3 targets, real owner keys, scheduled runs (workflows
disabled by default), production-scale timing. First real backup
needs the D-008 destination approval, then this report gains a
dated artifact entry.
