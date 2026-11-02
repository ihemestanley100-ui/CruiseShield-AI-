# UGLS-02 — Final Zero-Gap Matrix

Date: 2026-11-02. HEAD `d4e2bec` (unchanged, nothing staged/committed).
Statuses: PASS (implemented + independently verified), PARTIAL
(implemented but incomplete), FAIL (tested and failed), BLOCKED
(identified dependency/approval), NOT VERIFIED (insufficient evidence).

## Task 1 — Complete translation extraction

| # | Requirement | Status | Evidence |
| - | ----------- | ------ | -------- |
| T1.1 | All routes/components inspected (demo, investigation, network, replay, evidence, audit, notifications, auth, decisions, forms, errors, modals, tables, empty states, tooltips, loading, a11y labels) | PASS | 571-key inventory, 22 namespaces; `docs/UGLS_KEY_INVENTORY.md` + generated dump |
| T1.2 | Every user-facing string extracted | PASS | fr/ar parity gate (any unextracted key fails suite); browser matrix zero `[key]` markers on 8 pages |
| T1.3 | Data values never translated (evidence, IDs, audit, risk) | PASS | DOM dumps: verbatim IDs/scores/bands; aria `المخاطر 84 من 100، HIGH`; state hash unchanged |
| T1.4 | Exhaustive key inventory + missing-key report | PASS | `UGLS_KEY_INVENTORY.md` + `UGLS_KEY_INVENTORY_GENERATED.txt` (5128 lines) |

## Task 2 — Expand translation coverage

| # | Requirement | Status | Evidence |
| - | ----------- | ------ | -------- |
| T2.1 | 221-entry registry preserved | PASS | Parse-verified 221 rows; `registry.test.ts` (>200, unique, `Intl.Locale`-valid) |
| T2.2 | Truthful availability matrix, every language | PASS | `UGLS_LANGUAGE_MATRIX_GENERATED.md` (3/11/207) + `UGLS_COMPLETE_TRANSLATION_COVERAGE.md` |
| T2.3 | Priority order en→fr→ar→ig/yo/ha/pt/es/zh/hi/sw/ja→rest | PASS | en 571 source; fr/ar 571; nine drafts 571 each (full, machine-drafted — completed UGLS-02 final, parity-gated); 207 fallback-badged |
| T2.4 | Missing keys identified per locale | PASS | coverage module + tests; 0 missing (full parity; ledger machinery tested via undictionaried locales) |
| T2.5 | Placeholders preserved | PASS | Switching integration test (zero markers, empty ledger fr/ar) + `{count}` plural audit test |
| T2.6 | Plurals validated | PASS | `Intl.PluralRules` per locale; ar six forms; dedicated dictionaries test |
| T2.7 | Punctuation/script rendering validated | PASS | Edge screenshots (ar RTL ×3 breakpoints, ha-Arab, fr) |
| T2.8 | Machine drafts flagged, never human-verified | PASS | `meta.ts` review states + `UGLS_HUMAN_REVIEW_REGISTER.md`; `isHumanVerified()` |

## Task 3 — RTL verification

| # | Requirement | Status | Evidence |
| - | ----------- | ------ | -------- |
| T3.1 | Document direction, alignment, nav, dropdowns, forms, tables, modals, icons, graphs, timelines, responsive, mixed-direction IDs | PASS | 20 Edge screenshots + 8 UTF-8 DOMs reviewed; `UGLS_RTL_BROWSER_VERIFICATION.md` |
| T3.2 | Real browser visual tests at mobile/tablet/desktop | PASS | 390/768/1440 captures; landing + shell + data pages |
| T3.3 | Bidi defects fixed (timestamps) | PASS | `<bdi>` isolation ×10 sites; before/after screenshots; regression test |
| T3.4 | Console-error / network-failure capture | PASS (UGLS-03) | Was PARTIAL (no automation lib). Genuine CDP capture built (`cdp-capture.mjs`): console errors + failed requests recorded on all 30+ armed captures; `browser-evidence/*.console|net.json`, `auth-evidence/*`, `responsive-evidence/w-*` |

