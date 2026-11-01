# Phase A — Repository Audit (2026-10-28)

Checkout: clean tree at `0eaaaf5` on `master` (checkpoint for this program).
`0eaaaf5` ("fix: correct Render Docker Blueprint configuration") removed the
`startCommand` line from `render.yaml`; see CONFLICT-001 in 03-TRACEABILITY.

## Structure (verified by listing)

- `app/` — 14 modules: config, models, seed, store, events, graph, rules,
  evidence, cases, replay, simulate, ai_adapter, main. No middleware.
- `templates/` — base, command, investigation, system_health (Jinja2).
- `static/` — app.css, app.js, graph.js (vanilla, no build step).
- `tests/` — conftest, env_probe, 9 test files (48 tests).
- `data/` — `.gitkeep` + runtime `state.json` (89 KB, gitignored).
- Root — Dockerfile, render.yaml, requirements.txt (6 pinned deps),
  README.md, .env.example, .gitignore, .dockerignore, 2 spec files.
- `frontend/` — does NOT exist: no conflict for the planned directory.
- Reference image — NO image files anywhere in the repo (png/jpg/svg/webp
  search: zero matches). The brief's "supplied image" was not supplied in
  the repository. Visual design must proceed from the textual description.

## API contracts (all 24 routes, read from app/main.py)

Pages: `GET /`, `GET /investigations/{inv_id}`, `GET /system-health`.
JSON: health, demo scenarios/reset/start/judge-start, transactions/{id},
graph/{txn}, risk/{txn}?scope=, alerts, investigations/{id},
investigations/{id}/evidence-package (GET+POST),
investigations/{id}/ai-analysis (POST), ai-runs/{run}, replay/{scenario},
simulations (POST), cases (+/{id}, +/{id}/decisions POST, +/{id}/audit),
events (POST ingest only).
Error envelope everywhere: `{error: {code, message, trace_id}}`.
NOT present: event listing/search/pagination, metrics overview, AI
follow-up/conversation, notes, assignment. See 03-TRACEABILITY for the
additive endpoints these gaps imply (proposed, not built).

## Data, config, security, deploy (verified)

- Store: `DATA_DIR/state.json` (default `<root>/data`), atomic writes,
  auto re-seed on empty. IDs canonical; money integer kobo.
- Config: `MODEL_API_KEY` (required, server env/`.env`), `META_MODEL_ID`
  (muse-spark-1.3), `META_BASE_URL` (https://api.meta.ai/v1), `DATA_DIR`.
  `.env` exists locally, ignored + untracked; key server-side only.
- AI: prompt v2, `response_format json_object` w/ fallback, strict
  schema+evidence-ID validation, bounded failure diagnostics. Live run
  agentrun_0002 SUCCEEDED (19.4 s, VALIDATED/VALIDATED) — verified.
- Deploy: Dockerfile (python:3.13-slim, DATA_DIR=/srv/data, CMD :8000) +
  render.yaml (docker runtime, healthcheck, 1 GB disk, MODEL_API_KEY
  sync:false). Image never built (engine denied from sandbox).
- Tests: 41 passed, 7 socket-gated skips. Live state: 1 decision
  (NEW→TRIAGED, audit_0006), 1 sim, audit chain 0001–0006, seed hash match.
