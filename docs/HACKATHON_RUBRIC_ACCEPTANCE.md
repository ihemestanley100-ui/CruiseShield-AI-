# Hackathon Rubric Acceptance Matrix v1.0

Status vocabulary: NOT_STARTED, IN_PROGRESS, BLOCKED, IMPLEMENTED_UNVERIFIED,
VERIFIED_PASS, VERIFIED_FAIL. A requirement is VERIFIED_PASS only with a
completed test or direct observation cited below. Nothing here claims a full
category pass from a single success.

## Meta AI Tooling (25%)

- META-01 live analysis succeeds with validation — `app/ai_adapter.py`,
  `POST /api/v1/investigations/{id}/ai-analysis` — direct observation:
  stored `agentrun_0004` SUCCEEDED, muse-spark-1.3, 16733 ms, schema
  VALIDATED, refs VALIDATED, conclusion `requires_review` (runs 0001–
  0003 also SUCCEEDED/VALIDATED) — VERIFIED_PASS.
- META-02 unknown evidence IDs rejected — `validate_model_output`,
  `tests/test_ai_validation.py` — `pytest tests/test_ai_validation.py`
  (in full suite: 49 passed) — VERIFIED_PASS.
- META-03a backend failure codes explicit (refusal, truncation, malformed,
  timeout, provider errors) + bounded retries (429/502/503/504, max 3
  attempts) + MODEL_RATE_LIMITED — suite 51 passed; 3 async retry tests
  skip here (no loop), run in CI/user envs — VERIFIED_PASS.
- META-03b frontend failure states (error/timeout/invalid + retry) —
  `frontend/components/ai-panel.tsx`, `ai-panel.test.tsx` — targeted run
  2026-10-30: file green inside 7-file/33-test automated pass; full
  suite 165/165 exit 0 (P2.2J) — VERIFIED_PASS (automated).
- META-04a AI cannot mutate authoritative state (server) —
  `tests/test_ai_validation.py::test_ai_persistence_preserves_authoritative_state`
  + live risk still 35/84 after two runs — VERIFIED_PASS.
- META-04b AI cannot mutate authoritative state (UI) — page non-interference
  tests in `page.test.tsx` — green in the 2026-10-30 targeted + full
  165/165 runs — VERIFIED_PASS (automated).
- META-05a secrets server-side (backend) — header-only key use,
  `tests/test_secret_safety.py`, secret scan clean — VERIFIED_PASS.
- META-05b secrets absent from browser traffic — `api.test.ts` no-credentials
  test — user run 2026-10-29: 73/73 passed — VERIFIED_PASS.
- META-06 follow-up questions with context — `POST ai-followup`
  (same schema validation, prompt cs-prompt-v2-followup) + AiPanel UI
  + tests — backend + UI tests green in the 2026-10-30 full runs —
  VERIFIED_PASS (automated). One live AI follow-up call still pending.

## Technical Depth & Execution (20%)

- TECH-01 endpoints + schemas — 24 routes, contract tests — full pytest
  49 passed — VERIFIED_PASS.
- TECH-02 typed frontend client — `frontend/lib/api.ts` + `api.test.ts` —
  user run 2026-10-29: 73/73 passed — VERIFIED_PASS.
- TECH-03 UI loading/error/empty/not-found states — implemented + tested,
  green in the 2026-10-30 full 165/165 run — VERIFIED_PASS (automated).
  Browser eyeball still pending.
- TECH-04a graph integrity (backend) — provenance + counts tests —
  VERIFIED_PASS.
- TECH-04b graph UI — `frontend/app/network/[txnId]/`, `components/
  graph-explorer.tsx`, `graph-table.tsx`, `lib/graph-layout.ts` — user
  run 73/73 passed + user-confirmed 5/5 manual interaction checks
  (filters, detail, zoom, keyboard per report 2026-10-29) —
  VERIFIED_PASS.
- TECH-05a replay/simulation/decision engines — backend tests + live
  decision_0001/audit_0006 — VERIFIED_PASS.
- TECH-05b replay/simulation/decision UI — `frontend/app/replay/
  [scenarioId]/`, `app/cases/[caseId]/`, `components/replay-controls`,
  `simulation-panel`, `decision-form`, `audit-list` — all files green in
  the 2026-10-30 targeted + full 165/165 runs, tsc + build exit 0 —
  VERIFIED_PASS (automated). Browser check incl. one live decision +
  reset still pending.
