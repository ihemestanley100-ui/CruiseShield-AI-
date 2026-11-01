# 5. RENDER CONFIGURATION SPECIFICATION

DATE: 2026-11-01 | SOURCE OF TRUTH: `render.yaml` (structural lint CLEAN 11-01; full parse happens at Render Blueprint import — runbook step).

## Backend `cruiseshield-ai`
- Type web · runtime docker · plan starter (disk requires paid) · dockerfilePath ./Dockerfile · healthCheckPath /api/v1/health.
- Disk `cruiseshield-data` 1 GB → /srv/data. Env: MODEL_API_KEY (sync:false), META_MODEL_ID=muse-spark-1.3, META_BASE_URL, DATA_DIR=/srv/data, FRONTEND_ORIGINS=https://cruiseshield-ai-frontend.onrender.com (TEMPLATE — confirm post-deploy).

## Frontend `cruiseshield-ai-frontend`
- Type web · runtime node · plan starter (free sleeps; owner cost call) · rootDir frontend · build `npm ci && npm run build` · start `npm start -- --port $PORT` · healthCheckPath `/`.
- Env: NODE_VERSION=20.19.6 (relax to "20" if build image lacks patch), NEXT_PUBLIC_API_BASE_URL=https://cruiseshield-ai.onrender.com (TEMPLATE — MUST equal deployed backend URL; build-time baked).

## Deployment order (load-bearing)
1. Backend → note URL. 2. Set frontend API URL → (re)build frontend. 3. Set backend FRONTEND_ORIGINS → redeploy backend. 4. Smoke (doc 7). Skipping order = CORS-broken or mispointed demo (both failure modes proven locally).

## Rollback
- Service: redeploy prior Render release (kept history). Disk NOT rolled back — data persists; if state incompatible, restore state.json from owner-approved backup (D-008 precondition) + restart. Frontend: redeploy prior (stateless; rebuilds from git).
