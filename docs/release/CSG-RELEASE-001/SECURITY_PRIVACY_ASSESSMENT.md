# CSG-RELEASE-001 — Security & Privacy Assessment

Verdict basis: inspected configuration, committed controls, and the
passing suite (backend 1,431 + frontend 473). No control was weakened
for this release; no new integration was added.

## Verified controls

- Secrets: hosted Gitleaks PASS on `e099b7a` (fingerprint-pinned
  historical ignore, no allowlist expansion); local spot-check of
  `app/`, `frontend/lib`, `frontend/app` found zero genuine secrets
  (10 `sk-` English-word false positives only).
- CSRF/CORS: F-D1/F-D2 committed — CSRF on all unsafe methods, CORS
  explicit-origin + PUT/PATCH preflight; covered by
  `tests/test_csrf_methods.py`, `tests/test_cors.py` (green hosted;
  2 local errors are sandbox socket-bind restrictions, WinError 10013).
- AuthN/Z: session-secret-gated login that fails closed with honest
  503 `AUTH_DISABLED` when unconfigured; RBAC/ABAC/tenant isolation
  covered by the passing backend suite (`test_auth.py`,
  `test_verify.py`, governance and tenancy tests).
- Security headers: configured in `frontend/next.config.ts`, pinned
  by `frontend/next.config.test.ts` (passing).
- Rate limiting / retention: implemented in `app/` with dedicated
  tests (`test_rate_limit.py` and others, passing).
- Masking / no-names: UFI-PARTY restriction preserved (D-2); CS-FCA-013
  `.01/.02` carry no identity-resolution behavior.
- Human authority: UI copy and the new framework card state human
  investigator decision authority; no automatic enforcement path
  exists in the reviewed tree.

## CS-FCA-013 data classes

Registered records distinguish verified / provider-supplied /
estimated / inferred / unavailable; `.11/.13/.14` are
structure-only (D-3, NO-LIVE); no identity or exact location is
derivable from IP alone anywhere in the implementation.

## Open items (carried, not waived)

- F-CSG-002: `npm audit` reports 5 dev/build-toolchain findings
  (vitest/tinypool/postcss); none executes in the production bundle
  or handles untrusted input. Documented accepted risk pending a
  post-release update cycle with full retest.
- Local secret scanning binary unavailable; authoritative gate is
  hosted Gitleaks on push (required before merge).
