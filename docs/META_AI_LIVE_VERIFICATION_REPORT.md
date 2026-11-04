# META AI LIVE VERIFICATION REPORT

STATUS: BLOCKED (no quota-spend approval; no live call made
in this programme).

Standing evidence (not re-fabricated, cited):

- 7 historical live runs recorded in
  docs/SUBMIT_D_METAAI_EVIDENCE.md (code + runs).
- Red-team hostile-injection vs live API:
  docs/REDTEAM_LIVE_AI_REPORT.md.
- Phase 3.4 live demonstration: docs/PHASE_3_4_LIVE_AI.md.
- J7 incidental evidence: 2 live HTTP 200 completions
  during unsandboxed suites (disclosed, unapproved spend —
  hermetic fixture now prevents recurrence).

What a future approved live verification must show:

1. Single authorized call, inv_84721 package, observed 200.
2. Response validates (schema + evidence refs) and persists.
3. Timeout path (short timeout) returns MODEL_TIMEOUT.
4. Daily-limit path returns audited 429 at cap+1.
5. Key-absent path returns MODEL_NOT_CONFIGURED (hermetic).
6. Spend logged against owner quota; receipt retained.

Until then, "live AI" claims rest on the historical runs
above, and the demo storyboard uses the honest fallback
branch (see docs/DEMO_FAILURE_FALLBACK_PLAN.md).
