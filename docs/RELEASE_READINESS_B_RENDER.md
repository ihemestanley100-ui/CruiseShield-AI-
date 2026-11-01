# B. RENDER PRODUCTION DEPLOYMENT READINESS

DATE: 2026-11-01 | METHOD: inspection of `render.yaml`, `Dockerfile`, `.dockerignore`, app config, and measured local procedure. NO deployment performed or triggered.

## 1. Current blueprint coverage
- Backend service: DEFINED (`render.yaml` → Docker web `cruiseshield-ai`, plan starter, `Dockerfile`, health check `/api/v1/health` — endpoint exists and returns 200 locally).
- Build: `pip install --require-hashes -r requirements.lock` — reproducible, matches CI. `.dockerignore` present.
- Env: `MODEL_API_KEY` sync:false (Render prompts; secret store) — correct. `META_MODEL_ID`, `META_BASE_URL`, `DATA_DIR=/srv/data` pinned.
- Storage: 1 GB persistent disk `cruiseshield-data` → `/srv/data`; app reads `DATA_DIR` (`app/config.py`) and re-seeds deterministically on empty dir (fresh demo state, AI runs empty — honest cold start).
- Frontend service: NOT DEFINED — the single largest gap (see §3).

## 2. Per-requirement assessment
- Frontend service: MISSING. Needs a second Render service (Node runtime; build `npm install --prefix frontend && npm run build --prefix frontend`; start `npm start --prefix frontend -- --port $PORT`; health check `/`). NOT attempted.
- Backend start: READY (`uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`).
- Database: FILE STORE on persistent disk (no Postgres cutover; `STORE_BACKEND` stays `json`). Adequate for demo hosting; NOT a multi-user store (D-012 carries).
- Env vars (names): backend needs MODEL_API_KEY (+Nap defaults fine); frontend needs `NEXT_PUBLIC_API_BASE_URL` = backend URL — MUST be set at BUILD time (baked into chunks; verified behavior locally).
- CORS: `FRONTEND_ORIGINS` MUST be set to the deployed frontend origin (default is localhost:3000 — a hosted frontend would be blocked; proven failure mode locally). Required blueprint addition.
- Health checks: backend `/api/v1/health` READY; frontend `/` trivially addable.
- Secrets: MODEL_API_KEY via Render secret store; nothing secreted in repo/image. No `.env` copied into image (verify: Dockerfile copies only requirements/app/templates/static — PASS).
- Domain: Render default `*.onrender.com` available; custom domain = owner DNS action (not configured).
- Rollback: Render keeps prior deploys (service rollback available) BUT the persistent disk is NOT rolled back — data persists across rollback. Procedure: redeploy prior image + (if schema/state incompatible) restore state.json from the owner-approved backup. Backup execution (D-008) is a precondition for any rollback claim.

## 3. Gaps blocking deployment (do not deploy until closed)
1. No frontend service definition (render.yaml backend-only; Dockerfile excludes `frontend/`).
2. `FRONTEND_ORIGINS` + `NEXT_PUBLIC_API_BASE_URL` wiring for hosted origins (untested combination).
3. Backup unexecuted (D-008) — no rollback safety net.
4. Demo-grade limits go live with it: no authN/authZ (D-002), no rate limiting (D-001) — public URL abuse risk; restrict or accept explicitly.
5. Dockerfile never built (engine denied locally; Render builds server-side) — first build unproven.
6. Plan/cost approval (starter + disk are paid) + domain decision — owner.

## 4. Verdict
RENDER_DEPLOYMENT_NOT_READY — backend blueprint sound; frontend missing; six gaps above. Recommended path (all owner-approved): add frontend service + CORS wiring → backup first → deploy backend → deploy frontend → smoke (health, 6 routes, CSS 200) → record URLs. No deploy action taken.
