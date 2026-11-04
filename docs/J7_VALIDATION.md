# J7 — SECURITY, RELIABILITY AND PERFORMANCE VALIDATION

## A. Application security matrix

| Area | Result | Evidence |
|------|--------|----------|
| Auth/sessions/roles | PASS | J4 (PBKDF2, HMAC+revoke+epoch, 4 roles, perms, E2E) |
| CORS/CSRF/cookies/headers | PASS | suites green; Secure+proxy; Lax; XRW; baseline headers |
| CSP | DOCUMENTED GAP | none (Three.js inline) — production blocker, demo accepted |
| Input validation | PASS | 400/404/413/422 matrix, direct + transport twins |
| Output encoding/XSS | PASS | esc() node test (green unsandboxed) + secret-HTML tests |
| SQL injection | PASS | %s params everywhere; f-string SQL takes internal constants only (`LOAD_ORDER`, reconcile maps); live quote-escape probe → None, no error |
| SSRF | PASS | single outbound client, fixed owner-env base URL + constant path; no user input in URLs |
| Path traversal | PASS | no user-derived file paths (fixed STATE_PATH/tmp/.env) |
| Uploads | N/A | no upload endpoints |
| Rate limiting/body cap | PASS | 600/min IP, login 10/min, 1 MB 413 |
| Error leakage | PASS | envelope `{code,message,trace_id}`; no tracebacks/keys |
| Secrets | PASS | scans clean; hermetic-test fixture (see incident note) |
| Dependencies | PARTIAL | 37 pins + 463 hashes + pip_check green; OSV lookup offline |
| Container | PARTIAL | Dockerfile reviewed (slim, no-cache, PORT-aware); image never built (engine was blocked until J-series; build untested) |
| Logging/audit | PASS | append-only audits incl. auth events; log redaction tested |

## B/C. API + workflow

Every route: valid/invalid/unauth/forbidden/malformed/oversize/
duplicate/concurrent covered by twins + suites (459 backend green).
Workflow DETECT→AUDIT proven end-to-end (judge flow + auth E2E).
Deterministic scores authoritative; AI evidence-grounded, cannot
set scores/guilt/authorize; human decisions recorded + audited.

## D. Frontend

266/266 + tsc + build green; loading/empty/error/401/403/404/429/
500 states asserted; role gating (J4); WebGL fallback tested.
NOT_VERIFIED: real browsers, screen readers, real devices (FE-35).

## E. Performance (local-only; targets declared first)

Targets: reads p50 < 50 ms, writes < 100 ms, startup < 2 s.
Observed (`scripts/perf_smoke.py`): seed 15 ms; reads ≤ 0.02 ms;
audit-append 3.4 ms. All inside targets by >10×. Not measured:
hosted latency, cold starts, frontend load paint, RSS (no psutil),
load beyond demo (8-thread PG reads green; no soak test).

## F. Failure matrix (every failure has a safe outcome)

DB down → 503/degraded (tested) · pool N/A (no pool; conn-per-op
+ Neon pooler URL) · AI down/quota/invalid → 503 codes + fallback
(tested) · client abort → 35 s (tested) · session expiry → re-gate
(tested) · restart → state+revocations persist (tested) · refresh →
login re-check (unit; browser NOT_VERIFIED) · dup submit → ingest
idempotent; decisions append (both audited, acceptable) · migration
interrupted → single-txn rollback (tested live) · restore tamper →
fail closed (tested).

## Incident note (disclosed)

Two inadvertent live Meta calls occurred during J-series
unsandboxed full-suite runs (pre-existing socket-gated test
expected 200 with the owner’s `.env` key loaded). Both succeeded
— incidental live-integration evidence — but spend was unapproved.
Fixed the same turn: autouse key-clearing fixture makes every
test hermetic; the test now asserts hermetic 503. No recurrence
possible via the suite.
