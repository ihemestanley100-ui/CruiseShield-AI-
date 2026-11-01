# PHASE 10 — SECURITY AND RELIABILITY REPORT

PROGRAMME: CSAI-MASTER-RELEASE-001 | PHASE: 10 (Security & Reliability Certification)
PRODUCT: CruiseShield AI™ — The Financial Crime Immune System™
DATE: 2026-11-01 | EXECUTION: local, evidence-driven, safe tests only
GIT: HEAD 0eaaaf5 (master), 92 working-tree entries preserved; NO staging/commit/push/merge/tag.
STATE: persistent `data/state.json` SHA-256 BA1D4DB4…3790FE (101417 B), case NEW, 0 decisions — verified identical before and after all Phase 10 work. All write probes ran against disposable TEMP copies.

Companion docs: `docs/PHASE_10_SECURITY_FINDINGS_REGISTER.md`, `docs/PHASE_10_REMEDIATION_MATRIX.md`.
No formal external security certification is claimed.

## 1. Scope and method
INSPECT → BASELINE → GAP REGISTER → IMPLEMENT → TEST → VERIFY → DOCUMENT → GATE.
Sections 10.1–10.8 of the master directive mapped below. Safe authorised probes only (localhost, disposable stores, size/hostility-bounded); no destructive, external-spend, or visibility-changing actions.

## 2. Results by directive section
- 10.1 Authentication — NOT_APPLICABLE (no login/session/token code exists; verified by grep). No authN invented or claimed. Absence is itself the finding (SEC-004).
- 10.2 Authorisation — NOT_APPLICABLE as implemented (no roles/identities); demo-accepted limitation SEC-004. Default-deny N/A; localhost-only operation recommended.
- 10.3 API security — PASS_WITH_LIMITATIONS. Verified: structured domain errors (400/404/422 + trace_id), input caps added+live-verified (SEC-001), CORS single-source + tests (SEC-008), unknown IDs rejected. Missing: rate limiting (SEC-003), request-size limits at server level, authN/authZ (SEC-004). No SSRF/path-traversal/deserialisation sinks found in inspected routers (JSON-only bodies, no file-path inputs, no pickle/eval).
- 10.4 Secret management — PASS_VERIFIED (SEC-006). MODEL_API_KEY server-side only (`app/config.py`, never logged); `.env`/state git-ignored; example names-only; workflows use `${{ secrets.* }}` without echo; secret-safety tests pass; repo-wide value scan clean (only `risk-*` false positives). No values printed.
- 10.5 AI prompt-injection — PASS_WITH_LIMITATIONS. Adapter validation tests pass (evidence-ID grounding, schema checks); evidence treated as untrusted data in prompts. Live hostile-injection run NOT_RUN (no approval for adversarial live spend) — NV-02.
- 10.6 Audit integrity — PASS_WITH_LIMITATIONS. Decisions append case transition + audit event atomically (atomic tmp-write+replace in `Store._save`); actor/timestamp/rationale/evidence-viewed recorded. Immutability NOT claimed (JSON file store, no tamper-evidence); acceptable for demo, flagged for pilot.
- 10.7 Dependency security — PASS_WITH_LIMITATIONS (SEC-007). CVE-annotated pins installed exactly; hash-pinned lock + CI `--require-hashes` gate (push trigger fixed, SEC-005). Live pip-audit NOT_VERIFIED locally.
- 10.8 Reliability — PASS_WITH_LIMITATIONS. Verified: missing-state warning + fresh seed (SEC-002, live stderr proof); provider/model failures degrade to structured errors (fallback paths covered by tests); atomic writes; health/ready endpoints. NOT_VERIFIED under chaos: DB-unavailability (N/A — file store), prolonged provider outage drill, disk-full behaviour.

## 3. Changes implemented in Phase 10
1. `app/cases.py` — input caps (SEC-001) + tests.
2. `app/simulate.py` — input caps (SEC-001) + tests.
3. `app/store.py` — missing-state RuntimeWarning (SEC-002) + test.
4. `.github/workflows/security-gate.yml` — push trigger main→master (SEC-005).
5. Docs: this report + findings register + remediation matrix.

## 4. Verification summary (2026-11-01)
- Backend: 293 passed, 68 skipped, 0 failed (24s). Skipped ≠ passed; counted separately.
- Frontend: typecheck clean; vitest 233/233 (48 files; transient exit-1 flake, exit 0 on re-run); production build exit 0.
- Live probes (disposable backends :8004/:8005, current code): 400 REASON_TOO_LONG, 400 ASSUMPTION_TOO_LONG, 200 valid-control (disposable +939 B), RuntimeWarning on stderr for missing state, health 200s.
- Owned test processes stopped; ports 8004/8005 confirmed free. Pre-existing :8000–:8003 session backends left untouched.

## 5. Acceptance
Phase 10 outcome: 3 findings CLOSED with test + live evidence; 2 demo-accepted MEDIUM limitations (rate limit, authN/authZ) carried to Phase 12 gates / Phase 15; 0 CRITICAL/HIGH open. Security posture is DEMO-ADEQUATE, NOT production-certified.
