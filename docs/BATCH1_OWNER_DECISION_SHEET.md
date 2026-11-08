# BATCH 1 OWNER DECISION SHEET (Q1 + Security + B1 + B7)

2026-11-08 @ d82627d. Four SEPARATE decisions. Nothing here
authorizes execution. B1/B7 stay blocked until each is approved.

## Q1 — qa-scratch/data/state.json version (BLOCKS B1)

- HEAD `5697e03`: 26 keys, 18 audit events, includes a
  revoked_sessions entry; actors qa_es/qa_ar among others.
- Worktree `86f0978`: 25 keys, 12 audit events, revoked_sessions
  absent; actors qa_inv/qa_admin among others; rotated
  request/timestamp identifiers. Mtime Nov 3 (pre-existing).
- Both versions: synthetic scenario data only, no secrets or PII
  shapes detected, zero code references. Publication commits
  whichever version is in the worktree at stage time (86f0978)
  unless the owner directs otherwise.
- Impact: none on tests/runtime; evidence docs reference the path.
- DECIDED 2026-11-08: owner selected HEAD 5697e03; restore
  executed and hash-verified; worktree 86f0978 preserved off-repo.
  B1 remains BLOCKED pending separate publication approval.

## S1 — .edge-d-probe/ security containment

- Status: full Edge profile copy; Login Data (55KB) + Login Data
  For Account (51KB) + Web Data (327KB) present and non-empty;
  Secure Preferences/Local State present; Cookies not observed.
  Authentication material and session-adjacent data MAY be present.
  No file opened or reproduced. EXCLUDED from publication (verified).
- Possibly-affected actions (owner-side): treat stored logins as
  exposed — rotate important passwords, revoke web sessions, review
  account activity, enable MFA where missing.
- Quarantine/removal procedure (on approval): close Edge → delete
  `.edge-d-probe/` → empty Recycle Bin → verify `git status` clean
  of it. SSD caveat: deletion + TRIM do not guarantee erasure
  (wear-leveling, over-provisioning, GC timing); on SSDs without
  full-disk encryption, rotation of exposed credentials is the
  real containment — deletion limits casual recovery only.
- OWNER: reply "S1: authorize secure-removal procedure" or "S1:
  defer (directory stays, still excluded)".

## S2 — tmpbll76ret/ venv removal

- Status: full Python virtualenv (~1200 files), EXCLUDED from
  publication (verified). No project value; reproducible via
  `pip install -r requirements.lock` on a networked machine.
- OWNER: reply "S2: authorize deletion" or "S2: defer".
- Independent of S1 and B1 (safe to decide separately).

## B1 — Push + PR + CI observation (BLOCKED on Q1)

- Scope after Q1: push manifest scope (152/2/373, 7 exclusions
  enforced, qa-scratch at owner-selected version) → PR to
  production-launch → quote CI logs. Auto-runs security-gate only.
- Pre-execution regen (will run after Q1+S1/S2 resolved): recount
  files/paths, re-scan secrets/PII, confirm exclusions absent,
  confirm qa-scratch hash matches Q1, confirm workflow has no
  deploy side effects, confirm quota/billing understood.
- OWNER (only after Q1): B1 wording from the risk review.

## B7 — 73 scratch-PG tests (INDEPENDENT of B1)

- Scope: exact 73 `scratch-pg` IDs in docs/SKIP_TEST_REGISTER.json
  (parity 44, atomic 11, hardening 10, migration 5, j5 2, j6 1).
- Isolation: CI `postgres` service container, job-scoped,
  localhost-only, destroyed with the job; STORE_BACKEND stays
  `json`; DATABASE_URL never set to production (no production DB
  exists). Zero production data by construction.
- Workflow: runs inside security-gate.yml backend-pytest step via
  SCRATCH_DATABASE_URL; no separate workflow; no billable service
  in config (free runners; quota proof awaits B10).
- Evidence: full pytest log quoted; 73 IDs must show PASSED (not
  skipped) for QA-02; any failure blocks closure, fix-forward only.
- OWNER: "B7 approved: execute the 73 registered scratch-PG tests
  on job-scoped CI PostgreSQL with zero production data."

## Standing exclusions

Q1/S1/S2/B1/B7 authorize NONE of: merge, deploy, spend, credential
entry, DNS, migration, purge, AUTH/AI/provider activation, or any
other decision. Matrix stays 192 / NOT PRODUCTION READY.
