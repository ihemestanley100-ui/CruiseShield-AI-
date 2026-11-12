# TEST RESULTS — CruiseShield AI™ (consolidated, 2026-11-03)

Branch `production-launch` @ `ff7052b` + uncommitted worktree (see §worktree).
All runs local: backend :8000, frontend :3000. Synthetic data only.

## Backend (pytest)

- Full suite: **427 passed, 73 skipped, 0 failed** (55–113 s).
  Skips are capability-gated (`needs_scratch_pg`, model-key tests), not
  exclusions: each skip declares its missing capability.
- Focused C01–C05 (ai_validation, ai_cost, evidence, graph_rules_risk,
  cases_audit, di07, di09): 84/84. One transient Windows file-lock
  (`PermissionError` in `test_provider_timeout_fails_fast`) passed alone
  — known environmental flake, recorded, not a product defect.
- Live-source integrity: `data/state.json` byte-pinned (101417 B,
  SHA-256 `BA1D…0FE`). A verification probe dirtied it once; restored
  byte-exact and the suite re-verified green. Note: ANY runtime write
  (decision, mark-read, reset) legitimately dirties this file — the
  untouched-tests assert ship-state, not runtime immutability.

## Frontend (vitest + tsc + build)

- Full suite: **391 passed / 391, 71 files, 0 failed**.
- TypeScript `tsc --noEmit`: **0 errors**.
- Production build `npm run build`: **EXIT=0, 8/8 pages** (incl. panel
  + atlas work). One SSR defect found and fixed in-session
  (`useSyncExternalStore` needed `getServerSnapshot`).
- i18n parity enforced: 587 keys × 12 locales, dumps + review kits
  regenerated via `UGLS_REGEN_KIT=1` (deterministic, diff-reviewed).

## Browser verification (headless Edge, real servers)

- Landing: 1920 / 1440 / 1100 / 834 / 500 / 844×390 — hero copy
  complete, globe unobstructed, panels/cards/CTA clear, recognition
  panel floating ≥1500px + footer bar below, zero console errors.
  True 390 px viewports cannot render here (Edge 500 px minimum
  window); sub-500 CSS kept conservative (single columns, wrapping
  nav). Finding, not failure — recorded as PARTIAL where claimed.
- Command Center (`/demo`), Network Explorer, Case page: real data,
  orbital graph, evidence-grounded AI brief (recorded live run
  `agentrun_0002`, 25.3 s), graceful 404 page — zero console errors.
- Notifications: live GET + mark-read round trip verified
  (`unread 1→0`, persisted) before state restore.

## Security checks

- R-09 F1–F4 + R1–R4 regression: green in-suite.
- Live Task-4 probe (unarmed backend): invalid-decision POST →
  `400 INVALID_DECISION` (not 401) → write gate OPEN, `DEMO_WRITE_TOKEN`
  MISSING; audit re-read clean (zero mutation). Finding stands as the
  arming requirement, not a code defect.
- Secret scan: tracked diff clean (no keys/tokens/private keys);
  client bundle contains the demo-token NAME only, value empty (R6).
- `pip-audit`: **0 vulnerabilities**. `npm audit`: **2 advisories**
  (postcss via Next 15.5.28, moderate + high) — build-time only,
  author-controlled CSS input, not runtime-exploitable here; fix
  requires breaking Next 16 upgrade → documented, deferred to an
  explicit post-submission owner decision. Prior "0 vulns" claims for
  the frontend are superseded by this section.

## Worktree under test

Uncommitted: language/notification remediation, World Atlas lock,
recognition panel, i18n kits, docs. Backend `app/` + `render.yaml` +
`.env.example` changes are prior-session work, preserved untouched.

## Verdict

Every executable check passes. No FAIL. No skipped failures. Remaining
non-green items are external (dashboard reads, provisioning, live Meta
re-call, video, portal) — see `REMAINING_OWNER_ACTIONS.md`.