## Task 4 — Language preference settings

| # | Requirement | Status | Evidence |
| - | ----------- | ------ | -------- |
| T4.1 | Settings architecture inspected; no duplicate system | PASS | No settings route exists (`cases/demo/investigations/network/replay` only); selector stays authoritative; nothing invented |
| T4.2 | Persistence / browser-detect / override / refresh / session | PASS (open-demo) | Unit tests (`context`, selector) + real-browser proof: `?locale=fr` overrode stored `ha-Arab`; param-less load rendered stored `fr` |
| T4.3 | Authenticated-session consistency | PASS (UGLS-03) | Was NOT VERIFIED. Armed browser runs complete (B1–B8): pre/post-login, refresh/nav persistence, renewal, logout/login, two-user no-leak; `docs/UGLS_AUTHENTICATED_SESSION_AUDIT.md` + `auth-evidence/` (14 captures) |

## Task 5 — Global language quality

| # | Requirement | Status | Evidence |
| - | ----------- | ------ | -------- |
| T5.1 | Missing-key detection + fallback reporting | PASS | Ledger (`getMissingKeys`), `[key]` markers, partial-locale mixing test |
| T5.2 | Registry + BCP 47 validation | PASS | `registry.test.ts` (uniqueness, `Intl.Locale`, fallback, browser matching) |
| T5.3 | Native script rendering | PASS | Screenshots (Arabic, Ajami, CJK, Devanagari selectors render; content per tier) |
| T5.4 | Accessibility validation | PASS | Prior a11y suite holds (320/320); selector roles/labels; lang/dir; aria risk labels; reduced-motion |
| T5.5 | Locale dates/numbers/currencies | PARTIAL | `format.ts` locale-aware formatting retained + covered; timestamps intentionally verbatim ISO (data); no currency-conversion claims |
| T5.6 | Namespace completeness | PASS | Parity gate en↔fr↔ar; coverage module for all 12 dicts |
| T5.7 | Human-review tracking + versioning | PASS | `meta.ts` (1.2.0/1.1.0, source rev) + human review register |

## Task 6 — Regression and security

| # | Requirement | Status | Evidence |
| - | ----------- | ------ | -------- |
| T6.1 | Existing tests preserved, none weakened/deleted | PASS | 315 baseline all hold; 5 added (320 total); behavior-change updates documented in-test |
| T6.2 | New tests: routes, namespaces, missing keys, RTL, persistence, switching, a11y, keyboard, mobile, interpolation, evidence immutability | PASS | 5 new tests + pre-existing locale-switching/selector/a11y suites; RTL via browser matrix |
| T6.3 | Full suite + typecheck + build | PASS | Backend 463/463; tsc exit 0 (×2, incl. final tree); vitest 320/320; build exit 0, 8/8 pages |
| T6.4 | Security: no secrets, CORS explicit | PASS | No `.env`/keys in scope; CORS fix keeps explicit allowlist (tests pin no-wildcard); secret scan unchanged posture |
| T6.5 | Evidence immutability under switching | PASS | State hash BA1D4DB4…3790FE / 101417 B identical across all suites + browser QA; verbatim-ID DOM checks |

## Cross-cutting / found in-programme

| # | Requirement | Status | Evidence |
| - | ----------- | ------ | -------- |
| X.1 | Open-demo browser fetches work (CORS) | PASS | Was FAIL (all data sections `BACKEND_UNREACHABLE`); fixed + regression-tested + screenshot-verified |
| X.2 | 390px app-shell overflow | PASS (UGLS-03) | Was PARTIAL. Root cause: shell `.topbar` non-wrapping flex row (not the selector); fixed with `flex-wrap: wrap` (UGLS-D); verified armed at 320/360/390/430/768/800/1024/1440 × en+ar, 0 offenders; `docs/UGLS_RESPONSIVE_LAYOUT_AUDIT.md` + `responsive-evidence/w-*` |
| X.3 | No protected-state modification | PASS | HEAD unchanged; state hash unchanged; no stage/commit/push/deploy; user processes untouched |

