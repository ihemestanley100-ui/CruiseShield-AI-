# CRUISESHIELD-AI-PRODUCTION-GAP-REGISTER.md

Every gap between current implementation and a production-grade system.
 roduction readiness here means: provably deployed, live-verified,
 measured, and operable — not redesigned. IDs GAP-001..GAP-018.

### GAP-001 — Production PG cutover decision + design
- Affected module: app/main.py:182, app/store.py:19-39, app/db.py.
- Existing: app always boots JSON Store(); PgStore is scratch-parity
  only; `pg` selection affects health/ready probes only.
- Required: owner decision (keep JSON canonical vs PG cutover) + if PG:
  open_store boot wiring, boot-time migration gate, rollback, PG-backed
  sessions/epochs.
- Business importance: High — blocks any production-PG claim.
- Security impact: medium (session/epoch store moves).
- Dependencies: GAP-006, GAP-015, GAP-003.
- Proposed remediation: Phase 3 decision record; implement cutover only
  on approval.
- Acceptance: decision recorded; if PG: boot + migrate + health/ready +
  rollback tested.
- Verification evidence: decision doc + tests + deploy log.
- Status: NOT_VERIFIED (decision pending).

### GAP-002 — Audit tamper-evidence decision
- Affected: app/store.py:192-206, app/db.py:421-485, app/cases.py,
  migrations/loader.py.
- Existing: ordered audit_sequence + counter + PG contiguity; plaintext
  JSON editable; non-claim pinned by tests.
- Required: threat-model decision — keep ordered-for-demo vs add
  hash-chain/signing/append-only enforcement.
- Importance: Medium. Security: medium (forensic weight of audits).
- Dependencies: GAP-001 (enforcement point follows backend choice).
- Remediation: decision record; harden only if required.
- Acceptance: decision recorded; if hardening: chain/verify + tamper
  tests + loader gate.
- Status: PARTIAL 2026-11-05: hash-chain + HMAC signing implemented
  (app/audit_chain.py) with 9 tamper/rotation/export tests green;
  store-wiring + loader gate + production key ceremony still pending
  (D-018).
- Slice-5: Store.append_audit seals entries when an ephemeral/prod key
  is set (None = legacy path, zero behavior change) + 6 store-level
  tests green; loader gate + D-018 ceremony still pending.
- Slice-6: loader gate implemented (migrate_state/run_migration accept
  audit_keyring; tamper fails closed pre-write) + 3 hermetic tests
  green; D-018 ceremony still pending.

