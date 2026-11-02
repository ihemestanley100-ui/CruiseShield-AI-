# UGLS-03 git commit manifest (master, parent `d4e2bec`)

Date: 2026-11-02. Second commit on master: the J3–J10, R01–R17,
UGLS-02, and UGLS-03 programme worktree. Approval: owner structured
approval this session ("Commit tree"; push/deploy NOT approved).

## Staged set (789 files)

Modified tracked (97): frontend 59, docs 14, tests 12, app 7,
`render.yaml` / `.env.example` / `.gitignore` / `README.md` /
`Dockerfile` 1 each. Zero deletions.

New, previously untracked (643, incl. this manifest):
responsive-evidence 339, auth-evidence 98, docs 94 (81 audit set +
11 review-kit TSVs + README + this manifest), browser-evidence 34,
frontend 33 (i18n system + review-kit test), rtl-evidence-ugls02 28,
tests 5, scripts 2, qa-scratch 1, root repro tooling + listings 9
(`cdp-capture.mjs`, `cdp-interact.mjs`, `secret-scan-r06.py`,
`csp-qa-r07.ps1`, `rtl-{qa,matrix,dom}-ugls02.ps1`,
`tree-status-r16.txt`, `rtl-evidence-listing.txt`).

Force-added ignored evidence logs (49 root `*.log`: backend,
frontend, audit, evidence, and resume-run logs cited by the
matrices).

## Excluded (deliberate, stay untracked)

- `.edge-d-probe/` (315 files): live headless-Edge profile
  internals (cookie jars, LevelDB, cache) — may hold live session
  material; never committable.
- `tmpw_ta9ikh/` (1 file): scratch snapshot, excluded per J1
  precedent.
- `webgl-fail-r10.html`: backup-class evidence, excluded per R16
  remediation.
- Ignored-by-policy (untouched): `.venv/`, `node_modules/`,
  `.next/`, `.env` + variants, `data/*`, caches.

## Pre-commit gates (all green)

- Secret scan tracked+history+chunks: HITS_TOTAL 280 = r06 baseline
  (only +7 line shifts from the CORS-fix comment).
- Secret sweep over all 599 committable untracked text files + 49
  logs: every hit adjudicated benign (translation `password:` UI
  labels, labeled test fixtures, names-only/redacted prose, scanner
  source, scan-output logs). Zero real secrets.
- Suites: pytest 465/0/0 (scratch PG), vitest 343, tsc exit 0,
  production builds exit 0, `security_gate.py` GATE PASS.
- `data/state.json` `BA1D4DB4…3790FE` (101417 B), untouched, ignored,
  not staged. HEAD `d4e2bec` verified pre-commit.

## Reconciliation

Staged count MUST equal 789 before commit (`git diff --cached
--name-only | Measure-Object`). Any drift stops the commit.
