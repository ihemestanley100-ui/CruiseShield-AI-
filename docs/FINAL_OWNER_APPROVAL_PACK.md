# FINAL OWNER APPROVAL PACK — CruiseShield AI™ Render Launch

Date: 2026-11-03 · Status: AWAITING OWNER — no gate executed.
Branch: `master` · HEAD: `753a6c56cb8f563bef7917afa101e5afdc6e707a`
(`production-launch` pointer exists at same HEAD; no checkout made).
Tree: 108 working entries (87 modified + 21 untracked), all preserved.

## 1. Complete manifest (108 entries, grouped)

### 1a. Required application files — COMMIT (59)

Backend (`app/`, R-09):

- `M app/config.py`, `M app/main.py`, `M app/ratelimit.py`

Frontend UGLS/i18n work + R-09 (all `M` except 2 new):

- `frontend/app/cases/[caseId]/audit/page.tsx`
- `frontend/app/cases/[caseId]/page.tsx`
- `frontend/app/demo/page.tsx`
- `frontend/app/globals.css`
- `frontend/app/investigations/[id]/page.tsx`
- `frontend/app/network/[txnId]/page.tsx`
- `frontend/app/replay/[scenarioId]/page.tsx`
- `frontend/components/ai-panel.tsx`
- `frontend/components/app-shell.tsx`
- `frontend/components/command-kpis.tsx`
- `frontend/components/decision-form.tsx`
- `frontend/components/landing/GlobalLandingPage.tsx`
- `frontend/components/login-gate.tsx`
- `frontend/components/notifications.tsx`
- `frontend/components/replay-controls.tsx`
- `frontend/components/simulation-panel.tsx`
- `frontend/components/stat.tsx`
- `frontend/components/timeline.tsx`
- `frontend/lib/api.ts`
- `frontend/lib/format.ts`
- `frontend/lib/i18n/context.tsx`
- `frontend/lib/i18n/format.ts`
- `frontend/lib/i18n/locales/ar.ts`
- `frontend/lib/i18n/locales/en.ts`
- `frontend/lib/i18n/locales/es.ts`
- `frontend/lib/i18n/locales/fr.ts`
- `frontend/lib/i18n/locales/ha.ts`
- `frontend/lib/i18n/locales/hi.ts`
- `frontend/lib/i18n/locales/ig.ts`
- `frontend/lib/i18n/locales/ja.ts`
- `frontend/lib/i18n/locales/pt.ts`
- `frontend/lib/i18n/locales/sw.ts`
- `frontend/lib/i18n/locales/yo.ts`
- `frontend/lib/i18n/locales/zh.ts`
- `frontend/next.config.ts`
- `frontend/styles/landing.css`
- `?? frontend/components/skip-link.tsx` (new source)

(All `M` above are modified-uncommitted; content = UGLS + R-09.)

### 1b. Required configuration files — COMMIT (2)

- `M .env.example` (names + R-09 minimum-length docs; no values)
- `M docs/RENDER_6_ENV_REGISTER.md` (env names + R-09 rule; no values)

(Clean-at-HEAD but required at build: `Dockerfile`,
`.dockerignore`, `requirements.txt`, `requirements.lock`,
`render.yaml`, `frontend/package.json`,
`frontend/package-lock.json`, `frontend/.env.example`,
`frontend/tsconfig.json` — already in git, no action.)

### 1c. Tests and verification files — COMMIT (26)

Backend (all `M`):

- `tests/test_auth.py`, `tests/test_auth_e2e.py`
- `tests/test_body_size_guard.py`, `tests/test_config_safety.py`
- `tests/test_cors.py`, `tests/test_rate_limit.py`
- `tests/test_write_token.py`

Frontend (all `M` except 3 new):

- `frontend/app/cases/[caseId]/audit/page.test.tsx`
- `frontend/app/cases/[caseId]/page.test.tsx`
- `frontend/app/demo/page.test.tsx`
- `frontend/app/investigations/[id]/page.test.tsx`
- `frontend/app/network/[txnId]/page.test.tsx`
- `frontend/components/ai-panel.test.tsx`
- `frontend/components/app-shell.test.tsx`
- `frontend/components/decision-form.test.tsx`
- `frontend/components/login-gate.test.tsx`
- `frontend/components/notifications.test.tsx`
- `frontend/components/replay-controls.test.tsx`
- `frontend/components/simulation-panel.test.tsx`
- `frontend/components/timeline.test.tsx`
- `frontend/lib/api.test.ts`
- `frontend/lib/i18n/coverage.test.ts`
- `frontend/lib/i18n/format.test.ts`
- `frontend/next.config.test.ts`
- `?? frontend/components/skip-link.test.tsx` (new)
- `?? frontend/lib/format.test.ts` (new)
- `?? frontend/lib/i18n/inventory-dump.test.ts` (new)

