# FINAL SECURITY AUDIT (R05–R09)

Date: 2026-11-02. HEAD `d4e2bec`. Method: repo security gate + fresh
scans + live browser/container verification. No secrets are reproduced
in this report (locations only, values never).

## Verdicts

| Area | Status | Evidence |
| ---- | ------ | -------- |
| Repo security gate (`scripts/security_gate.py`) | PASS | Exit 0: 16 pins locked exactly; 37 pins installed exactly; 463 hashes; pip check clean; pip_audit zero open vulns; secret_scan clean. Log: `security-gate-r09.log` |
| Secret scan: history + tracked + bundles (R06) | PASS | 280 location-hits triaged, all benign (var-name plumbing, `[REDACTED]` prose, marked fixtures, redaction code). Zero hits in git history patches; zero in built `.next` chunks; live `.env` untracked + gitignored (names only: META_BASE_URL/META_MODEL_ID/MODEL_API_KEY). Generated logs scanned clean. Script + log: `secret-scan-r06.py`, `secrets-r06.log` |
| Python dependencies (R09) | PASS | pip-audit initially: 12 vulns in build-tool `pip` 25.2 only (no runtime findings). Remediated: pip 25.2→26.2.2 (venv-local). Re-audit: **no known vulnerabilities**. Logs: `pip-audit-r09*.log` |
| JS dependencies (R09) | PASS_WITH_LIMITATIONS | `npm audit`: 2 vulns (1 moderate + 1 high), both transitive `postcss` via next 15. Fix requires breaking major (next 16). ACCEPTED EXCEPTION: postcss touches only first-party CSS at build time (no user-CSS input; production serves compiled CSS). Remediation: revisit at next planned Next major upgrade. Log: `npm-audit-r09.log` |
| AuthN/Z + sessions (R05) | PASS (code + tests) | J4 suite green within backend 463/463 (`test_auth.py`, `test_auth_e2e.py`); open-demo/live CORS verified in Edge (ACA-C fix, `tests/test_cors.py`); secure headers pinned by `next.config.test.ts`; rate-limit/CSRF covered by unit tests. Armed-mode live login not exercised (no staging) — covered under Deployment |
| CSP + browser security (R07) | PASS | Policy shipped in `next.config.ts` (connect-src tracks build API origin; no wildcard; `object-src 'none'`, `frame-ancestors 'none'`), pinned by new unit test. Live: header verified + **8/8 routes CLEAN** (zero violations/JS errors) in Edge 156. `unsafe-inline` for scripts/styles documented as accepted (Next bootstrap + init scripts; React escaping + XSS suite primary). Script: `csp-qa-r07.ps1`, build log `build-csp-r07.log` |
| Container (R08) | PASS | `docker build` exit 0 (hash-pinned lock). Runtime: healthy 200 (self-seeded, no live data mounted), runs as non-root `appuser` (new), PORT-aware HEALTHCHECK (R17 fix — probes `$PORT`, verified healthy on PORT=8001), `docker stop` clean, image removed after. Dockerfile hardened (non-root + healthcheck). Logs: `docker-build-r08.log`, `docker-build-r17.log` |
| AI prompt-injection boundaries | PASS | Hermetic validation suite green (mock transports, no quota spend); evidence-as-untrusted-data design; see AI verification doc |

## Accepted limitations / exceptions

1. postcss HIGH (transitive, build-time only) — accepted, revisit at Next major upgrade.
2. CSP `unsafe-inline` (scripts/styles) — accepted, nonce infra is future work.
3. No live staging auth exercise — gated on deployment approval (R02).
4. npm audit covers prod+dev tree as installed; lockfile consistent (`npm run build` reproducible, exit 0).

## What was NOT done

No penetration test, no fuzzing beyond the existing suites, no secret
rotation (none exposed), no dependency upgrades except venv pip. No
production-readiness claim is made on security alone (see gate
decision).
