# PHASE 2B — REMAINING GAPS

**Date:** 2026-10-31 · Status after Phase 2B recovery: code-complete;
evidence-complete except R-11 (single-shot observation).

## Closed in Phase 2B

- Validator banned-score/enforcement/human-approval guards (+4 tests).
- Greedy sampling pinned + recorded (+1 test); seed intentionally not sent (documented).
- Production build proven (exit 0, clean dir); real-browser smoke rendered all routes;
  landing visually verified with working WebGL.

## Closed in recovery (post-interruption, same day)

- R-01 · RE-HASHED `data/state.json`: `BA1D4DB4BB4D…C8043453790FE`
  (full: `BA1D4DB4BB4DBC6FC3ACA346664A539610CCC6460CCD530F523C8043453790FE`),
  101417 B — byte-identical before and after every smoke run (GET-only traffic).
- R-02 · DELETED `frontend/.next-dev/` (90 MB untracked dev-server output).
  Verified still absent after recovery runs (dev servers used default `.next/`).
- R-03 · SMOKE ANALYSIS COMPLETE: 8/8 screenshots inspected, DOM assertions
  18/18 PASS, console triage PASS (7/8 clean; landing favicon.ico 404 only).
  Root cause of the earlier 0-byte DOM/console files diagnosed and documented
  (one-shot CLI stdout loss; CDP capture used instead).
- R-06 · STANDARD BUILD PASS: `npm run build` in `frontend/` → exit 0 in
  98.6 s. All 7 routes, 103 kB shared JS, static pages 5/5. The `.next/trace`
  lock observed earlier is gone; no workaround needed. (Build output is
  git-ignored under `frontend/.next/`.)

## Closed in logo integration (approved, same day)

- R-04 · FIXED: label sprite base height 0.28 → 0.18 world units
  (`scene/shared.ts`); regression test pins scale in `scene.test.ts`;
  verified smaller at 1440/768/390 px production screenshots.
- R-05 · FIXED: "Sound: Off" clip was the Next.js dev-mode indicator
  overlapping the button (dev-only overlay, absent in production).
  Verified fully visible in production screenshots; `.landing-audio`
  given `flex-wrap` hardening.
- R-11 · CLOSED AS NOT-A-DEFECT: hero wraps cleanly with no clipping at
  390, 768, and 1440 px in production screenshots; earlier clip was a
  loading-state artifact of the one-shot CLI capture.
- Logo: user-supplied original integrated via byte-identical copy
  (`cruiseshield-logo-original.png`, SHA-256 `1A0CC66B…C32A623`);
  original `.png.png` file untouched (same hash); 69×73 intrinsic dims
  match the 1219×1290 aspect exactly; renders verified in landing nav
  and app shell with zero logo 404s.

## Standing user-side items (unchanged)

- R-07 · Push approval → real CI execution → deploy approval → public URL.
- R-08 · Live rehearsal → screenshots → recording → video (+ perf numbers, FP narration).
- R-09 · Internet-exposure hardening decision (demo-mode guards) if a public URL is wanted.
- R-10 · Live Meta API follow-up call at demo time (needs key + network); fallback verified.

## Out of scope (unchanged)

AuthN/Z, tenancy, production backup schedules, 30-day reliability, GPS, paid providers,
global search UI (R13-C), production migration. Next authorized step (if any): rehearsal
prep — NOT started (STOP condition respected). Nothing committed, pushed, deployed,
purchased, or reset in recovery; no source files changed (docs only).
