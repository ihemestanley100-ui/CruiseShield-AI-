# J6 — BACKUP POLICY

**Scope:** synthetic demo data + code + config. No production data
exists; this policy governs the staging/demo corpus and its recovery.

## What is backed up

- PostgreSQL snapshot (canonical dump via `PostgresSnapshotter`) OR
  `data/state.json` bytes while JSON is authoritative — exactly one
  authority per environment (never both as “current”).
- `SCHEMA_VERSION` + migration/loader provenance in the manifest.
- Repo snapshot: git commit hash recorded in the manifest.
- Brand assets + docs travel with the repo (no separate backup).
- Secrets are NEVER in backups: `.env`/keys restore from the
  owner’s secret store (procedure, not values).

## Frequency / retention / objectives

- Demo/staging: manual generation before any cutover, deploy, or
  submission milestone; no schedule claimed.
- Retention: keep the last 2 verified generations + the
  pre-cutover generation; older expire only by explicit owner call.
- RPO: last verified generation (minutes of demo work at most).
- RTO: < 30 min restore-to-verified on a warm host (drill: ~2 s
  produce+verify at demo scale; host provisioning dominates).
- Owner: the repository owner (produce/restore approvals are
  owner-only; no automatic jobs — workflows disabled by default).

## Integrity rules

- Every generation: CSBK1 envelope + minisign manifest + cross-copy
  verification before promotion; divergent bytes fail closed and
  never overwrite (`UPLOAD_DIVERGENT`).
- No backup is claimed until `verify_backup_set` reports
  `verified:true` (see `docs/J6_RESTORE_TEST_REPORT.md`).
- Runbook (procedure): `docs/BACKUP_RECOVERY_RUNBOOK.md` — this
  policy defers to it for commands and never duplicates them.
