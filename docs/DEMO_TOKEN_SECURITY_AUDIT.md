# DEMO TOKEN SECURITY AUDIT — CruiseShield AI™

Date: 2026-11-03 · Method: read-only code inspection + proof build.
Scope: `NEXT_PUBLIC_DEMO_WRITE_TOKEN` (frontend) ↔
`DEMO_WRITE_TOKEN` (backend). No live writes, no quota spent.

## Verdict: FAIL (impact bounded to synthetic demo scope)

The public token reaches admin-restricted demo controls,
can burn the daily AI quota, reset shared demo state,
and forge audit actor names. No real-customer data,
session minting, or secret access is exposed. Small,
named fixes are required before release (see
Remediation Plan). This FAIL is about privilege anomaly
+ integrity, not about data breach (none possible —
store is synthetic-only).

## 1. Lifecycle (traced end to end)

- Declared: `app/config.py:43` (server env, default ""),
  `frontend/.env.example:6` + `.env.example:11` (docs).
- Frontend reads it once: `frontend/lib/api.ts:227` in
  `postJson` — attached to EVERY frontend POST as
  `Authorization: Bearer <token>` (omitted when empty).
- Backend validates with `hmac.compare_digest` against
  `DEMO_WRITE_TOKEN` (`app/main.py:233-242`).
- YES, values must be identical (exact-match compare).
- No other transport (no cookie, no body field).
- Never logged: only reference to the `authorization`
  header is the comparison read (`main.py:239`); error
  bodies carry codes, never credentials.

## 2. What the token grants (verified per route)

Middleware (`main.py:105-142`): when auth is armed, any
non-open path requires SOME credential; `kind=="token"`
passes the login gate but SKIPS the entire session block
(admin check, CSRF check, role-permission check). Route
handlers never consult `request.state.auth_role`.

Consequences (all verified in source):

| # | Capability | Evidence |
|---|---|---|
| 1 | Full READ of every authenticated GET (cases, audit, evidence, AI runs, graph…) | No handler checks role; token passes middleware |
| 2 | Admin-bypass on `/api/v1/demo/*` (admin-only for sessions) incl. `demo/reset` | `AUTH_ADMIN_PREFIXES` checked only inside `kind=="session"` |
| 3 | Write via 8 `_require_write_token` POSTs (demo×3, AI×2, simulations, decisions, events) | Gated list verified by AST |
| 4 | AI quota burn up to `AI_DAILY_CALL_LIMIT` (429 after) | `_run_ai` cap check `main.py:793-803` |
| 5 | Shared-demo reset (availability; recoverable by reseed) | `demo_reset` → `store.reset` |
| 6 | Audit actor forgery (free-form `actor_id` ≤256ch from body) | `post_decision` 995 + `cases.py:51-52,62` |
| 7 | Event injection (schema-validated, deduped, first-wins, no overwrite) | `store.py:208-222` |

What it canNOT do: mint sessions or log in (login
needs `DEMO_USERS` credentials; token irrelevant);
obtain roles; read env/secrets; touch non-synthetic
data (none exists); bypass rate limits (600/min/IP,
`ratelimit.py:19-20`); bypass AI daily cap.

## 3. Frontend exposure (PROVEN by proof build)

Build with dummy value `PROBE-NOT-A-SECRET-SSA9SK`
(EXIT=0): the literal appears verbatim in 8 build
outputs, including browser-delivered
`.next/static/chunks/app/**` page bundles. Any visitor
can extract it via DevTools/view-source in seconds and
replay it with curl — no frontend needed. Sourcemaps:
0 shipped (good). HTML: value not present (good).
Code itself documents this: "PUBLIC shared-demo
credential (baked into client chunks)" (`api.ts:223-226`).

## 4. Open-when-unconfigured (critical deploy note)

