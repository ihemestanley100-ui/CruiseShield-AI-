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
- Slice-7: CLI keyring wiring implemented (--audit-keyring loads an
  operator-supplied {key_id: hex} file before migration, rejects
  malformed/short keyrings without exposing key material, and calls
  run_migration with bytes) + 12 focused tests green; D-018 ceremony
  still pending.
- Slice-8 (2026-11-06): operator export + verification surface
  (audit_chain.verification_report + scripts/audit_export.py
  export/verify subcommands; structured ok/sealed/head/key_ids/
  error reports; key material never printed) + 10 tests green;
  D-018 production ceremony still pending (AUD-02 closed).

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
- Re-verified 2026-11-05: drill exit 0, parity true (75,242 B
  scratch plaintext, backup csbk-20261105-230835Z); canonical
  data/state.json hash unchanged (BA1D4DB4…3790FE).
- Re-verified 2026-11-06: drill exit 0, parity true, all
  signature/sha/decrypt checks green (backup
  csbk-20261106-021504Z, 0.06 s); scratch dir cleaned after;
  canonical hash unchanged.

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
- Tenant-slice rerun 2026-11-06: 908 passed, 141 skipped, same 1
  failed + 2 errors (node EPERM lstat, WinError 10013 CORS setup;
  identical sandbox-only signatures). Covers transaction/graph/
  risk tenant gating + agent visible_graph refactor. Frontend not
  re-run (untouched).
- Alert-slice rerun 2026-11-06: 911 passed (+3), 141 skipped,
  same sandbox-only 1F+2E. Covers alert/notification tenant
  filtering via visible transactions + mark-all scoping.
- DI-slice rerun 2026-11-06: 916 passed (+5), 141 skipped,
  same sandbox-only 1F+2E. Covers visible_state view wired
  into all 9 derived-intel handlers.
- Replay/AI-slice rerun 2026-11-06: 921 passed (+5), 141
  skipped, same sandbox-only 1F+2E. Covers replay
  visible_state gating + ai-runs tenant enforcement,
  stamping, and case-summary filtering.
- Simulation-slice rerun 2026-11-06: 924 passed (+3), 141
  skipped, same sandbox-only 1F+2E. Covers simulation
  target gating + visible-input recomputation + tenant
  stamps + investigation-page filtering.
- Identity-slice rerun 2026-11-06: 926 passed (+2), 141
  skipped, same sandbox-only 1F+2E. Covers README
  platform rewrite (docs-only) + product-identity hygiene
  gate; zero behavior change.
- Audit-slice rerun 2026-11-06: 936 passed (+10), 141
  skipped, same sandbox-only 1F+2E. Covers
  verification_report + audit_export CLI + 10 tests;
  backup drill separately re-verified exit 0/parity.
- Risk-slice rerun 2026-11-06: 948 passed (+12), 141
  skipped, same sandbox-only 1F+2E. Covers login-risk
  scoring + baselines + 12 tests; legacy login body,
  MFA ticket, and failure-audit shapes unchanged.
- Notif-slice rerun 2026-11-06 (resumption session): 958
  passed (+10), 141 skipped, same sandbox-only 1F+2E
  (node EPERM lstat on test_static_escaping + CORS-setup
  PermissionErrors, each re-verified individually).
  Covers D-029 per-user security notifications (risk/mfa
  notices, merged list/read endpoints, 10 tests).
- Gate-slice rerun 2026-11-06 (L13/L14 session): 961 passed
  (+3), 141 skipped, same sandbox-only 1F+2E. Covers
  tests/test_quality_gates.py (Part 21 gates 1/9/16).
  Read-only probes: NETWORK_PROXIMITY fires 11/136 seed
  signals (non-emptiness closed); family_errors entries
  untriggered by malformed-input probes (non-dict input
  raises uncaught AttributeError) — robustness finding
  queued for BATCH-7, no behavior changed.
- Dedup-slice rerun 2026-11-06 (Phase 2 BATCH-1): 962
  passed (+1 b64 test), 141 skipped, same sandbox-only
  1F+2E. Covers _b64 unification (auth canonical),
  verify_session removal (test migrated to parse_session),
  single live validation in write gate. Credential/actor
  unification investigated and REJECTED per D-034
  (unarmed-mode semantics + distinct contracts).
- Phase 3+4 rerun 2026-11-06: 974 passed (+12), 141 skipped,
  same sandbox-only 1F+2E. Covers POST /cases API + 6 tests
  (CASE-01), fault-path skip D-035 (DET-16), per-family
  emission test, 45/45 modules verified separately
  (315/315 isolated), conformance sweep + honesty/promote
  tests. Matrix 105 rows, 79 closed. Zero PRODUCTION_READY
  industry claims (all TESTING-or-below by evidence).
- Phase 5 rerun 2026-11-06: 1019 passed (+45), 141 skipped,
  same sandbox-only 1F+2E. Covers user registry + admin
  provision + flag-off self-register (9), verification
  tokens (10), password/sessions/prefs (6), trial/sub/
  founder/metering (11), payments/Web3 stub (9). Matrix
  111 rows, 84 closed. Passkeys deferred (SEC-PASSKEY),
  themes FE-gated, delivery/providers owner-blocked.
