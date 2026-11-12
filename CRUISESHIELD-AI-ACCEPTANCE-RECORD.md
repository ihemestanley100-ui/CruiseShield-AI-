# CRUISESHIELD-AI-ACCEPTANCE-RECORD.md

Delivery packages, criteria, results, evidence, reviewers, and
outstanding defects. Reviewer "Owner" with status REPORTED means
delivered and awaiting explicit sign-off; ACCEPTED means the
owner authorized follow-on work (implicit acceptance of the
package as a basis — not a quality certification).

## ACP-01 — Phase Zero audit pack
- Contents: forensic audit, current-state matrix, gap register
  (GAP-001..018), dependency register, roadmap.
- Criteria: read-only; file-level evidence per finding.
- Tests: none (audit). Evidence: 5 root docs.
- Reviewer: owner. Status: ACCEPTED (proceed authorized).
- Defects: none; gaps tracked in register.

## ACP-02 — Foundations (GAP-017/016/004/011/018)
- Contents: actor-role threading; deploy-manifest tests;
  AI-eval harness; token doc fix; flag/scale doc.
- Criteria: separate branch; preserve behavior; add tests.
- Tests: test_deploy_manifests 5 pass; test_ai_eval 8 pass.
- Evidence: branch feat/phasezero-foundations; suite runs.
- Reviewer: owner. Status: ACCEPTED (next workstream ordered).
- Defects: none open.

## ACP-03 — Batch 1.1 end-to-end workstream
- Contents: getTransaction/getAccountIntel/getAiRun clients;
  intel drill-downs; network/case expanders; matrix update.
- Criteria: genuine functionality, tests, no scope creep.
- Tests: route/component suites green (405 frontend asserts in
  release run).
- Evidence: frontend/lib/api.ts, intel-panels.tsx, pages.
- Reviewer: owner. Status: ACCEPTED (assessment ordered).
- Defects: none open.

## ACP-04 — Production release assessment
- Contents: full backend+frontend suites, builds, gates,
  evidence-backed matrix.
- Criteria: run everything; no readiness claim without gates.
- Tests: backend 396 pass / 137 skip / 1 fail + 2 env errors;
  frontend 405/405; tsc 0; build 8/8; secret_scan PASS.
- Evidence: CRUISESHIELD-AI-RELEASE-ASSESSMENT.md.
- Reviewer: owner. Status: REPORTED — verdict NOT READY.
- Defects (withheld gates): tenancy FAIL; deploy/CI/AI/backup
  NOT_VERIFIED or BLOCKED; license missing.

## ACP-05 — Framework alignment + registers
- Contents: alignment doc, decision log, RAID log, this record;
  backup lane + security gate re-runs.
- Criteria: counts verified; N/A proven; no unearned upgrades.
- Tests: backup lane 94 pass / 1 skip (2026-11-05).
  security_gate.py --skip-audit (2026-11-05): lock_covers PASS
  (16 pins); lockfile_hashes PASS (37 pins, 463 hashes);
  secret_scan PASS; installed_matches_lock + pip_check FAIL —
  same shared-interpreter signature as release assessment
  (torch/lerobot/moviepy data-science packages, not product).
- Evidence: CRUISESHIELD-AI-FRAMEWORK-ALIGNMENT.md,
  CRUISESHIELD-AI-DECISION-LOG.md, CRUISESHIELD-AI-RAID-LOG.md.
- Reviewer: owner. Status: IN PROGRESS (this report).
- Defects: pip_audit SKIPPED offline (OSV unreachable; full
  gate without --skip-audit hangs on network). Lock-installed
  env proof still outstanding — needs clean CI env.

## ACP-06 — Level-14 execution slice 1
- Contents: W1 closed-gap re-verification; industry registry +
  GET /api/v1/industries; demo removal matrix; ops runbook;
  D-019 proposal; GAP-005 blocker record.
- Criteria: implement + test unblocked items; no unverified
  upgrades; decision packages for the rest.
- Tests: backend re-verify 25 pass / 2 skip; industries +
  flow-direct 19 pass. Frontend rerun blocked (sandbox EPERM).