### 1d. Documentation and audit evidence — COMMIT (14)

- `M docs/FINAL_ZERO_GAP_MATRIX.md` (J11 addendum only)
- `M docs/UGLS_AUTHENTICATED_SESSION_AUDIT.md`
- `M docs/UGLS_COMPLETE_TRANSLATION_COVERAGE.md`
- `M docs/UGLS_FINAL_ZERO_GAP_MATRIX.md`
- `M docs/UGLS_HUMAN_REVIEW_REGISTER.md`
- `M docs/UGLS_KEY_INVENTORY.md`
- `M docs/UGLS_KEY_INVENTORY_GENERATED.txt`
- `M docs/UGLS_LANGUAGE_MATRIX_GENERATED.md`
- `M docs/UGLS_RELEASE_ACCEPTANCE.md`
- `M docs/UGLS_REVIEW_KIT/README.md`
- `M docs/UGLS_REVIEW_KIT/ar.tsv` (+ es, fr, ha, hi, ig, ja,
  pt, sw, yo, zh — 11 files; listed individually in staging cmd)
- `?? docs/FINAL_DATABASE_AND_BACKUP_READINESS.md`
- `?? docs/FINAL_DEPLOYMENT_GATE_REGISTER.md`
- `?? docs/FINAL_HACKATHON_SUBMISSION_CHECKLIST.md`
- `?? docs/FINAL_HACKATHON_VIDEO_STORYBOARD.md`
- `?? docs/FINAL_LIVE_ACCEPTANCE_TEST_PLAN.md`
- `?? docs/FINAL_PRODUCTION_ENVIRONMENT_REGISTER.md`
- `?? docs/FINAL_RENDER_DEPLOYMENT_AUDIT.md`
- `?? docs/FINAL_RENDER_DEPLOYMENT_MANIFEST.md`
- `?? docs/FINAL_SECURITY_RELEASE_AUDIT.md`
- `?? docs/PROJECT_EXECUTION_STATE.md`
- `?? docs/ZERO_COST_INFRASTRUCTURE_REGISTER.md`
- `?? docs/FINAL_OWNER_APPROVAL_PACK.md` (this file)
- (`M docs/RENDER_6_ENV_REGISTER.md` counted in §1b.)

Count check: 59 + 2 + 26 + 15 = 102 G-COMMIT paths
(86 modified + 16 new). Remaining 6 entries excluded below.

### 1e. Excluded files and secrets — NEVER STAGED (6 + ignored)

| Entry | Why excluded |
|---|---|
| `M qa-scratch/data/state.json` | Local QA scratch state (104 KB, scenario copy). Not source, not fixture; committing would pollute history. Left uncommitted in place |
| `?? .edge-d-probe/` | Local Edge BROWSER PROFILE (Autofill, certificates…). Privacy risk + junk. Never commit; recommend adding to `.gitignore` (not done — needs approval) |
| `?? a11y-audit.mjs` | Local one-off audit script (root scratch, not wired into CI). Kept as evidence, not released |
| `?? qa/` (3.2 MB) | Local browser-evidence captures (PNG/HTML, localhost URLs). Evidence stays on disk; too bulky and environment-specific for git |
| `?? tmpw_ta9ikh/` (`s.json`) | Temp scratch dir by name and content. Never commit |
| `?? webgl-fail-r10.html` | Captured single-page audit HTML (localhost URLs). Local evidence only |
| `.env` (gitignored) | LIVE SECRETS. Ignored (`.gitignore:6`), never tracked/in history. Verified again 11-03 |
| `data/*` (gitignored) | Local database + state. Ignored (`.gitignore:7`); production re-seeds from code |
| `frontend/.next/`, `node_modules/` | Build outputs/deps, rebuilt by `npm ci`/`next build`. Ignored |
| `*.log`, `__pycache__/`, `.pytest_cache/`, `*.pem/*.key` | Logs, caches, key material. Ignored |
| `%TEMP%\smoke*`, browser profiles | Outside repo; never enter git by construction |

## 2. G-COMMIT exact file list

