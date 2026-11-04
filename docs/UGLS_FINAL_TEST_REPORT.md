# UGLS-02 Task 6 — Final Test Report

Date: 2026-11-02. Final code state (incl. CORS + `<bdi>` fixes, meta
1.2.0): everything below ran against it except where noted. Raw logs:
`pytest-ugls02-final.log`, `tsc-ugls02-final.log`,
`vitest-ugls02-final.log`, `build-ugls02-final.log` (repo root,
untracked). Sandboxed node execution is blocked in this environment
(EPERM above the workspace root); node/browser suites ran unsandboxed
via owner-approved escalation. No quota-spending calls were made.

## Results

| Suite | Command | Result |
| ----- | ------- | ------ |
| Backend | `.venv\Scripts\python -m pytest tests -p no:cacheprovider -q` (+ live `SCRATCH_DATABASE_URL`, container `csai-scratch-pg`) | **463 passed**, 0 failed, 0 skipped (115s) |
| TypeScript | `npx --no-install tsc --noEmit -p tsconfig.json` (frontend/) | **exit 0**, no output |
| Frontend | `npx --no-install vitest run` (frontend/) | **60 files / 320 tests, all pass** (49s) |
| Production build | `npm run build` (default env, `NEXT_TELEMETRY_DISABLED=1`) | **exit 0**, compiled successfully, 8/8 static pages |

Baseline entering UGLS-02: backend 463 / frontend 315 / tsc clean /
build exit 0. Net: +5 frontend tests, zero regressions.

## New tests (5, all passing, all kept)

1. `locale-switching.test.tsx` → partial-locale mixing: Yoruba decision
   form renders drafted keys in Yoruba, missing keys in English, zero
   markers, gap ledgered (`yo:decision.selectPlaceholder`).
2. `coverage.test.ts` → (as written: nine drafts report 0 < coverage
   < 1 with 100+ missing; later updated to full parity for all eleven
   dictionaried locales — see Behavior-change test updates)
   drafted core present (`nav.cases`, `decision.record`);
   undrafted honestly missing (`landing.journey.0`).
3. `language-selector.test.tsx` → partial badge without the unavailable
   warning (Yoruba).
4. `dictionaries.test.ts` → `{count}` interpolation audit over all 8
   shipped fr/ar plural maps + exact fr/ar `droppedEdges` renders
   (regression for the `{n}` template bug found by the suite).
5. `cases/[caseId]/page.test.tsx` → ISO timestamp inside `<bdi>` with
   byte-identical English sentence (regression for the RTL scramble
   found by Edge QA).

## Behavior-change test updates (justified, documented in-test)

- `coverage.test.ts`: undictionaried example `yo`→`zu` (yo is now
  dictionaried); partial count 2→11 (nine drafts registered).
- `registry.test.ts`: `yo` status unavailable→partial; loop pins all
  nine drafts partial.
- `dictionaries.test.ts`: undictionaried fallback example `yo`→`zu`;
  `lookupList("yo",…)` now asserts partial-dict list fallback + ledger.
- `language-selector.test.tsx`: unavailable-badge example
  Yorùbá→isiZulu (yo is now partial).
- `tests/test_cors.py`: open-demo `allow_credentials` False→True
  (the False policy broke every browser fetch; explicit origins keep
  it safe) + ACA-C header regression assertion.
- `system-status.test.tsx`: `Checked …` query spans the new `<bdi>`
  (textContent pin unchanged).

No test was weakened, deleted, or skipped to obtain green. Pre-existing
pins ( landing copy, en byte-identity, risk semantics, evidence IDs )
hold unmodified.

## Defects found by the suites (all fixed, all re-verified)

1. `{n}` instead of `{count}` in en/fr/ar `graph.droppedEdges`
   templates → raw `{n}` rendered. Caught by
   `orbital-explorer.test.tsx`. Fixed + test 4 above. Focused 23/23
   green before the final full run.
2. Open-demo CORS (found by Edge QA, fixed backend-side) — see RTL
   report. `test_cors.py`: 10 passed, 1 socket-gated skip sandboxed;
   full pass in the final unsandboxed run.
