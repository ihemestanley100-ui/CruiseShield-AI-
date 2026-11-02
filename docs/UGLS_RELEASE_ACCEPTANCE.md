# UGLS-02 — Release Acceptance

Date: 2026-11-02. Programme: Universal Global Language Selector final
zero-gap closure. HEAD `d4e2bec` unchanged; all work uncommitted for
owner review (183 changed entries); no stage/commit/push/deploy per
directive.

## Task 8 acceptance checklist

| # | Criterion | Verdict | Evidence |
| - | --------- | ------- | -------- |
| A1 | All translation namespaces inventoried | PASS | 571 keys / 22 namespaces, generated dump |
| A2 | Truthful coverage classification per language | PASS | 3 translated / 11 partial / 207 unavailable; tested counts |
| A3 | No missing keys hidden by fallback | PASS | Ledger + `[key]` markers + mixing test; zero markers in browser |
| A4 | RTL visual browser testing passes | PASS | 20 Edge screenshots + 8 DOMs, 3 breakpoints, findings fixed |
| A5 | Language preference persistence passes | PASS | Unit + real-browser override/persistence proof (open-demo) |
| A6 | Accessibility tests pass | PASS | 320/320 incl. a11y/selector/keyboard suites; lang/dir/aria live |
| A7 | No regressions introduced | PASS | 315/315 baseline hold; backend 463/463; tsc + build exit 0 |
| A8 | Human review requirements explicit | PASS | Review register; all non-English machine-drafted, none verified |
| A9 | All limitations documented | PASS | Zero-gap matrix (4 PARTIAL + 1 NOT VERIFIED, each evidenced) |

## Decision

**UGLS-02 ACCEPTED WITH DOCUMENTED LIMITATIONS.**

A language is selectable without being falsely classified as
translated: the selector, coverage module, matrix, and tests agree on
every tier. The two functional defects found by real-browser QA (CORS,
bidi timestamps) are fixed, regression-tested, and re-verified
visually. `data/state.json` (BA1D4DB4…3790FE, 101417 B) is untouched.

## Scope notes (read before calling this "complete translation")

- Only English is human-authoritative. fr/ar are COMPLETE but
  machine-drafted (571/571); nine priority locales are full 571-key
  machine drafts (completed UGLS-02 final; earlier 11.6% figures
  superseded); 207 languages intentionally fall back to English.
  Human review (register + review kit provided) is the remaining
  work, owned by reviewers, not code.
- Authenticated (armed) session locale check is NOT VERIFIED —
  requires a staging environment with login; no code reason to expect
  failure (localStorage-based, session-independent).
- 390px app-shell overflow is pre-existing (identical in English),
  responsive-layout ownership, deliberately untouched.
- Full CDP console/network capture was unavailable; substituted with
  renderer-stderr monitoring + rendered-DOM assertions + screenshots.

## Deliverable index

1. `docs/UGLS_FINAL_ZERO_GAP_MATRIX.md` — 31 requirements, evidenced.
2. `docs/UGLS_COMPLETE_TRANSLATION_COVERAGE.md` + generated 221-row
   `docs/UGLS_LANGUAGE_MATRIX_GENERATED.md`.
3. `docs/UGLS_HUMAN_REVIEW_REGISTER.md` (+ `meta.ts` states).
4. `docs/UGLS_RTL_BROWSER_VERIFICATION.md` + `rtl-evidence-ugls02/`
   (20 PNG + 8 HTML: 14 matrix + 6 ad-hoc) + `rtl-*-ugls02.ps1` repro
   scripts.
5. `docs/UGLS_FINAL_TEST_REPORT.md` + `*-ugls02*.log` raw logs.
6. This file.
7. Supporting: `docs/UGLS_KEY_INVENTORY.md` +
   `docs/UGLS_KEY_INVENTORY_GENERATED.txt`.

## Owner gates (unchanged, still gated)

Staging/commit/push of the UGLS-02 tree, human translation review,
armed-mode browser check, backup execution, deployment, submission —
all require separate explicit approval. Nothing here authorizes any of
them.

## UGLS-03 addendum — browser acceptance closure (2026-11-02)

The resume run executed the UGLS final translation & browser
acceptance directive (Sections B–E) against an armed local QA stack:

- Authenticated sessions B1–B8: PASS
  (`UGLS_AUTHENTICATED_SESSION_AUDIT.md`).
- Browser verification C1–C9: PASS
  (`UGLS_BROWSER_VERIFICATION.md`).
- Responsive root cause + sweep D: PASS
  (`UGLS_RESPONSIVE_LAYOUT_AUDIT.md`).
- Three blocking defects found by genuine browser QA, root-caused,
  fixed, regression-tested (fail pre-fix), and re-verified:
  armed-mode CORS order, `/me` recheck storm, locale hydration
  mismatch.
- Residual verification closed same-day: secret re-scan clean,
  PG-backed pytest 465/0/0, security gate recompute PASS (463
  hashes verified), npm audit unchanged.

**UGLS-03 browser acceptance: CLOSED.** Remaining owner-side work is
unchanged in kind: human translation review, screen-reader runtime
pass, and the standing staging/commit/deploy gates. HEAD `d4e2bec`
unchanged; `data/state.json` (`BA1D4DB4…3790FE`, 101417 B) untouched;
no stage/commit/push/deploy performed.
