# 7. DEPLOYMENT RUNBOOK (staging — EXECUTE ONLY ON OWNER APPROVAL)

PRECONDITIONS: backup approved + executed (D-008) · paid plan approved · acceptance of demo-grade limits (no auth/rate-limit) · this checklist printed.
0. Sanity: `git status` reviewed; record HEAD + tree state; suites green (backend 300/68/0, frontend 234/234, build exit 0 — re-run if tree changed).
1. Render dashboard → New → Blueprint → select repo → pick `render.yaml` → confirm parse (this validates YAML fully).
2. Set MODEL_API_KEY when prompted (sync:false). Confirm plan starter ×2 (or owner-chosen).
3. Deploy BACKEND first. Wait healthy (`/api/v1/health` status healthy; expect reseed warning in logs on first boot = normal cold start).
4. Record backend URL EXACTLY (e.g. `https://cruiseshield-ai.onrender.com`).
5. Set frontend NEXT_PUBLIC_API_BASE_URL to step-4 URL → deploy FRONTEND (build bakes the URL; ~2–5 min).
6. Set backend FRONTEND_ORIGINS to the frontend URL → redeploy backend.
7. SMOKE (record each): backend /api/v1/health 200 + status field; frontend / 200 + CSS 200 + secure headers present; /demo, /cases/case_84721, /investigations/inv_84721, /network/txn_84721, /replay/scn_primary all 200 with data (proves CORS); risk strip 35/MOD + 84/HIGH; evidence 39; graph 22n/30e; one simulation (sim labelled, baseline kept); one human decision on the STAGING store + audit event (staging data only).
8. Record deployed URLs + image digests + timestamps in the release log. Keep the staging store SYNTHETIC ONLY.
FAILURE BRANCHES: build fail → read logs (likely NODE_VERSION patch — relax to "20"); CORS errors → recheck steps 5–6 values + rebuild frontend; unhealthy backend → logs (disk mount? DATA_DIR?); any persistent-local-data risk → STOP (staging must never touch local `data/`).
