# 4. SECURITY REMEDIATION REPORT (staging scope)

DATE: 2026-11-01 | POLICY: implement only safely testable controls; design + defer the rest with rationale. No fake claims.

## Implemented + tested (this programme)
- SEC-009 body-size guard: 1 MB Content-Length cap → 413 envelope + trace_id (`app/main.py`, 6 tests incl. boundary/malformed/missing; live 1.1 MB → 413). Limitation: header-present bodies only; chunked relies on proxy limits.
- SEC-010 secure headers both surfaces: backend middleware + frontend `next.config.ts` (nosniff/DENY/strict-origin-when-cross-origin/camera-mic-geo-off). Tested (backend unit) + live-verified (both surfaces). No CSP (Three.js inline scripts; needs nonce design — documented, not skipped silently).
- Prior standing: SEC-001 caps, CORS single-source, enveloped errors, secret hygiene (gate PASS), AI validators, audit append-only.

## Gap-closure 11-01 (implemented + live-verified after this report)
- SEC-011 (D-001 CLOSED for single-instance scope): per-IP fixed-window throttle, 600 req/min, health/ready exempt, 429 envelope + Retry-After (`app/ratelimit.py` + middleware; 6 unit tests; live flood: 600 pass → 50×429, health stays 200). Limits: in-memory (single instance), XFF-spoofable key — documented in module.
- SEC-012 (D-002 narrowed to low-assurance demo control): shared write token — unset = open local demo (unchanged); set = 8 POST endpoints require the credential (401 otherwise), reads stay open; frontend sends it on POSTs only when `NEXT_PUBLIC_DEMO_WRITE_TOKEN` set (PUBLIC-by-design shared credential). 6 backend + 3 frontend tests; live 401/401/200/200. Reads stay anonymous by design.
- D-005 CLOSED: live red-team 3/3 refused (`docs/REDTEAM_LIVE_AI_REPORT.md`).

## Still deferred (need owner/institutional decisions — NOT implemented)
- Real authentication/authorization + roles (OAuth2/OIDC users, per-route guards) and CSP (nonce design around Three.js): dedicated workstreams.
- Verdict: staging may proceed as a DEMO-HOSTING surface with throttle + write-token + headers active (owner accepts low-assurance model). Production MUST NOT proceed without real auth + CSP + shared-store rate limiting + the remaining institutional gates.

## Residuals (unchanged, restated)
No inbound auth/rate-limit; chunked-body proxy reliance; no CSP; append-only-not-tamper-evident audit; single-instance store.