- Evidence: app/industries.py, tests/test_industries.py,
  CRUISESHIELD-AI-DEMO-REMOVAL-MATRIX.md, docs/OPERATIONS_RUNBOOK.md.
- Reviewer: owner. Status: REPORTED.
- Defects: G2–G5 rename slices await naming confirm; coverage
  deps await approval; tenancy/PG/audit/deploys still gated.

## ACP-07 — Level-14 execution slice 2 (backend rename)
- Contents: /platform canonical routes + deprecated aliases;
  contract-value + seed-ID migration; canonical fixture regen
  (75242 / 36D55C94…); templates/static aligned; live docs
  updated; release manifest; license evidence (partial).
- Criteria: fail-closed renames; suite green; no alias-removal.
- Tests: backend 401 pass / 137 skip / 2 env errors
  (socket-denial signature); static-escaping EPERM deselected
  (known sandbox failure). Fixture anchors match generator.
- Evidence: app/, tests/, templates/, static/ diffs;
  CRUISESHIELD-AI-RELEASE-MANIFEST.md.
- Reviewer: owner. Status: REPORTED.
- Defects: frontend slice (G3–G5, 12 locales) next; alias
  removal + coverage + tenancy/PG/audit/deploys still gated.

## ACP-08 — Level-14 execution slice 3 (frontend rename)
- Contents: /platform route dir; nav/CTA/href renames; api
  client + hook idents; 12-locale key renames; EN reword;
  TSV + inventory regen; cleanup pass 2 fixes.
- Criteria: asserted-count edits; residue scans; no node.
- Tests: vitest/tsc BLOCKED (sandbox node EPERM, proven).
  Proof: TSV mechanics calibrated + re-validated (6,501 rows
  ×2 runs); source/key/column scans clean; backend untouched.