### GAP-003 — Backup execution + restore load-into-scratch
- Affected: backups/*, .github/workflows/backup-*.yml.
- Existing: full producer/restore code unit-tested with fakes;
  workflows header-disabled manual; no keys/connections; restore
  returns a plan only.
- Required: ceremony keys/shares off-repo, workflow enablement +
  reviewers, schedules, restore drill, implement load-into-scratch.
- Importance: High — no real backup exists despite tested code.
- Security: high (key custody, restore isolation).
- Dependencies: owner approval + secrets stores; GAP-010.
- Acceptance: manual dispatch green + keyless verify + read-only drill
  + scratch-load path exists.
- Status: BLOCKED (owner keys + approval) — narrowed 2026-11-05:
  LocalDirTarget + scripts/backup_drill.py execute produce→verify→
  restore→parity green with ephemeral test keys (75,242 B, parity
  true); scratch-load path + ceremony keys still outstanding.
- Slice-6: scratch-load path implemented (backups/load_scratch.py:
  live-path refusal, no-overwrite, count verification) + 5 tests
  green; ceremony keys + workflow enablement still pending.

### GAP-004 — Model eval / golden AI harness
- Affected: app/ai_adapter.py, tests/.
- Existing: rule determinism 200× + recorded latencies + mock
  fixtures; no live quality/drift check.
- Required: golden prompt/response fixtures + quality/drift
  assertions (offline) + optional live-eval lane.
- Importance: Medium. Security: low.
- Dependencies: GAP-014 (capture golden from live call if run).
- Acceptance: hermetic eval suite with thresholds + drift signal.
- Status: IMPLEMENTED 2026-11-05 (branch feat/phasezero-foundations):
  tests/test_ai_eval.py, 8 golden fixtures, all passing. Live-quality
  lane still gated on GAP-014.

### GAP-005 — Coverage measurement
- Affected: tests/, frontend/, CI.
- Existing: no pytest-cov / vitest coverage / codecov config; broad
  suites unmeasured.
- Required: coverage providers + thresholds + CI report, or explicit
  no-coverage decision.
- Importance: Low-Medium. Dependencies: GAP-006.
- Acceptance: coverage command + config + CI artifact, or decision.
- Status: NOT_IMPLEMENTED.
- 2026-11-05: tooling absent (no pytest-cov; no
  @vitest/coverage-*). Install = lock churn + gate re-proof →
  BLOCKED pending owner approval of coverage-dependency pins.
- 2026-11-05 slice-4: pins verified with PyPI hashes (pytest-cov
  7.1.0 `a0461110…d4678`; coverage 7.10.6 win `62805529…79d32` +
  linux `0f3f56e4…d4f27`; pytest 9.0.3/pluggy 1.7.0 already locked;
  vitest provider 3.2.7 matches lock). Awaiting lock-churn approval
  (D-020).

### GAP-006 — Full green run for current tree
- Affected: tests/ (518 backend), frontend/ (72 files).
- Existing: latest logs cover 476 (403+73) / 64-file-354; tree grew
  past them (c0bec5e/ed7674d/b4732cb + dirty worktree).
- Required: fresh full backend + frontend runs on clean HEAD +
  updated checkpoint; fresh --collect-only settles 46/47 drift.
- Importance: High — TESTED verdicts rest on older logs + bodies.
- Dependencies: none (first gate).
- Acceptance: dated pass logs matching HEAD + refreshed matrix.
- Status: PARTIAL 2026-11-05: 49 files / 536 collected (drift settled:
  47 pre-change + 2 new files). Full backend run: 396 passed, 137
  skipped (sandbox socket gates), 1 failed + 2 errors — all three are
  sandbox-only environment failures (node EPERM, WinError 10013),
  identical to the known resume-r06 signature. Frontend not re-run
  (untouched).
- Slice-4 rerun 2026-11-05: 431 passed (+30 new), 137 skipped,
  same 1 failed + 2 errors (identical sandbox-only signatures).

### GAP-007 — Live-WebGL hero path untested
- Affected: frontend/components/landing/GlobalHeroScene.tsx:52-327.
- Existing: only fallback path tested (jsdom has no WebGL).
- Required: browser smoke (manual checklist or Playwright/WebGL
  harness) + context-loss restore proof.
- Importance: Medium (landing-critical). Dependencies: GAP-009 or
  local live run.
- Acceptance: recorded browser pass incl. gestures + restore.
- Status: NOT_VERIFIED.

### GAP-008 — netlify.toml stale (publish .next, no adapter)
- Affected: netlify.toml:1-4, frontend/package.json, docs.
- Existing: 4-line minimal; SSR app incompatible with static hosting;
  migration recorded "unbuilt"; Render canonical.
- Required: owner call — remove file, or add OpenNext adapter +
  plugin + verified build/serve.
- Importance: Medium — invites a broken deploy if pointed at repo.
- Dependencies: owner hosting decision; GAP-009.
- Acceptance: removed/corrected + verified build log, or explicit
  legacy-stub label.
- Status: PARTIAL 2026-11-05: OpenNext plugin configured in
  netlify.toml (owner choice: repair path); verified build/serve log
  still pending (GAP-009/GAP-010). See Netlify A-E report.

### GAP-009 — Deploy never executed / Render state unverified
- Affected: Dockerfile, render.yaml:13-104, docs/DEPLOYMENT.md.
- Existing: manual Blueprint complete; no CI deploy; dashboard not
  inspected.
- Required: owner-approved first deploy (backend→frontend order) +
  dashboard-vs-blueprint reconciliation + health/ready proof.
- Importance: High — deployability unproven.
- Dependencies: GAP-006, GAP-010, GAP-011.
- Acceptance: live /api/v1/health + /ready + / + deploy log.
- Status: BLOCKED (owner approval).

### GAP-010 — GitHub Actions dispatch greenness unverified
- Affected: .github/workflows/security-gate.yml.
- Existing: only local 6/6 PASS log; no GitHub run record in repo.
- Required: push/PR/weekly dispatch observed green on GitHub.
- Importance: Medium. Dependencies: GAP-006.
- Acceptance: linked green gate run.
- Status: NOT_VERIFIED.

### GAP-011 — Docs token-rule conflict + count drift
- Affected: docs/RENDER_6_ENV_REGISTER.md:23 vs render.yaml:95-100 +
  frontend/.env.example; docs/TEST_RESULTS.md @ff7052b.
- Existing: register says public demo token = backend value (staging);
  R6 rule says LEAVE-EMPTY; TEST_RESULTS predates HEAD.
- Required: one-line register correction + refresh counts to HEAD.
- Importance: High (live env-wiring conflict) / Low (drift).
- Dependencies: GAP-006 (fresh counts).
- Acceptance: register matches render.yaml; checkpoint matches HEAD.
- Status: FIXED 2026-11-05 (docs/RENDER_6_ENV_REGISTER.md:23 now states
  the R6 LEAVE-EMPTY rule verbatim).

### GAP-012 — 9 backend routes with no frontend client
- Affected: frontend/lib/api.ts vs app/main.py.
- Existing: zero frontend references for txn base GET, accounts-intel
  (only DI route without a client), ai-runs GET, events POST, cases
  list, demo start, demo judge-start, ready, evidence-package alias.
- Required: per-route product decision — wire, keep API-only, or
  deprecate.
- Importance: Medium. Dependencies: none.
- Acceptance: per-route wired/documented/removed + client tests.
- Status: IMPLEMENTED 2026-11-05 (branch feat/phasezero-foundations):
  3 wired with new clients + page tests (txn base → network header,
  accounts-intel → investigation account blocks, ai-runs → case run
  expander); 6 recorded API-only with reasons (events, cases list,
  demo start/judge-start, ready, evidence alias). Zero new i18n keys
  (all labels reused across the 12 locales).
- 2026-11-05: new GET /api/v1/industries ships API-only (no
  client yet) per this gap's convention. Batch-1.1 frontend
  rerun BLOCKED by sandbox node EPERM; hosted-CI confirm
  pending (GAP-010). Backend slices re-verified: 25 passed.

### GAP-013 — 5 frontend clients dead outside tests
- Affected: frontend/lib/api.ts, frontend/app, frontend/components.
- Existing: getDevice, getIpObservations, getGeoObservations,
  getTransactionIntel, listAlerts — tested, never called by pages.
- Required: wire into pages/components, or remove/keep-as-library
  with documented reason.
- Importance: Medium. Dependencies: GAP-012 (joint pass).
- Acceptance: each called by a page/component or explicitly
  library-only/removed.
- Status: IMPLEMENTED 2026-11-05 (branch feat/phasezero-foundations):
  4 wired — device/IP/geo drill-downs in IntelSection, txn intel on
  the network page; listAlerts explicitly library-only (notification
  center is the canonical surface). Component + page tests added.

### GAP-014 — Live AI provider call never executed
- Affected: app/ai_adapter.py, app/config.py, TEST_EVIDENCE.md B-001.
- Existing: live-capable impl; MODEL_API_KEY unset; contract via
  docs; 4 historical latencies; verification pending.
- Required: keyed staging live call, or explicit no-live decision.
- Importance: Medium. Dependencies: secrets provisioning; feeds
  GAP-004 golden capture.
- Acceptance: keyed run log (VALIDATED path) or recorded decision.
- Status: BLOCKED (key + approval; free-tier policy).

### GAP-015 — Scratch-PG live pass unverified
- Affected: tests/test_pg_*.py, SCRATCH_DATABASE_URL.
- Existing: live-PG tests skip without scratch DB; never executed
  this audit.
- Required: provision scratch PG + run parity/migration/atomic/
  hardening suites.
- Importance: Medium. Dependencies: scratch DB provisioning.
- Acceptance: scratch-PG green log on HEAD.
- Status: NOT_VERIFIED.
- Slice-6: local execution impossible (no psql/pg_config/pgserver;
  docker pipe denied); suites remain CI-gated via the postgres
  service job. Loader-gate logic covered hermetically instead.

### GAP-016 — Manifests untested + no digest pin
- Affected: Dockerfile, render.yaml, requirements files.
- Existing: complete + coherent; no asserting test inspected;
  install not executed; no digest pin (R-09 F5 PREPARED, NOT APPLIED).
- Required: manifest-assertion tests + locked install + digest-pin
  decision.
- Importance: Low-Medium. Dependencies: GAP-006, GAP-009.
- Acceptance: install green + pins asserted or decision recorded.
- Status: PARTIAL 2026-11-05: tests/test_deploy_manifests.py pins all
  Dockerfile/render.yaml properties (5 passing). Locked-install
  execution + digest-pin decision still open.

### GAP-017 — actor_role hardcode + attribution follow-up
- Affected: app/cases.py:63, app/main.py:281-290.
- Existing: role hardcoded INVESTIGATOR; token→demo-token fallback.
- Required: thread real session role into record_decision (keep
  token fallback) + audit test.
- Importance: Low. Dependencies: none.
- Acceptance: decision audit carries caller role; token path still
  demo-token; tests pass.
- Status: IMPLEMENTED 2026-11-05 (branch feat/phasezero-foundations):
  cases.ACTOR_ROLES + record_decision(actor_role) with fail-closed
  validation; endpoint threads live session role; 5 new tests
  (3 run green locally, 2 socket-gated for CI).

### GAP-018 — Single-instance rate limit + RISK flag provider doc
- Affected: app/ratelimit.py, app/main.py:152-169,732,755.
- Existing: in-memory window, documented single-instance-only; RISK
  flag provider undocumented (test fixture only).
- Required: scale note (sticky/Redis design if multi-instance) +
  flag-provider documentation.
- Importance: Low (fine for demo/staging).
- Dependencies: GAP-001/GAP-009 if scaling.
- Acceptance: scale note + flag doc; no demo code change needed.
- Status: DONE 2026-11-05: verified the single-instance scale limit is
  already documented in app/ratelimit.py:1-12 and the flag provider in
  app/risk_intel.py:28-54; added the missing RISK_INTELLIGENCE_V2_ENABLED
  entry to .env.example (names-only).
