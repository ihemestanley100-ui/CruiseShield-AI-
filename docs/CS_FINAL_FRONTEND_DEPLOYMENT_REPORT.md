# CS FINAL — FRONTEND DEPLOYMENT REPORT (CS-FINAL-EXECUTION-010)

Date: 2026-11-03 · Status: PREPARED, NOT provisioned.

## Readiness (Phase 6 — all verified)

- Next 15.5 / React 19 / Node 20.19.6; tsc 0; 366/366;
  build EXIT=0 (8/8); start verified live.
- API base: `https://cruiseshield-ai.onrender.com`
  (build-time baked; set before first build).
- Token var: EMPTY (R6 proven — dead branch, 0 literals).
- Session auth via HttpOnly cookie + CSRF header; 401/403
  drive the login prompt; loading/error/404 boundaries;
  i18n + a11y + responsive evidence on file.
- Service type: Web Service (Node) REQUIRED — dynamic
  routes + `headers()` + `next start`; static export
  would break it. Do not use Static Site.
- CORS: backend allowlist design ready; live value awaits
  the frontend URL (owner sets `FRONTEND_ORIGINS` +
  redeploys backend after creation).

## Exact Render configuration (Option B, awaiting approval)

- `cruiseshield-ai-frontend`, Node, Free, branch
  `production-launch`, root `frontend`,
  build `npm ci && npm run build`,
  start `npm start -- --port $PORT`, health `/`.
- Env: `NODE_VERSION=20.19.6`,
  `NEXT_PUBLIC_API_BASE_URL=<backend URL>`,
  `NEXT_PUBLIC_SITE_URL=<self URL, then rebuild>`,
  `NEXT_PUBLIC_DEMO_WRITE_TOKEN` LEAVE EMPTY.

## Gate (Phase 7 — all must pass first)

Armed backend · R1–R4 live green · health green · CORS
wired · frontend suite green · cost established · no
critical findings · spend within approved limit ($0:
Free ×2 within allowances — account proof pending).
ALL deployment gates currently BLOCKED on owner evidence.
No service created; nothing provisioned.
