# 3. DATABASE DECISION REPORT

DATE: 2026-11-01 | CURRENT: JSON file store (`app/store.py`), single-process, lock-serialized writes (PERF-001), atomic tmp+replace. Active backend hardwired (`app/main.py:36`); `STORE_BACKEND` validated, `pg` supported by health/ready checks only.

## Option A — Controlled synthetic-data demo deployment (RECOMMENDED for staging)
- Store: JSON on the 1 GB Render persistent disk (`/srv/data/state.json`).
- Cold start: deterministic reseed on empty disk (warns); demo dataset regenerates identically (golden invariants 35/84).
- Concurrency: safe in-process (lock); single Render instance only (no multi-instance writes — disk + lock are per-process).
- Backup/restore: disk snapshots (Render) + state.json copy-outs; restore = replace file + restart (drill-verified pattern locally).
- Limits (accepted for staging): single user/instance, no horizontal scale, disk doesn't roll back with deploys.
- Data: synthetic only; decisions/audits persist across restarts (paid disk) or reset (free tier — documented in blueprint).

## Option B — Production-grade PostgreSQL (NOT ready; requirements listed)
- Adapter exists: `app/db.py` (502 lines) + `models_pg.py` + `migrations/` + 4 test files — explicitly SCRATCH-VERIFICATION ONLY: no pooling, no cutover wiring, no migration runner discipline, no backup/restore design.
- To productionize: (1) connection pooling + timeouts, (2) `STORE_BACKEND=pg` cutover in main (replace hardwired `Store()`), (3) migration runner + version gate in health (schema check exists: `_pg_check`), (4) parity suite on Render Postgres, (5) backup/PITR + restore drill, (6) independent review. Estimated: separate engineering workstream, not a flag flip.
- Decision: Option A for staging; Option B requires the workstream above + owner/institutional approval. No migration performed; live data untouched.