- TECH-06 exact-origin CORS — `tests/test_cors.py` + live browser
  confirmation — VERIFIED_PASS.
- TECH-07 keyboard/a11y/reduced-motion — implemented, browser checks 7–8
  pending — IMPLEMENTED_UNVERIFIED.
- TECH-08 measured browser/API performance — no measurements taken — MISSING.

## Impact (30%)

- IMP-01 problem/user/workflow narrative — README + docs exist, demo not
  rehearsed — IMPLEMENTED_UNVERIFIED.
- IMP-02 measured demo metrics — backend evidence exists (35/84 scores,
  39-item package, 16 s live latency, seed/count pins in TEST_EVIDENCE);
  browser-side none — IMPLEMENTED_UNVERIFIED.
- IMP-03 limitations + synthetic labelling — KNOWN_LIMITATIONS.md,
  in-UI badges, model disclaimer observed in live run — VERIFIED_PASS.

## Demo (25%)

- DEMO-01 backend end-to-end (reset→reveal→AI→decision→audit) — all steps
  observed live with stored records — VERIFIED_PASS.
- DEMO-02 frontend demo path — agent run 2026-10-30: 165/165 tests
  exit 0 (40 files), typecheck exit 0, production build exit 0;
  dev browser renders of all five surfaces remain user-confirmed
  2026-10-29 — VERIFIED_PASS.
- DEMO-03 rehearsal checklist + backup recording — `docs/DEMO_SCRIPT.md`
  written (9-step run, recovery, smoke checklist); live rehearsal +
  recording still pending — IMPLEMENTED_UNVERIFIED.

## Next action

Automated rows are closed (agent-side 165/165 + tsc + build, 2026-10-30).
Remaining: browser checks (TECH-03/05b/07 eyeball + one live UI-driven
decision + reset), live AI follow-up call (META-06), measured perf
(TECH-08), rehearsal + recording (DEMO-03/IMP-01/02), first CI run
(push approval), screenshots/video (user capture).

## Gate audit 2026-10-29 (read-only + backend suite)

- Backend re-run: 49 passed, 8 skipped, 0 failed. No backend files changed
  since the approved CORS batch + gate tests.
- Repo integrity: tracked diffs limited to `.env.example`, `app/config.py`,
  `app/main.py`, `docs/TEST_EVIDENCE.md`, `tests/test_ai_validation.py`;
  staged area empty; no stash; specs/Dockerfile/render.yaml/`.env`
  unaltered; `.env` ignored.
- Frontend `npm test`/`typecheck`/`build` NOT executable from the dev
  sandbox (npm EPERM + no network, standing blocker). Evidence must come
  from user-side runs; nothing frontend flips to VERIFIED_PASS here.

## Batch 3 implementation 2026-10-29 (awaiting user verification)

- Implemented `/network/[txnId]` + explorer + table + layout lib, all data
  from `GET /api/v1/graph/{txn}` (field names verified against
  `app/seed.py` + `get_graph`); no invented nodes/edges/provenance.
- Backend re-run after Batch 3: 49 passed, 8 skipped — scores (35/84)
  and evidence untouched; zero backend/spec/deploy/secret files changed
  (tracked diff still only the approved CORS batch + gate tests).
- Frontend tests/typecheck/build NOT run here (sandbox blocker above):
  TECH-04b stays IMPLEMENTED_UNVERIFIED until the user run reports green.

## Batch 3 verification repair 2026-10-29 (awaiting user re-run)

- Fix 1: added `@testing-library/jest-dom@^10` (single new devDependency)
  + `import "@testing-library/jest-dom/vitest"` in `vitest.setup.ts`;
  Batch 3 tests are the only `toHaveTextContent` users; no assertions
  weakened. TS matcher types load via the setup file (in tsconfig
  include). Requires user `npm install`.
- Fix 2: `graph-explorer.test.tsx` + `graph-table.test.tsx` imports
  corrected `../../lib/api` → `../lib/api` (canonical source, verified
  all other component imports already use it).
- Fix 3: three `node` PIDs observed (30168, 33124, 44372, started
  09:37:46–48) but command lines unreadable from sandbox → ownership
  UNCONFIRMED, nothing terminated. User to stop the dev server in its
  own terminal (Ctrl+C), then delete only `frontend/.next` if the
  build still reports a lock, then rebuild.
- No gate flips: TECH-04b and all frontend rows stay
  IMPLEMENTED_UNVERIFIED/BLOCKED until actual user command output.

