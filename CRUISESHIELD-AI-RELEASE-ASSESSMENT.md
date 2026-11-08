# CRUISESHIELD-AI-RELEASE-ASSESSMENT.md

Production release assessment, executed 2026-11-05 on branch
`feat/phasezero-foundations` (uncommitted work; base HEAD `b4732cb`).
Every verdict below rests on a command executed this session, not on
prior reports. No deployment was performed; no production readiness is
claimed — several gates below are FAIL / NOT_VERIFIED by evidence.

Labels: PASS (fresh evidence) / PARTIAL (partly evidenced) / FAIL
(evidence of non-satisfaction) / NOT_VERIFIED (no fresh evidence).

## 1. Backend tests — PARTIAL

- Full suite: 396 passed, 137 skipped, 1 failed, 2 errors
  (`python -m pytest tests/ -q`, 37s).
- The 3 non-pass results are the known sandbox-only environmental
  signature, unchanged from the pre-change baseline: node EPERM on
  `lstat` (`test_static_escaping`) and WinError 10013 socket denial
  (2 × `test_cors` fixture setup). Neither executes product code
  paths changed this session; identical failures were recorded on
  the untouched tree (resume-r06 log).
- Lane breakdown (same session): CONTRACT 139 passed / 1 env-fail;
  AUTHZ 97 passed / 2 env-errors; SECRETS 12 passed; PG 14 passed /
  74 explicit skips (no scratch DB); AI 40 passed / 17 skips;
  BACKUP 94 passed.
- PARTIAL because the suite is not fully green in this environment
  (environmental, not product) and PG/AI-live lanes skip without
  their services.

## 2. Frontend typecheck — PASS

- `npm run typecheck` (tsc --noEmit): exit 0, no errors.

## 3. Frontend tests — PASS

- `npx vitest run`: 72 files, 405 tests, all passing, 0 skipped.

## 4. Production build — PASS

- `npm run build`: exit 0, "Compiled successfully", 8/8 routes
  (landing static; demo/investigations/cases/network/replay dynamic).

## 5. API contract checks — PARTIAL

- CONTRACT lane: 139 passed covering flows, DI-03..DI-09, events,
  notifications, evidence, graph/rules/risk, seed reset, rehearsal
  and drill scenarios; 27 skips are socket-gated in the sandbox.
- Same single environmental failure as §1 (static_escaping node
  harness). No contract assertion failed.
- PARTIAL only for that environmental failure; contracts themselves
  are green where executable here.

## 6. AuthN/AuthZ checks — PARTIAL

- AUTHZ lane: 97 passed (login journeys, write-token gate,
  demo-token R1–R4 remediation, rate limits, body guard, CORS
  options, case audit incl. new actor-role threading); 19 skips
  are socket-gated here.
- 2 errors are the WinError 10013 sandbox socket denials at
  TestClient setup (pre-existing signature, CI-executed).
- PARTIAL for the same environmental reason; no authorization
  assertion failed.

## 7. Secret handling — PASS

- Security-gate `secret_scan`: PASS, no real-credential shapes.
- Backend `test_secret_safety` + `test_security_gate` + new
  `test_deploy_manifests`: all passing; `.env.example` names-only
  (verified by reading); frontend bundle carries token NAME only.

## 8. Dependency manifests — PASS

- Gate `lock_covers_requirements`: PASS (16 direct pins locked).
- Gate `lockfile_hashes`: PASS (37 pins, 463 sha256 hashes).
- `test_deploy_manifests`: 5 passing (Dockerfile + render.yaml pins).

## 9. Installed-environment match — NOT_VERIFIED (local FAIL)

- Gate `installed_matches_lock`: FAIL — but the local interpreter
  is a shared data-science environment (torch, moviepy, gymnasium…
  present; fastapi/starlette versions differ from the lock). The
  project has no local venv; Docker installs from the lockfile.
- Gate `pip_check`: FAIL for the same reason (moviepy/pillow
  conflict between two non-project packages).
- Honest reading: these two checks can only pass inside the
  Docker build or a lock-installed venv, neither of which was
  executed here. NOT_VERIFIED, not a product defect. Dockerfile
  install path itself is untested (GAP-016 remainder).

## 10. Python vulnerability audit — NOT_VERIFIED

- Gate `pip_audit`: FAIL with "audit unreachable (timeout): OSV
  query did not complete" — no network route to the OSV database
  from this environment. A standalone `pip-audit` run behaved the
  same. No fresh vulnerability statement can be made either way.
- Historical note (not evidence): a prior session recorded
  pip-audit clean; that result predates this tree and is not
  re-claimed here.

## 11. JavaScript vulnerability audit — PARTIAL (accepted residual)

