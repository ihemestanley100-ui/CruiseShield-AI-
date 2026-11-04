# FINAL DATABASE AND BACKUP READINESS — CruiseShield AI™

Date: 2026-11-03 · Launch path: JSON store. No migration, cutover,
or backup executed (all owner-gated).

## 1. Production database decision — JSON (verified path)

- Active backend: `STORE_BACKEND=json` (default), atomic-write
  file `DATA_DIR/state.json` (101417 B, SHA-256
  `BA1D4DB4…3790FE`, unchanged across all sessions).
- `render.yaml` provisions `/srv/data`; on Render Free the
  filesystem is EPHEMERAL: seeds re-seed deterministically on
  empty dir (verified behavior), runtime writes do not survive
  sleep/restart (register L1 — disclosed).
- PostgreSQL is NOT required for launch and NOT claimed
  production-ready. `app/db.py` states: scratch verification
  only, zero production cutover; no pooling (demo scale).

## 2. Schema and migration status (PG path, ready-but-unpromoted)

- DDL: 19 tables (`app/models_pg.py`): schema_meta, scenarios,
  transactions, graph_nodes, events, graph_edges, rule_results,
  risk_assessments, alerts, investigations, evidence_packages,
  evidence_items, ai_runs, cases, decisions, audit_events,
  simulations, session_revocations, user_epochs.
- `migrations/loader.py`: refuses the live file (COPY only),
  verifies SHA-256, single transaction with full rollback,
  idempotent upserts, 7-check reconciliation (counts, dup PKs,
  FK orphans, exact risk scores, audit sequence, package hashes,
  runtime meta). CLI: `--source COPY --database-url URL
  [--expected-hash H]`.
- Skipped PG tests (`SCRATCH_DATABASE_URL`-gated) cannot run in
  this environment (no local postgres, no URL). They are the
  FIRST step of any future cutover sprint, against an isolated
  scratch database — never production first.

## 3. Connection handling

- JSON: file I/O, no connections. PG (scratch): `psycopg`
  direct connections, 5 s connect timeout (fail-safe), URL
  never logged/raised/returned, audit appends under an
  advisory lock. Pooling and production PG review are part of
  the (unstarted) cutover sprint, not the launch.

## 4. Seed-data policy

- Seeds are code (`app/seed.py` + fixtures in git). Fresh/empty
  `DATA_DIR` re-seeds deterministically; health endpoint
  verifies seed integrity (`seed_integrity: PASS`) and graph
  provenance on every boot. No manual seeding step at deploy.

## 5. Backup and restore (launch)

- Launch backup posture: NOTHING durable to back up beyond git.
  Seed fixtures + code live in the repository (pushed at
  release); runtime records are ephemeral by $0 design (L1).
- `backup-produce/restore-drill/verify` workflows exist but are
  DISABLED by default (manual dispatch + `backup-production-gate`
  reviewers, B2/C3 destinations needing owner accounts). No
  backup executed; execution is separately gated.
- Restore procedure at launch: redeploy (or wake) → automatic
  reseed → verify `/api/v1/health` seed_integrity PASS. RTO ≈
  cold-start time; RPO = session start (ephemeral records).
- Durability upgrade path: Supabase Free PG (7-day pause caveat)
  or Neon free (auto-resume) + the cutover sprint above. No
  commitment made; no account created.

## 6. Synthetic data separation

- All fixtures synthetic (kobo minor units, seeded IDs,
  `synthetic_flag` / `SYNTHETIC` labelling, `synthetic_data_flag`
  on AI runs). No real user, customer, or financial records in
  tree, seeds, tests, or evidence (audited 11-01, secret-clean
  since). Demo traffic stays synthetic by construction.

## Status

Database: PASS for $0 JSON launch. Backup: PASS (nothing to back
up; procedure documented). PG cutover: NOT_STARTED (gated,
optional, post-launch).
