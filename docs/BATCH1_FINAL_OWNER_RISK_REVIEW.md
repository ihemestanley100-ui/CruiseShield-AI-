# BATCH 1 FINAL Owner Risk Review

2026-11-08 @ d82627d. Read-only. B1/B7 NOT executed.
Full per-file data: docs/BATCH1_FILE_INVENTORY.json
(1811 files expanded; 534 git-status entries).

## 1. Findings

- Scope: 152 modified + 2 deleted + 373 untracked in-scope +
  7 excluded (git view). Expanded: 1811 files (152/2/448/1209).
- Composition: docs/evidence 145, backend tests 137, backend
  modules 110, frontend 98, reports 13, tooling/CI/misc rest.
- In-scope sensitivity scan: ZERO high-risk shapes (no AWS keys,
  private-key blocks, gh/xox tokens). 34 test-constant hits
  (Passwords/secrets as test values), 3 dummy localhost PG URLs
  (gate workflow + 2 PG tests), 8 fixture phones (555 fictional +
  +234*1234567 synthetic patterns; tsx hit is an input
  placeholder), 2 fixture emails (a@b.co, ops@acme.example).
  Gate `secret_scan` PASS corroborates. Large files: none.
- Excluded dirs contain a full Python venv (~1200 files,
  tmpbll76ret/) and an Edge browser profile (.edge-d-probe/)
  WITH REAL PERSONAL DATA (emails, login-data password
  identifiers, a phone number). Correctly excluded from the
  manifest; present in the worktree.
- qa-scratch: HEAD blob 5697e03, worktree blob 86f0978;
  36+/126- (audits 18→12, revoked_sessions removed, actors
  swapped); mtime Nov 3 (pre-existing, untouched this session).
  BOTH versions scan clean (no secret/PII shapes; qa_* synthetic
  actors). Zero code references; evidence docs mention path only.
  Publication would commit the WORKTREE version.
- Remote: origin https://github.com/ihemestanley100-ui/
  CRUISESHIELD-AI-.git, branch feat/phasezero-foundations → PR
  base production-launch. Push: `git push -u origin
  feat/phasezero-foundations`; PR via `gh pr create --base
  production-launch --head feat/phasezero-foundations` (or web).
- security-gate.yml triggers on ANY PR (pull_request, no base
  filter) → YES, the PR auto-runs the gate. No workflow deploys
  or touches externals (gate = checks only; backups are
  manual-dispatch + enabled=false + reviewer environment).
- CI jobs are non-production (STORE_BACKEND=json, PG service
  job-scoped, zero secrets) and non-billable in config (free
  runners + OSS actions; quota proof awaits B10 readings).
- Branch protection / required checks: UNKNOWN (no credentials;
  ls-remote fails). Cannot confirm; recorded, not assumed.
- PR close: no artifacts uploaded by any job (zero
  upload-artifact steps); logs retained per GitHub policy.
- Remote branch deletion: safe — affects only the pushed feature
  branch; production-launch/master/owner work untouched; local
  branch remains. Full rollback path.

## 2. Exact risks

- R1 HIGH (mitigated by exclusion): Edge profile PII in worktree.
  Safe ONLY while the 7-path exclusion holds. Recommend owner
  secure-delete the directory (needs separate authorization;
  NOT done here).
- R2 MEDIUM (mitigated by exclusion): venv + tmp bulk (~1200
  files). Same reliance on exclusion; same delete recommendation.
- R3 MEDIUM (needs owner confirmation): qa-scratch ships the
  Nov-3 worktree version. Consistent with REMAINS TRACKED, but
  confirm this is the intended version before any commit. Impact
  if shipped: none on tests/runtime (unread); evidence stays coherent.
- R4 LOW: protections unknown → a careless merge could skip gates.
  Mitigated: B1 authorizes observation only, never merge.
- R5 LOW: heuristic scan limits. Residual unknown-unknowns;
  gitleaks in hosted CI is the independent second check.
- R6 INFO: Actions quota unknown → CI may queue/fail on limits;
  non-destructive and retryable.

## 3. Unresolved questions (owner-side)

1. Is the qa-scratch WORKTREE version (86f0978) the intended one?
2. Authorize secure deletion of .edge-d-probe/ + tmp*? (separate)
3. B10 readings (quota/billing) — still awaited.
4. Branch protection readout — still awaited (PKG-02).

## 4. Recommended disposition

- B1: APPROVE (observe-only) AFTER Q1 confirmed yes. Conditions:
  exclusion manifest enforced at stage time (no `git add -A`),
  PR to production-launch, logs quoted before any status change.
- B7: APPROVE. 73 exact IDs, job-scoped CI Postgres, zero
  production data, auto-destroyed with the job. Independent of B1's
  file risk (runs inside the same gate job once pushed).

## 5. Exact approval wording

- B1: "B1 approved: push feat/phasezero-foundations (manifest
  152/2/373, 7 exclusions enforced, qa-scratch worktree version
  86f0978 confirmed) and open PR to production-launch for CI
  observation only."
- B7: "B7 approved: execute the 73 registered scratch-PG tests on
  job-scoped CI PostgreSQL with zero production data. Results
  quoted before any matrix change."

## 6. NOT AUTHORIZED (even after B1+B7)

No merge, no deploy, no billing change, no DATABASE_URL or
production migration, no credential entry, no DNS/domain change,
no deletion/untrack/purge, no AUTH/AI/provider activation, no
destructive cleanup, no other owner decision. Each needs its own
explicit approval. Production stays NOT PRODUCTION READY.
