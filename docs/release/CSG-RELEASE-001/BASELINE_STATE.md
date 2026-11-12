# CSG-RELEASE-001 — Baseline State

Recorded 2026-11-10T15:05:00+01:00. Machine-readable companion: `BASELINE_STATE.json`.

## Verified state (all four SHAs agree)

- Branch: `feat/phasezero-foundations`
- Local HEAD: `e099b7a13e1e6b10a0298e3524bee14387fec6a0`
- Remote branch SHA: `e099b7a…` (identical)
- PR #2 head SHA: `e099b7a…` (identical)
- PR state: OPEN, mergeable, unmerged (`mergedAt: null`)
- Staged files: none
- `package-lock.json`: clean (last touched `d4e2bec`); `node_modules` rebuilt via `npm ci` with no lockfile diff

## Uncommitted non-scratch files: 15 (not 13)

A prior report said "13 uncommitted files"; the verified count is **15**:
5 modified, 3 deleted, 7 new (see JSON for paths). The discrepancy is a
counting correction, not a tree change. Full disposition in
`REPOSITORY_RECONCILIATION_REGISTER.md`.

## Scratch and temp

- Nine protected scratch entries present and untouched (see JSON).
- Eight empty `pip-*` temp dirs in repo root (side effect of an
  authorized `pip install playwright` into the project venv): present
  but ACL-locked against every removal attempt including ownership
  change. Not deletable from this session; owner cleanup instructions
  in the reconciliation register. Zero functional impact (untracked,
  invisible to git and all gates).

## Deployments and CI

- Hosted CI run 42775901098: `security-gate` SUCCESS on `e099b7a`
  (backend 1,577 passed; frontend 459; tsc/build/ruff/gitleaks clean).
- Netlify deploy `6af2c85accbf912dbc76f14c` associated with `e099b7a`
  via commit check-runs; build conclusion not reported via API;
  preview URL returns HTTP 401 to unauthenticated callers.
