# PHASE 10 — SECURITY FINDINGS REGISTER

PROGRAMME: CSAI-MASTER-RELEASE-001 | PHASE: 10 (Security & Reliability)
PRODUCT: CruiseShield AI™ — The Financial Crime Immune System™
DATE: 2026-11-01 | HEAD: 0eaaaf5 (master, uncommitted work preserved, no commit/push)
PERSISTENT STATE (pre/post): SHA-256 BA1D4DB4…3790FE, 101417 bytes, case NEW, 0 decisions — unchanged.

Severity scale: CRITICAL / HIGH / MEDIUM / LOW / INFORMATIONAL (no formal external certification claimed).

## Closed in Phase 10 (fixed + retested)

### SEC-001 — Unbounded free-text inputs persisted (state-bloat / abuse) — HIGH → CLOSED
- Component: POST /api/v1/cases/{id}/decisions (reason, recommendation, actor_id), POST /api/v1/simulations (assumption, ignored_edge_ids).
- Reproduction (pre-fix): a 2 MB `reason` was accepted and persisted; state file grew to ~4 MB (reason + audit echo). Persistent file was restored byte-identical from a hash-verified candidate (BA1D4DB4…3790FE).
- Fix: `MAX_REASON_CHARS=10000`, `MAX_ACTOR_ID_CHARS=256`, `MAX_RECOMMENDATION_CHARS=10000` in `app/cases.py`; `MAX_ASSUMPTION_CHARS=10000`, `MAX_IGNORED_EDGES=10000` in `app/simulate.py`. Violations raise ValueError → HTTP 400 (`_domain_error`, `app/main.py`).
- Tests: new backend tests pin every cap (reason/actor/recommendation/assumption/edge-count).
- Live retest (2026-11-01, disposable DATA_DIR backend :8004, current code): 20000-char reason → `400 {"code":"REASON_TOO_LONG"}`; 20000-char assumption → `400 {"code":"ASSUMPTION_TOO_LONG"}`; valid control decision → 200 (disposable copy 101417→102356 B; persistent unchanged).
- Residual: no inbound rate limiting (see SEC-003); caps bound size, not frequency.

### SEC-002 — Silent reseed on missing state file (data-loss masquerading as healthy start) — MEDIUM → CLOSED
- Component: `Store.__init__` (`app/store.py`).
- Previous behaviour: missing `state.json` silently seeded a fresh demo.
- Fix: emits `RuntimeWarning: state file <path> missing; seeding fresh demo state` (visible on uvicorn stderr) before seeding.
- Tests: new test asserts the warning fires on a missing path.
- Live retest (2026-11-01, empty DATA_DIR backend :8005): warning present on stderr naming the exact path; health 200; fresh seed written (72972 B, correctly ≠ pristine 101417 B).
- Note: backend suite now reports 136 warnings (intentional fresh-store tests); no `-W error` policy, suite green.

### SEC-005 — CI security-gate push trigger never fires (wrong branch) — LOW → CLOSED
- Component: `.github/workflows/security-gate.yml` (`branches: ["main"]`, actual branch `master`).
- Fix: trigger changed to `["master"]` (one word). PR + weekly-schedule triggers already covered the gate; push coverage restored.
- Verified: no test pins workflow content; gate remains read-only, secret-free (pip-audit via public OSV, hash-pinned lock install).

## Open / accepted limitations (demo-grade, owner decision required for pilot/prod)

### SEC-003 — No inbound API rate limiting — MEDIUM → OPEN (accepted for demo)
- Evidence: no ratelimit/slowapi/throttle code in `app/*.py`.
- Impact: brute-force/flood abuse possible if exposed beyond localhost demo. SEC-001 caps bound payload size, not request frequency.
- Recommendation: add per-IP/per-key throttling + request-size limits at reverse proxy or middleware before any network exposure (Phase 15 gate).

### SEC-004 — No API authentication / authorisation — MEDIUM → OPEN (accepted for demo)
- Evidence: no OAuth2/JWT/API-key/session code in `app/*.py`; all endpoints anonymously callable on localhost.
- Impact: any local process/user can read demo data and (on a writable store) record decisions. No horizontal/vertical escalation surface exists because there are no identities — but also no protection.
- Recommendation: demo-only on loopback; authN/authZ design required before pilot (Phase 15 gate). No auth capabilities invented or claimed.

## Informational / verified-clean

### SEC-006 — Secret handling — INFORMATIONAL → VERIFIED CLEAN
- Scan 2026-11-01 (repo-wide, excl. .venv/node_modules/.git/.next, patterns for API keys/tokens/private keys): only false positives — `sk-` substring inside `risk-intelligence…` / `risk-badge` (already documented in prior audit).
- `.env` and `data/state.json` are git-ignored (`git check-ignore` confirms); `.env.example` holds names only; backup workflows reference `${{ secrets.* }}` with no echo of values; CI security gate needs no secrets.
- Pinned by passing tests: `tests/test_secret_safety.py` (gitignore, example-names-only, state-has-no-secrets). No secret values printed or logged.

### SEC-007 — Dependency vulnerabilities — INFORMATIONAL → PASS_WITH_LIMITATIONS
- `requirements.txt` pins were lifted with CVE annotations (FastAPI 0.133.0, starlette 1.3.1, anyio 4.14.2, urllib3 2.8.0, idna 3.15, certifi 2026.10.19); installed `.venv` versions verified equal to pins.
- Hash-pinned `requirements.lock` exists; CI installs with `--require-hashes`.
- LIMITATION: live `pip-audit` scan NOT_VERIFIED (no-install policy in this environment); CI gate runs it on push/PR/weekly once pushed.

### SEC-008 — CORS / request validation — INFORMATIONAL → PASS_VERIFIED (via tests)
- `app/config.py::cors_options()` is the single source of truth (explicit origins incl. localhost dev, credentials off, methods GET/POST/OPTIONS, headers Content-Type/X-Request-ID); `FRONTEND_ORIGINS` env-overridable; covered by `tests/test_cors.py` (passing).
- Domain errors return structured `{error:{code,message,trace_id}}` with 400/404/422 mapping; unknown-transaction/edge/case rejected (live 404s observed on probes).

## Not verified (blocked / out of scope)
- NV-01: `tmpw_ta9ikh/` contents unscannable (OS permission denied) — unreferenced by code, left untouched.
- NV-02: Live hostile prompt-injection against the paid Meta API NOT_RUN (no approval for adversarial live spend); adapter-level validation tests pass (`tests/test_ai_validation.py`), incl. evidence-ID grounding rules.
- NV-03: Formal penetration test / external certification — not performed, not claimed.
