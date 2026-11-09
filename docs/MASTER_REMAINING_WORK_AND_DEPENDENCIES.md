# MASTER REMAINING WORK AND DEPENDENCIES — Campaign 2026-11-08

Dependency order. Items marked DONE were completed by this campaign.

1. DONE — M3A verification: ruff gate green locally; ESLint blocked
   (sandbox Node EPERM, zero existing deps); governance doc added.
2. DONE — Additive suites: 22 tests (store durability, billing
   edges, fraud validation matrix, security edges) green + linted.
3. DONE — Full local validation: 1401 passed / 142 skipped /
   1F+2E sandbox-only; matrix untouched (192/152/40).
4. DONE — Registers: traceability (192), gap register (40),
   evidence index, approval blockers, readiness report, this file.
5. NEXT — Owner: O-04 commit+push approval → hosted gate observes
   the new ruff step (unblocks M3A hosted proof, FE-01 refresh).
6. NEXT — Owner: O-01 B7 approval → 73 scratch-PG tests → QA-02.
7. NEXT — Owner: O-02 matrix transitions ×11 → 163/192.
8. NEXT — Owner: O-03 Netlify branch readout → merge-risk verdict.
9. NEXT — Owner: `gh auth login` refresh → submit prepared PR
   COMMENT → O-05 independent human review.
10. BLOCKED — Merge/deploy/DET-14/INF-01: require O-03 + O-05 +
    explicit merge + deploy approvals (none granted).
11. BLOCKED — DB/DATA/BAK/AUD/REL/LEAFLET/AUTH/AI-LIVE lanes:
    require their O-06 decisions one by one; code packages are
    prepared, execution forbidden without approval.
12. BLOCKED — I18N-02/VIS-01/providers/legal: external inputs only.
13. NEVER auto — production data, secrets, billing, purges,
    migrations, paid resources: each needs its own explicit grant.

Critical path to RELEASE CANDIDATE: O-04 → O-01 → O-02 → O-03 →
O-05 → merge approval → deploy approval → DET-14/INF-01 → G-gates.
Production-verified additionally needs O-06 database/backup/legal
decisions and live operations evidence.
