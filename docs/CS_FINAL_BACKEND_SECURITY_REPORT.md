# CS FINAL — BACKEND SECURITY REPORT (CS-FINAL-EXECUTION-010)

Date: 2026-11-03 · Code: `ff7052b` · Live: UNARMED (see §4).

## R1–R4 (local: TESTED — 17 remediation + 61 subset green)

- R1: token → 403 ADMIN on `/api/v1/demo/*`; admin session
  required. R2: token decisions forced `demo-token`.
  R3: AI needs login (`AI_LOGIN_REQUIRED`, armed only).
  R4: evidence POST gated. Rate limits, validation, audit,
  RBAC, HSTS/CSP intact.

## Arming instructions (owner executes in dashboard)

Run LOCALLY (values never leave your machine except into
Render prompts; never paste into chat):

1. `SESSION_SECRET`: run
   `python -c "import secrets;print(secrets.token_urlsafe(32))"`
   → paste output into backend env (must be 32+ chars).
2. `DEMO_USERS`: for each login run
   `python -m app.auth provision <username> <role>`
   (roles: `investigator`, `admin`, `auditor`,
   `demo_viewer`; password typed blind) → join lines with
   commas, no spaces → paste. Minimum: one `admin` (for
   demo resets) + one `investigator` (for judges).
3. `DEMO_WRITE_TOKEN`: fresh `secrets.token_urlsafe(32)`
   output → backend ONLY. Never into any frontend var.
4. Save → Render redeploys automatically.

## Post-arming verification (Muse resumes)

- `/api/v1/auth/mode` must read `true`; health 200.
- Then safe R1–R4 probes: anonymous 401s, token 403s on
  demo/AI paths, session flows — synthetic only, no
  resets, no AI quota (auth-gate behavior only, never
  past the gate to the provider).

## Current live posture (UNARMED — not releasable as-is)

- `auth_enabled:false`: all guards inert, all writes open
  to the internet. This is the documented local default,
  now public. Arming is MANDATORY before release; R1–R4
  live are NOT_TESTED until then (probing now would
  mutate shared state — withheld by rule).
