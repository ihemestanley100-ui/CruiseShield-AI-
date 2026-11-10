# O-04b Engineering Package Closure Record

**Mission:** CS-O04B-EXEC-001 — Stage 1
**Charter:** CS-O04B-CHARTER-001 (owner decision D1–D6 approved with amendments)
**Baseline SHA:** `844a5462492ad73d62701dc09468d97e309e5d8c`
**Stage 1 status:** EXECUTED — AWAITING OWNER REVIEW
**Production release:** LOCKED (unchanged)

## 1. Charter traceability (D1)

This document is the single new closure record approved under charter
decision D1. The five existing artifacts it closes over are those named
in the approved CS-O04B-CHARTER-001 proposal/decision package; this
record does not redefine them. Original O-04b evidence context (M3
provider-lifecycle package) is unchanged by Stage 1.

## 2. Scope compliance (D2)

Stage 1 executed ONLY:

- The approved L-01 repair in
  `frontend/components/landing/GlobalHeroScene.tsx`.
- One dedicated failure-path test:
  `frontend/components/landing/GlobalHeroScene.failure.test.tsx`.
- This closure record.

No other source, test, config, or governance file was modified. No
staging, commit, push, merge, deployment, settings change, migration,
or live-provider action was performed.

## 3. L-01 repair evidence (D3)

**File:** `frontend/components/landing/GlobalHeroScene.tsx`, lines 105–138
(new guarded assembly block; verified via `git diff` hunk `@@ -103,23
+103,39 @@`).

**Defect:** scene-assembly statements (builders, hub mapping,
`parts.push`, `scene.add`) executed unguarded after renderer creation.
A throw there aborted the effect with a live canvas appended, GPU
resources undisposed, and the branded fallback never activated.

**Repair (behavior-preserving on success path):**

- The five builder results are hoisted as `ReturnType<typeof …>` lets;
  all assembly statements run inside one `try`.
- On any setup throw, the `catch` releases exactly the two resources
  that can exist at that point — `renderer.dispose()` and
  `canvas.remove()` — then calls the pre-existing `setFailed(true)`
  and returns, activating the unchanged branded `WebGLFallback`.
- Listener/observer/frame cleanup is provably unnecessary in this
  handler: every `addEventListener`, the `IntersectionObserver`, and
  the animation loop attach strictly below the guarded region, so a
  setup throw cannot leave any of them behind.
- No visual code, fallback markup, styling, or copy was touched. The
  success path executes the identical statements in the identical
  order.

## 4. Test battery (D4)

Environment for all runs below: Windows, Node v20.19.6, repository
`node_modules` (no installs), Python 3.x for repo gates. Tested SHA:
`844a5462492ad73d62701dc09468d97e309e5d8c` plus the uncommitted Stage 1
worktree described in section 6.

| # | Command | Passed | Failed | Skipped | Errors |
|---|---------|--------|--------|---------|--------|
| T1 | `npx vitest run components/landing/GlobalHeroScene.failure.test.tsx` (pre-fix) | 0 | 1 | 0 | 0 |
| T2 | same focused file (post-fix) + `GlobalHeroScene.test.tsx` | 3 | 0 | 0 | 0 |
| T3 | `npx vitest run` full frontend suite (run A) | 459 | 0 | 0 | 0 |
| T4 | `npx vitest run` full frontend suite (run B) | 458 | 1 | 0 | 0 |
| T5 | `npx vitest run` full frontend suite (run C) | 459 | 0 | 0 | 0 |
| T6 | `npx vitest run app/platform/page.test.tsx` focused | 10 | 0 | 0 | 0 |
| T7 | `npx tsc --noEmit -p tsconfig.json` | — | 0 in repo source | — | 3 stale-cache only |
| T8 | `python scripts/zero_gap_matrix.py --check` | valid, 213 rows | 0 | — | 0 |
| T9 | `python scripts/evidence_manifest.py --check` | ok, 11 files | 0 | — | 0 |
| T10 | `python -m ruff check .` | clean | 0 | — | 0 |
| T11 | `pytest tests/test_evidence_manifest.py -q` | 1 | 0 | 0 | 0 |

