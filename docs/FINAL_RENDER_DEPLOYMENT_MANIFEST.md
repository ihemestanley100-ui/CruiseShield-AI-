# FINAL RENDER DEPLOYMENT MANIFEST — CruiseShield AI™

Date: 2026-11-03 · HEAD 753a6c5 (master, 1 ahead of origin/master).
Branch pointer `production-launch` created; NO commit, NO push.

## A. Exact deployment values (all derived from source, none invented)

| Item | Value | Source |
|---|---|---|
| Repository | https://github.com/ihemestanley100-ui/CRUISESHIELD-AI-.git | `git remote origin` |
| Branch | `production-launch` @ 753a6c5 + working tree (commit pending owner approval) | git state |
| Backend root dir | `.` (repo root) | `render.yaml` (no rootDir = root) |
| Backend runtime | Docker (`Dockerfile`: `python:3.13-slim`, non-root `appuser`) | `Dockerfile` |
| Backend build | Render `docker build` (hash-pinned `pip install --require-hashes -r requirements.lock`) | `Dockerfile` |
| Backend start | `python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}` | `Dockerfile` CMD |
| Backend port | `$PORT` (Render-provided; local default 8000) | `Dockerfile`, `render.yaml` |
| Backend health path | `/api/v1/health` (readiness: `/api/v1/ready`) | `render.yaml`, `app/main.py` |
| Frontend root dir | `frontend` | `render.yaml` `rootDir` |
| Frontend runtime | Node (20.19.6 per blueprint; engines >= 18.18.0) | `render.yaml`, `frontend/package.json` |
| Frontend service type | Web Service (REQUIRED: dynamic SSR routes; static export would break `/cases`, `/investigations`, `/network`, `/replay`) | build output (`ƒ` routes), `render.yaml` |
| Frontend build | `npm ci && npm run build` (requires `frontend/package-lock.json` in git) | `render.yaml` |
| Frontend start | `npm start -- --port $PORT` | `render.yaml` |
| Frontend health path | `/` | `render.yaml` |
| $0 plans | Render Free × 2 (no disk block); Vercel Hobby REJECTED (ToS per J8); Cloudflare Pages is a future alternative pending adapter work | zero-cost register |
| Backend public URL | TBD at provisioning (`https://<backend>.onrender.com`) | platform-assigned |
| Frontend public URL | TBD at provisioning (`https://<frontend>.onrender.com`) | platform-assigned |
| Frontend API base | MUST equal the backend public URL (build-time baked; rebuild after set) | `render.yaml` DEPLOY_ORDER |
| Allowed CORS origins | MUST equal the frontend public URL (backend redeploy after set) | `render.yaml` DEPLOY_ORDER |
| Python pins | fastapi==0.133.0, uvicorn==0.40.0, pydantic==2.12.5, httpx==0.28.1, jinja2==3.1.6, psycopg==3.3.2 | `requirements.txt` |

## B. Deploy order (load-bearing, from `render.yaml`)

1. Deploy backend first; note its https URL.
2. Set frontend `NEXT_PUBLIC_API_BASE_URL` to that URL; (re)build.
3. Set backend `FRONTEND_ORIGINS` to the frontend https URL;
   redeploy backend.
4. Smoke: backend `/api/v1/health` + frontend `/` + one
   cross-origin page. Then run the acceptance plan.

## C. Required files (deploy-critical subset with Git status)

Status key: `M` = modified-uncommitted, ` ` = clean at HEAD,
`??` = untracked. Full 96-entry status captured in §D.

Backend runtime (all required in the Docker build context):

- `Dockerfile` (clean), `.dockerignore` (clean),
  `requirements.txt` + `requirements.lock` (clean),
  `app/*.py` (25 files; `M`: `config.py`, `main.py`,
  `ratelimit.py` — R-09; rest clean), `templates/*.html` (clean),
  `static/*` (clean).

Frontend runtime (`rootDir: frontend`):

- `package.json`, `package-lock.json` (clean, committed),
  `next.config.ts` (M — R-09 HSTS), `tsconfig.json`,
  `vitest.config.ts` (clean), `app/**`, `components/**`,
  `lib/**`, `styles/**`, `public/**` (M per §D — UGLS work;
  new: `skip-link.*`, `format.test.ts`,
  `inventory-dump.test.ts`), `.env.example` (clean).

Config / CI (required for deploy + gates):

- `render.yaml` (clean), `.github/workflows/security-gate.yml`
  (clean), `.env.example` (M — R-09 doc), `migrations/loader.py`
  (clean, optional PG path only).

Seed / state:

- `data/.gitkeep` (clean); `data/state.json` correctly IGNORED
  (re-seeds deterministically in a fresh DATA_DIR).

## D. Full working-tree status (verbatim, 2026-11-03)

86 modified + 10 untracked entries (see session record for the
complete `git status --short`; modified areas: `.env.example`,
`app/config.py`, `app/main.py`, `app/ratelimit.py`, 20 UGLS docs,
~50 frontend UGLS/i18n files, `qa-scratch/data/state.json`,
7 R-09 backend tests, `frontend/next.config.*`; untracked:
`.edge-d-probe/`, `a11y-audit.mjs`, `docs/PROJECT_EXECUTION_
STATE.md`, `docs/ZERO_COST_INFRASTRUCTURE_REGISTER.md` + the 9
new FINAL_* docs below, 4 new frontend test/component files,
`qa/`, `tmpw_ta9ikh/`, `webgl-fail-r10.html`).
Selection rule for commit: source + docs + tests + examples;
NEVER `.env*` (beyond examples), `data/state.json`, `.next/`,
`node_modules/`, `*.log`, `__pycache__/`, `*.pem/*.key`,
`.edge-d-probe/`, `tmpw_ta9ikh/`, scratch evidence.

## E. URL status

No public URL exists yet: nothing provisioned, nothing pushed.
`BACKEND_URL_TBD` and `FRONTEND_URL_TBD` are filled at
provisioning; the acceptance plan stays NOT_VERIFIED until then.