## Dependency repair 2026-10-29 (ETARGET on jest-dom@^10)

- Installed stack observed in `frontend/node_modules`: TLR 16.3.3,
  vitest 3.2.7, React 19.3.1, TS 5.9.3; user Node v20.19.6.
- v10 does not exist (hence ETARGET). v7.0.1 exists but requires
  Node >= 22, incompatible with the user's Node 20. Selected
  `@testing-library/jest-dom@^6.9.1`: published 6.x line, supports
  Node >= 14, exports the `/vitest` entry used by `vitest.setup.ts`,
  and the caret stays below 7. Lockfile has no stale jest-dom entry;
  it regenerates on the user's `npm install` (cannot run npm or reach
  the registry from this sandbox; no hashes hand-written).
- Still IMPLEMENTED_UNVERIFIED until user commands succeed.

## Batch 3 manual verification checklist (user-observed)

- Counts 22 nodes / 30 edges / 0 provenance errors — USER_VERIFIED_PASS.
- Complete relationship table with provenance + evidence — USER_VERIFIED_PASS.
- All visible Graph Explorer buttons clickable and responding —
  USER_VERIFIED_PASS (responsiveness only, not correctness).
- Entity-type filter correctness — NOT_VERIFIED.
- Relationship filter correctness — NOT_VERIFIED.
- Node detail correctness (label, type, source records, rel list) —
  NOT_VERIFIED.
- Edge detail correctness (edge_0002 → evt_demo_84721, evidence,
  valid range, trace) — NOT_VERIFIED.
- Zoom in/out + fit-to-screen reset correctness — NOT_VERIFIED.
- Keyboard: Tab/Enter/Space selection, arrow-key pan — NOT_VERIFIED.
- Both themes readable on graph page — NOT_VERIFIED.
- Batch 3 as a whole: NOT fully verified; TECH-04b stays
  IMPLEMENTED_UNVERIFIED. Batch 4 blocked on user approval.

## Batch 3 completion gate 2026-10-29 — NOT PASSED

- `npm test` attempted from dev sandbox: EPERM on `C:\Users\HP`
  (fresh output, same standing blocker). `typecheck`/`build` not
  attempted from here — same root cause. No frontend command output
  exists from either side yet (user run still pending).
- Manual criteria: 3 USER_VERIFIED_PASS (counts, table, button
  responsiveness); 7 interaction criteria still NOT_VERIFIED.
- Gate verdict: Batch 3 NOT verified. Needs: (a) user `npm test`
  (expect now 71 passed incl. Batch 4) + `typecheck` + `build`
  outputs, (b) 7 interaction outcomes. Batch 3 stays NOT PASSED.
  (Batch 4 implementation below was explicitly ordered in parallel.)

## Batch 4 implementation 2026-10-29 (awaiting user verification)

- Implemented `/replay/[scenarioId]` (reset with two-step confirm +
  stated wipe consequences, deterministic playback, simulation with
  server-fetched baseline beside labelled-hypothetical result) and
  `/cases/[caseId]` (status/transitions/history/validated decision
  form/audit trail). All shapes verified against `app/replay.py`,
  `app/simulate.py`, `app/cases.py`, `app/store.py`; no invented
  endpoints, no client-side risk math, no silent duplicates (submit
  disabled in flight).
- Backend re-run after Batch 4: 49 passed, 8 skipped — scores,
  evidence, AI, cases, audits untouched; zero backend/spec/deploy/
  secret files changed.
- Frontend tests/typecheck/build NOT run here (sandbox npm EPERM,
  standing blocker): TECH-05b IMPLEMENTED_UNVERIFIED; Batch 3 gate
  still NOT PASSED. Nothing flips without user command output.

## Batch 4 test repair 2026-10-29 (3 failures, user output 70/73)

- F1 replay page duplicate label: inner control group renamed to
  `Replay step controls` (component fix, genuine a11y defect);
  section keeps `Replay controls`; assertion unchanged.
- F2 simulation mock args: `signal?` is optional in `api.ts`; the
  panel passes none, so the test expectation was outdated — fixed to
  the actual contract-correct calls. No meaningless argument added.
- F3 replay double-step: second click landed on the correctly
  disabled loading button; test now deterministically awaits step 1
  before stepping again. Assertion and component behavior unchanged.
- Fixes NOT verified here (npm EPERM): user re-run required.

## User verification 2026-10-29 — suite/build green

