# CRUISESHIELD-AI-REPOSITORY-FORENSIC-AUDIT.md

Phase Zero forensic audit of the existing CruiseShield AI™ repository.
Method: 6 parallel read-only researchers (R1 backend-core, R2 data-auth,
R3 frontend-live, R4 threejs-deploy, R5 ai-detection, R6 quality-ops) +
1 independent critic + synthesis. Every verdict below is backed by an
inspected file body, never by grep alone. Live servers (:3000/:8000) were
not touched; no network, install, build, deploy, or GitHub action was run.

Audit date: 2026-11-05. HEAD at audit time: `b4732cb` (dirty worktree).
Critic verdict: **no hard inter-report contradiction**; all cross-checks
are 2–3-way consistent. Deltas are complementary coverage only.

Classification key: IMPLEMENTED_TESTED / IMPLEMENTED_UNTESTED / PARTIAL /
MISSING / SIMULATED (honestly labeled decoration) / BLOCKED (by design).

## 1. Backend core (R1) — app/main.py, app/config.py, app/auth.py

API surface: **42 routes = 3 HTML pages + 39 JSON**, all JSON under
`/api/v1/*` (`app/main.py:31-1144`). `APP_VERSION = "1.0.0-p0"`
(`app/main.py:33-35`). No v2 or unversioned JSON route exists.
IMPLEMENTED_TESTED.

- Pages: `GET /` command center (351-361),
  `GET /investigations/{inv_id}` (364-388),
  `GET /system-health` (391-395).
- Health/readiness: `GET /api/v1/health` (413-436),
  `GET /api/v1/ready` (457-471), `_pg_check` (439-454, never leaks
  connection info). Blocking checks: store, seed_integrity,
  graph_provenance, storage_backend; `model_configured` and non-selected
  `pg` are non-blocking. IMPLEMENTED_TESTED.
- Auth (5): login (488-536, 503 disabled/misconfigured, 429 rate limit,
  401 audited, sets `csai_session`), logout (539-554), logout-all epoch
  bump (557-573), me (576-583), mode (586-588). IMPLEMENTED_TESTED.
- Demo control (4, admin-gated when armed): scenarios, reset, start,
  judge-start (591-628). IMPLEMENTED_TESTED.
- Transactions/intel (12): base txn, DI-03 devices, DI-04 ip-obs, DI-05
  geo-obs, DI-06 txn/acct/inv intel, DI-07 overlay, DI-08 risk-intel
  (flag-gated), DI-09 intel-evidence (flag-gated), graph, risk?scope
  (632-788). IMPLEMENTED_TESTED.
- Alerts/notifications (3): alerts, notifications GET (per-caller read
  state, cap 200), notifications/read POST (791-861). IMPLEMENTED_TESTED.
- Investigations/evidence/AI (6): investigation GET, evidence-package
  POST alias + GET, ai-analysis, ai-followup, ai-runs GET (864-1016).
  IMPLEMENTED_TESTED (mock-transport).
- Replay/simulation/cases/events (7): replay, simulations, cases list,
  case get, decisions POST (token→`demo-token` attribution), case audit,
  events ingest (1020-1144). IMPLEMENTED_TESTED.
- Cross-cutting: body_size_guard 1 MB → 413 (45-71), session_guard
  fail-closed 503 + 401/403/CSRF/permission/admin-prefix (89-148),
  rate_limit_guard per-IP window + Retry-After (151-169), CORS explicit
  origins + credentials + `Content-Type/X-Request-ID/X-Requested-With`
  (177 + `app/config.py:108-132`), AppError envelope + domain 404
  mapping (305-320). All IMPLEMENTED_TESTED.

Config surface (`app/config.py:7-159`): DATA_DIR/STATE_PATH, MODEL_API_KEY
(server-only, "" = unconfigured), META_MODEL_ID `muse-spark-1.3`,
META_BASE_URL `https://api.meta.ai/v1`, DEMO_WRITE_TOKEN, SESSION_SECRET
(≥32 chars arms login), DEMO_USERS `name:role:pbkdf2$…` CSV, AI caps
(daily 100, timeout 30, max-output 4096, all fail-safe), FRONTEND_ORIGINS
explicit allowlist (never `*`), STORE_BACKEND validated default `json`,
DATABASE_URL (never logged), PG_CONNECT_TIMEOUT 5. `.env` loader never
overrides real env, returns names only. IMPLEMENTED_TESTED.

