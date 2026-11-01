# CRUISESHIELD AI™ — ZERO-COST CLOUD DEPLOYMENT TRANSFORMATION

**Programme:** CSAI-MASTER-RELEASE-001, zero-cost workstream (Phases 1–8)
**Date:** 2026-11-01
**Target:** $0/month controlled demonstration, synthetic data only, protected login
**Status vocabulary:** PASS_VERIFIED / PASS_WITH_LIMITATIONS / PARTIAL / FAIL /
BLOCKED / NOT_VERIFIED (same as master programme)

**Constraints in force:** no paid plans, purchases, deployments, commits,
pushes, migrations, backup overwrites, or destructive changes without explicit
owner approval. Nothing in this package executes anything — it specifies.

---

## A. ZERO-COST ARCHITECTURE — PASS_VERIFIED (design)

```
Judge browser ──HTTPS──▶ Vercel Hobby (Next.js frontend, static + ISR)
       │                        │  NEXT_PUBLIC_API_BASE_URL (build-time)
       │                        ▼
       │                 Render Free (FastAPI backend, Docker)
       │                        │  DATABASE_URL (Neon pooled)
       │                        ▼
       │                 Neon Free (PostgreSQL, serverless)
       │
       └── session cookie (HttpOnly, SameSite=Lax) ──▶ Render backend only
```

| Layer | Provider / plan | Monthly cost | Role |
|---|---|---|---|
| Frontend | Vercel Hobby | $0 | Next.js 15, existing build, no code change |
| Backend | Render Free web (Docker) | $0 | Existing FastAPI + Dockerfile, env delta only |
| Database | Neon Free Postgres | $0 | PgStore via `open_store()` cutover (owner-gated) |
| Source | GitHub Free | $0 | Existing repo, no LFS, no Actions minutes needed |
| AI | Meta Model API, free quota | $0 | Capped client-side (100/day default), fallback on error |
| Domain | Provider subdomains | $0 | `*.vercel.app`, `*.onrender.com`, Neon endpoint |

**Request flows (all verified in code, not yet live):**

1. Page load: browser → Vercel (static shell) → API calls direct to Render
   origin (`https://<backend>.onrender.com`).
2. Login: `POST /api/v1/auth/login` → `Set-Cookie: csai_session=…; HttpOnly;
   SameSite=Lax` (Secure on https). Cookie flows on later cross-origin
   fetches via `credentials: "include"` + credentialed CORS (§B, §F).
3. Reads: `GET` with cookie → `session_guard` → handler.
4. Writes: `POST` with cookie + `X-Requested-With: XMLHttpRequest` →
   CSRF check → handler. Admin-only: `/api/v1/demo/*`.
5. AI: `POST …/ai-analysis` → daily-cap check → Meta API (30 s timeout,
   ≤3 attempts) → validated run persisted → JSON response.
6. Sleep behavior: Render Free sleeps after 15 min idle (30–60 s cold
   start); Neon suspends after 5 min idle (first query wakes it, ~1–3 s).
   The login gate + page error states surface these as retryable errors,
   never as silent wrong data.

**What changes vs the paid Render plan (`render.yaml`, Starter + disk):**
frontend moves Vercel (Render static was never specified; the paid plan
ran Next on a Starter web service), backend drops to Free without disk,
persistence moves from disk-backed JSON to Neon. No application feature
is removed.

---

## B. PROVIDER ELIGIBILITY REPORT — PASS_WITH_LIMITATIONS

Verified 2026-11-01 via web sources checked against provider docs (links
below). Owner re-confirms on the provider pricing page before deploy —
free tiers change (Render cut bandwidth in April 2026).

### B1. Vercel Hobby — ELIGIBLE

| Quota | Limit | Our use | Headroom |
|---|---|---|---|
| Price | $0 | — | — |
| Bandwidth | 100 GB/mo | <1 GB (demo) | >99× |
| Function invocations | 1,000,000/mo | Low thousands (dynamic SSR pages) | >100× |
| Build minutes | 6,000/mo | ~2 min/build, a few builds | >100× |
| Seats | 1 | Solo | Exact fit |

- **Use restriction:** Hobby is **non-commercial use only**. A hackathon
  evaluation demo is non-commercial, but this is a terms interpretation,
  NOT_VERIFIED with Vercel. If the demo is judged commercial activity,
  Pro ($20/seat/mo) applies. Owner decision: accept the interpretation
  or budget Pro. Flagged, not blocking.
