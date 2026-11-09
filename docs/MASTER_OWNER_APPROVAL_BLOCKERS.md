# MASTER OWNER APPROVAL BLOCKERS — Campaign 2026-11-08

Approval-ready packages. Nothing below is authorized until the owner
grants that exact item. $0-only throughout.

## O-01 — B7 scratch-PG execution (unblocks QA-02)
Exact approval: "B7 approved: execute the 73 registered
scratch-PG tests on job-scoped CI PostgreSQL with zero production
data." Evidence after: hosted run ID + per-test results. No
provisioning, no migration, no production data.

## O-02 — Matrix-owner transitions ×11 (planning-approved only)
Transition to CLOSED_VERIFIED: DET-12, DET-13, FE-01, SITE-01,
THEME-01, TEL-05, MAP-02, UFI-UI, UFI-UI2, AGOS-UI, REC-UI.
Basis: hosted runs 42501376167/42515350200 SUCCESS. Limitation:
aggregate evidence (per-test PG lines unobserved); I18N-02 stays open.

## O-03 — Netlify production-branch confirmation (unblocks DET-14/INF-01 path)
Owner reads Netlify dashboard (Site cruiseshieldai → Settings →
Build & deploy → Production branch) and records the value. Merging
PR #2 into `production-launch` may trigger production deployment.

## O-04 — M3A + campaign commit & push (16 + 10 paths)
Commit exactly: pyproject.toml, governance doc, 6 MASTER docs,
4 M3 test files, security-gate.yml, 9 micro-fixed source files.
Then push `feat/phasezero-foundations` and observe the gate (ruff
step runs hosted for the first time). No merge.

## O-05 — Independent human PR review (G12 path)
Reviewer (not the change author) submits APPROVE/REQUEST_CHANGES/
COMMENT on PR #2 at its final SHA. Muse COMMENT draft is prepared;
submission itself is blocked on `gh auth login` refresh.

## O-06 — Held/deferred decisions (each separate, none recommended here)
GAP-001/DB-01 (PostgreSQL), D-018/BAK-01/AUD-01 (prod backup/keys),
D-015/REL-01 (licence), D-056/DATA-01 (retention purge),
D-019b/REL-02 (demo aliases), D-053/AI-01/AI-03/LIVE-*/TEL-08/UFI-LIVE
(NO-LIVE lift), D-054/UFI-AIMODEL (PII lane), D-055/LEAFLET (tiles),
PKG-09/AUTH-01..09 (federation), D-057 (scratch PG), D-058 (scheme
law), CICD-01 (coverage thresholds), P1/P2 (logging/perf harness).

## External (non-owner) inputs
I18N-02 human translators; VIS-01 reference image; provider
credentials/agreements for any LIVE lane; qualified legal/privacy
review (D-058, D-056, D-015).