- User-confirmed: `npm test` 73/73 passed (my 71 estimate was off by 2;
  evidence rules), `npm run typecheck` clean, `npm run build` green.
  Flipped to VERIFIED_PASS: TECH-02, META-05b, DEMO-02.
- Browser-observed: all five surfaces render; decision form rejects
  missing reason. No decision recorded by the agent.
- Still NOT_VERIFIED: Batch 3 interaction detail (filters, node/edge
  detail correctness, zoom, keyboard, themes), META-03b/04b browser
  behavior, TECH-03/04b/05b/07 browser checks, one live UI-driven
  decision + audit entry. Batch 3 gate stays NOT PASSED.
- Live state at this point: case_84721 TRIAGED, decision_0001
  recorded, 8 audits (last: simulation.run). No reset performed.

## Final acceptance review 2026-10-29

- agentrun_0004 verified in persisted state (not just user report):
  SUCCEEDED, muse-spark-1.3, 16733 ms, schema VALIDATED, refs
  VALIDATED, conclusion `requires_review`. EXPLAIN (live) now
  VERIFIED_PASS. Audit chain extended to audit_0012
  (ai.run.succeeded); decision chain decision_0001–0004 and
  audit_0011 (AWAITING_REVIEW→ESCALATED) intact; case ESCALATED.
- Network Explorer manual interactions: user-confirmed 5/5 passed.
  Combined with prior passes (counts 22/30/0, table, buttons) and
  73/73 automated, Batch 3 gate now PASSED; TECH-04b VERIFIED_PASS.
  Note: my working checklist had 7 items vs the user's 5 checks —
  treated as covering filters/detail/zoom/keyboard; correct me if
  theme readability was not among them.
- Backend re-run: 49 passed, 8 skipped. Risk 84 HIGH, 30 edges,
  39-item package unchanged.
- Frontend trio NOT re-run here (sandbox npm EPERM); prior user
  73/73 + typecheck + build stands. No code changed since, so no
  staleness.
- Full workflow DETECT→AUDIT verified locally. Hosted deployment
  remains NOT VERIFIED (no public URL, no hosted smoke).

## Batch B orbital explorer 2026-10-29 (IMPLEMENTED_UNVERIFIED)

- ORB-01 orbital renderer + real-data adapter — `lib/orbital-layout.ts`,
  `components/orbital-explorer.tsx`, Orbital/Flat toggle in
  `app/network/[txnId]/` (+18 tests: 9 layout, 8 explorer, 1 toggle) —
  require user `npm test` (new expect: 91 passed) + typecheck + build
  + browser check — IMPLEMENTED_UNVERIFIED.
- SVG approved over three.js (no new deps); flat explorer preserved
  as fallback; 8 tokens added both themes; risk token reserved, never
  applied to nodes (no per-node risk in API). Backend untouched.

## Master mandate execution 2026-10-29 (G01–G27)

- Wrote `docs/RELEASE_GAP_AUDIT.md` (initial classification) and
  `docs/DEMO_SCRIPT.md` (script + recovery + smoke list).
- G12: bounded provider retries + MODEL_RATE_LIMITED + 3 tests.
- G10: `POST ai-followup` endpoint (shared persist helper, same
  validation) + AiPanel follow-up UI + 5 tests (2 backend sync pass;
  UI needs user run). META-06 MISSING → IMPLEMENTED_UNVERIFIED.
- Backend: 51 passed, 11 skipped (8 transport + 3 loop-gated, all
  disclosed). Live state intact (ESCALATED, 4 decisions, 12 audits,
  4 runs, risk 84). No reset, no secret/deploy changes.
- Frontend trio NOT run here (npm EPERM). Next user run covers
  Batch B orbital (+18 tests) and mandate follow-up UI (+3 tests):
  combined expect is 73 + 18 + 3 = 94 passed.

## Mandate round 2 2026-10-29 (G05, G18, §4.7)

- New `scn_ambiguous` (txn_84740 ₦250,000): 4 nodes / 4 edges,
  transaction 20 LOW, network 38 MODERATE (R-002/R-003/R-007 only),
  own case_84740/inv_84740. Listed in demo scenarios; no UI change
  needed (list renders dynamically).
- Restart round-trip test: decisions/audit/scores survive Store
  re-init from disk. Simulation isolation assertions: case stays NEW,
  no decisions, no case.decision audits after sim.
