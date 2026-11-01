# 2. BACKEND READINESS REPORT (Render)

DATE: 2026-11-01 | RUNTIME: Docker `python:3.13-slim` | IMAGE: built locally 11-01 (`cruiseshield-ai:staging-check`, 184 MB, sha256:21fc33…) — first successful build (engine previously blocked).
CONTAINER SMOKE (ephemeral, cleaned): health 200, risk 200, PORT binding OK, reseed RuntimeWarning fires on empty disk (SEC-002 working in-container).
START: `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}` (custom-port verified :8011/:8012 → 200).
HEALTH: `/api/v1/health` (deep: seed integrity, provenance, backend selection, pg-when-selected) + `/api/v1/ready` (gates on pg when selected). Render healthCheckPath set.
DEPS: hash-pinned lock install in image (37 pins, 463 hashes); gate PASS.
ERRORS: enveloped 400/404/413/422 + trace_id; 413 BODY_TOO_LARGE live-verified (1.1 MB → 413); headers stamped live.
SECRETS: MODEL_API_KEY sync:false (Render secret store); image copies only requirements/app/templates/static (no .env/data — .dockerignore + Dockerfile verified).
DISK: 1 GB `cruiseshield-data` → `/srv/data` = DATA_DIR; cold start reseeds fresh demo (AI runs empty — honest).
SHUTDOWN: SIGTERM → uvicorn graceful (standard); restart reloads disk state (verified hash-identical locally).
GAPS: Render-side build unproven (local build de-risks); chunked-body limit relies on proxy (documented).
VERDICT: BACKEND_READY_FOR_STAGING.
