# CS-STAGE1-COMPLETE-001 — Baseline Evidence Report

Date: 2026-11-12. Candidate line: `feat/phasezero-foundations`.
Program worktree evidence home: `docs/release/CS-STAGE1-COMPLETE/`.

## Frozen baseline (verified, not assumed)

- Branch: `feat/phasezero-foundations` (no upstream configured).
- Local HEAD: `3cbbb48abad26d8215c8ef6b23545a13b3713f01` (ERD-001 closeout).
- Production base: `b4732cb12e8991885975a9ff402e47c6e64c97fc` (untouched).
- Local master: `753a6c5` (untouched).
- Index: empty. Stash: empty.
- Remote-tracking `origin/feat/phasezero-foundations`: `3cbbb48`
  (cache; live remote unverifiable from sandbox).
- PR #2: open/unmerged per owner record (live state unverifiable
  here); target `production-launch`, source `feat/phasezero-foundations`.

## Protected states (must survive the programme)

- 12-file translation sync: intact, 12 files +13/−1,
  EN_KEYS 608→609, one `system.gapsOk` row per locale TSV.
  NOT to be staged/committed without separate authorization.
- `tests/test_pg_parity.py`: stat-noise only, zero content diff.
- 12 untracked user paths: preserved, never deleted/repurposed.
- All commits immutable (no amend/rebase/reset/clean/stash).

## Prior verified evidence incorporated by reference

- CS-ERD-002 audit: D-1/A-1/C-1/E-1 code verified; backend
  1456P/145S/sandbox-only 1F+2E; ruff/matrix/manifest green.
- CS-ERD-004: push-scope 41 files clean; security-gate is the
  only push-triggered workflow (tests/build, no deploy path).
- CS-ERD-006C/D: 12-file sync replicated + integrity-audited;
  canonical node execution BLOCKED in sandbox (owner/hosted only).
- No app/test/config modification exists in the worktree beyond
  the recorded states above (workstream 1 verification).
