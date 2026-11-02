# CRUISESHIELD AI — NEON MIGRATION READINESS (J3)

**Verdict:** READY-TO-REHEARSE (spec + scratch-verified adapter). No
cutover performed or authorized.

## What exists (verified in repo)

- `app/db.py` `PgStore` (JSON-interface parity), `init_schema`
  (idempotent, `SCHEMA_VERSION 5.1.0`), `database_health` probe;
  `migrations/loader.py` atomic COPY load with `--expected-hash`
  rollback-on-failure; `psycopg==3.3.2` pinned + hashed.
- Local parity proven earlier: 86 PG tests on `postgres:16-alpine`
  (scratch, container removed). PG suites re-collected here
  (socket-gated skips as designed).
- Canonical plan: `docs/ZERO_COST_A_TO_J.md` §E (6 steps incl. parity
  checks + one-line `open_store()` cutover + rollback-by-unset).

## J3 verification

- JSON backend remains authoritative; `STORE_BACKEND` defaults `json`;
  `DATABASE_URL` unused until cutover (RENDER_6 row corrected).
- Identifier preservation: loader migrates a verified COPY
  (`BA1D4DB4…` hash gate), never the live file; IDs/scores/audits
  compared in plan step 4.

## Gaps & gates

- Cutover + Neon project + rehearsal require owner approval (separate).
- No pooling, 5-min suspend wake cost, single worker assumed —
  documented demo scope. Neon storage figure conflict (0.5 vs 1 GB)
  immaterial at 101 KB but still NOT_VERIFIED.