Entry points: ASGI `app = FastAPI(...)` (`app/main.py:35`); canonical
`python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`
(`Dockerfile:26`, README.md:72, docs/DEPLOYMENT.md:13).

Dockerfile (1-26), render.yaml (13-104), requirements.txt (16 pins) +
requirements.lock (37 pins / 463 hashes): complete and coherent,
IMPLEMENTED_UNTESTED (no asserting test body inspected; install not run).

## 2. Data, auth, audit, backups (R2)

- JSON store (ACTIVE backend): atomic tmp+replace under `_save_lock`,
  deterministic reseed preserving login (`app/store.py:46-162`).
  IMPLEMENTED_TESTED.
- Backend selection: STORE_BACKEND validated, default json
  (`app/config.py:143-154`, `app/store.py:19-39`). IMPLEMENTED_TESTED.
- PostgreSQL adapter: PgStore mirrors JSON interface, per-access
  materialized state, single-txn mutations, advisory-lock audits
  (`app/db.py:177-656`); DDL 5.1.0 full-document JSONB
  (`app/models_pg.py:14-163`). Live-PG tests need SCRATCH_DATABASE_URL
  and skip explicitly otherwise — never false-green.
  IMPLEMENTED_TESTED (scratch-verification only).
- Production PG cutover: MISSING (by design). App always boots
  `Store()` (`app/main.py:182`); no production caller of
  open_store/PgStore; `pg` selection affects only health/ready probes.
- Migration safety: loader refuses live `data/state.json` (41-47),
  SHA-256 gate (52-55), single atomic transaction with rollback
  (404-431), 7 reconcile gates incl. counts/FK/risk/audit-seq/
  package-hash/meta (321-401), L4 DDL-in-txn, L6 fail-closed.
  IMPLEMENTED_TESTED.
- Auth: HMAC-SHA256 cookie sessions, 12h TTL, PBKDF2 210k
  (`app/auth.py:54-135`); 4 roles + least-privilege PERMISSIONS +
  `can()` (35-52); logout revocation + logout-all epochs on BOTH
  backends; login 10/min + audited failures; weak-secret 503.
  Wart: `actor_role` hardcoded `"INVESTIGATOR"` (`app/cases.py:63`).
  IMPLEMENTED_TESTED.
- CSRF: cookie POSTs require `X-Requested-With` (`app/main.py:129-137`);
  token-authed exempt; CORS allowlists the header. IMPLEMENTED_TESTED.
- Rate limiting: in-memory fixed-window 600/min/IP, login 10/min,
  10k buckets, health/ready exempt; documented single-instance-only.
  IMPLEMENTED_TESTED.
- Audit logging: PARTIAL. 9 append_audit call sites; sequential
  audit_NNNN + counter; PG seq UNIQUE + contiguous check. Explicitly
  NOT hash-chained (non-claim pinned by tests); JSON audits are
  plaintext file records. Demo-forensics sufficient, not tamper-proof.
- Backups: code IMPLEMENTED_TESTED (CSBK1 X25519+NaCl envelope,
  minisign chained manifests, producer snapshot→encrypt→sign→upload→
  verify, restore verifies+decrypts and never writes any DB; socket-free
  fakes). Execution BLOCKED by design: all 3 workflows header-disabled
  manual dispatch + reviewers; no keys/connections; restore returns a
  plan only (`backups/restore.py:8-10`).