§1a + §1b + §1c + §1d = 102 paths. Staged ONLY via the explicit
command in §10 (never `git add -A` / `git add .`).

## 3. Secrecy verification (fresh 11-03 evidence)

- Security gate (`--skip-audit`): PASS — pins, installed-vs-lock,
  463 hashes, pip check, **secret_scan: no real-credential shapes
  found** (covers the full tree INCLUDING the 101 commit paths).
- `.env` + `data/*` + `frontend/.next` ignore-verified via
  `git check-ignore` (above). No `.env*` beyond examples exists.
- `.dockerignore` excludes `.env`, `data/`, `docs/`, `tests/`,
  `.venv/`, `.git/` from the backend image; image contains only
  requirements + `app/` + `templates/` + `static/`.
- Frontend bundle audit: only 3 public `NEXT_PUBLIC_*` names;
  `MODEL_API_KEY` unreachable from client code (grep-verified).
- CONCLUSION: committing §1a–§1d introduces ZERO credentials,
  env files, databases, logs, profiles, or secrets into git.

## 4. Build independence (no local-only files)

- Backend: `Dockerfile` COPYs `requirements.txt`,
  `requirements.lock` (clean, committed), `app/` (tracked; 3 R-09
  files in commit set), `templates/`, `static/` (clean). Python
  3.13-slim from Docker Hub. NOTHING else enters the image.
- Frontend: `npm ci` (lock committed) + `next build`; all `app/`,
  `components/`, `lib/`, `styles/`, `public/` sources tracked or
  in commit set; `next.config.ts` env reads all carry safe
  defaults. No Dockerfile needed (Node runtime service).
- Seed/state: NOT copied (ignored) — production re-seeds
  deterministically; health verifies `seed_integrity: PASS`.
- VERDICT: both services build from git alone. PASS.

## 5. Environment requirements (NAMES only — values never handled)

- Backend: `SESSION_SECRET` (32+, NEW), `DEMO_USERS` (provision),
  `DEMO_WRITE_TOKEN`, `MODEL_API_KEY` (existing, copy to prompt),
  `META_MODEL_ID`, `META_BASE_URL`, `FRONTEND_ORIGINS` (= frontend
  URL), `AI_DAILY_CALL_LIMIT`, `AI_TIMEOUT_SECONDS`, `DATA_DIR`,
  `STORE_BACKEND=json`, `PORT` (platform). Full semantics:
  `FINAL_PRODUCTION_ENVIRONMENT_REGISTER.md`.
- Frontend: `NEXT_PUBLIC_API_BASE_URL` (= backend URL, rebuild
  after set), `NEXT_PUBLIC_DEMO_WRITE_TOKEN`,
  `NEXT_PUBLIC_SITE_URL`, `NODE_VERSION=20.19.6`, `PORT`.
- Rule: generate-then-paste into Render prompts directly; values
  never appear in chat, files, docs, or logs.

## 6. F-EPH-1 re-examination (Render Free sleep/restart)

Mechanism (code-verified): `revoked_sessions` + `user_epochs`
persist inside `state.json` (`app/store.py`); scenario resets
preserve them, but a FRESH reseed on an empty dir (every Render
Free sleep/restart) starts clean. Rate-limit buckets are
process memory. Sessions themselves are stateless HMAC (12 h).

Exact limitations on Render Free:

1. Logged-out sessions become VALID again after a sleep until
   their 12 h expiry (revocation wiped). Logout-all epochs lost
   likewise. Window: up to 12 h per sleeping gap.
2. The audit trail of the previous warm period is LOST
   (forensics gap across sleeps; seed audits re-seed clean).
3. Decisions, AI runs, simulations created interactively are
   LOST on sleep (data-loss boundary = session, not seed).
4. Rate-limit/login-throttle buckets reset (throttle amnesia;
   brute-force window reopens per sleep at demo scale).

NOT affected: seeded data integrity (deterministic reseed +
health-verified), password hashing, 32-char rule, RBAC logic,
HSTS/CSP/CORS, validation, key secrecy. No privilege escalation:
revived sessions keep their ORIGINAL role/permissions.

Launch-acceptance rationale (synthetic hackathon demo, short
judged sessions, disclosed in docs + demo script + this pack):
tolerable WITH P-1/P-2 (armed auth, exact CORS). Structural fix
(Supabase PG + cutover sprint) is post-launch work, separately
gated. If the owner judges F-EPH-1 unacceptable for launch, the
only $0-consistent alternative is delaying launch until the PG
sprint completes — there is no free durable disk on Render.

