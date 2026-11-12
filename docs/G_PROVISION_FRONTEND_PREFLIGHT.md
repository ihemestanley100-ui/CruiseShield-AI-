# G-PROVISION FRONTEND PREFLIGHT — CruiseShield AI™

Date: 2026-11-03 · Method: read-only (no services, env, deploy,
or quota actions). No project files modified except this report.

## 1. Git state — PASS

- Branch: `production-launch`, in sync with
  `origin/production-launch` (verified post-push).
- HEAD: `ff7052bdf0ac48a68f69c3937d9b8708ca265354`
  (`security: enforce demo-token authorization and
  document remediation`, parent `58a3d50`).
- Deploy source for G-PROVISION: this branch @ this HEAD.

## 2. Backend health — PASS (with deploy-lag note)

- `GET https://cruiseshield-ai.onrender.com/api/v1/health`
  → 200 `healthy` (live probe 11-03): store PASS,
  seed_integrity PASS, graph_provenance PASS, storage
  json PASS. `model_configured: NOT_CONFIGURED`,
  `pg: NOT_CONFIGURED` (expected: no key, JSON store).
- NOTE: served `version: 1.0.0-p0` predates `ff7052b` —
  the live backend still runs pre-R1–R4 code. A backend
  redeploy is REQUIRED before release so R1–R4 + R5
  token enforcement are live (see §9).

## 3. Frontend framework/commands — PASS

- Next.js ^15.0.0, React ^19, Node engines >=18.18.0
  (`frontend/package.json`, verified).
- Blueprint pins `NODE_VERSION 20.19.6` (locally verified
  runtime; relax to major "20" only if the image lacks
  the patch — failure is loud).
- Build: `npm ci && npm run build` (verified EXIT=0,
  8/8 pages, `/` 5.76 kB static).
- Start: `npm start -- --port $PORT` (verified live on
  :3100: `/` 200 + "Global Intelligence Core", `/demo`
  200). Health check: `/`.

## 4. Frontend env vars — PASS

Only three `NEXT_PUBLIC_*` read in code (repo grep):
`NEXT_PUBLIC_API_BASE_URL` (`lib/api.ts:68`),
`NEXT_PUBLIC_DEMO_WRITE_TOKEN` (`lib/api.ts:227`),
`NEXT_PUBLIC_SITE_URL` (`lib/site-url.ts:9`).
Plus platform `NODE_VERSION`, `PORT`.

## 5. API base URL — PASS

`NEXT_PUBLIC_API_BASE_URL` MUST equal
`https://cruiseshield-ai.onrender.com` (matches
`render.yaml:78-79` and DEPLOY_ORDER step 2).
Build-time baked — set BEFORE first build.

## 6. Demo-token var EMPTY — PASS (R6)

`NEXT_PUBLIC_DEMO_WRITE_TOKEN` MUST remain empty/unset
(owner-approved R6). Verified posture: clean build with
var unset (EXIT=0), dead `""!==f` branch only, 0 value
literals, 0 sourcemaps, tsc 0, 366/366. All browser
writes use login sessions. No public fallback.

## 7. Backend env vars (Render prompts) — PASS (list)

Names only (R5): `SESSION_SECRET` (32+, armed, R09-F2),
`DEMO_USERS`, `DEMO_WRITE_TOKEN` (**MANDATORY**, fresh
32+ random — empty re-opens write gates), `MODEL_API_KEY`
(only if live AI approved), `META_MODEL_ID`,
`META_BASE_URL`, `FRONTEND_ORIGINS` (see §8),
`AI_DAILY_CALL_LIMIT=100`, `AI_TIMEOUT_SECONDS=30`,
`DATA_DIR`, `STORE_BACKEND=json`, `PORT` (platform).

## 8. CORS — PASS (config ready, pending URLs)

`FRONTEND_ORIGINS` = exact deployed frontend origin
(allowlist, never "*"; credentialed). Set AFTER the
frontend URL is known (DEPLOY_ORDER step 3) + backend
redeploy. Evil-origin denial verified in code/tests;
live re-verify post-deploy.

## 9. Exact Render frontend configuration (Option B manual)

- Service: `cruiseshield-ai-frontend` · Type: Web Service
- Runtime: Node · Plan: Free · Branch: `production-launch`
- Repo: `ihemestanley100-ui/CruiseShield-AI-`
  (note GitHub case-redirect notice observed 11-03)
- Root: `frontend` · Build: `npm ci && npm run build`
- Start: `npm start -- --port $PORT` · Health: `/`
- Env: `NODE_VERSION=20.19.6`;
  `NEXT_PUBLIC_API_BASE_URL=https://cruiseshield-ai.onrender.com`;
  `NEXT_PUBLIC_SITE_URL=<self URL after first deploy, then rebuild>`;
  `NEXT_PUBLIC_DEMO_WRITE_TOKEN` = LEAVE EMPTY (R6).
- Order: create frontend → note URL → backend
  `FRONTEND_ORIGINS` + R5 token + redeploy (picks up
  `ff7052b`) → smoke (§10 of recovery plan) → 7 landing
  tests → 18-row acceptance.

## 10. Blockers

- B1 (MINOR, doc fix, needs approval): `render.yaml:80-83`
  and `frontend/.env.example` still describe the OLD
  token posture ("MUST equal backend value"). Must be
  updated to R6-EMPTY wording before deploy to prevent
  operator error. Read-only in this preflight — no change
  made. (Blueprint `plan: starter` is already bypassed
  via Option B manual Free creation.)
- B2 (STANDARD): backend redeploy required (live code
  predates R1–R4/R5) — part of G-DEPLOY, not preflight.
- B3 (STANDARD): owner must hold the Render account and
  re-confirm Free terms/bandwidth at signup.
- No code, infra, or quota blockers. No secrets exposed
  in this report (names only).

Overall: PASS — ready for G-PROVISION approval once B1
wording is fixed (or explicitly accepted as-is with the
R6 register overriding). Nothing created, changed (except
this doc), deployed, or spent.