- data/ + .gitignore + seed: data/* + .env + keys ignored; data/ holds
  only .gitkeep (state.json runtime-generated); deterministic seed +
  seed_hash; secret-safety pinned by tests. IMPLEMENTED_TESTED.

## 3. Frontend live bindings (R3)

- Routes are live-bound by code call-graph (no network-trace run):
  landing `/` static (`frontend/app/page.tsx:1-5`); `/demo` live loaders
  (health/investigation/graph/case/audits/replay); `/investigations/[id]`
  +evidence+intel; `/cases/[caseId]` +audit; `/network/[txnId]`
  graph+overlay; `/replay/[scenarioId]` scenarios+replay.
  IMPLEMENTED_TESTED.
- API client (`frontend/lib/api.ts`): credentialed GET with timeout +
  ApiError (119-144), credentialed POST with CSRF header (248-301),
  auth mode/me/login/logout (965-997), UNAUTHORIZED_EVENT (60-67).
  Key never in browser (`api.ts:4`). IMPLEMENTED_TESTED.
- Auth gate: login-gate mode check + fail-open + re-gating + LoginCard;
  app-shell keeps landing public and gates chrome; useCan role gating.
  IMPLEMENTED_TESTED.
- Components live: notifications list + mark-read, decision-form,
  ai-panel analysis + followup, simulation-panel baseline + post,
  replay-controls stepping. IMPLEMENTED_TESTED.
- i18n: registry BCP47 fallback, persisted LocaleProvider
  (browser+URL override), dictionary lookup + missing-key ledger,
  searchable listbox selector. IMPLEMENTED_TESTED.
- a11y/responsive: skip link, focus-visible, reduced-motion,
  breakpoints 1024/640, error/loading/404 boundaries; a11y suite is
  jsdom-level only by its own header. IMPLEMENTED_TESTED.
- `.env.example`: public base URL only, no secrets. IMPLEMENTED_TESTED.
- Critic missing-scope (verified, no report disputes): 9 backend routes
  have NO frontend client (txn base GET, accounts-intel — the only DI
  route without a client — ai-runs GET, events POST, cases list,
  demo start, demo judge-start, ready, evidence-package POST alias);
  5 clients dead outside tests (getDevice, getIpObservations,
  getGeoObservations, getTransactionIntel, listAlerts — api.test.ts
  covers them, no page/component calls them).

## 4. Three.js visuals, graph provenance, deploy wiring (R4)

- Landing composition, scene builders (earth/brain/network/orbital/
  stars/shared), GlobeController + controls + keyboard:
  IMPLEMENTED_TESTED (rotation rates 0.05/0.09 rad/s, label size,
  disposal, hub tagging, drag/zoom/select/reset clamps).
- GlobalHeroScene live canvas (loop, gestures, context-loss):
  IMPLEMENTED_UNTESTED — jsdom has no WebGL, only fallback tested;
  live path covered only by manual browser evidence.
- Landing hero "network" (8 hard-coded REGION_HUBS `earth.ts:46-55`,
  brain-to-earth beams, satellites): SIMULATED and honestly labeled
  ("Decorative visualization", "Illustrative objects/signal").
- GraphExplorer/OrbitalExplorer/GraphTable/CommandNetworkPreview:
  IMPLEMENTED_TESTED and record-backed — render exactly supplied
  nodes/edges; filters hide only; orbital layout explicitly
  non-semantic; preview is a deterministic 12-node subset with honest
  counts. AmbientBackground decorative ("No data shown").
- Graph provenance chain (genuinely data-driven): store.state
  (synthetic_flag seed) → GET /api/v1/graph + validate_provenance
  (`app/main.py:767-777`) → getGraph (`api.ts:378-386`) → network page
  + explorers; overlay merges render-side, best-effort.
- Assets: 8 files real bytes, manifest + icons tests, immutable logo.
  next.config headers/CSP: connect-src tracks build API origin by
  construction; standard SSR (no output/export). IMPLEMENTED_TESTED.
- render.yaml frontend service: wiring correct (rootDir, npm ci+build,
  start $PORT, health /, pinned node, build-time API URL, empty write
  token). IMPLEMENTED_UNTESTED.
- netlify.toml: PARTIAL stale — publish=.next with no Next/OpenNext
  plugin; SSR app incompatible with static hosting; Render canonical.

## 5. AI, detection, replay, approval boundaries (R5)

- Provider integration: live-capable httpx POST /chat/completions,
  Bearer [REDACTED] server-side, temp 0, json_object
  (`app/ai_adapter.py:232-239,436-441`); config META_MODEL_ID
  `muse-spark-1.3`. Tests MockTransport-only; MODEL_API_KEY unset
  (len 0) so live calls fail fast MODEL_NOT_CONFIGURED; frontend key
  never in browser; 35s client abort > 30s server timeout.
  IMPLEMENTED_TESTED (mock-transport; live call never executed).
- Schemas/validation: in-prompt schema cs-prompt-v2, follow-up variant
  with untrusted-question quoting; critical-field gate, banned score
  fields, evidence-ID allowlist, enforcement-phrase ban,
  requires_human_approval gate, conclusion enum; refusal/truncation/
  malformed mapping with bounded 2000-char excerpt. TESTED.
- Retries/timeouts: 429/502/503/504 ×3 with (1.0,2.0) delays;
  timeouts/connect fail fast; single response_format-400 fallback;
  429→RATE_LIMITED, 401/403→AUTH_FAILED. TESTED.
- Usage caps: daily cap incl. restarts (0 disables) → 429 audited, no
  run persisted; max-output 4096 sent on analysis + follow-up. TESTED.
- Detection: 8 versioned rules R-001..R-008 (weights 5–15),
  score=min(100,12+Σ), bands LOW/MOD/HIGH/CRIT; full traceability
  RuleResult → evidence items → package sha256 → evidence_ids_sent
  allowlist → validated citations; seed manifest pins expected results.
  TESTED (incl. 200× determinism, boundary 39999999/40000000).
- DI-03..DI-09 + risk-v2-candidate: TESTED, flag-gated, NullProviders
  report UNKNOWN, v1 scores pinned (35 txn / 84 net).
- Replay/simulation: cursor-sorted clamped replay; sim caps + guards,
  filtered recompute, never mutates baseline. TESTED.
- Human approval: advisory-only prompt, requires_human_approval gate,
  enforcement-language ban; AI persists run+audit ONLY (risks/rules/
  evidence/cases byte-identical); decisions human-only via 5-label
  state machine with token→demo-token attribution. TESTED.
- Failure behavior: 11 explicit fail-closed codes; diagnostics bounded,
  never the key; injection quoting + hostile-output rejection. TESTED.
- Model eval / golden AI tests: MISSING. Only rule determinism +
  recorded latencies + mock fixtures; no live quality/drift check.

## 6. Quality, CI, docs, secrets (R6)

- Backend tests: 46 files (critic: 47 test_*.py on disk — drift to
  settle), 518 collected; isolated Store + TestClient + hermetic
  key-strip + snapshot guard; skipif-only gating, never silent; no
  pytest config file exists. IMPLEMENTED_TESTED.
- Frontend tests: 72 first-party files, 0 skips, jsdom + RTL, API
  boundary mocked per-file; a11y jsdom-level only. TESTED.
- CI gate: security-gate.yml (push master/production-launch, all PRs,
  weekly) → hash-locked install + 6-check gate script (unit-pinned) +
  pytest + gitleaks + npm ci + tsc + vitest + next build; local 6/6
  PASS log (37 pins/463 hashes, pip-audit clean). GitHub dispatch
  itself unobserved. TESTED (local).
- Backup workflows: PARTIAL — logic tested with fakes; yml dispatch
  never exercised (by design).
- Deploy pipeline: PARTIAL — Dockerfile + Blueprint + runbook complete;
  manual only; never executed (owner-gated).
- Docs: PARTIAL — 312 files, headline chain internally consistent,
  honest staleness framing; tree outgrew last full-run logs; one LIVE
  conflict: RENDER_6_ENV_REGISTER.md:23 says the public demo token is
  the "same value as backend token" vs R6 LEAVE-EMPTY rule
  (render.yaml:95-100) — needs one-line correction.
- Manifests: TESTED — hash-locked backend + locked frontend,
  gate-enforced; npm 2 advisories documented-deferred.
- Secrets: TESTED — ignores verified by execution, names-only
  examples, gate + gitleaks + unit tests, hermetic strip, sync:false,
  bundle carries token NAME only.
- Coverage measurement: MISSING — no pytest-cov / vitest coverage /
  codecov config anywhere.
- qa/ + qa-scratch/: evidence store only, not suites.

## 7. Preserved unresolved items (all reports, verbatim-carried)

R1: no test body inspected for Dockerfile/render.yaml; no install or
live :3000/:8000 probes (read-only); RISK_INTELLIGENCE_V2_ENABLED flag
provider outside R1 scope. R2: scratch-PG live pass unexecuted;
off-repo backup keys unknown. R3: no live-backend run (call-graph
only); explorer/landing bodies unopened by R3 but opened by R4
(critic: complementary). R4: live-WebGL render, Netlify serve
behavior, Render dashboard state uninspected. R5: none. R6: GitHub
dispatch greenness, current-tree green run, Netlify deployability
unverified. Critic: 46/47 backend-file drift; logout-all implemented
but omitted from one enumeration (incomplete, not false); 9 unwired
routes + 5 dead clients (see §3).
