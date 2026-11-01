# PHASE 13 — NEW-WORK CONTRIBUTION REGISTER (delta C-15…C-16)

PROGRAMME: CSAI-MASTER-RELEASE-001 | PHASE: 13 | DATE: 2026-11-01
BASE: `docs/HACKATHON_NEW_WORK_CONTRIBUTION_REGISTER.md` (C-01…C-14, all in-window, T1/T3). This file records ONLY the delta since that register. Same timestamp basis (T1 committed / T3 mtime; all post-Oct-28 work uncommitted, HEAD 0eaaaf5). "Eligible" = evidence supports in-window creation, NOT an organizer ruling.

## C-15 · Product UI/UX Phases 4–8 — 11-01 (T3)
- Files: investigation/case pages, application shell, command activity, feature cards, workflow strip, system status, audit list, decision form, demo page, global styles + associated tests (see `docs/PRODUCT_UIUX_PHASE_4_TO_8_COMPLETION_REPORT.md`).
- Before: Phase 3.x rehearsal state. New/material: case/investigation workspace completion, network+replay UX, evidence/audit readability, responsive+accessibility verification, full regression.
- Meta AI use: none directly (UI over existing backend AI endpoints).
- Tests: frontend 233/233 (48 files), backend 289/68/0 at that point, build exit 0, 69/69 browser matrix.
- Eligible: YES (T3).

## C-16 · System acceptance + security + performance + release evidence (Phases 9–12) — 11-01 (T3)
- Files: `app/cases.py` + `app/simulate.py` (SEC-001 input caps + tests), `app/store.py` (SEC-002 reseed RuntimeWarning + test; PERF-001 save lock + failing-first regression test), `tests/test_seed_reset.py` (+2 tests), `.github/workflows/security-gate.yml` (SEC-005 branch fix), `docs/KNOWN_LIMITATIONS.md` (reconciliation), `docs/PHASE_9…PHASE_12_*` (11 reports/registers/matrices).
- Before: unbounded decision/simulation inputs (2 MB reason persisted); silent reseed; dead CI push trigger; concurrent-write 500s (WinError 32).
- New: all four fixed with test + LIVE retest proof (400 REASON_TOO_LONG / ASSUMPTION_TOO_LONG; stderr warning; 10/10 post-fix race); perf baseline (API p50 3 ms, pages ~1 s); 69/69 matrix 2nd re-run (0 console errors); release gates + defect register.
- Meta AI use: none (no new live calls; boundaries re-verified from existing artifacts).
- Tests: backend 294/68/0 (final), frontend 233/233, build exit 0 (49.7 s).
- Eligible: YES (T3).

## Standing notes (unchanged from base register)
- Commit-hardening weakness persists: everything after `0eaaaf5` (10-28) is uncommitted — timestamps rest on mtimes. No commits made (owner decision; Q-NEW-1).
- Pre-event baseline unchanged: sole pre-Oct-26 artifact remains the V5.0 spec text (disclose as input, not code).
- Full register = C-01…C-14 (base file) + C-15…C-16 (this file): 16 in-window contribution groups.
