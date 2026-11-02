# J5 — NEON POSTGRESQL MIGRATION (rehearsed, not cut over)

**Status:** rehearsal VERIFIED on disposable scratch PG; live cutover
NOT performed (owner approval required). JSON remains authoritative.

## Source-to-target dictionary

| JSON key | PG table | PK | Notes |
|----------|----------|----|-------|
| transactions | transactions | transaction_id | full doc JSONB |
| nodes | graph_nodes | node_id | |
| edges | graph_edges | edge_id | node refs validated by loader |
| events | events | event_id | |
| rule_results | rule_results | rule_result_id | keyed per txn |
| risk | risk_assessments | (target_id, target_type) | 35/84 pinned |
| alerts | alerts | alert_id | |
| investigations | investigations | investigation_id | |
| evidence_packages + items | evidence_packages + evidence_items | package/item ids | package_hash re-verified |
| cases | cases | case_id | |
| decisions | decisions | decision_id | 0 rows in seed |
| audits | audit_events | audit_event_id | chain order re-verified |
| ai_runs | ai_runs | agent_run_id | |
| simulations | simulations | simulation_id | |
| (runtime) | session_revocations | nonce | J4; never migrated |
| (runtime) | user_epochs | username | J4; never migrated |

Schema: `app/models_pg.py` DDL (`SCHEMA_VERSION 5.1.0`, additive
`IF NOT EXISTS`; auth tables outside `LOAD_ORDER` by design).
Manifest: `docs/J5_MIGRATION_MANIFEST.md` (counts, ID samples,
content hashes, referential checks — all OK).

## Pooling decision

No client pool driver (`psycopg_pool` uninstallable offline, and
unneeded): pooling rides on **Neon's pooled endpoint** (pooler host
in `DATABASE_URL`). The client is URL-agnostic (`connect()` takes
any libpq URL); unreachable pooler-style URLs fail closed with a
fixed reason (tested, no leak). Single worker assumed; pool sizing
is a Neon-dashboard setting at provisioning (owner).

## Rehearsal evidence (`tests/test_j5_rehearsal.py`, 2 passed)

Hash-gated load of live bytes → `passed:true`; idempotent re-run
identical; 13/13 table counts match manifest; risk 35/84, audit
chain, 39 evidence items verified on PG; decision write + restart
reconnect + 8-thread reads green; corrupt source → MigrationError
with data unchanged; live `state.json` hash unchanged after all ops.

## Cutover procedure (owner-gated, sequential)

1. Owner provisions Neon project (Free) + records pooled endpoint.
2. Fresh scratch rehearsal against Neon (same test, Neon URL).
3. Copy live bytes, hash-verify, `run_migration --expected-hash`.
4. Set `STORE_BACKEND=postgres` + `DATABASE_URL` on backend only.
5. Staging acceptance (J8 suite); keep JSON file as rollback source.
6. Rollback triggers (any): reconcile mismatch, staging failure,
   quota/suspend errors, 5xx spike → unset `STORE_BACKEND` (JSON
   resumes instantly; PG left for forensics). Rollback is one env
   change + restart; no data moves back (JSON was never written to
   during PG operation... see note).

Note: while on PG, writes go to PG only; rolling back abandons
PG-side writes (acceptable for synthetic demo; real cutover needs
a PG→JSON export step — NOT implemented, owner decision).
