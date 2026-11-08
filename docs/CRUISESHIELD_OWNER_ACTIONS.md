# CRUISESHIELD OWNER ACTIONS — CS-FRC-2026-001 §13.5

Date: 2026-11-04. Ordered by dependency. Nothing below can be executed without
the owner; everything else executable is already done.

1. **R1/R2/R11/R12 read-outs** (names/plans only, never secret values):
   env-var presence (3 names), full 40-char deployed SHA, services-page
   plan/price list, pipeline spend-cap value. Unblocks P2/P5/P6 evidence.
2. **R3 arming**: set `SESSION_SECRET`, `DEMO_USERS`, backend-only
   `DEMO_WRITE_TOKEN` in the Render dashboard and redeploy. I then verify
   `auth_enabled:true` and run safe R1–R4 probes. Unblocks P2/P4 live PASS.
3. **Frontend provisioning authorization**, only after the $0 gate passes.
   Unblocks P2 and deployed-browser evidence for P3.
4. **Meta decision**: approve ONE explicit diagnostic call (key on file timed
   out; bare egress works) or rotate/revoke the key; when arming, set
   `AI_DAILY_CALL_LIMIT` to 1–5 initially. Unblocks P5 diagnosis.
   UPDATE 11-04: timeout mechanism solved — key passes auth, stall is
   downstream. Open `dev.meta.ai/platform` and report key status,
   usage/quota, billing state; then fund/enable or approve one
   instrumented call (≤~$0.025, synthetic only).
5. **Manifest + LICENSE + push**: approve the 141/383 split in
   `CRUISESHIELD_RELEASE_MANIFEST.md`, select a license, authorize the exact
   commit message and push. Unblocks P7.
6. **PostCSS**: accept the residual risk or approve the breaking Next-16
   upgrade (with full re-verification). Closes S-03 either way.
7. **Video + portal submission** (deadline-driven, owner-performed).

No question above is answerable from the repository — each needs dashboard
access, a legal call, a spending decision, or an explicit authorization.