`_require_write_token` returns OPEN when backend
`DEMO_WRITE_TOKEN` is empty (`main.py:257-259`, test
`test_open_when_unconfigured`). If Render leaves it
empty, all 8 write POSTs are world-open with NO
credential at all. Backend value MUST be set.

## 5. Findings register

- F-PRIV-1 (HIGH, bounded): token bypasses admin gate
  on demo paths — anonymous browser exceeds non-admin
  login. Fix required.
- F-AUDIT-1 (MEDIUM): self-asserted `actor_id` lets
  token users sign decisions as anyone (e.g. "judge").
  Fix required.
- F-QUOTA-1 (MEDIUM): token can exhaust the 100/day AI
  budget (feature-DoS on demo day). Mitigate.
- F-AVAIL-1 (LOW): token can reset shared demo mid-judge
  (one-click recovery). Mitigate or accept.
- F-CONSIST-1 (LOW): evidence-package POST has no gate
  (harmless today — read-only alias of GET). Harden.

## 6. Tests as intent evidence

`tests/test_write_token.py` (8 tests: open-when-empty,
exact match, 401/403 paths, session equivalence) +
`frontend/lib/api.test.ts:329,354` (header sent/omitted).
Intent "either credential satisfies the gate" is
explicit — the admin-bypass interaction is the gap the
tests never covered.

## 7. Re-audit addendum (2026-11-03, R1–R4 implemented)

Re-verdict: **PASS WITH LIMITATIONS**.

- F-PRIV-1 CLOSED: demo/* requires genuine admin session;
  token → 403 ADMIN_REQUIRED (tests R1×6).
- F-AUDIT-1 CLOSED: token decisions attributed
  "demo-token" server-side; forged "judge" eliminated
  from record + audit (tests R2×4).
- F-QUOTA-1 CLOSED: AI endpoints require login session in
  armed mode; token → 403 AI_LOGIN_REQUIRED; unarmed
  local dev unchanged (tests R3×4).
- F-CONSIST-1 CLOSED: evidence POST gated (tests R4×3).
- F-AVAIL-1 CLOSED as a consequence of R1 (reset is
  admin-only now).
- Full backend suite: 420 passed / 73 skipped (17 new
  tests); gate script: pip_audit PASS (0 vulns),
  secret_scan PASS (lock/pip_check fails are system-env
  drift, unrelated to this change).
- Extraction remains trivial BY DESIGN (public demo
  credential, documented). Residual: token keeps
  synthetic-only reads + validated, rate-limited,
  attributed writes (simulations/events/decisions).
  R6-empty (no frontend value ⇒ login-required writes)
  remains the lowest-risk posture option.

## 8. R5/R6 verification addendum (owner-approved 2026-11-03)

Decisions recorded in `DEMO_TOKEN_OWNER_CONFIRMATION_REGISTER.md`.

| # | Check | Verdict | Evidence |
|---|---|---|---|
| V1 | Frontend correct with var empty | PASS | Clean build EXIT=0 (var unset); tsc 0; vitest 366/366 (68 files); `api.test.ts:354` locks header-omitted |
| V2 | No backend-token exposure (source/bundle/maps/HTML/API) | PASS | Frontend refs only `NEXT_PUBLIC_*` (api.ts:227 + tests); 0 probe remnants; 0 value literals (dead `""!==f` branch); 0 maps; secrets used only for compare/sign/outbound (`app/` grep 11-03); gate secret_scan PASS |
| V3 | Login-only writes + auth regression | PASS | Backend 420/73 green incl. 17 R1–R4 tests; session write paths pass; anon/token-denied paths 401/403 per matrix |
| V4 | Backend token mandatory, never empty/predictable | PARTIAL | Mandatory at G-DEPLOY gate (must-set + anon-401 verify, documented); code default "" retained for local-open (test-locked). Code fail-closed needs separate R7 approval |

Resulting posture: public reads + login-gated writes; no
public credential exists to extract. Threats T1–T3 stay
closed; T4 (token writes) is now UNREACHABLE without a
login session on the public deployment.