- Backend: 53 passed, 11 skipped. Live demo state intact
  (ESCALATED, 4 decisions, 12 audits, 4 runs). G05/G18 → PASS.

## Zero-gap round 2026-10-29 (G03, G06)

- G06: homepage workflow nav (Investigate → Network → Replay →
  Decide) + onboarding copy + `page.test.tsx` (+3 tests: routes,
  live-values-only, honest error).
- G03: 200× determinism benchmark test + measured 21.8 ms / 0.109 ms
  per eval recorded in TEST_EVIDENCE.
- Backend: 54 passed, 11 skipped. Next user frontend run expect:
  103 + 3 = 106 passed.

## Rubric push 2026-10-29 (scoring gaps)

- Meta AI depth: follow-ups now carry prior-run context
  (`latest_run_context`, degrades cleanly); +2 tests.
- Contracts: malformed simulation/follow-up bodies → 400 codes
  (INVALID_BODY/INVALID_EDGE_LIST), never 500; +1 test.
- Impact/Demo evidence: `docs/IMPACT_CASE.md` (users, pilot path,
  limits) + `docs/VIDEO_STORYBOARD.md` (5-min shot list + fallback).
- Backend: 57 passed, 11 skipped. Live state intact.
- A11y smoke: `frontend/a11y.test.tsx` (+3 tests: h1/buttons/labels
  on Command Center, DecisionForm, graph canvas). Next user run
  expect: 106 + 3 = 109 passed.

## Safeguard patch F1+F2 2026-10-30 (IMPLEMENTED_UNVERIFIED→backend PASS)

- F1: DecisionForm no longer preselects ("Select a decision…",
  submit blocked until chosen). F2: GET case detail gains additive
  `latest_ai_run` (conclusion, findings+confidence+evidence refs,
  missing info, validation statuses); case page renders read-only
  "AI Investigation Assessment" with advisory disclaimer; null-safe.
- Tests: +2 backend (present/absent incl. read-only proof), +3
  frontend (1 form, 2 page). Backend: 59 passed, 11 skipped.
  Frontend trio NOT run here (npm EPERM); next user run expect
  109 + 3 = 112 passed.
- Live Take-2 activity observed (user-side, not mine): agentrun_0001/
  0002 SUCCEEDED + sim_0001 + audits 0003–0005. No decision recorded
  by the agent; F3 not implemented; no deploy changes.

## F2 hotfix 2026-10-30 (undefined latest_ai_run crash)

- Cause: backends predating F2 omit the key (undefined, not null);
  `=== null` fell through → crash on `.conclusion`. Fix: dedicated
  `AiAssessmentSection` guards detail/key/every field; renders only
  on a valid object; empty text now exactly "No AI investigation
  assessment is available yet." API errors still use page-level state.
- Tests: +2 (undefined key, partial fields), 1 empty-text update.
  Backend regression 59/11. Next user run expect 112 + 2 = 114.

## Test-failure repair 2026-10-30 (114 run: 111 pass, 3 fail)

- Deeper F2 root cause: the case page's Promise.all handler
  destructured only case/decisions/allowed_transitions and rebuilt
  detail WITHOUT latest_ai_run — so the key was ALWAYS undefined at
  runtime. This was both the original browser crash AND the 2 case
  assessment-test timeouts. Fix: pass the whole CaseDetail through.
- Investigation "renders loading then live data" timeout: no
  application defect — the page waits on the real-time 900ms rAF
  count-up animation. Fix in test only: stub reduced-motion (existing
  repo pattern) so the badge renders the same authoritative final
  text immediately; 5s waits reverted to default. Animation timing
  stays covered by use-count-up/risk-badge fake-timer tests.
- Added case loading-state test. No assertion weakened anywhere.
  Expect 115 tests on the next user run.

## Frontend repair 2026-10-29 (5 failed / 101 passed → fixes)

- F0 suite error: `use-count-up.test.ts` contained JSX → renamed `.tsx`.
- F1/F2 matchMedia crash (ambient cleanup, orbital zoom): test mocks
  via defineProperty were neutered by global restore, returning
  undefined → mocks now use stubGlobal/unstub; components hardened
  with `?.matches ?? false` (incl. replay-controls, same shape).
- F3–F5 investigation badge text: count-up races synchronous
  assertions → same `/84\/100 HIGH/` expectations awaited via
  waitFor (convergence, not weakening); explicit 5000ms timeout
  since 900ms animation + fetch latency can exceed the 1000ms default.
