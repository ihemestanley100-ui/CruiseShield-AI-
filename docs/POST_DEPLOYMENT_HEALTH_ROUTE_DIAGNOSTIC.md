# POST-DEPLOYMENT HEALTH ROUTE DIAGNOSTIC — CruiseShield AI™

Date: 2026-11-03 · Method: read-only (code inspection + git
forensics + public GET probes only; no writes, no auth attempts,
no state-changing calls). Production URL:
`https://cruiseshield-ai.onrender.com`.

## Outcome up front

The reported `{"detail":"Not Found"}` on `/api/v1/health` DOES
NOT reproduce: the endpoint returned HTTP 200 `healthy` on
2026-11-03 (verified firsthand, cache miss). No application
defect found. Root cause: almost certainly a wrong-path request
or stale observation (see §6). NO code change recommended.

## 1. Application entry point (actual)

- `app/main.py:35`: `app = FastAPI(title="CruiseShield AI",
  version=APP_VERSION)`. Package marker `app/__init__.py` only.
- No routers, no `include_router`, no `root_path`, no
  `app.mount` except `/static` (line 172). No custom OpenAPI
  generator; default `/openapi.json` + `/docs` served.

## 2. Startup command (actual)

- `Dockerfile` CMD: `python -m uvicorn app.main:app --host
  0.0.0.0 --port ${PORT:-8000}` — loads exactly the app in §1.
- No `--reload`, no workers flag, no env-conditional app swap.

## 3. Registered routes (local code vs live)

- Local: 40 endpoints, all `@app.<method>` with literal paths
  incl. `@app.get("/api/v1/health")` (line 383) and
  `@app.get("/api/v1/ready")` (line 427).
- Live (`/openapi.json`, fetched 11-03): 39 paths, INCLUDES
  `/api/v1/health`, `/api/v1/ready`, auth, demo, AI, cases —
  consistent with the local inventory (count delta = path-vs-
  operation counting + my two guessed probe paths, which were
  never real routes: correct paths are `/api/v1/demo/scenarios`
  and the AI-analysis endpoint).

## 4. Expected vs actual health route

| Probe (11-03, live) | Result |
|---|---|
| `GET /api/v1/health` | 200 `healthy` (store/seed/provenance PASS; `model_configured: NOT_CONFIGURED`; `pg: NOT_CONFIGURED`) |
| `GET /api/v1/ready` | 200 `{"ready":true,"backend":"json",…}` |
| `GET /api/v1/alerts` | 200 seeded OPEN alert (proves API + store serve) |
| `GET /openapi.json` | 200, `/api/v1/health` registered |

## 5. Deployed-commit match — NOT_VERIFIED (from outside)

- The route exists IDENTICALLY in every candidate commit
  (`f75c3fb`, `d4e2bec`, `58a3d50` — verified via
  `git show` + `git log -S`), so the 404 cannot be explained
  by branch/commit choice.
- Health-body markers (`run_id`, `active=`) also exist in all
  three — no externally visible fingerprint distinguishes
  them. Definitive check: owner reads the Render dashboard
  deploy log (branch + commit SHA). Expected: branch
  `production-launch` @ `58a3d50`.

## 6. Root cause (ranked)

1. MOST LIKELY: the observed request used a wrong path
   (`/health`, `/api/health`, typo, pasted URL error).
   FastAPI returns exactly `{"detail":"Not Found"}` for
   unregistered paths — the observed body is the framework's
   stock 404, not an app error page.
2. Possible: stale observation from a pre-deploy window (DNS /
   cold service returning proxy behavior — though Render proxy
   errors are not FastAPI-shaped, so this ranks lower).
3. RULED OUT: missing route in code, wrong app instance,
   prefix/mount misconfiguration, OpenAPI override, branch
   mismatch (route present in ALL branches), crashed app
   (would refuse/502, not JSON-404).

## 7. Incidental security finding (no probe beyond public GETs)

- The public backend is currently OPEN DEMO: `/api/v1/alerts`
  reads without credentials and no auth challenge appears.
  `MODEL_API_KEY` is unset. This matches a freshly provisioned
  pre-hardening state — but P-1/P-2 (armed SESSION_SECRET +
  DEMO_USERS, exact CORS origin) MUST be completed before
  release. Do NOT treat this backend as hardened.

## 8. Recommended correction (smallest, safe)

- Code: NONE — no defect found; do not "fix" a healthy route.
- Process: (a) re-request the EXACT failing URL + timestamp if
  the 404 is seen again; (b) owner confirms Render dashboard
  shows branch `production-launch` @ `58a3d50`; (c) complete
  P-1/P-2 provisioning; (d) then run the acceptance plan.

## 9. Required verification tests (before any "operational" claim)

- Repeat §4 probes post-provisioning (health/ready/alerts +
  openapi presence).
- Auth: bad login → 401; good login → 200 + HttpOnly cookie;
  `/me` → 200; logout → 200; alerts-without-cookie → 401.
- CORS: deployed-frontend origin allowed; evil origin denied.
- Headers: HSTS/CSP/nosniff/DENY present on HTTPS responses.
- No PASS without captured bodies for each row.

Backend is RESPONDING — it is NOT yet verified operational or
hardened. No "fully operational" claim is made here.