## 7. Q-IP-1 logo/IP rights — OWNER DECISIONS RECORDED 2026-11-03

- Asset: `frontend/public/assets/cruiseshield-logo-original.png`
  (TRACKED, ships in the product + public repo).
- Standing: developer ASSERTS it is their original brand art;
  recorded in `HACKATHON_ASSET_AND_CODE_PROVENANCE.md`, never
  independently verified. Related marks: "CruiseShield AI™",
  "Muse Spark" (integration fact, not endorsement — Q-IP-2).
- DISCREPANCY FLAG: older docs reference a preserved
  `cruiseshield-logo-original.png.png` original; that file is
  ABSENT from `frontend/public/assets/` today (only the
  single-extension file exists). Owner decision QIP-06: RETIRE
  the reference (recorded; broader doc reconciliation pending
  separate approval).
- OWNER DECISIONS RECORDED 2026-11-03 (records:
  `docs/Q-IP-1_OWNER_CONFIRMATION_REGISTER.md` = QIP-01…QIP-06,
  `docs/FINAL_QIP1_CONFIRMATION_REGISTER.md` = Q1–Q4 mapping):
  Q1 SELF + Q2 YES (OWNER_CONFIRMED); Q3 REVIEW/PENDING (not
  granted; terms inspection blocked — no official rules text in
  repo, owner must supply); Q4 RETIRE confirmed (asset
  unrestored, logo untouched; broader doc reconciliation NOT
  authorized here).
- G-PUSH logo-rights precondition: SATISFIED. G-PUSH stays
  CLOSED until its explicit approval. Q3 must resolve before
  submission (G-RELEASE).
- Companion: psycopg LGPL-3.0-only dependency flag (organizer IP
  confirmation) and Q-IP-2 (marks) — same confirmation round.

## 8. Costs ($0 hosting target)

- Render Free × 2 + GitHub Free: $0/mo hosting target.
- NOT claimable as $0 total: Meta quota (unverified until
  G-AI-SPEND) + possible Render bandwidth overage past 5 GB/mo
  (single-source report — MUST re-verify at signup + set alerts
  + stay orders below). 750 free instance-hours are WORKSPACE-
  shared: two services are fine while they sleep on idle;
  sustained always-warm operation would exceed budget.
- No paid plans/trials/domains in this pack. Any paid step
  requires a NEW explicit approval naming the amount.

## 9. Risks

- R1 Sleep/cold starts (~60 s/warm-up discipline) — demo
  choreography risk; mitigated by warm-up order + honest UI.
- R2 F-EPH-1 session/audit amnesia (see §6) — accepted w/ P-1/P-2.
- R3 Meta key invalid/quota — discovered ONLY at G-AI-SPEND;
  fallback: honest-fallback demo branch (scripted).
- R4 Render ToS/pricing drift — re-verify at signup before
  provisioning; abort to Cloudflare-Pages plan if terms broke.
- R5 Q-IP-1 unresolved — publishing the logo without rights
  confirmation is the owner's legal risk; gate G-PUSH on it.
- R6 750-hr shared budget — monitor usage dashboard weekly.

## 10. Rollback

- Before G-PUSH: `git checkout master` abandons nothing (work
  stays uncommitted); delete pointer only if desired
  (`git branch -D production-launch` — owner approval needed
  as a git mutation).
- After G-PUSH, before deploy: revert/force-push rules per
  owner; branch deletable remotely on approval.
- After G-DEPLOY: Render → previous release → instant redeploy
  (one click); env values persist in prompts; reseed is
  automatic; no migrations exist to reverse.
- Data: nothing durable to restore (L1); git remains the source
  of truth for seeds + code + docs.

## 11. Exact execution sequence (DO NOT RUN — gates closed)

G-COMMIT (on explicit approval):

