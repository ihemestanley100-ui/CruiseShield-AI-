# PHASE 2B — TECHNICAL ACCEPTANCE REPORT

**Date:** 2026-10-31 · **Scope:** validator hardening, sampling determinism, CI checks,
build, browser smoke, routes, demo journey. Narrow fixes only; no rebuilds.

## Objective 1 — Intel AI banned-score/enforcement gap: CLOSED
- **Investigation:** `validate_model_output` (`app/ai_adapter.py`) ignored unknown fields, so a
  model-invented `risk_score` passed VALIDATED; enforcement language unchecked; the DI-only
  `human_review_status` field does not exist in the main schema.
- **Fix (additive, fail-closed):** validator now rejects top-level + per-finding
  `BANNED_SCORE_FIELDS`, per-finding `ENFORCEMENT_PHRASES`, and any suggested next step
  without `requires_human_approval: true` (the main-schema equivalent of the DI human-review
  gate). Constants shared via import from `app/intel_ai` — no duplication, no cycles.
- **Files:** `app/ai_adapter.py`, `tests/test_ai_validation.py` (+4 tests: score fields,
  enforcement phrases, approval gate, greedy temperature).
- **Verification:** `tests/test_ai_validation.py` 33/33 pass. One pre-existing Phase-2A test
  expectation updated to the stronger contract (banned-field gate now fires before the
  evidence-ID check — earlier fail-closed, documented in-test).

## Objective 2 — Sampling repeatability: CLOSED (with documented bound)
- **Investigation:** no `temperature`/`seed`/`top_p` was sent — provider defaults applied.
  Tests already use deterministic mock-transport fixtures (no seeds required there).
- **Fix:** `REQUEST_TEMPERATURE = 0` sent on analysis + follow-up bodies and recorded on the
  run for provenance. Provider `seed` deliberately NOT sent (non-portable, unknown-param 400
  risk — the adapter already carries one such fallback).
- **Bound:** live outputs are more deterministic, not guaranteed stable; validation remains
  the determinism backstop. Test pins temperature==0 and absence of `seed`.

## Objective 3 — CI checks executed locally: PASS (2 unavailable, reported)
- `scripts/security_gate.py`: **GATE PASS 6/6** (pins, hashes, pip check, pip-audit clean,
  secret scan).
- Backend `pytest tests/`: **289 passed / 68 skipped / 0 failed** (skips = PG-live without
  scratch DB; `STORE_BACKEND=json` as in CI).
- Frontend `tsc --noEmit`: exit 0. Frontend vitest: **204/204**, 46 files, exit 0.
- `npm ci` (fresh-install proof): SKIPPED — disproportionate tree churn for zero signal about
  these changes; lock integrity already enforced by the gate's hash check.
- `gitleaks` action: UNAVAILABLE — no binary installed, no install approval; gate's own
  secret-scan passed instead. Real GitHub Actions execution still needs push approval.

## Objectives 4–5 — Build + browser smoke
- **Build:** `next build` **exit 0** to a clean output dir (all 7 routes, 103 kB shared JS).
  The standard `.next/` path remains blocked by another process's lock on `.next/trace`
  (standard-path attempt hangs; see PHASE_2B_BUILD_VERIFICATION.md). Temp config reverted;
  `tsconfig.json` restored; `.next-verify/` deleted.
- **Browser smoke:** real headless Chrome against live backend (8123) + frontend (3110):
  all 6 routes + 2 mobile viewports rendered, exit 0. Landing screenshot visually inspected:
  brand/logo/hero/panels/Earth/brain/orbitals/modules/CTA/controls all render; WebGL works.
  Two P2 visual notes: region label sprites oversized vs globe; audio control text possibly
  clipped at bottom-left (single-viewport evidence — needs confirmation, not yet a defect).
  DOM-assertion + console-log analysis was cut short by a shell-runner outage — see
  PHASE_2B_BROWSER_SMOKE_TEST.md. No scene tuning changed on partial evidence.

## Objectives 6–10 — Routes, access, landing, responsive, journey
- Route table (build output): `/`, `/demo`, `/cases/[caseId]`, `/investigations/[id]`,
  `/network/[txnId]`, `/replay/[scenarioId]` — all compile; all 6 served 200 + rendered in
  headless Chrome. Deep-link spot assertions (risk 35/84, 39/22/30, SIMULATED) pending the
  DOM re-analysis pass (artifacts on disk).
- Public demo access: no-registration flow confirmed reachable at `/` → `/demo` in the
  smoke run; mutating endpoints unchanged (reset/decision/ingest still open locally —
  the previously reported internet-exposure hardening still awaits approval).
- Landing + logo + responsive: landing visually verified desktop; mobile screenshots
  captured but not yet inspected (runner outage).

## Regression + integrity
- Full suites after final edit: backend 289/68/0, frontend 204/204 exit 0, tsc 0, gate 6/6.
- `data/state.json` (`BA1D4DB4…3790FE`, 101417 B) unchanged at last check; smoke traffic was
  read-only page loads (no POST-driving clicks). Final re-hash + `.next-dev/` cleanup are
  queued for shell recovery (see REMAINING_GAPS).
- Risk engine, DI workstream, Three.js scenes, logo asset, routes, records: untouched.
- Nothing committed, pushed, deployed, or purchased.

## Recovery addendum (2026-10-31, post-interruption)

- R-01 CLOSED: `data/state.json` re-hashed after every smoke run —
  `BA1D4DB4…3790FE`, 101417 B, byte-identical throughout.
- R-02 CLOSED: `frontend/.next-dev/` (90 MB untracked) deleted; still absent.
- R-03 CLOSED: fresh CDP-driven smoke run — 8/8 screenshots inspected, DOM
  assertions 18/18 PASS, console triage PASS (one favicon 404 disclosed).
  Root cause of the earlier empty DOM/console files diagnosed (one-shot CLI
  stdout loss) and documented in PHASE_2B_BROWSER_SMOKE_TEST.md.
- R-06 CLOSED: standard `npm run build` exit 0 in 98.6 s (see
  PHASE_2B_BUILD_VERIFICATION.md).
- New single-shot observation R-11 (mobile hero clip) plus confirmed R-04/R-05
  recorded in PHASE_2B_REMAINING_GAPS.md; no tuning without approval.
- Regression spot-check in recovery: `tests/test_ai_validation.py` 24 passed /
  9 skipped / 0 failed. No source files changed in recovery (docs only).
  STOP after Phase 2B respected.