- No serverless functions are authored; dynamic Next routes (`/network/[txnId]`
  etc., marked ƒ in the build) render on demand within the invocation quota.
- Sources: [Vercel free-tier limits 2026](https://www.promptstoproduct.com/vercel-free-tier-limits),
  [Vercel Hobby limits](https://costbench.com/software/developer-tools/vercel/free-plan/),
  [Vercel vs VPS Oct 2026](https://dev.to/zforzain2000/vercel-vs-vps-for-nextjs-the-real-monthly-cost-in-2026-431o).

### B2. Render Free web service — ELIGIBLE WITH LIMITATIONS

| Quota | Limit | Our use | Headroom |
|---|---|---|---|
| Price | $0 | — | — |
| Instance hours | 750 hrs/mo per workspace | 1 service ≈ 744 hrs | Thin — exactly one service |
| Sleep | 15 min idle → ~30–60 s cold start | Demo judges wait once | Accepted limitation |
| CPU / RAM | 0.1 CPU / 512 MB | Image 184 MB; runtime NOT measured on Free | **VERIFY AT STAGING** |
| Bandwidth | **5 GB/mo** (cut from 100 GB, Apr 2026) | MBs (JSON KBs × demo clicks) | >10× at demo scale |
| Build minutes | 500/mo | ~3–5 min/build | >50× |
| Disk | None on Free | JSON won't persist → Neon required (§E) | By design |

- Only **one** Free web service fits in 750 hrs/mo if left running; the
  backend is that service. The frontend is on Vercel, so no second
  service is needed.
- Cold starts are the main demo risk: rehearse the wake-up (hit
  `/api/v1/health` 60 s before screen-share).
- Sources: [Render free-tier summary](https://freetier.co/directory/products/render)
  (verified Aug 29 2026), [free-hosting comparison](https://snapdeploy.dev/blog/free-cloud-deployment-platforms-2026-comparison)
  (Sep 26 2026), [Render's own cost article](http://render.com/articles/how-much-does-cloud-application-hosting-cost-for-small-businesses).

### B3. Neon Free Postgres — ELIGIBLE

| Quota | Limit | Our use | Headroom |
|---|---|---|---|
| Price | $0 | — | — |
| Storage | 0.5 GB/project (some Oct-2026 reports say 1 GB — **conflict**, verify) | ~101 KB state | >5000× either way |
| Compute | 100 CU-hours/project/mo | Demo bursts at 0.25 CU | >10× |
| Autosuspend | Fixed 5 min idle, cannot disable | First query wakes (~1–3 s) | Accepted |
| Egress | 5 GB/project/mo | KBs | >100× |
| Projects / branches | 100 / 10 | 1 / 1 | Ample |

- Storage conflict (0.5 vs 1 GB) is immaterial at 101 KB but recorded
  honestly: NOT_VERIFIED which figure is current.
- `psycopg==3.3.2` is pinned in `requirements.txt:24` and
  `requirements.lock:350` — the Docker image already carries the driver.
- No connection pooling in `app/db.py` (documented scratch scope) —
  fine for one demo backend, not for production.
- Sources: [Neon free-tier research](https://github.com/sanika1356/ai-vr-career-guidance-system/blob/HEAD/server/deployment-free-tier-findings.md)
  (Aug 18 2026), [free Postgres ranking](https://theword360.com/2026/10/17/best-free-cloud-database-hosting-postgresql-mongodb-2026/)
  (Oct 17 2026), [Supabase vs Neon measurement](https://dev.to/karthik_yk/supabase-vs-neon-i-measured-both-free-postgres-tiers-from-india-5da8)
  (Oct 6 2026).

### B4. GitHub Free + Meta API — ELIGIBLE

- GitHub Free: repo is KBs of source; no LFS/Actions load. PASS_VERIFIED.
- Meta Model API: usage is assumed metered against a free quota or trial;
  the app never assumes free — §G caps calls at 100/day default and
  degrades to stored results + honest errors. Actual quota/price:
  NOT_VERIFIED (owner's account). Cost control, not cost proof.

---

## C. FRONTEND DEPLOYMENT CONFIGURATION — READY (spec)

No code change. Vercel project settings (dashboard, owner applies):

| Setting | Value | Evidence |
|---|---|---|
| Root Directory | `frontend` | Repo layout |
| Framework | Next.js (auto-detected) | `frontend/package.json` |
| Build command | `npm ci && npm run build` (default `npm run build` also fine once lockfile committed) | Build verified locally 2026-11-01 |
| Output | `.next` (default) | — |
| Node | 20.x | Local 20.19.6; engines ≥18.18 |
| Env `NEXT_PUBLIC_API_BASE_URL` | `https://<backend>.onrender.com` (from §I step 1) | Baked at build; rebuild after set |

**Pre-deploy gates (both owner actions):**

1. `frontend/package-lock.json` is **untracked** (`??` in git status).
   `npm ci` fails without it in a fresh clone. The approved commit MUST
   include it. BLOCKED until committed.
2. Backend URL must exist first (§I deploy order) — the value is baked
   into client chunks at build time (mechanism verified locally per
   `render.yaml` comments).

**Compatibility notes (verified in repo):**

- Secure headers ship in `frontend/next.config.ts` (nosniff, DENY,
  referrer, permissions). No CSP — Three.js inline scripts forbid a
  strict policy; documented, unchanged from staging plan.
- `distDir` honors `NEXT_DIST_DIR`, default `.next` — Vercel default works.
- No `vercel.json` is added: dashboard settings suffice and avoid a
  second config source. If the owner prefers config-as-code, the table
  above maps 1:1 to `vercel.json` + project settings.
- Same-origin API proxying was considered and rejected: direct
  cross-origin calls with credentialed CORS (§F) keep one backend URL
  for web + judges' curl, and the backend already gates by origin.

---

## D. BACKEND DEPLOYMENT CONFIGURATION — READY (spec)

Render Free web service, Docker runtime, from the existing `Dockerfile`
(verified 184 MB image per Render engineering report). Delta vs the
paid `render.yaml` blueprint — apply as edits, do not fork the file:

| render.yaml today | Zero-cost value | Reason |
|---|---|---|
| `plan: starter` (backend) | `plan: free` | $0 |
| `disk:` 1 GB block | **Remove** (disks need paid) | No disk on Free |
| `DATA_DIR: /srv/data` | Ephemeral (any path; JSON reseeds, see note) | Free has no persistence |
| `FRONTEND_ORIGINS` (Render URL) | `https://<app>.vercel.app` | Vercel origin |
| `DEMO_WRITE_TOKEN` (optional) | Leave **empty** — sessions replace it | Cookie auth is the credential |
| *(absent)* | `SESSION_SECRET` (sync: false, owner-generated) | Arms login |
| *(absent)* | `DEMO_USERS` (sync: false, `name:role:hash,…`) | Login accounts |
| *(absent)* | `AI_DAILY_CALL_LIMIT=100`, `AI_TIMEOUT_SECONDS=30` | §G |
| *(absent, post-cutover)* | `STORE_BACKEND=pg`, `DATABASE_URL` (sync: false) | §E |
| `healthCheckPath: /api/v1/health` | Unchanged | Open path, works logged-out |
| `dockerfilePath`, uvicorn CMD | Unchanged | PORT-binding verified |

**Persistence note:** with no disk, JSON mode reseeds deterministically
on every cold start (SEC-002 warns loudly on stderr). Decisions, AI
runs, and audits made during a demo **do not survive sleep** until the
Neon cutover (§E) lands. Two owner choices: (a) accept ephemeral JSON
for the first staging pass (simplest, $0, data loss on sleep), or
(b) cut over to Neon before any judged demo (recommended). The
migration is specified and owner-gated in §E regardless.

**NOT_VERIFIED until first staging deploy:** 512 MB / 0.1 CPU sufficiency
for uvicorn + app (no load failure is expected at demo scale, but Free
OOMs are loud, not silent — the staging smoke test in §I proves it).

---

## E. DATABASE MIGRATION PLAN — READY (spec, owner-gated)

**Do not execute without separate owner approval. No migration has run;
`data/state.json` (`BA1D4DB4…3790FE`, 101417 B) is the untouched source
of truth.** Local PG parity was proven earlier (86 tests on
`postgres:16-alpine`, scratch only, container removed).

**Verified building blocks (all in-repo):**

- `app/db.py`: `PgStore` with JSON-Store interface parity, `init_schema()`
  (idempotent, stamps `SCHEMA_VERSION 5.1.0`), `database_health()` probe.
- `migrations/loader.py`: `run_migration(source, url, expected_hash,
  init_schema)` — loads a state COPY atomically, rolls back on failure,
  never touches the live JSON store. CLI: `--source --database-url
  --expected-hash [--no-init-schema]`.
- `app/store.py:31`: `open_store()` selects `Store` vs `PgStore` from
  `STORE_BACKEND` (default `json`). Production `app/main.py` still
  constructs `Store()` directly — cutover is a one-line change (§E.4).

**Steps (owner executes or explicitly approves each):**

1. **Neon project.** Create one Free project + database (region nearest
   the Render region). Copy the pooled `DATABASE_URL`
   (`…pooler…?sslmode=require`). Never commit it.
2. **Verified COPY.** Copy `data/state.json` to a scratch path, verify
   SHA-256 `BA1D4DB4BB4DBC6FC3ACA346664A539610CCC6460CCD530F523C8043453790FE`.
   The loader reads the COPY, never the live file.
3. **Load:** `python -m migrations.loader --source <copy>
   --database-url "$NEON_URL" --expected-hash BA1D4DB4…3790FE`
   (expects hash match, inits schema, atomic load; any failure rolls
   back, database left unchanged).
4. **Parity check:** compare counts (investigations, transactions,
   evidence, audits, decisions) PG vs JSON; spot-check IDs
   (`inv_84721`, `txn_84721`, `case_84721`, `scn_primary`) and the
   authoritative scores (84 HIGH network / 35 MODERATE txn). Mismatch =
   stop, keep JSON.
5. **Cutover (one line + env):** `app/main.py`: `store = Store()` →
   `store = open_store()`; set `STORE_BACKEND=pg` + `DATABASE_URL` on
   Render; redeploy backend; run §I smoke (login → investigate →
   decision → audit, then cold-start and re-read the decision).
6. **Rollback (any time):** unset `STORE_BACKEND` (or set `json`) and
   redeploy — JSON reseeds from scratch on Free (ephemeral), or from
   disk if a disk is later attached. Neon data stays for forensics.

**Known limits:** no pooling (one demo backend — fine); Neon 5-min
suspend adds ~1–3 s to the first query after idle; concurrent-write
safety across workers was proven for JSON (PERF-001 lock) and PG uses
an advisory lock for audits — single Render worker assumed (Free runs
one). Multi-worker PG writes: NOT_VERIFIED, out of demo scope.

---

## F. SECURITY IMPLEMENTATION REPORT — PASS_VERIFIED (tests)

Protected login was implemented with stdlib-only server code (no new
dependencies, $0 preserved) and a login gate in the single shell choke
point. Local demo behavior with `SESSION_SECRET` unset is byte-identical
(open); setting it arms enforcement.

**Backend (`app/auth.py`, `app/main.py`, `app/config.py`):**

| Control | Mechanism | Test evidence |
|---|---|---|
| Sessions | HMAC-SHA256 signed cookie, 12 h TTL, stateless (multi-instance safe) | `test_session_roundtrip_expiry_tamper` |
| Passwords | PBKDF2-HMAC-SHA256, 210k iters, per-user salt; `python -m app.auth hash` owner tool | `test_password_roundtrip_and_wrong` |
| Users/roles | `DEMO_USERS="name:role:hash,…"`, roles investigator/admin, bad entries skipped | `test_parse_users_skips_bad_entries` |
| Enforcement | `session_guard`: all data endpoints 401 without valid session; `/`, health, login, mode open | `test_gated_api_needs_login`, `test_open_paths_bypass`, `test_disabled_means_open` |
| Admin fence | `/api/v1/demo/*` requires admin (403 otherwise) | `test_session_allows_and_roles_gate_demo` |
| CSRF | Cookie-authed POSTs require `X-Requested-With` (403 `CSRF_HEADER_REQUIRED`); token calls exempt | `test_csrf_header_required_for_cookie_posts` |
| Login throttle | 10/min per IP, no user enumeration (dummy record path) | `test_login_rate_limited`, `test_login_rejects_bad_password_no_enumeration` |
| Login/logout/me | Cookie flags HttpOnly + SameSite=Lax (+Secure on https); logout clears | `test_login_success_sets_cookie`, `test_me_and_logout` |
| Credentialed CORS | Armed only when login armed; explicit origins, never `*`; XRW through preflight | 3 staging CORS tests + legacy-policy test |
| Route wiring | Every auth URL maps to its handler | `test_auth_routes_wired_to_handlers` |
| Full flow | mode→401→login→cookie→me→data→CSRF-403→CSRF-200→admin-403→logout→401 | `test_full_stack_login_cookie_csrf_roles` (socket-gated, runs in CI/user envs) |

**Frontend (`frontend/lib/api.ts`, `components/login-gate.tsx`, `app-shell.tsx`):**

- All fetches send `credentials: "include"`; all POSTs send
  `X-Requested-With: XMLHttpRequest` (3 new client tests).
- `useDemoSession` + `LoginCard`: mode check → session restore → gate
  (8 gate tests). AppShell renders the gate for every demo route when
  armed and logged out, shows user/role + Sign out when authed, and
  never gates `/` (3 shell integration tests).
- Fail-open is UI-only and deliberate: if the backend is unreachable
  the shell renders and pages show their existing backend-error states;
  data protection is enforced server-side regardless.
- Incidental fix: drawer effects moved above the early returns so hook
  count is stable across landing/gate/shell renders (login/logout and
  client-side navigation can no longer change hook count).

**Residual risks (honest, unchanged or new):** no CSP (Three.js inline
code, pre-existing); `DEMO_USERS` rotation is manual (restart to
change); demo passwords are shared credentials — low assurance by
design, appropriate for judged demos, never for production.

---

## G. AI USAGE-COST CONTROLS — PASS_VERIFIED (tests)

API usage is never assumed free. Controls are server-side, default-on,
env-tunable (`.env.example` documents names only):

| Control | Setting | Behavior | Evidence |
|---|---|---|---|
| Daily cap | `AI_DAILY_CALL_LIMIT` (default 100, 0 = unlimited) | Counts persisted `ai_runs` attempts started today (UTC); restarts can't reset it. Breach → audited `ai.run.rejected`, HTTP 429 `AI_DAILY_LIMIT_EXCEEDED`, no run persisted | 4 tests in `tests/test_ai_cost.py` |
| Timeout | `AI_TIMEOUT_SECONDS` (default 30) | Bounds one provider call; frontend aborts at 35 s so the server always answers first | `test_timeout_passed_to_provider_call` |
| Retries | `MAX_ATTEMPTS=3`, transient-only (429/502/503/504), 1 s/2 s backoff | Timeouts/connection errors fail fast (no blind retry on a ~15 s call) | Pre-existing adapter tests |
| Errors | Mapped codes → HTTP 503 | `MODEL_TIMEOUT`, `MODEL_RATE_LIMITED`, `MODEL_AUTH_FAILED`, `MALFORMED_RESPONSE`, `MODEL_OUTPUT_INVALID`, … | Pre-existing + `_run_ai` failure path |
| Monitoring | Every run persists `usage` (prompt/completion/total tokens), latency, attempts | Cost attribution per run from stored data | `interpret_provider_body` + run record |

**Fallback chain (verified in code):** live call fails → AI panel shows
`CODE: message` + Retry (`ai-panel.tsx`); the last stored assessment
stays visible on the case page (`latest_ai_run`, guarded render +
tests); risk scores never depend on the model (deterministic engine
authoritative). A `max_tokens` request cap was considered and rejected:
truncation would break the required-JSON contract and surface as
`MODEL_RESPONSE_TRUNCATED` anyway — the daily cap is the cost lever.

---

## H. MONTHLY COST CALCULATION — $0.00 (with conditions)

| Line | Provider | Cost | Condition / tripwire |
|---|---|---|---|
| Frontend hosting | Vercel Hobby | $0.00 | Non-commercial use; <100 GB b/w, <1 M invocations |
| Backend hosting | Render Free | $0.00 | 1 service; <750 hrs; <5 GB b/w; sleep accepted |
| Database | Neon Free | $0.00 | <0.5–1 GB storage; <100 CU-hrs; <5 GB egress |
| Source control | GitHub Free | $0.00 | — |
| AI calls | Meta API quota | $0.00 assumed | **Owner verifies quota**; app caps at 100/day |
| Monitoring | Provider dashboards | $0.00 | No APM |
| Domain | Provider subdomains | $0.00 | No custom domain |
| Backup | Owner-approved copy (not executed) | $0.00 | Local/owner storage |
| **Total** | | **$0.00/mo** | |

**What breaks $0 (tripwires, all loud, none silent):** Vercel
reclassifies the demo as commercial → Pro $20/seat; Render bandwidth
>5 GB → overage/upgrade; Neon compute >100 CU-hrs → suspend until next
cycle (no charge, but demo pauses — the honest failure mode); Meta
quota exhausted → 429s, demo continues on stored results. At judged-demo
scale (tens of page loads, <20 AI calls), every quota holds >10× margin
except Render instance-hours (exactly one service — by design).

---

## I. DEPLOYMENT AND ROLLBACK INSTRUCTIONS — READY (spec)

**Gates before step 1:** owner commits (incl. `frontend/package-lock.json`)
and pushes; owner confirms Vercel non-commercial interpretation; owner
generates `SESSION_SECRET` + `DEMO_USERS` hashes locally
(`python -m app.auth hash`); owner confirms Meta API quota.

1. **Backend (Render dashboard, Blueprint from repo):** create Free web
   service from edited `render.yaml` (§D, disk removed); set
   `SESSION_SECRET`, `DEMO_USERS`, `AI_*`, `FRONTEND_ORIGINS` (temp
   value); deploy; note `https://<backend>.onrender.com`; smoke
   `GET /api/v1/health` (200, no login) and `GET /api/v1/alerts` (401).
2. **Frontend (Vercel dashboard):** import repo, Root `frontend`, set
   `NEXT_PUBLIC_API_BASE_URL` to step-1 URL; deploy; note
   `https://<app>.vercel.app`.
3. **Close the loop:** set backend `FRONTEND_ORIGINS` to step-2 URL;
   redeploy backend.
4. **Acceptance smoke (logged out → in):** open Vercel URL → landing
   renders, no gate; open `/demo` → sign-in card; wrong password →
   inline error; login → Command Center; investigate `inv_84721`
   (scores 84/35, 39 evidence) → AI analysis → simulation → decision →
   audit shows `ai.run.*` + decision; logout → gate returns. Cold-start
   rehearsal: wait 16 min, reload, confirm wake ≤60 s.
5. **Database (only with §E approval):** §E steps 1–6; re-run step 4
   plus cold-start persistence (decision survives sleep).

**Rollback:** frontend — Vercel instant rollback to previous deployment;
backend — Render rollback to previous deploy, or unset `SESSION_SECRET`
to reopen (emergency only, audit it); database — unset `STORE_BACKEND`
(§E.6); full — keep the paid `render.yaml` (Starter + disk) values in
git history as the funded fallback. Nothing here deletes the paid plan;
it specifies the free one.

---

## J. FINAL APPROVAL MATRIX — OWNER DECISIONS REQUIRED

| # | Decision | Recommended | Blocks | Status |
|---|---|---|---|---|
| J1 | Commit + push incl. `package-lock.json` | Yes, exact file list reviewed | C, D, deploy | OWNER ACTION |
| J2 | Vercel Hobby non-commercial interpretation for judged demo | Accept (demo is non-commercial) | $0 claim | OWNER ACTION |
| J3 | `SESSION_SECRET` + `DEMO_USERS` values | Generate locally, enter in Render dashboard | Login on staging | OWNER ACTION |
| J4 | Create Render Free service + Vercel project | Yes, per §I | Staging | OWNER ACTION |
| J5 | Ephemeral JSON first vs Neon before judged demo | Neon before judged demo (§E) | Persistence | OWNER ACTION |
| J6 | Execute Neon migration (§E steps) | After J4 smoke passes | §E | OWNER ACTION |
| J7 | Meta API quota confirmation | Confirm free quota covers ~100 calls | AI live demo | OWNER ACTION |
| J8 | Backup destination + secret handling | Approve per `SUBMIT_G_BACKUP_READINESS.md` | Preservation | OWNER ACTION (pre-existing) |
| J9 | Record + upload 3-min video | After staging smoke | Submission | OWNER ACTION (pre-existing) |
| J10 | Final hackathon submit | After J1–J9 | Done | OWNER ACTION (pre-existing) |

**Technical verdict:** ZERO_COST_PACKAGE_COMPLETE — architecture,
configs, migration plan, login, and AI cost controls are implemented,
tested, and specified. **Nothing is deployed, migrated, committed, or
submitted.** Every remaining step is an owner action above.

---




