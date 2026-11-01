# PHASE 10 — REMEDIATION MATRIX

PROGRAMME: CSAI-MASTER-RELEASE-001 | PHASE: 10 | DATE: 2026-11-01 | HEAD: 0eaaaf5 (no commit/push)

| ID | Severity | Status | Fix (files) | Test evidence | Live retest | Residual / owner action |
|---|---|---|---|---|---|---|
| SEC-001 | HIGH | CLOSED | `app/cases.py` caps (10000/256/10000), `app/simulate.py` caps (10000/10000) | New backend cap tests pass; suite 293 passed / 68 skipped / 0 failed | :8004 disposable: oversized reason→400 REASON_TOO_LONG, oversized assumption→400 ASSUMPTION_TOO_LONG, valid control→200; persistent hash unchanged (BA1D4DB4…3790FE, 101417 B) | Frequency abuse still possible → SEC-003 |
| SEC-002 | MEDIUM | CLOSED | `app/store.py` RuntimeWarning on missing state file | New warning test passes | :8005 empty DATA_DIR: warning on stderr with path; health 200 | Warning noise in intentional fresh-store tests (136 warnings, no `-W error`) — accepted |
| SEC-005 | LOW | CLOSED | `.github/workflows/security-gate.yml`: push branch main→master | No test pins workflows; YAML trigger-only change | N/A (CI-side; PR+schedule triggers already live) | None |
| SEC-003 | MEDIUM | OPEN (demo-accepted) | None (design decision) | N/A | Confirmed absent (code grep) | Owner: add throttling before any network exposure (Phase 15 gate) |
| SEC-004 | MEDIUM | OPEN (demo-accepted) | None (design decision) | N/A | Confirmed absent (code grep) | Owner: authN/authZ design before pilot (Phase 15 gate); run demo on loopback only |
| SEC-006 | INFO | VERIFIED CLEAN | None needed | `tests/test_secret_safety.py` passes | Repo-wide pattern scan: only `risk-*` false positives; .env + state.json git-ignored | None |
| SEC-007 | INFO | PASS_WITH_LIMITATIONS | Pins lifted w/ CVE notes (pre-existing P2.2A) | Installed == pinned (pip list verified) | Live pip-audit NOT_VERIFIED (no-install policy); CI gate covers post-push | Owner: review CI audit output after push |
| SEC-008 | INFO | PASS_VERIFIED | None needed (pre-existing) | `tests/test_cors.py` passes | Structured 400/404/422 errors observed live | None |

Regression after all Phase 10 changes (2026-11-01): backend 293 passed / 68 skipped / 0 failed; frontend typecheck clean, 233/233 vitest (exit 0 on re-run after transient exit-1 flake), production build exit 0. Frontend untouched by Phase 10 edits.