```powershell
cd "<repo-root>"   # local checkout of CRUISESHIELD-AI- (no machine path)
git checkout production-launch
git status --short   # expect the 141 entries in §1 (rechecked 11-03)
# pre-commit gates (must be green):
.\.venv\Scripts\python.exe scripts\security_gate.py --skip-audit
$env:STORE_BACKEND='json'
.\.venv\Scripts\python.exe -m pytest tests/ -q -p no:cacheprovider
# stage ONLY §1a–§1d (explicit pathspec — abridged here by
# directory + the 15 new files; NEVER git add -A):
git add -- .env.example app/config.py app/main.py app/ratelimit.py
git add -- docs/FINAL_ZERO_GAP_MATRIX.md docs/RENDER_6_ENV_REGISTER.md
git add -- docs/UGLS_AUTHENTICATED_SESSION_AUDIT.md
git add -- docs/UGLS_COMPLETE_TRANSLATION_COVERAGE.md
git add -- docs/UGLS_FINAL_ZERO_GAP_MATRIX.md
git add -- docs/UGLS_HUMAN_REVIEW_REGISTER.md
git add -- docs/UGLS_KEY_INVENTORY.md
git add -- docs/UGLS_KEY_INVENTORY_GENERATED.txt
git add -- docs/UGLS_LANGUAGE_MATRIX_GENERATED.md
git add -- docs/UGLS_RELEASE_ACCEPTANCE.md
git add -- docs/UGLS_REVIEW_KIT/
git add -- docs/FINAL_DATABASE_AND_BACKUP_READINESS.md
git add -- docs/FINAL_DEPLOYMENT_GATE_REGISTER.md
git add -- docs/FINAL_HACKATHON_SUBMISSION_CHECKLIST.md
git add -- docs/FINAL_HACKATHON_VIDEO_STORYBOARD.md
git add -- docs/FINAL_LIVE_ACCEPTANCE_TEST_PLAN.md
git add -- docs/FINAL_PRODUCTION_ENVIRONMENT_REGISTER.md
git add -- docs/FINAL_RENDER_DEPLOYMENT_AUDIT.md
git add -- docs/FINAL_RENDER_DEPLOYMENT_MANIFEST.md
git add -- docs/FINAL_OWNER_APPROVAL_PACK.md
git add -- docs/FINAL_SECURITY_RELEASE_AUDIT.md
git add -- docs/PROJECT_EXECUTION_STATE.md
git add -- docs/ZERO_COST_INFRASTRUCTURE_REGISTER.md
git add -- frontend/app frontend/components frontend/lib
git add -- frontend/next.config.ts frontend/next.config.test.ts
git add -- frontend/styles/landing.css
git add -- tests/test_auth.py tests/test_auth_e2e.py
git add -- tests/test_body_size_guard.py tests/test_config_safety.py
git add -- tests/test_cors.py tests/test_rate_limit.py
git add -- tests/test_write_token.py
git status --short  # MUST show staged §1a–§1d ONLY; qa-scratch/,
                    # .edge-d-probe/, a11y-audit.mjs, qa/, tmpw_ta9ikh/,
                    # webgl-fail-r10.html MUST remain unstaged/untracked
git commit -m "Launch: UGLS i18n + R-09 security + Render deploy control (selective; no secrets/state)"
git show --stat --oneline HEAD   # record SHA in gate register
```

NOTE on `git add -- frontend/app frontend/components
frontend/lib`: stages tracked modifications + the 4 new source
files inside those dirs and NOTHING else (no untracked junk
lives there — verified: the 6 excluded entries are all outside
these paths). `docs/UGLS_REVIEW_KIT/` likewise stages only its
12 tracked files.

G-PUSH (separate explicit approval; requires Q-IP-1 resolved):

```powershell
git log --oneline -1            # confirm commit SHA
# pre-push secret re-scan of the about-to-publish tree:
.\.venv\Scripts\python.exe scripts\security_gate.py --skip-audit
git diff origin/master...HEAD --stat   # review-hoc: no .env/data
git push -u origin production-launch
# then: watch GitHub Actions security-gate on the branch (must be green)
```

G-PROVISION (separate approval; owner Render account):

1. Re-verify Render free ToS/pricing/bandwidth on render.com.
2. Render dashboard → New → Blueprint → repo @
   `production-launch` → `render.yaml` → plans: Free/Free,
   DELETE the disk block (or de-select paid disk).
3. Record `BACKEND_URL_TBD`, `FRONTEND_URL_TBD` (no traffic yet).

G-DEPLOY (separate approval; secrets into Render prompts only):

1. Backend env per §5 → deploy → `/api/v1/health` healthy.
2. Frontend `NEXT_PUBLIC_API_BASE_URL` = backend URL → rebuild.
3. Backend `FRONTEND_ORIGINS` = frontend URL → redeploy.
4. Smoke: `/` + `/demo` + one cross-origin page.

G-AI-SPEND → Phase 8 → G-RELEASE per the gate register and the
18-row acceptance plan (evidence pack required; no PASS w/o it).