- Evidence: frontend/ diffs; docs/UGLS_REVIEW_KIT/*.tsv.
- Reviewer: owner. Status: REPORTED.
- Defects: non-EN values need native review; hosted CI must
  run the 405 frontend asserts; alias removal still gated.

## ACP-09 — Detection intelligence directive (§1–§15)
- Contents: 11-family registry + 8-channel taxonomy; 10
  signal APIs (summary/search/series/detail/matrix/drill-down
  + outcome/link POSTs); UTC bucketing + strict filters;
  FP rate + execution envelope; DetectionSection, txn panel,
  time-series panel; 3 EN keys + 608-row kit TSVs.
- Criteria: every metric reconciles to source events; tenant
  isolation on all reads; write-gated audited mutations; no
  fabricated stats or integrations.
- Tests: backend 34 green + 4 socket-gated (CI); full suite
  503 pass / 141 skip / same sandbox-only 1F+2E; offline
  slice-3 probe 33/34 + 1 inspection-resolved; vitest/tsc
  BLOCKED (sandbox node EPERM, proven).
- Evidence: app/detection.py, app/channels.py, app/main.py
  signals block, app/store.py writers, tests/test_detection.py,
  frontend detection panels/api/i18n, UGLS kit TSVs.
- Reviewer: owner. Status: REPORTED.
- Defects: hosted CI + deployment gated (D-017/GAP-009);
  persisted signal_events awaits GAP-001; non-EN detection
  values need native review.

## ACP-10 — v14.0 production batch (inventory + identity + industry)
- Contents: forensic inventory generator + JSON (1111 files,
  57 API routes, 668 tests); machine-readable zero-gap
  matrix (78 rows, validated); es/pt demo-identity removal
  (40 strings + TSV rows, 12/12 locales residue-free);
  fx-remittance, government, tax-revenue industry modules
  (8 TESTING / 37 NOT_STARTED).
- Criteria: reproducible inventories; zero user-facing demo
  wording outside D-019b-gated aliases; honest module
  statuses with engine-asserted profiles.
- Tests: backend 545 pass / 141 skip / same sandbox-only
  1F+2E; industry 61/61; TSV structure + vars consistency
  verified; matrix --check green; vitest/tsc still
  CI-gated (sandbox node EPERM).
- Evidence: scripts/forensic_inventory.py,
  docs/FORENSIC_INVENTORY.json, scripts/zero_gap_matrix.py,
  docs/ZERO_GAP_MATRIX.json, es/pt locale + TSV diffs,
  app/industries_{fx,government,tax}.py + tests.
- Reviewer: owner. Status: REPORTED.
- Defects: owner push + hosted CI pending; PG cutover, live
  AI, MFA, license, alias removal still gated; 37 industry
  modules NOT_STARTED.
- Note 2026-11-06: live matrix is now 105 rows; the 78-row
  figure above is preserved as that batch's contemporary
  record. Current count: see matrix generator.

## ACP-11 — v14.0 industry completion (45/45 TESTING)
- Contents: remaining 37 industry profiles + 37 test files
  (taxonomy, scenarios, rule maps, workflows, reports,
  permissions, compliance placeholders, BLOCKED data feeds);
  retired untouched-triple assertions; matrix at 64/78
  CLOSED_VERIFIED with 1 NOT_STARTED (MFA).
- Criteria: every mapped rule exists in engine; every
  workflow/report step resolves to a live route; roles real;
  no compliance certification claimed; external data
  BLOCKED, never faked.
- Tests: industry 320/320 (5 registry + 45×7); full suite
  804 pass / 141 skip / same sandbox-only 1F+2E; matrix
  --check green.
- Evidence: app/industries_*.py (45 profiles),
  tests/test_industry_*.py (45 files), ZERO_GAP_MATRIX.json.
- Reviewer: owner. Status: REPORTED.
- Defects: PILOT+ stages need connector data + owner
  approvals; push + hosted CI still pending.

## ACP-12 — Tenant boundary slice for new surfaces
- Contents: tenant scoping for connections, SAR/DSR/holds, and
  agent plans/runs/tools; legacy connection `tenant` fallback;
  tenant-scoped legal-hold checks.
- Criteria: cross-tenant list/read/write attempts return existing
  not-found shapes without oracles; same-tenant flows unchanged.
- Tests: tests/test_tenant_new_surfaces.py 12 passed;
  touched-surface bundle 103 passed / 4 skipped; full backend
  893 passed / 141 skipped with same sandbox-only 1F+2E.
- Evidence: app/tenancy.py, app/main.py, app/agents.py,
  app/governance.py, app/connectors.py,
  tests/test_tenant_new_surfaces.py.
- Reviewer: owner. Status: REPORTED.
- Defects: D-014 user→tenant map still owner-gated; push +
  hosted CI still pending; TEN-01 remains IN_PROGRESS.

## ACP-13 — Audit loader CLI keyring slice
- Contents: operator-supplied audit-keyring loading and CLI
  wiring for the pre-write migration gate; errors never expose
  key material.
- Criteria: malformed keyrings fail before migration/DB access;
  valid keyrings reach the migration as bytes; omission preserves
  the existing opt-in gate.
- Tests: audit focused bundle 30 passed; migration suites
  14 passed / 74 skipped (scratch-PG-gated).
- Evidence: migrations/loader.py, tests/test_loader_gate.py.
- Reviewer: owner. Status: REPORTED.
- Defects: D-018 production key ceremony still owner-gated;
  AUD-01 remains IN_PROGRESS.

## ACP-14 — Transaction-evidence tenant boundary slice
- Contents: tenant gating for get_transaction, get_risk, and
  get_graph; tenant-visible risk-evaluation inputs; shared
  tenancy.visible_graph helper reused by the agent graph tool;
  transaction gating inside get_investigation/investigation_page.
- Criteria: foreign txn/risk/graph reads return existing
  UNKNOWN_TRANSACTION 404; own-tenant reads unchanged; default
  graph still 22 nodes / 30 edges with clean provenance.
- Tests: tests/test_tenant_new_surfaces.py 15 passed (3 new);
  affected bundle 246 passed / 17 skipped; full backend 908
  passed / 141 skipped with same sandbox-only 1F+2E.
- Evidence: app/tenancy.py, app/main.py, app/agents.py,
  tests/test_tenant_new_surfaces.py, tests/test_tenant_api.py
  (fixture made tenant-consistent; assertions unchanged).
- Reviewer: owner. Status: REPORTED.
- Defects: D-014 user→tenant map still owner-gated; legacy
  device/IP/geo/account/link/risk-intel endpoints remain
  unscoped; TEN-01 remains IN_PROGRESS.

## ACP-15 — Alert/notification tenant boundary slice
- Contents: alerts, notifications, and mark-all-read scoped to
  alerts whose transaction is visible to the request tenant via
  a shared _visible_alerts helper.
- Criteria: foreign alerts absent from list/unread/mark-all;
  own-tenant and default behavior unchanged; no orphan seed
  alerts (verified: 1 alert, 0 orphans).
- Tests: tests/test_tenant_new_surfaces.py 18 passed (3 new);
  full backend 911 passed / 141 skipped with same sandbox-only
  1F+2E.
- Evidence: app/main.py (_visible_alerts, list_alerts,
  list_notifications, mark_notifications_read),
  tests/test_tenant_new_surfaces.py.
- Reviewer: owner. Status: REPORTED.
- Defects: D-014 user→tenant map still owner-gated; TEN-01
  remains IN_PROGRESS.

## ACP-16 — Derived-intel tenant boundary slice
- Contents: tenancy.visible_state view (tenant-visible
  transactions/nodes/edges/events/investigations) wired into
  all 9 derived-intel handlers: device, ip-observations,
  geo-observations, transaction/account/investigation intel,
  graph overlay, risk-intelligence, intel-evidence.
- Criteria: foreign anchors return existing 404s; own-tenant
  summaries contain only visible records; default behavior
  unchanged across DI03-DI09 suites.
- Tests: tests/test_tenant_new_surfaces.py 23 passed (5 new);
  DI bundle 154 passed / 13 skipped; full backend 916 passed
  / 141 skipped with same sandbox-only 1F+2E.
- Evidence: app/tenancy.py (visible_state), app/main.py (9
  handlers), tests/test_tenant_new_surfaces.py.
- Reviewer: owner. Status: REPORTED.
- Defects: D-014 user→tenant map still owner-gated; replay
  and ai-runs scoping remain follow-ups; TEN-01 stays
  IN_PROGRESS.

## ACP-17 — Replay/AI-run tenant boundary slice
- Contents: get_replay serves tenancy.visible_state
  (tenant-visible events/edges); ai-analysis/followup gate
  investigation + transaction ownership and stamp new runs
  with the request tenant; get_ai_run enforces reads;
  followup prior context, case summaries, and the
  investigation HTML run list filter by tenant.
- Criteria: foreign replay shows only own-tenant events;
  foreign ai-runs/investigations return existing 404s;
  inconsistent inv/txn ownership 404s; default behavior
  unchanged (unstamped legacy runs stay default-visible).
- Tests: tests/test_tenant_new_surfaces.py 28 passed (5 new);
  tenant+AI bundle 70 passed / 31 skipped; API/PG bundle
  14 passed / 87 skipped; full backend 921 passed / 141
  skipped with same sandbox-only 1F+2E.
- Evidence: app/main.py (_run_ai, _investigation_summary,
  ai_analysis, ai_followup, get_ai_run, get_replay,
  latest_ai_run_for_case, get_case, investigation_page),
  tests/test_tenant_new_surfaces.py.
- Reviewer: owner. Status: REPORTED.
- Defects: D-014 user→tenant map still owner-gated;
  simulations scoping remains follow-up; TEN-01 stays
  IN_PROGRESS.

## ACP-18 — Simulation tenant boundary slice
- Contents: post_simulation gates the target transaction
  (foreign/missing → existing UNKNOWN_TRANSACTION 404),
  recomputes what-if scores over tenant-visible inputs,
  and stamps new records server-side; investigation-page
  simulation context filters by tenant.
- Criteria: foreign targets 404 identically to missing
  ones; ignored-edge validation runs against visible
  edges only; own-tenant sims carry stamps; default
  behavior unchanged across flow/seed/PG suites.
- Tests: tests/test_tenant_new_surfaces.py 31 passed (3 new);
  flow/seed bundle 22 passed / 13 skipped; PG/tenancy
  bundle 30 passed / 53 skipped; full backend 924 passed
  / 141 skipped with same sandbox-only 1F+2E.
- Evidence: app/main.py (post_simulation,
  investigation_page), tests/test_tenant_new_surfaces.py.
- Reviewer: owner. Status: REPORTED.
- Defects: D-014 user→tenant map still owner-gated; all
  planned handler surfaces now scoped; TEN-01 stays
  IN_PROGRESS pending the map.

## ACP-19 — L13 Phase 0 baseline + product-identity batch
- Contents: read-only forensic baseline (branch/HEAD/worktree,
  inventory coverage, banned-phrase search with per-occurrence
  dispositions, exact-SHA duplicate analysis, offline security
  gate, secrets-tracking check, Part 20 schema mapping);
  README rewritten to platform identity with current verified
  test evidence; new `tests/test_product_identity.py` hygiene
  gate (Part 21 gate 5). Zero behavior change.
- Criteria: banned demo-product phrases absent from README,
  EN locale, Next.js app/components sources, and Jinja
  templates; every remaining code occurrence allowlisted;
  gate proven to catch violations (negative control).
- Tests: new file 2 passed; full backend 926 passed / 141
  skipped with same sandbox-only 1F+2E.
- Evidence: docs/L13_PHASE0_BASELINE.md, README.md,
  tests/test_product_identity.py, matrix row PDI-01.
- Reviewer: owner. Status: REPORTED.
- Defects: none new; non-EN human review still pending
  (I18N-02); owner packages PKG-01…PKG-07 still awaiting.

## ACP-20 — Audit export/verify surface + drill re-run
- Contents: `audit_chain.verification_report` (structured
  ok/sealed/head/key_ids/error, never raises, never leaks
  keys) + `scripts/audit_export.py` export/verify CLI (JSON
  reports, exit codes, keyring via loader, no key material
  in output); scratch backup drill re-executed.
- Criteria: export/verify round-trip green; tamper and
  unknown-key detected with check names only; malformed
  inputs fail closed with codes; drill exit 0 + parity.
- Tests: tests/test_audit_export.py 10 passed (new); audit
  bundle 40 passed; full backend 936 passed / 141 skipped
  with same sandbox-only 1F+2E. Drill: exit 0, parity
  true, csbk-20261106-021504Z, scratch cleaned after.
- Evidence: app/audit_chain.py, scripts/audit_export.py,
  tests/test_audit_export.py, matrix row AUD-02.
- Reviewer: owner. Status: REPORTED.
- Defects: D-018 production ceremony still pending; AUD-01
  and BAK-01 stay IN_PROGRESS; PKG-01…PKG-07 awaiting.

## ACP-21 - Unknown-location login-risk scoring
- Contents: `app/login_risk.py` (weighted novelty scoring,
  UA classifier, hour buckets, bounded per-user baselines)
  + `Store.login_risk_for/save_login_risk` + post-password
  wire-in on `/api/v1/auth/login` returning an additive
  `risk` key only for elevated/high.
- Criteria: first login learns baseline and scores low;
  new IP/device elevate, both high; unknown users and
  429s learn nothing; no raw IP/UA persisted; legacy
  success body and MFA ticket shapes unchanged.
- Tests: tests/test_login_risk.py 12 passed (new); auth
  neighbors (auth/mfa/abac/demo-token) 74 passed /
  15 skipped with no failures.
- Evidence: app/login_risk.py, app/main.py, app/store.py,
  tests/test_login_risk.py, matrix row SEC-RISK.
- Reviewer: owner. Status: REPORTED.
- Defects: none in slice; notification delivery (Part 9)
  events remain a later batch.

## Data-integrity note (2026-11-05)
- `data/state.json`: 101417 bytes (matches pin), mtime
  2026-11-04 (predates this work), all source-integrity tests
  pass. Measured SHA-256:
  `BA1D4DB4BB4DBC6FC3ACA346664A539610CCC6460CCD530F523C8043453790FE`.
  A prior 63-character transcription of this hash was malformed
  (SHA-256 is 64 chars) and is superseded by this measurement.
