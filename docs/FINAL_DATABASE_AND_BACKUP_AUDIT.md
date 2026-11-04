# FINAL DATABASE AND BACKUP AUDIT (R03–R04)

Date: 2026-11-02. Live state: `data/state.json` SHA-256
`BA1D4DB4…3790FE`, 101417 B, mtime Nov 1 (untouched by all QA —
verified before/after every suite and browser run).

## Database / migration (R03)

| Check | Status | Evidence |
| ----- | ------ | -------- |
| Schema, ordering, rollback, constraints, concurrency | PASS (disposable) | J5 rehearsal suite green inside backend 463/463 against live scratch PG (`csai-scratch-pg`, `SCRATCH_DATABASE_URL`): migrations, idempotency, rollback, concurrent writes, failure/recovery |
| Production file-store integrity | PASS | Hash identical across programme; JSON store remains the live authority; no destructive reset path exercised or present |
| **Live Neon cutover** | BLOCKED | Requires owner approval (migration + cutover + rollback window). Migration code exists and is rehearsed; no live migration performed or claimed |

## Backup / disaster recovery (R04)

| Check | Status | Evidence |
| ----- | ------ | -------- |
| Policy, runbook, DR plan, integrity validation | PASS (documents) | `docs/J6_BACKUP_POLICY.md`, `J6_DISASTER_RECOVERY_PLAN.md`, `J6_DATA_INTEGRITY_VALIDATION.md`, `J6_RESTORE_TEST_REPORT.md` (J6 programme) |
| Disposable restore drill | PASS | J6 drill green (documented in restore test report); backup crypto tooling present (`backups/`, pynacl/shamir, hash-pinned) |
| **Authorised real backup + isolated restore + measured RTO** | BLOCKED | Requires owner-approved destination + handling method (standing gate). No backup artifact exists; none is claimed. Procedure ≠ PASS |

## Standing approval requests (unchanged)

1. Neon live migration/cutover (exact window + rollback trigger).
2. Real backup: destination, contents, exclusions, secret handling,
   retention, restore drill target.
