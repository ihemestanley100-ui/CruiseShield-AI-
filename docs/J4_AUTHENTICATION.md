# J4 — AUTHENTICATION, AUTHORIZATION AND SESSION SECURITY

**Status:** implemented + verified (backend + frontend + E2E).
Evidence: `tests/test_auth.py` (J4 block), `tests/test_auth_e2e.py`,
`tests/test_pg_parity.py::test_j4_revocation_epoch_parity`,
`frontend/lib/session.test.tsx`,
`frontend/components/decision-form.test.tsx` (role gating).

## Role / permission matrix (canonical)

| role | read | audit_read | ai_run | write | manage |
|------|------|------------|--------|-------|--------|
| admin | ✓ | ✓ | ✓ | ✓ | ✓ |
| investigator | ✓ | ✓ | ✓ | ✓ | — |
| auditor | ✓ | ✓ | — | — | — |
| demo_viewer | ✓ | — | — | — | — |

Enforced in `session_guard` per request (`_required_perm`) and
defense-in-depth in `_require_write_token`. Token credentials keep
legacy demo access (documented demo-only). No frontend-only control.

## Sessions

- HMAC-SHA256 stateless tokens, 12 h TTL, unique nonce (`n`) +
  issued-at (`iat`) per token; PBKDF2-HMAC-SHA256 210k passwords.
- Logout revokes the nonce server-side (`revoked_sessions`, expiry
  GC); logout-all bumps the user epoch (`user_epochs`, timestamp).
- Live validation rejects: bad signature, expiry, revoked nonce,
  pre-epoch token, deprovisioned user, changed role.
- Revocation/epochs persist on BOTH backends (JSON keys +
  `session_revocations`/`user_epochs` tables), survive restart and
  demo reset, never migrate across environments.
- Rotation/fixation: every login mints a fresh token; login never
  honors a client-presented token (tested).
- Cookies: HttpOnly, SameSite=Lax, Secure on HTTPS incl. TLS-proxy
  detection; CSRF header required for session POSTs; login throttle
  10/min/IP; generic 401s;auth.login/logout/logout_all audited
  (failures not audited: spam vector — rationale recorded).

## Demo provisioning (owner, local only)

`python -m app.auth provision <username> <role>` prompts for the
password and prints one `name:role:hash` line for `DEMO_USERS`.
No default passwords exist in code or docs. Treat `.env` as secret.

## Boundaries (not claimed)

- Shared demo credentials, manual rotation, no tenant isolation,
  single worker, no CSP (Three.js) — unchanged demo scope.
- `demo_viewer` cannot read audit trail or run AI (cost + oversight).
- Tests are hermetic: autouse fixture clears `MODEL_API_KEY` so no
  test can spend quota (two inadvertent live calls during J-series
  unsandboxed runs disclosed in J7/R4 evidence; recurrence blocked).