- Audit-slice rerun 2026-11-07: 1081 passed (+7 vs the 1074
  Phase 7-8 line in PROJECT_EXECUTION_STATE.md), 141
  skipped, same sandbox-only 1F+2E (node EPERM lstat +
  2 CORS-setup PermissionErrors, signatures re-verified).
  Covers AUD-03 ingest audit + AUD-04 health chain
  presence + 7 tests (D-049/D-050). Matrix 115 rows,
  91 closed. data/state.json hash unchanged.
- Export/review-slice rerun 2026-11-07: 1089 passed (+8),
  141 skipped, same sandbox-only 1F+2E (same test names).
  Covers EVID-01 canonical export + hash header + 4 tests
  (D-051) and SEC-REV admin access-review + 4 tests
  (D-052). Matrix 115 rows, 93 closed. data/state.json
  hash unchanged (BA1D4DB4…3790FE, 101417 B).


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

### DETECTION ACCEPTANCE — Live detection intelligence directive §14
- Scope: app/detection.py, app/channels.py, 10 APIs
  (/detectors, /signals/summary, /channels/summary,
  /detection/matrix, /signals/by-transaction/{txn_id},
  /signals/search, /signals/time-series, /signals/{signal_id},
  /signals/{signal_id}/outcome, /signals/{signal_id}/link),
  Command Center DetectionSection + txn panel + kit rows.
- Evidence: tests/test_detection.py (34 green + 4 socket-gated
  for CI), offline slice-3 probe 33/34 automated + 1 resolved
  by inspection (pre-existing env-name read, value empty per
  R6), suite 503 passed / 141 skipped / same sandbox-only
  1F+2E (WinError 10013 + node EPERM re-verified 2026-11-05),
  state hash BA1D4DB4…3790FE intact.
- AC-01 detector statuses: PASS (10 OPERATIONAL + ML_ANOMALY
  NOT_IMPLEMENTED, registry-tested).
- AC-02 channel taxonomy: PASS (8 canonical + UNMAPPED alert).
- AC-03 signal persistence: PARTIAL (outcome + link records
  persist with history in signal_outcomes/signal_links;
  signal_events stay derived-on-read per D-021 and await
  GAP-001 PG cutover).
- AC-04 frequency reconciliation: PASS (summary + time-series
  buckets reconcile to source signals).
- AC-05 channel reconciliation: PASS.
- AC-06 matrix verification: PASS (88 cells + evidence refs).
- AC-07 tenant isolation: PASS (summary, drill-down, search,
  detail, outcome, link — foreign reads 404).
- AC-08 drill-down: PASS (API + consistency tests).
- AC-09 investigation linkage: PASS (derived chain + explicit
  POST link, idempotent, audited).
- AC-10 audit provenance: PASS (audits-target-case + sealing;
  outcome/link writes audited).
- AC-11 backend tests: PASS (modulo sandbox-only 1F+2E).
- AC-12 frontend tests: BLOCKED (node EPERM: realpathSync must
  lstat C:\\Users\\HP; 4 workarounds failed; needs hosted CI).
  TimeSeriesPanel + FP-row tests written, unexecuted locally.
- AC-13 hosted CI: BLOCKED (D-017 push authorization).
- AC-14 deployment: BLOCKED (D-017 / GAP-009).
- AC-15 no fabricated stats: PASS (measured zeros, SEED_FEED,
  NOT_IMPLEMENTED labels, FP null-basis, all asserted).
- Slice-3 extras: UTC bucketing (hour/day/week/month), strict
  ISO-8601 filters, paged search, execution envelope
  (execution_id, per-family runs/latency/errors), FP rate with
  review basis, unique-investigation counts, write-gated +
  audited outcome/link POSTs, SVG time-series panel.
- Follow-up: hosted CI execution + deployment (AC-12/13/14);
  persisted signal_events store (GAP-001).

### PUSH-AUDIT — feat/phasezero-foundations pre-push review (2026-11-05)
- Range: master..HEAD = 16 commits (58a3d50..d82627d);
  11 new vs origin/production-launch tip b4732cb
  (fe9f64e..d82627d); 198 files, +11788/-5734.
- Filenames: only .env.example files (verified names-only),
  DEMO_TOKEN docs, pre-existing secret-scan tooling (on
  master, not introduced here), token tests. No .env, keys,
  keystores, DBs. 77 added files, zero binary/junk by
  extension. data/state.json never in history (.gitkeep only).
- Content (added lines): zero private-key/AWS/GitHub/Slack/
  Stripe/Google shapes; zero DB-URL credentials; 4 literals
  all in tests/ with obviously-fake values
  (test-secret-*-not-a-real-cred / -not-a-secret,
  test-secret-32-chars-minimum-ok!!); zero emails; zero
  phone-like sequences; DEMO_USERS prose-only; 2 doc lines
  are scan-verification meta-text (benign, context-checked).
- Committed secrets-r06.log: finding metadata only
  (HIT file:line:rule), no embedded values (one long line is
  the ENV_NAMES name list).
- Vulns at HEAD (app/*.py): zero eval/exec/os.system/
  shell=True/pickle.loads/yaml.load/__import__.
- Verdict: PASS — no production secrets, credentials,
  customer data, accidental files, or flagged vuln patterns
  in the 16 commits. Safe to push.
- Push NOT executed from this session: origin unreachable
  (SEC_E_NO_CREDENTIALS) and gh token invalid (account
  cruisestore05-debug). Owner handoff commands recorded in
  the session report; PR + CI evidence pending owner push.
- Worktree preserved: 255 entries untouched (233 in the
  approval was stale); no stage/commit/discard performed.