Notes:

- T1 is the authentic pre-fix failure: `Error: simulated scene-setup
  failure` thrown uncaught from the buildEarth call site, proving the
  test targets the real gap.
- T2–T3/T5: the new L-01 test passes; full suite is 83 files / 459
  tests (458 baseline + 1 new). Process exit codes: run A exited 1
  despite its all-passed summary; run C exited 0. A passing test
  count does not override a nonzero process exit. The cause of run
  A's exit code 1 remains unverified: the captured output window
  showed a clean 83/459 summary and no error, and no log was
  persisted for post-hoc diagnosis.
- T4: one failure in `app/platform/page.test.tsx`, a module with zero
  imports of the changed file; it passes 10/10 focused (T6) and in
  both other full runs. Classified as an unrelated load-dependent
  flake; hosted CI is the arbiter.
- T7: zero errors in repository source. The 3 reported errors are all
  inside git-ignored `frontend/.next/` (stale type cache referencing
  deleted `app/demo/page.tsx`); no error names any repo file.
- T8–T11: canonical matrix, evidence manifest, lint, and manifest test
  all green; no backend files were in scope, so no wider backend
  regression was run.

**Synthetic-data confirmation:** every executed test uses in-repo mocks
or synthetic fixtures; no test performs network I/O or touches
production data.
**NO-LIVE confirmation:** no live provider, financial-institution, or
external-intelligence call was made or enabled by any test or gate.
**Coverage provenance and limitations:** no coverage artifacts were
generated in Stage 1, and no historical coverage snapshot is cited as
proof of the new catch path. The new test asserts the behavior
directly (dispose called, fallback rendered, canvas removed). Hosted
CI coverage is the remaining verification step.

## 5. Acceptance authority (D5)

Dual acceptance is required and remains outstanding:

1. Owner approval of this Stage 1 package.
2. Independent reviewer approval against the exact committed revision
   (commit itself still unauthorized).

Status separation is preserved: L-01 is IMPLEMENTED and TESTED (local
evidence above); it is NOT independently verified and NOT accepted.

## 6. Preservation evidence

- Canonical matrix: 213 rows valid (`zero_gap_matrix.py --check`).
- The three uncommitted CS-FCA-013 registration files
  (`docs/EVIDENCE_MANIFEST.json`, `docs/ZERO_GAP_MATRIX.json`,
  `scripts/zero_gap_matrix.py`) remain modified-but-uncommitted with
  their approved contents untouched by Stage 1 — Stage 1 added no
  hunks to them.
- All nine protected scratch entries remain untouched.
- CS-FCA-013 decisions D-2 (no-names), D-3 (structure-only), D-4
  (dual acceptance), D-5 (build deferred) are unaffected: no identity,
  provider, or feature work was performed.
- $0-only, NO-LIVE, synthetic-data-only, and production-lock
  constraints held for every action.

## 7. Worktree change manifest (Stage 1 only)

Modified:

- `frontend/components/landing/GlobalHeroScene.tsx` — L-01 guard only.

Created:

- `frontend/components/landing/GlobalHeroScene.failure.test.tsx` — L-01
  failure-path test.
- `docs/O04B_ENGINEERING_PACKAGE_CLOSURE.md` — this record.

## 8. Remaining risks and blockers

1. Hosted CI verification of the L-01 commit is pending (commit/push
   unauthorized in Stage 1).
2. `app/platform/page.test.tsx` flaked once in three full local runs;
   hosted CI result governs.
3. Local `tsc` reports 3 stale-cache errors from ignored `.next/`;
   fresh-checkout CI is unaffected, but a local `next build` refresh
   would clear the noise.
4. No local coverage measurement for the new catch path (see section
   4).
5. O-05 independent human review still outstanding against any future
   revision.

## 9. Stage 1 verdict

STAGE 1 EXECUTION PASSED — AWAITING OWNER REVIEW
