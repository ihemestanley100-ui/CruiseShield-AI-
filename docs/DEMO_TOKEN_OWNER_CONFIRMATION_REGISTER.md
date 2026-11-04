# DEMO TOKEN — OWNER CONFIRMATION REGISTER (R5 / R6)

Date: 2026-11-03 · Status: OWNER-APPROVED, recorded verbatim.
This register authorizes DOCUMENTATION + LOCAL VERIFICATION
only. It does not open G-COMMIT, G-PUSH, G-DEPLOY, or G-RELEASE.

## R5 — BACKEND TOKEN (APPROVED)

- Backend `DEMO_WRITE_TOKEN` MUST be a securely generated
  value, stored exclusively as a server-side secret.
- Documented: generation (`secrets.token_urlsafe(32)`),
  configuration (Render env prompt, never files/chat),
  rotation (regenerate → redeploy backend; frontend
  unaffected under R6-empty), revocation (unset ⇒ see
  limitation L1), verification (anonymous write → 401).
- NEVER exposed via frontend code, browser responses,
  logs, or any `NEXT_PUBLIC_*` variable.
- Limitation L1 (disclosed, accepted by proceeding):
  code default is "" (open local demo, test-locked);
  production-mandatory is enforced at the G-DEPLOY gate,
  not fail-closed in code. A code fail-closed change
  needs a separate approval (proposed R7, not started).

## R6 — PUBLIC FRONTEND TOKEN (APPROVED)

- `NEXT_PUBLIC_DEMO_WRITE_TOKEN` stays EMPTY in the public
  frontend deployment. No public write-token fallback.
- All frontend write operations use authenticated login
  (session cookie + CSRF header, existing mechanism).
- Verified 11-03: clean build EXIT=0 with var unset; 0
  probe remnants; 0 value-bearing `Bearer` literals (one
  dead `""!==f` branch carries the scheme word only);
  0 sourcemaps; tsc 0; vitest 366/366.

## Boundaries (standing)

No staging, commit, push, deploy, provisioning, prod env
changes, credential rotation, or AI quota spend under
this register. Next approval required for any of those.
