# G-PROVISION PREFLIGHT REPORT — CruiseShield AI™ Render Launch

Date: 2026-11-03 · Method: read-only (no services, billing,
secrets, deploy, git, or quota actions). Source of truth: pushed
commit `58a3d50` on `origin/production-launch` (verified via
GitHub API: SHA match, unprotected branch).

## 1. Repository / branch — PASS

- Remote `origin/production-launch` @ `58a3d50…`, message exact,
  parent `753a6c5`. Local tracking branch in sync, nothing ahead.
- Deploy tree == verified tree: zero changes under `app/`,
  `frontend/`, `requirements.*`, `Dockerfile`, `render.yaml`
  since the commit (only doc leftovers differ).

## 2. Committed build configuration — PASS

- Backend: `Dockerfile` (`python:3.13-slim`, hash-pinned
  install, non-root `appuser`, `EXPOSE 8000`, `${PORT}`-aware
  HEALTHCHECK, uvicorn CMD on `0.0.0.0:$PORT`). Local
  `docker build` green 11-03 (image written).
- Frontend: Node service, `NODE_VERSION 20.19.6`
  (engines ≥18.18), `npm ci && npm run build`
  (lockfile committed), `npm start -- --port $PORT`.
  `tsc 0`, `366/366`, `next build` green on this exact tree.
- Health: backend `/api/v1/health` (+ `/api/v1/ready`);
  frontend `/`. 40 API routes in committed code.

## 3. Environment variables (NAMES only) — PASS

- Backend: `SESSION_SECRET` (P-1: 32+, armed), `DEMO_USERS`,
  `DEMO_WRITE_TOKEN`, `MODEL_API_KEY` (existing key only; no
  new spend), `META_MODEL_ID`, `META_BASE_URL`,
  `FRONTEND_ORIGINS` (= frontend URL), `AI_DAILY_CALL_LIMIT=100`,
  `AI_TIMEOUT_SECONDS=30`, `DATA_DIR=/srv/data`,
  `STORE_BACKEND=json`, `PORT` (platform).
- Frontend: `NEXT_PUBLIC_API_BASE_URL` (= backend URL,
  rebuild after set), `NEXT_PUBLIC_DEMO_WRITE_TOKEN` (same
  value as backend), `NEXT_PUBLIC_SITE_URL` (= frontend URL),
  `NODE_VERSION`, `PORT`.
- All secrets via Render prompts (`sync: false` style); zero
  values in repo/docs/CI (secret-scan PASS).

## 4. CORS / auth / persistence / restart — PASS_WITH_LIMITATIONS

- CORS allowlist = deployed frontend origin only (set at
  deploy step 3); credentialed; tested. P-1/P-2 enforced.
- Auth armed with owner-provisioned secrets; login throttle,
  HSTS/CSP/headers active; Secure cookies follow
  X-Forwarded-Proto (Render TLS).
- Persistence: app FUNCTIONS FULLY on ephemeral disk
  (deterministic reseed; health-verified). Bounded $0 losses
  on sleep/restart (F-EPH-1, disclosed): revocations/epochs,
  session audits, interactive records, throttle buckets.
  No uploads, no required durable writes — nothing crashes
  without a disk.

## 5. Fresh terms recheck (Nov 2026 sources) — PASS_WITH_LIMITATIONS

- Free: $0, no card, 512 MB/0.1 CPU, sleep after 15 min idle,
  ~60 s wake, 750 instance-hours per workspace/month (shared),
  5 GB bandwidth/month then $0.15/GB WITH card / service
  SUSPENSION without card. Free PG expires in 30 days (not
  used). Disks paid-only ($0.25/GB, needs $7+ plan).
- Demo traffic is kilobytes against a 5 GB cap; two sleeping
  services share 750 h comfortably. Monitor usage dashboard;
  set alerts; re-confirm at signup (terms drift).

## 6. MANDATORY pre-deploy decision (blocker, owner to pick)

- The committed `render.yaml` specifies `plan: starter` (paid)
  + a `disk:` block (paid-only). It CANNOT be Blueprint-deployed
  as-is for $0.
- Option B (RECOMMENDED): manual dashboard creation of 2 Free
  web services with the exact settings in §7 (no new commit,
  no re-verify cycle; blueprint kept for a future paid tier).
- Option A: new commit changing blueprint to Free + no disk
  (needs a fresh G-COMMIT-2 approval + CI + re-push; slower,
  more reproducible). Either is valid; pick one.

## 7. Exact manual service settings (Option B)

Backend `cruiseshield-ai` (Free):

- Repo/branch: `ihemestanley100-ui/CRUISESHIELD-AI-` @
  `production-launch` · Runtime: Docker · Dockerfile: `./Dockerfile`
- Plan: Free · Health check: `/api/v1/health` · No disk
- Env: per §3 (generate SESSION_SECRET 32+ / write token via
  `secrets.token_urlsafe(32)`; provision DEMO_USERS; copy
  MODEL_API_KEY; FRONTEND_ORIGINS after frontend URL known)

Frontend `cruiseshield-ai-frontend` (Free):

- Same repo/branch · Runtime: Node 20.19.6 · Root: `frontend`
- Build: `npm ci && npm run build` · Start: `npm start -- --port $PORT`
- Plan: Free · Health check: `/`
- Env: per §3 (API base = backend URL → rebuild; SITE_URL =
  self URL; token = same value as backend)

Order: backend → note URL → frontend env + build → backend
FRONTEND_ORIGINS + redeploy → smoke (§8).

## 8. Post-deploy smoke + acceptance

- Smoke (5 min): backend `/api/v1/health` healthy + `/api/v1/ready`
  200; frontend `/` 200; `/demo` renders with data; login 401→200→
  `/me`→logout; evil-origin CORS check; header spot-check.
- Then the 18-row acceptance plan (all NOT_VERIFIED until live),
  G-AI-SPEND single call, video, G-RELEASE.

## 9. Changes needed — verdicts

- MANDATORY: pick §6 Option A or B (no code changes needed
  under B). Provision P-1/P-2 secrets. Re-confirm Render
  ToS/pricing/bandwidth at signup.
- OPTIONAL (defer): Cloudflare-Pages adapter, Supabase
  persistence sprint, digest pin, PR for remote CI.
- NOTHING ELSE: no rebuild, no migration, no backup, no new
  integration required for $0 launch.

Overall: PASS (ready to provision once §6 is decided). Nothing
created, billed, entered, deployed, committed, or spent.