- `npm audit --omit=dev`: 2 vulnerabilities (1 moderate, 1 high) —
  the known PostCSS GHSA-r28c-9q8g-f849 advisory, fixable only via
  breaking upgrade to next@16.4.5. Same residual as previously
  recorded (R08): safe fix requires a major framework upgrade, so
  it stays documented-deferred. No other findings.

## 12. Tenant isolation — FAIL (architectural)

- Requirement (master directive Phase 5): tenant isolation with
  tests. Evidence: zero occurrences of tenant/organisation/org
  concepts anywhere under `app/` (verified by search); the store
  is a single JSON document with one DEMO_USERS space and no
  organisation scoping.
- Adjacent passing tests (per-account DI isolation, per-identity
  notification isolation) prove single-tenant data separation, not
  multi-tenancy. A production release requiring tenant isolation
  cannot be certified on this architecture.

## 13. AI integration evaluation — PARTIAL

- Offline lane: 40 passed, incl. the new 8-fixture golden eval
  harness (`tests/test_ai_eval.py`), validator, cost caps, timeout/
  retry mapping — all hermetic, no network, no key.
- Live lane: BLOCKED BY DESIGN — no MODEL_API_KEY is provisioned
  and no live call was attempted (free-tier policy + no approval).
  The adapter is live-capable and mock-transport-tested only.
- PARTIAL: contract evaluated offline; live quality/drift
  unevaluated (GAP-004 remainder, GAP-014).

## 14. Backup and recovery — PARTIAL

- Code lane: 94 passed — CSBK1 envelope, manifest signing/chain,
  producer snapshot→encrypt→sign→upload→verify and isolated
  restore-verify, all socket-free with fakes.
- Execution lane: BLOCKED BY DESIGN — all three backup workflows
  are header-disabled manual dispatch; no ceremony keys exist;
  restore returns a plan only (load-into-scratch unimplemented).
  No real backup exists and no drill has ever run (GAP-003).
- PARTIAL: implementation tested, operation never exercised.

## 15. Deploy and live verification — NOT_VERIFIED

- No deploy was performed (not authorized this turn).
- Dockerfile + render.yaml + runbook are complete and
  manifest-pinned by tests, but the image was never built here,
  the Render dashboard was never inspected, and no live health/
  ready check was executed (GAP-009). Netlify file remains the
  stale un-adapted stub pending the owner's hosting call (GAP-008).

## 16. Working-tree release hygiene — PARTIAL

- Release work sits uncommitted on `feat/phasezero-foundations`
  alongside extensive pre-existing dirty state; no commit or push
  was made (not authorized). Secret scan is clean, but no release
  manifest, license decision, or clean-checkout reproducibility
  test exists yet (GAP-007 remainder).

## Consolidated matrix

| # | Gate | Verdict | Fresh evidence |
|---|---|---|---|
| 1 | Backend suite | PARTIAL | 396 pass; 3 env-only fails |
| 2 | Frontend typecheck | PASS | tsc exit 0 |
| 3 | Frontend suite | PASS | 405/405 |
| 4 | Production build | PASS | exit 0, 8/8 routes |
| 5 | API contracts | PARTIAL | 139 pass; 1 env-only fail |
| 6 | AuthN/AuthZ | PARTIAL | 97 pass; 2 env-only errors |
| 7 | Secrets | PASS | gate scan + 12 tests |
| 8 | Manifests | PASS | 16 pins, 37/463 hashes |
| 9 | Installed match | NOT_VERIFIED | local interp ≠ lock env |
| 10 | Python vuln audit | NOT_VERIFIED | OSV unreachable |
| 11 | JS vuln audit | PARTIAL | 2 known, upgrade-blocked |
| 12 | Tenant isolation | FAIL | no tenancy in arch |
| 13 | AI evaluation | PARTIAL | offline green; live gated |
| 14 | Backup/recovery | PARTIAL | code green; never operated |
| 15 | Deploy/live | NOT_VERIFIED | never executed |
| 16 | Release hygiene | PARTIAL | uncommitted; no manifest |

## Release verdict: NOT READY FOR PRODUCTION RELEASE

PASS count: 5. Nothing here is shippable as production: tenant
isolation FAILs architecturally, deploy/live/pip-audit are
unverified, and the backup system has never operated. The codebase
is in strong shape for a demo/staging release (suites green,
contracts green, secrets clean, build green), but production
readiness requires, at minimum: GAP-001/GAP-002/GAP-003 decisions
and execution, GAP-009 first deploy with live verification,
GAP-010 hosted CI green, GAP-014 live-AI decision, a lock-installed
environment proof for §9, network-available pip-audit for §10, and
either multi-tenancy or an explicit single-tenant production scope
decision for §12 — plus the owner's commit/push/release approvals.