- Fixes NOT run here (npm EPERM): user re-run decides.

## User verification 2026-10-29 — 109/109 + typecheck green

- User run: `npm test` 109 passed / 0 failed (23 files); `npm run
  typecheck` clean. All repair assertions hold.
- `npm run build` FAILED environmentally: EPERM (-4048) opening
  `frontend/.next/trace`. Cause: file exclusively locked; three
  lingering node PIDs (42688/51764/55240, started 13:33) with no
  :3000 listener — consistent with a hung/crashed Next worker
  holding the handle. Ownership unprovable from sandbox: user must
  stop it (Ctrl+C in dev terminal, else Stop-Process on those PIDs
  after confirming no dev work), delete ONLY `frontend/.next`,
  then rebuild. No source/data/tests touched by this issue.

## Local verification COMPLETE 2026-10-29 (user screenshot)

- `npm test`: 109 passed / 0 failed, 23 files. `npm run typecheck`:
  clean. `npm run build`: Next.js 15.5.28 production build succeeded
  (compile + types + page data + static generation + optimize).
- Automated frontend verdict: VERIFIED_PASS (all suites incl. orbital,
  follow-up UI, visual system, nav, a11y smoke).
- Still pending (not code): orbital/visual browser eyeball (ORB-01,
  VIS-01 stay IMPLEMENTED_UNVERIFIED), live AI follow-up call
  (META-06 stays IMPLEMENTED_UNVERIFIED), Batch 4 browser checks
  (TECH-05b stays IMPLEMENTED_UNVERIFIED), demo recording (DEMO-03),
  all deployment rows (NOT VERIFIED — no public URL).

## Visual excellence directive 2026-10-29 (IMPLEMENTED_UNVERIFIED)

- VIS-01 motion/design system — `lib/use-count-up`, `AmbientBackground`,
  RiskBadge gauge+count-up, motion tokens, button variants, glass hero,
  skeleton, float, entrance, responsive rules (+9 tests: 3 count-up,
  4 ambient, 2 badge) — require user trio (new expect: 103 passed) +
  browser visual check — IMPLEMENTED_UNVERIFIED.
- Three.js intentionally NOT used: no prior install; 22-node SVG
  orbital already satisfies selection/provenance/a11y; WebGL would add
  bundle + fallback cost without investigative value. Documented.
- Backend untouched this round: 53/11 re-verified.

## Deployment-readiness checklist (all need approval)

1. Approve Batch 3/4 frontend file set for commit (explicit paths).
2. Resolve CONFLICT-001 (Render $PORT vs :8000) — proposal in
   docs/COMMAND_EXPERIENCE/05-CONFLICT-001.md, unapplied.
3. Decide paid tier: starter+disk vs free ephemeral.
4. Push, Render Blueprint deploy, public-URL smoke (health,
   investigation, graph, AI, decision-read, audit), screenshots.
5. Rehearsal checklist + backup recording (DEMO-03, still MISSING).

## R18 reconciliation 2026-10-30 (doc-only; history above preserved)

- Flipped to VERIFIED_PASS (automated) on fresh agent-side evidence:
  META-03b, META-04b, META-06 (automated; one live follow-up call still
  pending), TECH-03 (automated; browser eyeball pending), TECH-05b
  (automated; browser check + live decision pending).
- Evidence: targeted vitest run 7 files / 33 tests all passed
  (`ai-panel`, `page`, `decision-form`, `simulation-panel`,
  `replay-controls`, `audit-list`, replay page); full frontend 165/165
  exit 0 (40 files); `tsc --noEmit` exit 0; `next build` exit 0;
  backend 250 passed / 0 skipped with scratch PG; security gate 6/6.
- Unchanged: TECH-07/TECH-08, IMP-01/02, DEMO-03, all deployment rows,
  first CI run. No browser, rehearsal, recording, or hosted claims added.

## R13 decision 2026-10-30 — global search OUT OF SCOPE (doc-only)

- Read-only audit found no search screen, component, endpoint, test, or
  doc reference anywhere in the repo: nothing to complete or retain.
- Approved Option C: global search is OUT OF SCOPE for the hackathon
  demo. Phase 3 navigation scope = sidebar + notifications + alert
  listing, all delivered and preserved.
- In-scope navigation aids (preserved, not search): sidebar nav, alert
  listing, graph type/relationship filters, scenario picker, AI
  follow-up input. No search interface, endpoint, API, or DB feature
  was created; no functionality deleted or modified.
