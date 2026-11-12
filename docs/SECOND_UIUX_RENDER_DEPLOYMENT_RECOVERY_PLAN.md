# SECOND UI/UX RENDER DEPLOYMENT RECOVERY PLAN — CruiseShield AI™

Date: 2026-11-03 · Root cause: frontend never deployed (no
service exists). Recovery = execute the ALREADY-APPROVED
Option-B frontend provisioning. No code changes required.

## Step 0 — Preconditions (verify, don't change)

- Commit `58a3d50` on `origin/production-launch` (verified).
- Backend live + healthy (verified 200).
- Owner holds Render account; Free terms re-confirmed.

## Step 1 — G-PROVISION (frontend only; owner executes in dashboard)

- Service: `cruiseshield-ai-frontend`, Free, Node 20.19.6.
- Repo/branch: `CRUISESHIELD-AI-` @ `production-launch`.
- Root `frontend`; build `npm ci && npm run build`; start
  `npm start -- --port $PORT`; health `/`.
- Env: `NEXT_PUBLIC_API_BASE_URL=https://cruiseshield-ai.
  onrender.com` (+ `NEXT_PUBLIC_SITE_URL` = self URL after
  first deploy + rebuild; token = backend value or empty).

## Step 2 — Backend CORS completion (dashboard env edit + redeploy)

- Set backend `FRONTEND_ORIGINS` = exact frontend URL.
- Verify: evil-origin probe denied; app origin allowed.

## Step 3 — Landing verification tests (must all pass)

1. `GET <frontend>/` 200, contains "Global Intelligence Core".
2. Hero canvas OR WebGL fallback renders (both valid).
3. All 10 capability cards link to 200 screens.
4. `/demo` loads data from the backend (cross-origin works).
5. 390/768/1440 screenshots match prior evidence.
6. Reduced-motion + keyboard-only pass; no console errors
   except known cold-start retry.
7. Backend `/` STILL serves legacy Command Center (expected —
   it is the API service's no-JS surface, not the product home).

## Step 4 — Records + video

- Record frontend URL in the gate register; run the 18-row
  acceptance plan; record the 3:00 video against the LIVE
  landing (not localhost).

## Dependencies / risks

- Depends ONLY on G-PROVISION approval + Render account access.
- No git, code, asset, or config changes needed — any "fix"
  that edits code for this issue would be mistargeted.
- Cold starts (~60 s) affect first-load filming: warm up first.
- Do NOT decommission the backend `/` legacy page in this
  recovery (separate decision; it costs nothing and aids API-only
  checks).
