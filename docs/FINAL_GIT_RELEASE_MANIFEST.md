# FINAL GIT RELEASE MANIFEST (R16)

Date: 2026-11-02. HEAD `d4e2bec` (public master). Tree: **97 modified
+ 94 untracked = 191 entries**. NO staging/commit/push performed or
authorized by this programme — this manifest is the approval request
artifact. Raw list: `tree-status-r16.txt` (local, transient).

Note: 11 further untracked docs landed after the count (the 10
`FINAL_*` audits + `FINAL_INDEPENDENT_AUDIT.md` itself) → 202 entries
at close. They belong to Group 4 by the same INCLUDE rule; regenerate
the raw list before any staging approval.

## Proposed commit groups (recommendation; owner approves exact list)

### Group 1 — Application source (modified, 78 files) → INCLUDE

- `app/`: auth, config, db, main, models_pg, rules, store (7).
- `frontend/`: converted pages/components/lib incl. i18n call sites,
  `<bdi>` isolation, CSP header config, CORS-compatible client (57,
  excluding the 2 config files in Group 3).
- `tests/`: 12 modified suites (auth, CORS, AI, PG parity, flow…).
- `Dockerfile` (non-root + PORT-aware healthcheck), `render.yaml`.

### Group 2 — New source (untracked, 17 paths) → INCLUDE

- `frontend/lib/i18n/` (registry, dictionaries, 12 locales, meta,
  format, coverage, context + tests), `language-selector.*`,
  `locale-switching.test.tsx`, `session.*`, `site-url.*`,
  `next.config.test.ts`, `icons.test.ts`.
- `scripts/migration_manifest.py`, `scripts/perf_smoke.py`.
- `tests/test_auth_e2e.py`, `test_config_safety.py`,
  `test_j5_rehearsal.py`, `test_j6_drill.py`, `test_security_gate.py`.

### Group 3 — Configuration (modified) → INCLUDE

- `.env.example`, `frontend/.env.example` (names + placeholders only —
  scanned, no values), `.gitignore`, `README.md`, `frontend/README.md`.

### Group 4 — Programme documentation (14 modified + 68 untracked = 82) → INCLUDE*

- All J3–J10 / judging / UGLS / Final reports (the 14 modified docs
  are COMMAND_EXPERIENCE ×6, HACKATHON_ASSET_AND_CODE_PROVENANCE,
  HACKATHON_ZERO_GAP_MATRIX, KNOWN_LIMITATIONS,
  PHASE_13_ASSET_AND_CODE_PROVENANCE, PHASE_2B_REMAINING_GAPS,
  RENDER_6_ENV_REGISTER, TEST_EVIDENCE, ZERO_COST_A_TO_J).
  *Owner may curate; default recommendation is the full record (it is
  the audit trail).

### Group 5 — QA reproducibility scripts (untracked) → INCLUDE

- `rtl-qa-ugls02.ps1`, `rtl-matrix-ugls02.ps1`, `rtl-dom-ugls02.ps1`,
  `csp-qa-r07.ps1`, `secret-scan-r06.py`.

### EXCLUDE (never stage)

- `rtl-evidence-ugls02/` (screenshots/DOMs) — preserve via backup,
  not source commit. Owner may override.
- `webgl-fail-r10.html` — same evidence class as above; backup, not
  commit.
- `tmpw_ta9ikh/` — preserved untouched per standing directive.
- `tree-status-r16.txt` — transient manifest working file.
- `*.log` (gitignored) — local evidence only.
- `.env` (live secrets) — untracked + gitignored; verified.
- `data/state.json` — hash-stable (BA1D4DB4…3790FE, 101417 B) and
  gitignored (not tracked in HEAD); no action.

Reconciliation: 78 + 5 + 82 + 17 + 5 + 4 excluded paths = 191. (R17
correction: Group 1 was undercounted at 71; modified docs and
`webgl-fail-r10.html` were unassigned — fixed.)

## Pre-commit verification (all green at manifest time)

Backend 463/463 · frontend 321/321 · tsc 0 · build 0 · security gate
PASS · secret scan clean (history + tracked + bundles) · state hash
unchanged.

## Required owner approvals (separate, in order)

1. Approve this exact file manifest (or amended list).
2. Approve `git add` of the listed paths only (no `add -A`).
3. Approve commit message + commit execution.
4. Approve push (separate), tag/release (separate).