3. RTL timestamp scramble (found by Edge QA, fixed with `<bdi>`) —
   see RTL report. Touched files re-tested focused, then full suite.

## Data preservation

`data/state.json` SHA-256 `BA1D4DB4…3790FE`, 101417 bytes — identical
before the programme, after every suite, and after all browser QA
(GET-only traffic; file mtime untouched since Nov 1).

## Resume run (UGLS-03, 2026-11-02)

Final code state incl. the three armed-QA fixes (CORS order,
`/me`-storm exclusion, hydration two-pass). Raw logs: `vitest-
resume*.log`, `build-resume*.log` (repo root, untracked); backend
runs logged inline. Node/python suites ran unsandboxed via
owner-approved escalation (sandboxed execution blocks sockets).

| Suite | Command | Result |
| ----- | ------- | ------ |
| Backend | `.venv\Scripts\python -m pytest tests/ -q -p no:cacheprovider` | **392 passed, 73 skipped** (70s). Skips are live-PG-gated (no scratch container this run); UGLS-02's 463 = 463+0 with container. 392+73 = 465 = 463 + 2 new CORS tests |
| Backend focused | `pytest tests/test_cors.py -q` | **13 passed** (11 existing + 2 new, both failed pre-fix) |
| TypeScript | `npx tsc --noEmit` (frontend/) | **exit 0**, twice (after each frontend edit) |
| Frontend | `npx vitest run` (frontend/) | **332 passed** (60 files), exit 0 — 320 baseline + prior-session additions + extended expiry test + new hydration test |
| Production builds | `npm run build` with `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8010` | **exit 0** (×2, after each frontend fix) |

New/changed tests (all fail-pre-fix, all kept):

1. `tests/test_cors.py::test_armed_guard_401_carries_cors_headers` —
   armed 401 carries ACAO + credentials through the full stack.
2. `tests/test_cors.py::test_armed_preflight_answered_before_guard` —
   preflight to a guarded path returns 200 from CORS, not 401.
3. `frontend/lib/api.test.ts` expiry-signal test extended — `/me`
   and logout 401s emit no event (was: `/me` re-signalled → storm).
4. `frontend/lib/i18n/context.test.tsx` first-render test — first
   client render equals SSR fallback with a stored locale (was:
   stored locale → React #418).

No test was weakened, deleted, or skipped to obtain green.
`data/state.json` re-verified after all resume QA: SHA-256
`BA1D4DB4…3790FE`, 101417 bytes, git-clean (all QA writes went to
`qa-scratch/data/state.json`).

## Gap-closure addendum (same day, post-reboot)

| Check | Result |
| ----- | ------ |
| Secret re-scan (`secret-scan-r06.py`) | HITS_TOTAL 280 = r06 baseline; only diff is +7 line shifts in `app/main.py` from the CORS-fix comment (same 5 adjudicated code-pattern hits); 4 resume-new files scanned separately: 0 credential patterns. Log: `secret-scan-resume.log` |
| PG-backed backend suite (scratch `postgres:16-alpine` container, trust auth, removed after) | **465 passed, 0 skipped, 0 failed** (148s). Log: `pytest-resume-pg.log` |
| Security gate recompute (`scripts/security_gate.py`) | **GATE PASS** exit 0: 16/37 pins, 463 hashes, pip-audit clean, secrets clean. Closes the independent audit's last UNVERIFIABLE (463 recompute). Log: `security-gate-resume.log` |
| npm audit re-check | Unchanged vs r09: postcss 1 moderate + 1 high, fix still requires breaking `next@16`; prior build-time-only acceptance stands. Log: `npm-audit-resume.log` |

State hash re-verified after the PG run: `BA1D4DB4…3790FE`,
101417 B, unchanged. No containers left running.

Translation-review starter (same day): review-kit freshness test
(`review-kit.test.ts`, 11 tests, regen+verify modes green); full
frontend suite now **343 passed** (60→61 files), tsc exit 0
(`vitest-kit.log`). No translation content changed — kit + doc
corrections only.
