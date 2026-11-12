# Demo Removal, Production Reuse & Domain Migration Audit

Directive: COMPLETE DEMO REMOVAL, PRODUCTION CODEBASE REUSE &
DOMAIN MIGRATION AUDIT. Date: 2026-11-07. HEAD d82627d.
Prior work reconciled: CRUISESHIELD-AI-DEMO-REMOVAL-MATRIX.md
(G1-G10 dispositions, 2026-11-05) — this audit verifies those
dispositions still hold and covers what came after. No deploy,
push, purchase, DNS, hosting, or credential action taken.

## 1. Demo inventory (classified)

LEGITIMATE_PRODUCTION_FEATURE (retain, no action):
- DEMO_USERS / DEMO_WRITE_TOKEN / NEXT_PUBLIC_DEMO_WRITE_TOKEN /
  demo_viewer identifiers (G1/G10 RETAIN per D-019; deployment
  contract + R2 semantics, not user branding). All app + api.ts
  matches verified to be these identifiers only.
- Deprecated /api/v1/demo/* aliases (G2; removal gated on D-019b
  HOLD — owner decision stands, do not remove).
- app/simulate.py bounded what-if engine (non-mutating, tested).
- payments.py manual-reconciliation stub (PAY-01: live charging
  disabled by construction, live raises). Honest by design.
- Three.js landing scene (procedural geometry only — zero fetch,
  zero network, zero Math.random in scene sources; verified).
  Visual only; carries no simulated metrics.
- loading.tsx ("no fake progress" by comment + implementation).
- Input placeholder= attributes and "synthetic" honesty badges
  (labels that mark synthetic data as synthetic).

SYNTHETIC_PRODUCTION_DATA_RISK (remediated this turn):
- Store reseeds synthetic scenario (txn_84721 ledger, manifest
  carries synthetic_notice) whenever the state file is missing.
  On ephemeral free-tier hosting this meant every cold start
  served seed data as live API content (scenario endpoints
  labeled it; record endpoints did not).
- Fix: CS_ENV production guard (config.is_production; store
  refuses seed-on-missing with RuntimeError; store.reset raises
  PRODUCTION_REFUSED → HTTP 403 via _domain_error; all three
  reset endpoints covered at one chokepoint). Default
  development/staging behavior unchanged. 6 tests green
  (tests/test_production_guard.py). SEC-PROD CLOSED_VERIFIED.
- Owner step: set CS_ENV=production on the production service
  only, with persistent DATA_DIR or database provisioned
  (else boot fails loudly — by design, not silently).

TEST_FIXTURE (retain, isolated):
- tests/test_demo_token_remediation.py, tests/fixtures/
  canonical-state.json, txn_84721/case_84721/inv_84721 IDs in
  tests + tmp_store seeds. Fixtures never touch the deployed
  store (conftest uses tmp paths); production guard now also
  blocks seed paths in prod.

DOCUMENTATION_REFERENCE (retain):
- ~150 live docs + frozen evidence (*-evidence/, qa/,
  responsive-evidence/, rtl-*, HACKATHON_*, SUBMIT_*,
  blueprints, closed logs) — G8 EXEMPT, rewriting falsifies
  records. Root-level evidence dirs are outside frontend/ and
  backend builds (never bundled or served). Manifest rule
  already excludes them from release commits.

PUBLIC_DEMO_CONTENT (owner decision, not removed):
- HackathonRecognitionPanel on the landing page ("Built at the
  Meta Global AI Developer Hackathon", Participant tag, repo
  link). Truthful provenance, not fake functionality — but an
  enterprise face may want it gone. OWNER CALL: retain for
  provenance or remove for enterprise positioning. No action
  taken (hackathon contribution tracking depends on it).

DEMO_ONLY_APPLICATION_FEATURE: none found unaccounted. The
/demo page route is deleted (REL-02 direction); scenario/reset
endpoints are admin-gated platform controls, now prod-guarded.

## 2. Frontend reuse assessment

Reusable as-is: routing (11 page routes), app-shell + login
gate + session snapshot, api.ts client (env-driven base URL),
all intel/investigation/agent/recovery sections, security
headers (CSP tracks build API origin per-env), i18n system,
a11y/responsive patterns, static SITE-01 pages.
Reusable after modification: none identified statically.
Demo-only: none in shipped components (G3/G4 verified held).
Missing: nav wiring for SITE-01 pages (deliberately deferred
to avoid i18n-dictionary churn; pages cross-link each other).
Not tested (execution): all vitest suites (node EPERM;
hosted CI deferred per PKG-01) — contract parity + static
link audit (0 dead) substitute locally.

## 3. Backend reuse assessment

Reusable as-is: all 219 routes (contracts preserved), auth
(PBKDF2/MFA/passkeys/risk/sessions/keyring), tenancy (+D-014
map), detection/graph/investigation/evidence/recovery/agent
engines, telecom/geo adapters (honest NOT_CONFIGURED),
rate limits, validation, audit chain, security headers.
Mocks/sims: only payments stub (documented, tested, live
impossible). Incomplete-but-honest: live provider lanes
(NO-LIVE by decision), PG cutover (HOLD), model lane
(deferred). Nothing requires replacement or duplication.

## 4. Environment separation

DEVELOPMENT (default): CS_ENV unset/development; JSON store
with seed-on-missing; auth open unless SESSION_SECRET set;
localhost origins; mock transports. Current worktree state.
STAGING: same code; SESSION_SECRET + DEMO_USERS armed;
CS_ENV=staging (guard off, behavior = dev); deploy previews.
Owner sets secrets; no prod data.
PRODUCTION (target): CS_ENV=production (refuses synthetic
seed/reset — enforced in code); persistent DATA_DIR or PG
(required); SESSION_SECRET + rotated keyring; DEMO_USERS =
real operator set; FRONTEND_ORIGINS = prod frontend URL;
NEXT_PUBLIC_API_BASE_URL = prod backend URL (rebuild after
set); no demo tokens in frontend (R6 empty); provider
credentials only per handshake approvals; logs/audits
retained per authorized schedule. Never: demo users,
demo tokens in client, synthetic txns, test credentials,
dev/staging data copies.

## 5. Domain migration checklist

No code rewrite needed — all origins are env-driven:
1. NEXT_PUBLIC_API_BASE_URL → new backend URL; rebuild +
   redeploy frontend (build-time baked, incl. CSP
   connect-src which tracks it automatically).
2. FRONTEND_ORIGINS → new frontend URL; redeploy backend
   (CORS single source of truth).
3. NEXT_PUBLIC_SITE_URL → new frontend URL (metadata).
4. Cookies: host-only, no Domain pinning — nothing to change;
   HTTPS keeps Secure+SameSite=None working.
5. OAuth redirect URLs (planned /api/v1/auth/federation/
   callback): register exact new URL in each provider
   console at PKG-09 time.
6. Webhooks (provider interface): re-register receiver URL
   per vendor when a vendor binds.
7. CSP/X-Frame/HSTS: automatic (no host literals except
   the API origin variable).
8. Sitemap/canonical: via NEXT_PUBLIC_SITE_URL.
9. Verify on the real domain: DNS + SSL, backend /health,
   frontend /, one cross-origin authed page, login +
   logout cookie flow, CSP console clean.
NOT done (all owner-gated): registration, DNS, SSL,
hosting changes. Migration is config-only by design.

## 6. Leakage assessment

- .env (MODEL_API_KEY key-shaped, untracked) +
  .env.arming.local (local arming secrets, untracked):
  both gitignored, never committed; secret scans PASS.
  MODEL_API_KEY presence-only True locally; value never
  read; NO-LIVE stands (validity untested, untestable
  without approval). Owner: confirm key provenance.
- qa-scratch/data/state.json: TRACKED dev runtime state
  (pre-existing). Recommend owner rule: untrack/ignore at
  release (left untouched — needs owner call).
- No passwords/PINs/CVVs/private keys/seed phrases in
  source (scans + matrix SEC rows).
- Test fixtures cannot reach prod: tmp-path stores +
  production guard double barrier.

## 7. Changes, tests, gaps

Files modified: app/config.py, app/store.py, app/main.py,
.env.example (+tests/test_production_guard.py new,
scripts/zero_gap_matrix.py SEC-PROD row + AI-01 evidence,
decision log D-016 refinement).
Tests: 6 guard + seed/map regression 24/24 green; full
suite fresh 1374 passed / 142 skipped / same sandbox-only
1F+2E (node EPERM + 2x WinError 10013, identities verified).
Gaps/owner actions: hackathon panel keep/remove;
qa-scratch tracking rule; .env key provenance;
CS_ENV=production + persistent storage at deploy;
domain purchase/DNS (never by agent).
