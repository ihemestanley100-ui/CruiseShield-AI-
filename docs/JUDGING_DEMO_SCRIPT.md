# JUDGING DEMO SCRIPT (Category D — 25%)

Canonical long-form scripts: docs/SUBMIT_H_DEMO_SCRIPT.md,
docs/HACKATHON_FINAL_DEMO_SCRIPT.md. This is the verified
18-step judging path; every step names its real route and
was verified to exist with tests on 2026-11-02.

1. Open `/` — landing, Three.js hero, honest impact copy.
2. Read the problem: disconnected transactions hide crime
   (hero copy, pinned by test).
3. `Enter Demo` → login-gate (J4 protected login) → `/demo`.
4. Open `/investigations/inv_84721` — the case workspace.
5. Suspicious txn: #84721, ₦480,000, MOBILE_APP (demo data).
6. Deterministic scores with rule refs (R-001…R-008).
7. Txn-only 35 MODERATE vs network 84 HIGH — scopes labelled.
8. `/network/txn_84721` — 22-node / 30-edge graph.
9. Trace edges; each has source evidence.
10. Triggered rules panel with contributions.
11. AiPanel → Run analysis (live if quota approved, else the
    honest fallback branch — never a mock labelled live).
12. Evidence IDs cited per finding.
13. Missing/conflicting evidence + uncertainty shown.
14. Suggested next steps (each requires human approval).
15. `/replay/scn_primary` — controlled simulation.
16. decision-form — investigator records the decision.
17. `/cases/case_84721/audit` — append-only trail.
18. Close: connected evidence + human accountability; pilot
    metrics to be measured, none claimed.

Timing: fits 3 minutes at natural pace with the storyboard
beats (docs/JUDGING_VIDEO_STORYBOARD.md).