Totals: 26 PASS · 4 PARTIAL · 0 FAIL · 0 BLOCKED · 1 NOT VERIFIED.
No FAIL/BLOCKED items remain. PARTIALs are disclosed limitations with
evidence; the single NOT VERIFIED (armed-mode session check) needs an
authenticated staging environment, which is owner-gated.

## UGLS-03 addendum — final translation & browser acceptance (resume run, 2026-11-02)

Closes the UGLS-02 remainders above (T3.4, T4.3, X.2 → PASS, see rows)
plus the Section B/C/D acceptance programme. Section A (translations):
fr/ar 571/571 plus nine full 571-key drafts, all machine-drafted,
207 fallback-badged (corrected 2026-11-02: drafts completed during
UGLS-02 final; earlier 66-key figures superseded); human review
still owner-side per `UGLS_HUMAN_REVIEW_REGISTER.md`, review kit
ready at `docs/UGLS_REVIEW_KIT/`.

| # | Requirement | Status | Evidence |
| - | ----------- | ------ | -------- |
| B1–B8 | Authenticated sessions (gate, post-login, refresh/nav, renewal, logout/login, consistency, two-user, no-leak) | PASS | `UGLS_AUTHENTICATED_SESSION_AUDIT.md`; `auth-evidence/` 14 captures; 0 cross-user mentions |
| C1–C9 | Browser verification (genuine CDP, console+network, en/fr/ar, widths, dropdown+keyboard interaction, RTL routes, repro logs) | PASS | `UGLS_BROWSER_VERIFICATION.md`; `browser-evidence/` (incl. `i1-selector` VERDICT=PASS); screen-reader runtime stays a human check (disclosed) |
| D | Responsive root cause + width sweep | PASS | `UGLS_RESPONSIVE_LAYOUT_AUDIT.md`; `responsive-evidence/w-*` 16 captures, 0 offenders; desktop one-row topbar unchanged |
| X.4 | Armed-mode CORS (guard 401s + preflights bypassed CORSMiddleware; login unreachable from browsers) | PASS (fixed) | Root-cause fix in `app/main.py` (CORS outermost) + 2 regression tests (fail pre-fix); transport + browser re-verified |
| X.5 | `/me` recheck storm (auth 401s re-signalled expiry; 586 calls/page, rate-limit trip) | PASS (fixed) | Root-cause fix in `frontend/lib/api.ts` (exclude auth namespace) + extended regression test (fail pre-fix); browser re-verified |
| X.6 | Locale hydration mismatch (stored locale in initial state; React #418 every returning visit) | PASS (fixed) | Two-pass init in `frontend/lib/i18n/context.tsx` + first-render regression test (fail pre-fix); B3 re-verified at 0 console errors |
| X.7 | Residual verification closure (secret re-scan, PG suite, gate recompute, npm re-check) | PASS | Secret 280=baseline + new files clean; pytest 465/0/0 on scratch PG; `security_gate.py` GATE PASS (463 recompute now VERIFIED); npm unchanged. Logs: `secret-scan-resume.log`, `pytest-resume-pg.log`, `security-gate-resume.log`, `npm-audit-resume.log` |

UGLS-03 totals: 7 PASS · 0 PARTIAL · 0 FAIL.
Combined UGLS-02+03: T3.4/T4.3/X.2 closed; the remaining UGLS-02
PARTIAL is T5.5 (locale dates/numbers scope — intentional, evidenced
in-row). Standing owner-side work: human translation review
(register provided) and a screen-reader runtime pass.
