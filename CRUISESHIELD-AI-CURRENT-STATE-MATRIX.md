# CRUISESHIELD-AI-CURRENT-STATE-MATRIX.md

One-line status per capability. Evidence pointers are file:line ranges
from bodies inspected 2026-11-05. Legend: T = IMPLEMENTED_TESTED,
U = IMPLEMENTED_UNTESTED, P = PARTIAL, M = MISSING, S = SIMULATED
(honestly labeled), B = BLOCKED (by design).

## Backend / API

| Capability | Status | Evidence |
|---|---|---|
| 42 routes (3 pages + 39 JSON, all `/api/v1/*`) | T | app/main.py:31-1144 |
| Versioning (APP_VERSION 1.0.0-p0, v1 only) | T | app/main.py:33-35, health:434 |
| Config/env incl. fail-safe AI ints | T | app/config.py:7-159 |
| Auth primitives + sessions + epochs (both backends) | T | app/auth.py:32-198; store.py:255-289; db.py:564-632 |
| session/CSRF/RBAC/rate/body-guard/CORS middleware | T | app/main.py:45-177; config.py:108-132 |
| Health + readiness + _pg_check | T | app/main.py:413-471; Dockerfile:24-25; render.yaml:24 |
| JSON store (active) atomic + reseed | T | app/store.py:19-162; boots main.py:182 |
| Backend selection (validated, default json) | T | app/config.py:143-154; store.py:19-39 |
| PG adapter (scratch parity only) | T | app/db.py:177-656; models_pg.py:14-163 |
| Production PG cutover | M (by design) | no production open_store/PgStore caller |
| Migration safety + idempotency + 7 gates | T | migrations/loader.py:38-431 |
| CSRF (X-Requested-With, token exempt) | T | app/main.py:129-137 |
| Rate limiting (single-instance limit) | T | app/ratelimit.py; main.py:152-169 |
| Audit logging (ordered, NOT hash-chained) | P | store.py:192-206; db.py:421-485; 9 call sites |
| Actor attribution (`demo-token`; INVESTIGATOR hardcode wart) | P | main.py:281-290; cases.py:63 |
| Backups code (CSBK1 + manifests + produce/restore) | T | backups/*.py; tests/test_p1_*, test_p2_* |
| Backups execution (no keys/schedules; plan-only restore) | B (by design) | backup-*.yml:1-7; restore.py:8-10 |
| data/ ignores + deterministic seed | T | .gitignore:1-28; app/seed.py |

## AI / detection / replay

| Capability | Status | Evidence |
|---|---|---|
| Provider/model/endpoint/auth (mock-transport; live never run) | T | ai_adapter.py:232-441; config.py:34-36 |
| Schemas + output validation + approval gate | T | ai_adapter.py:33-199,315-373; intel_ai.py |
| Retries / timeouts / fallback mapping | T | ai_adapter.py:302-479; config.py:83-86 |
| Usage caps (daily + max-output 4096) | T | main.py:915-925; ai_adapter.py:206-218,235,427 |
| Rules R-001..R-008 + risk-score-v1 + traceability | T | rules.py; graph.py:50-83; evidence.py |
| DI-03..DI-09 + risk-v2-candidate (flag-gated) | T | main.py:642-764; flag :732,755 |
| Replay + simulation/what-if | T | replay.py; simulate.py; main.py:1020-1050 |
| Human-approval boundaries (advisory-only AI, human decisions) | T | ai_adapter.py:29-30,191-194; cases.py:38-77 |
| Signal analytics APIs (10 routes + FP/execution envelope) | T | detection.py; channels.py; main.py signals block; test_detection.py 34 green |
| Fail-closed behavior (11 codes, no key leak) | T | ai_adapter.py:382-489 |
| Model eval / golden AI harness (offline) | T | tests/test_ai_eval.py 8 fixtures; live lane GAP-014 |

## Frontend / Three.js

| Capability | Status | Evidence |
|---|---|---|
| Live route bindings (demo/inv/cases/network/replay) | T (call-graph) | frontend/app/*/page.tsx; lib/api.ts |
| API client (credentialed + CSRF + auth + timeout) | T | frontend/lib/api.ts:60-997 |
| Login gate + public landing + useCan roles | T | login-gate.tsx; app-shell.tsx:150-174; session.ts:42-47 |
| Notifications / decision / AI / sim / replay components | T | components/*.tsx (live clients) |
| i18n registry + provider + selector | T | lib/i18n/*; language-selector.tsx:66-94 |
| a11y + responsive + error/loading/404 | T (jsdom-level) | globals.css; a11y.test.tsx:1-4; app/*.tsx |
| Landing composition + scene builders + GlobeController | T | landing/*; scene.test.ts; controls.test.ts |
| GlobalHeroScene live canvas (loop/gestures/context-loss) | U | GlobalHeroScene.tsx:52-327 (fallback only tested) |
| Landing hero network (hubs/beams/satellites) | S (labeled) | earth.ts:46-55; network.ts:1-3; orbital.ts:1-2 |
| Graph/orbital/table/preview explorers (record-backed) | T | graph-explorer.tsx; orbital-explorer.tsx; graph-table.tsx |
| Graph provenance chain (store → API → explorers) | T | main.py:767-777; api.ts:378-386; network page |
| Public assets + immutable logo | T | frontend/public/*; public-assets.test.ts; icons.test.ts |
| next.config headers + CSP tracks build origin | T | next.config.ts:5-52; next.config.test.ts |
| Detection panels (frequency/health/channels/matrix/series) | P | detection-panels.tsx; TimeSeriesPanel + FP rows CI-gated |

## Deploy / quality / ops

| Capability | Status | Evidence |
|---|---|---|
| render.yaml (backend + frontend wiring) | U (correct) | render.yaml:13-104 |
| Dockerfile (pinned, nonroot, healthcheck; no digest pin) | U | Dockerfile:1-26 |
| requirements.txt + requirements.lock (37/463) | U | requirements.txt:6-34; lock:1-6 |
| netlify.toml (publish .next, no adapter; SSR-incompatible) | P (stale) | netlify.toml:1-4 |
| Backend tests (46-47 files, 518 collected, hermetic) | T | tests/*; conftest.py:9-48 |
| Frontend tests (72 files, 0 skips, mocked boundary) | T | frontend/**/*.test.*; vitest.config.ts |
| CI security gate (6 checks + suites + build; local PASS) | T (local) | security-gate.yml:18-90; scripts/security_gate.py |
| Backup workflows (logic tested; dispatch never run) | P | backup-*.yml |
| Deploy pipeline (manual Blueprint; never executed) | P | render.yaml; docs/DEPLOYMENT.md |
| Docs (312 files; consistent chain; 1 live token conflict) | P | docs/*; RENDER_6_ENV_REGISTER.md:23 vs render.yaml:95-100 |
| Dependency manifests (hash-locked, gate-enforced) | T | lock files; gate-r09f.log 6/6 |
| Secrets handling (ignores verified, names-only, scans) | T | .gitignore; .env.example; test_secret_safety.py |
| Coverage measurement | M | no pytest-cov/vitest coverage/codecov config |
| qa/ + qa-scratch/ (evidence store, not suites) | — | qa/*; qa-scratch/state.json |

## Cross-cutting gaps (critic missing-scope, verified)

- 9 backend routes with zero frontend references (batch 1.1, 2026-11-05):
  WIRED — txn base GET (network header), accounts-intel (investigation
  account blocks), ai-runs GET (case run expander). API-ONLY by
  documented product decision — events POST (ingest path), cases list
  (single-case demo links directly), demo start / judge-start (replay
  reset UI covers the flow), ready (orchestrator), evidence-package
  POST alias (R4 test gate).
- 5 clients dead outside tests (batch 1.1, 2026-11-05): WIRED —
  getDevice / getIpObservations / getGeoObservations (IntelSection
  drill-downs), getTransactionIntel (network intel section).
  LIBRARY-ONLY by documented decision — listAlerts (notification
  center is the canonical alerts surface; raw feed serves
  drivers/tests).
- Current tree (518 backend / 72 FE) has no full green run log; latest
  logs cover 476 / 64-file-354. 46-vs-47 backend-file drift unsettled.
- GitHub dispatch greenness, Netlify serve behavior, Render dashboard
  state, scratch-PG live pass, off-repo backup keys: all
  unverified/uninspected.
