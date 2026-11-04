# CRUISESHIELD AI — SECURITY ACCEPTANCE REPORT (J3)

**Verdict:** ACCEPTED for protected-demo scope with documented limitations.

## Verified controls (all test-backed)

- Login/logout, HMAC sessions (12 h, stateless), PBKDF2 210k, roles
  investigator/admin, demo-route admin fence, CSRF header for
  cookie POSTs, login throttle, credentialed CORS (armed-only,
  explicit origins), Secure cookie incl. TLS-proxy honor (J3-P2).
  Tests: `test_auth.py` (20), `test_cors.py` (8), gate suites (8).
- Session-expiry re-gating (J3-P6): 401/403 anywhere re-checks `/me`.
- Rate limits (600/min/IP), login throttle (10/min/IP), 1 MB body cap
  (413), request validation, error-envelope discipline (no leakage).
- Secrets: 4 clean scans (gate, J1 extended, staged, committed-object);
  `.env` ignored + excluded; examples names-only; workflows names-only.
- Supply chain: pinned + hashed lockfiles both tiers; pip-audit clean;
  headers baseline (nosniff/DENY/referrer/permissions) both tiers.

## Documented limitations (not defects at demo scope)

- No CSP (Three.js inline); shared demo credentials, manual rotation;
  single-worker rate limits; Content-Length-only body metering;
  Secure-cookie localhost exception by design.
- `.gitignore` hardening awaits D2 approval (no exposure today).

## Residual risks

- Live-secret handling discipline at staging (owner procedure).
- Hosted-tier behavior (WAF/edge) unverified until staging deploy.
