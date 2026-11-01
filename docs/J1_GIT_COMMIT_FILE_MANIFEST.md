# J1 CONTROLLED GIT FILE REVIEW — COMMIT MANIFEST

**Date:** 2026-11-01
**Repository:** `C:\Users\HP\Projects\CruiseShield AI™`
**Remote:** `https://github.com/ihemestanley100-ui/CruiseShield-AI-` (fetch/push
not verified this session; no network operation performed)
**Branch:** `master`
**HEAD:** `0eaaaf53390bf56b1027b0db34432d09c3ace983`
**Gate:** J1 — NOTHING STAGED, COMMITTED, OR PUSHED. Owner approval required.

**Reconciliation (2026-11-01, ~15:15 WAT):** owner decisions D1–D4
applied (D1 EXCLUDE duplicate, D2 gitignore proposal, D3 one commit,
D4 push NOT approved). All 312 appendix paths re-verified against live
`git status` (mechanical diff: zero gaps). Staging area confirmed empty
(`git diff --cached`: 0 paths). Staging plan switched from pathspec
form to explicit paths per instruction (§7, dry-run proven).

## 1. Verdict counts (final)

- Modified tracked files, proposed INCLUDE: **20**
- New files, proposed INCLUDE: **292** (incl. this manifest)
- REVIEW_REQUIRED remaining: **0**
- Excluded with reason (EXCLUDE): **2** (§4)
- Total proposed commit paths: **312**
- Secret scan over all text candidates: **0 real secrets**
  (2 labeled test fixtures, adjudicated safe; rescan PASS)

## 2. Counts by category

- Backend source (`app/`): 7 modified + 12 new = 19
- Backend tests (`tests/`): 5 modified + 30 new = 35
- Backup package (`backups/`, code not archives): 10 new
- Migrations (`migrations/`): 2 new
- Scripts (`scripts/`): 1 new
- CI (`.github/workflows/`): 4 new
- Frontend (`frontend/`): 135 new (duplicate EXCLUDED per D1)
- Docs (`docs/`): 2 modified + 97 new (incl. this manifest) = 99
- Root config: 5 modified + 1 new (`requirements.lock`) = 6
- Legacy static (`static/app.js`): 1 modified
- Check: 19+35+10+2+1+4+135+99+6+1 = **312**

## 3. REVIEW_REQUIRED — NONE REMAINING (was 1, resolved by D1)

Owner decision D1: EXCLUDE
`frontend/public/assets/cruiseshield-logo-original.png.png` from the
commit. **Reconciliation finding:** the file is ABSENT from disk at
reconciliation time (it was listed by `git ls-files --others` during
the J1 review ~40 min earlier; untracked count moved 294 → 293 on that
single path). Cause of disappearance is UNKNOWN — no command in this
session deletes files except transient `_probe_stage_*.py` stagers I
created (removed by exact name). I did not delete, move, or overwrite it.

- No recovery action taken and none required for J1: the file was
  proven byte-identical to the canonical logo (SHA-256 `1A0CC66B…C32A623`,
  1273370 B, zero code references — see closeout + provenance reports),
  and D1 excludes it regardless. It is NOT re-created here (no
  fabricated assets, ever).
- Canonical original VERIFIED INTACT: hash
  `1A0CC66B6385C38029F326C7B84908DC93B208C3B6191BBAF51EBEC86C32A623`,
  1273370 B, referenced by `app-shell.tsx:57` and
  `LandingChrome.tsx:7`. Display, favicon chain, and brand header are
  unaffected (frontend 250/250 green on this exact tree).
- If the owner did not delete it, treat the disappearance as an
  environment note (sync/AV/tooling unknown) — worth one glance at the
  Recycle Bin, but no bytes of value are at stake.

## 4. EXCLUDE (2 paths + ignored classes)

- `tmpw_ta9ikh/s.json` — stale scratch snapshot of demo state
  (SHA-256 `88a213bc…`, 72972 B; live `data/state.json` is
  `BA1D4DB4…`, 101417 B — NOT identical). Not referenced by any
  tracked code. Preserve on disk per standing rule; do NOT commit.
- `frontend/public/assets/cruiseshield-logo-original.png.png` —
  EXCLUDED per owner D1. Absent from disk at reconciliation (see §3);
  exclusion is automatic. Canonical original committed instead
  (`frontend/public/assets/cruiseshield-logo-original.png`).
- `docs/J1_STAGING_COMMAND.txt` (helper, untracked) — machine-generated
  display copy of the §7 command. NOT in the manifest; explicit paths
  mean it can never be swept in. Owner may delete after staging.
- Ignored by `.gitignore` (verified, never added by the §7 command):
  - `.env` (live secrets, 206 B, on disk) and any `frontend/.env`
    (none exists; the bare `.env` pattern covers all levels)
  - `data/*` except `data/.gitkeep` — `data/state.json` can never commit
  - `__pycache__/`, `*.pyc`, `.pytest_cache/`, `pytest-of-*/`
  - `frontend/test-output*.txt`, `test-output*.txt`
- Ignored by `frontend/.gitignore` (verified): `node_modules/`, `.next/`,
  `out/`, `.env*.local`, `*.tsbuildinfo`
- Ignored by `.venv.bak-retired/.gitignore` (`*`): whole retired venv
- Empty tool dirs (nothing to add): `.agents/`, `.muse/`, `.eden/`,
  `.sl/`, `.hg/`

## 5. Modified files (20, all INCLUDE)

Reviewed `git diff` in full (+1629/−89). Every deletion is an in-program
refactor (import reorganization, endpoint consolidation into
`_run_ai`/`_investigation_summary`, hashed-requirements Dockerfile,
PERF-001 store lock); nothing destructive, nothing secret-bearing
(scan §6 covers the working tree, which equals post-commit content).

- `.env.example` (+32: SESSION_SECRET, DEMO_USERS, AI_* knobs, names only)
- `.gitignore` (+2: test-output ignores)
- `Dockerfile` (hashed lockfile install, PORT binding)
- `app/ai_adapter.py` (+160/−8: follow-ups, retries, usage, cap helper)
- `app/cases.py` (+14)
- `app/config.py` (+86: CORS/auth/AI/storage settings)
- `app/main.py` (+512/−26: guards, auth routes, AI cap, endpoints)
- `app/seed.py` (+63)
- `app/simulate.py` (+11)
- `app/store.py` (+50/−6: lock, `open_store`)
- `docs/KNOWN_LIMITATIONS.md` (+29/−15)
- `docs/TEST_EVIDENCE.md` (+34/−1)
- `render.yaml` (+47/−5: Blueprint + gates)
- `requirements.txt` (+27/−2: prior-session P2.2A CVE lifts, not J1-session)
- `static/app.js` (+32/−22: legacy page upkeep)
- `tests/test_ai_validation.py` (+305)
- `tests/test_cases_audit.py` (+76)
- `tests/test_flow_direct.py` (+62/−1)
- `tests/test_graph_rules_risk.py` (+16)
- `tests/test_seed_reset.py` (+68)

Advisory (non-blocking): git emits `LF will be replaced by CRLF` for
these files (repo `core.autocrlf` behavior). bytes on disk unchanged by
review; normalization happens at checkout, not at review.

## 6. Secret scan (values never printed)

- repo gate `check_secret_scan` (whole tree, 7 shape patterns): PASS.
- J1 extended scan (334 tracked+untracked text files, +generic
  `key/secret/passwd/token/bearer = "…16+…"` assignment pattern): 2
  hits, both adjudicated false positives by direct line inspection:
  - `tests/backup_fakes.py:122` — `FAKE_SECRET = "TEST-ONLY-…"` label
  - `tests/test_auth.py:14` — `SECRET = "test-secret-not-a-real-…"` label
- `.github/workflows/*.yml`: secrets referenced by `${{ secrets.NAME }}`
  only (30 references, 0 literal values).
- Env files on disk: root `.env` (ignored, excluded), root
  `.env.example` (names/placeholders only, included),
  `frontend/.env.example` (public URL placeholder + empty token, included).
  No `frontend/.env`, no `.env.local`, no `.env.*` variants anywhere.
- Reconciliation rescan (repo gate `check_secret_scan`): PASS.
- Docs deep read (99 files: 97 new + 2 modified): 0 exact duplicates
  (SHA-256); 0 absolute local paths; 1 email
  (`HACKATHON_PRE_EVENT_BASELINE.md:16` — quoted git author identity
  `CruiseTech Dev <dev@cruisetech.com>`, evidentiary, safe); 11 IPv4
  hits, all loopback/bind-all in run commands (safe); eligibility
  verdicts consistent (AT_RISK family, no contradictions); backup
  state consistent (`BACKUP_NOT_EXECUTED_PENDING_APPROVAL`, no
  executed-claim anywhere).
- Frontend tree verified complete: 135/135 manifest paths present on
  disk incl. `package-lock.json`; junk-suffix sweep (log/tmp/bak/
  coverage/pycache) over all 293 untracked: 0 hits.
- **Result: safe to commit. No redaction required.**

## 7. Staging command — EXPLICIT PATHS (NOT EXECUTED)

Per instruction: explicit approved paths, no add-all. The full command
(4 grouped `git add --` lines, 312 quoted paths, POSIX shell form) is
`docs/J1_STAGING_COMMAND.txt` — machine-generated FROM Appendices A–D,
so transcription error is impossible. Run it in Git Bash (or join each
group onto one line / swap trailing `\` for backticks in PowerShell).

Proof (non-destructive, this session): `git add -n -- <all 312 paths>`
dry-run exits 0 and stages EXACTLY the manifest set (in-manifest-not-
staged: none; staged-not-in-manifest: none). Working tree untouched
afterwards; staging area still empty.

After the owner runs it, `git status --short` must show exactly 20 `M`
+ 292 `A` = 312 staged, with `?? tmpw_ta9ikh/` and
`?? docs/J1_STAGING_COMMAND.txt` remaining untracked. Do NOT run bare
`git add -A`: it would sweep in `tmpw_ta9ikh/s.json`.

Group summary (full text in the .txt): A 20 modified · B 60
backend/test/CI · C 135 frontend · D 97 docs.

## 8. Lockfile verification

- `frontend/package-lock.json`: lockfileVersion 3, name matches
  `package.json`, root `dependencies` + `devDependencies` sections
  match the manifest EXACTLY, 289 locked packages.
- `requirements.lock`: 37 pins, 463 sha256 hashes (`lockfile_hashes`
  gate PASS); Dockerfile installs `--require-hashes` from it.
- Honest limit: `npm ci` end-to-end reproduction is NOT_VERIFIED in
  this offline sandbox (no network installs). Static consistency +
  local `npm run build` green is the evidence; first CI/Vercel/Render
  build proves it loudly (failure mode is a loud build error, never
  silent wrong deps).

## 9. Validation results (non-destructive, state hash before = after)

- `data/state.json` BEFORE: `BA1D4DB4BB4DBC6FC3ACA346664A539610CCC6460CCD530F523C8043453790FE`, 101417 B
- Backend (re-run at reconciliation): **318 passed**, 86 pre-existing
  socket/loop-gated skips, 1 deselected env-blocked test; that test
  (`test_static_escaping.py`) is **3/3** on the approved unsandboxed
  rerun (sandbox blocks node file exec; proven environmental).
  Effective full suite: 321 green.
- Frontend (same exact tree — no frontend file changed since the green
  run; verified via identical status set): `tsc --noEmit` clean;
  vitest **49 files / 250 tests pass**; `next build` succeeds.
- Security gate: `pip_audit` PASS (no vulns), `secret_scan` PASS
  (incl. reconciliation rescan), `lockfile_hashes` PASS;
  `installed_matches_lock` + `pip_check` FAIL = pre-existing
  shared-interpreter drift, untouched by J1 (zero new deps).
- `data/state.json` AFTER: identical hash + size (above). No test or
  check wrote to it (tests use tmp stores).

## 10. Proposed commit message (single program commit)

```
J1: program worktree — backend, frontend, tests, docs, CI

Commits the CSAI-MASTER-RELEASE-001 program worktree on master:
FastAPI backend + protected-demo login + AI cost controls, full
Next.js frontend (previously untracked) with lockfile, backend +
frontend test suites, PG migration path (spec + scratch-verified
adapter, no cutover), Render/Vercel/Neon zero-cost specs, CI
workflows, and the phase 2B-15 + submission evidence trail.

State: data/state.json intentionally untracked (gitignored runtime
state, hash BA1D4DB4…3790FE at review). No secrets committed
(secret scan clean). tmpw_ta9ikh/ scratch snapshot excluded;
logo .png.png duplicate excluded per D1 (canonical committed).

Verified: backend 321 pass (+86 env-gated skips), frontend
typecheck + 250 vitest + production build green.
```

Single initial source-import commit per owner D3: the tree has never
held the frontend; this establishes the reviewable baseline.

## 11. Risks and owner decisions (reconciled)

1. **D1 — RESOLVED: logo duplicate EXCLUDED.** File also absent from
   disk at reconciliation (§3); canonical verified intact. No action.
2. **D2 — `.gitignore` hardening: proposed diff VERIFIED SAFE (not
   applied — awaiting approval to edit):**
   ```diff
   --- .gitignore (11 lines, adds 7)
   +++ .gitignore
   @@
    frontend/test-output*.txt
    test-output*.txt
    .DS_Store
   +# J1 hardening: env variants, logs, coverage (examples stay tracked)
   +.env.local
   +.env.*.local
   +.env.production
   +.env.development
   +.env.test
   +*.log
   +coverage/
   ```
   Verification: simulated via `core.excludesFile` — untracked set
   identical (293 = 293, zero newly ignored); probe proves the
   patterns match `debug.log`, `.env.local`,
   `frontend/.env.production` while sparing both `.env.example`
   files. NOTE: bare `.env.*` was deliberately NOT proposed — it
   would swallow `.env.example`. Apply in a follow-up edit (+ amend
   or second commit) only on explicit approval.
3. **D3 — RESOLVED: ONE initial source-import commit** (§10).
4. **D4 — push + visibility: NOT APPROVED.** Separate approval needed
   after the commit exists locally. This manifest authorizes no push,
   visibility change, deploy, or submit.
5. **Risk — CRLF normalization:** checkout on Windows yields CRLF for
   committed files; builds/tests are line-ending agnostic (verified
   green on this CRLF checkout). No action.
6. **Risk — `npm ci` unproven offline (§8):** first cloud build is the
   proof; failure is loud. No action before commit.
7. **Risk — 96-doc evidence weight:** the docs/ trail is large by
   design (audit deliverable). Excluding any report weakens the
   submission trail; all 96 scanned clean. No action recommended.

**FINAL GATE: no `git add`, `commit`, `push`, deploy, migration, or
backup was executed. Awaiting explicit owner approval.**

---

## Appendix A — Modified paths (20)

```
.env.example
.gitignore
Dockerfile
app/ai_adapter.py
app/cases.py
app/config.py
app/main.py
app/seed.py
app/simulate.py
app/store.py
docs/KNOWN_LIMITATIONS.md
docs/TEST_EVIDENCE.md
render.yaml
requirements.txt
static/app.js
tests/test_ai_validation.py
tests/test_cases_audit.py
tests/test_flow_direct.py
tests/test_graph_rules_risk.py
tests/test_seed_reset.py
```

## Appendix B — New backend/test/CI/migration paths (60)

```
.github/workflows/backup-produce.yml
.github/workflows/backup-restore-drill.yml
.github/workflows/backup-verify.yml
.github/workflows/security-gate.yml
app/auth.py
app/db.py
app/device_intel.py
app/geo_intel.py
app/graph_intel.py
app/intel_ai.py
app/intel_evidence.py
app/intel_link.py
app/ip_intel.py
app/models_pg.py
app/ratelimit.py
app/risk_intel.py
backups/__init__.py
backups/crypto.py
backups/integrity.py
backups/logutil.py
backups/manifest.py
backups/produce.py
backups/restore.py
backups/shamir.py
backups/signing.py
backups/targets.py
migrations/__init__.py
migrations/loader.py
requirements.lock
scripts/security_gate.py
tests/backup_fakes.py
tests/test_ai_cost.py
tests/test_auth.py
tests/test_backup_manifest.py
tests/test_body_size_guard.py
tests/test_cors.py
tests/test_di03_device.py
tests/test_di04_ip.py
tests/test_di05_geo.py
tests/test_di06_link.py
tests/test_di07_graph.py
tests/test_di08_risk.py
tests/test_di09_evidence.py
tests/test_p1_crypto.py
tests/test_p1_integrity.py
tests/test_p1_shamir.py
tests/test_p1_signing.py
tests/test_p1_targets.py
tests/test_p2_integration.py
tests/test_p2_logutil.py
tests/test_p2_produce.py
tests/test_p2_resilience.py
tests/test_p2_restore.py
tests/test_pg_atomic_decision.py
tests/test_pg_hardening.py
tests/test_pg_migration.py
tests/test_pg_parity.py
tests/test_rate_limit.py
tests/test_static_escaping.py
tests/test_write_token.py
```

## Appendix C — New frontend paths (135; duplicate EXCLUDED per D1)

```
frontend/.env.example
frontend/.gitignore
frontend/a11y.test.tsx
frontend/app/cases/[caseId]/audit/page.test.tsx
frontend/app/cases/[caseId]/audit/page.tsx
frontend/app/cases/[caseId]/page.test.tsx
frontend/app/cases/[caseId]/page.tsx
frontend/app/demo/page.test.tsx
frontend/app/demo/page.tsx
frontend/app/favicon.ico
frontend/app/globals.css
frontend/app/icon.png
frontend/app/investigations/[id]/page.test.tsx
frontend/app/investigations/[id]/page.tsx
frontend/app/layout.tsx
frontend/app/manifest.ts
frontend/app/network/[txnId]/page.test.tsx
frontend/app/network/[txnId]/page.tsx
frontend/app/page.tsx
frontend/app/replay/[scenarioId]/page.test.tsx
frontend/app/replay/[scenarioId]/page.tsx
frontend/components/ai-panel.test.tsx
frontend/components/ai-panel.tsx
frontend/components/ambient-background.test.tsx
frontend/components/ambient-background.tsx
frontend/components/app-shell.test.tsx
frontend/components/app-shell.tsx
frontend/components/audit-list.test.tsx
frontend/components/audit-list.tsx
frontend/components/breadcrumbs.test.tsx
frontend/components/breadcrumbs.tsx
frontend/components/command-activity.test.tsx
frontend/components/command-activity.tsx
frontend/components/command-ai-brief.test.tsx
frontend/components/command-ai-brief.tsx
frontend/components/command-kpis.test.tsx
frontend/components/command-kpis.tsx
frontend/components/command-network-preview.test.tsx
frontend/components/command-network-preview.tsx
frontend/components/command-rule-summary.test.tsx
frontend/components/command-rule-summary.tsx
frontend/components/decision-form.test.tsx
frontend/components/decision-form.tsx
frontend/components/evidence-list.test.tsx
frontend/components/evidence-list.tsx
frontend/components/exec-kpis.test.tsx
frontend/components/exec-kpis.tsx
frontend/components/feature-cards.test.tsx
frontend/components/feature-cards.tsx
frontend/components/graph-explorer.test.tsx
frontend/components/graph-explorer.tsx
frontend/components/graph-table.test.tsx
frontend/components/graph-table.tsx
frontend/components/intel-panels.test.tsx
frontend/components/intel-panels.tsx
frontend/components/landing/GlobalHeroScene.test.tsx
frontend/components/landing/GlobalHeroScene.tsx
frontend/components/landing/GlobalLandingPage.tsx
frontend/components/landing/LandingChrome.tsx
frontend/components/landing/LandingContent.test.tsx
frontend/components/landing/LandingControls.tsx
frontend/components/landing/LandingPanels.tsx
frontend/components/landing/LandingStrips.tsx
frontend/components/landing/scene/brain.ts
frontend/components/landing/scene/earth.ts
frontend/components/landing/scene/network.ts
frontend/components/landing/scene/orbital.ts
frontend/components/landing/scene/scene.test.ts
frontend/components/landing/scene/shared.ts
frontend/components/landing/scene/stars.ts
frontend/components/landing/scene/webgl.ts
frontend/components/landing/WebGLFallback.tsx
frontend/components/login-gate.test.tsx
frontend/components/login-gate.tsx
frontend/components/modal.test.tsx
frontend/components/modal.tsx
frontend/components/notifications.test.tsx
frontend/components/notifications.tsx
frontend/components/orbital-explorer.test.tsx
frontend/components/orbital-explorer.tsx
frontend/components/replay-controls.test.tsx
frontend/components/replay-controls.tsx
frontend/components/risk-badge.test.tsx
frontend/components/risk-badge.tsx
frontend/components/section-nav.test.tsx
frontend/components/section-nav.tsx
frontend/components/simulation-panel.test.tsx
frontend/components/simulation-panel.tsx
frontend/components/stat.test.tsx
frontend/components/stat.tsx
frontend/components/system-status.test.tsx
frontend/components/system-status.tsx
frontend/components/tabs.test.tsx
frontend/components/tabs.tsx
frontend/components/theme-provider.test.tsx
frontend/components/theme-provider.tsx
frontend/components/theme-selector.tsx
frontend/components/timeline.test.tsx
frontend/components/timeline.tsx
frontend/components/toast.test.tsx
frontend/components/toast.tsx
frontend/components/why-risk-panel.tsx
frontend/components/workflow-strip.test.tsx
frontend/components/workflow-strip.tsx
frontend/lib/api.test.ts
frontend/lib/api.ts
frontend/lib/format.ts
frontend/lib/graph-layout.test.ts
frontend/lib/graph-layout.ts
frontend/lib/landing-audio.test.ts
frontend/lib/landing-audio.ts
frontend/lib/orbital-layout.test.ts
frontend/lib/orbital-layout.ts
frontend/lib/privacy.test.ts
frontend/lib/privacy.ts
frontend/lib/theme.test.ts
frontend/lib/theme.ts
frontend/lib/use-count-up.test.tsx
frontend/lib/use-count-up.ts
frontend/next.config.ts
frontend/next-env.d.ts
frontend/package.json
frontend/package-lock.json
frontend/public/assets/cruiseshield-logo-original.png
frontend/public/icons/apple-touch-icon.png
frontend/public/icons/favicon-16x16.png
frontend/public/icons/favicon-32x32.png
frontend/public/icons/favicon-48x48.png
frontend/public/icons/icon-192.png
frontend/public/icons/icon-512.png
frontend/README.md
frontend/styles/landing.css
frontend/tsconfig.json
frontend/vitest.config.ts
frontend/vitest.setup.ts
```

## Appendix D — New docs paths (97, incl. this manifest)

```
docs/BACKUP_RECOVERY_RUNBOOK.md
docs/CLOSEOUT_BACKUP_PROCEDURE.md
docs/CLOSEOUT_PILOT_GAP_REGISTER.md
docs/COMMAND_EXPERIENCE/01-AUDIT.md
docs/COMMAND_EXPERIENCE/02-BASELINE.md
docs/COMMAND_EXPERIENCE/03-TRACEABILITY.md
docs/COMMAND_EXPERIENCE/04-DESIGN.md
docs/COMMAND_EXPERIENCE/05-CONFLICT-001.md
docs/COMMAND_EXPERIENCE/06-ACCEPTANCE-1B.md
docs/CRUISESHIELD_AI_PHASE_9_TO_15_MASTER_COMPLETION_REPORT.md
docs/DEMO_SCRIPT.md
docs/GAP_CLOSURE_10_REPORT.md
docs/HACKATHON_ASSET_AND_CODE_PROVENANCE.md
docs/HACKATHON_CRITICAL_GAP_REGISTER.md
docs/HACKATHON_FINAL_DEMO_SCRIPT.md
docs/HACKATHON_FINAL_SUBMISSION_READINESS_REPORT.md
docs/HACKATHON_JUDGING_RUBRIC_AUDIT.md
docs/HACKATHON_META_AI_CONTRIBUTION_REPORT.md
docs/HACKATHON_NEW_WORK_CONTRIBUTION_REGISTER.md
docs/HACKATHON_OFFICIAL_RULES_COMPLIANCE.md
docs/HACKATHON_PRE_EVENT_BASELINE.md
docs/HACKATHON_PUBLIC_REPOSITORY_SECURITY_AUDIT.md
docs/HACKATHON_READINESS_REPORT.md
docs/HACKATHON_RUBRIC_ACCEPTANCE.md
docs/HACKATHON_SUBMISSION_ELIGIBILITY_REPORT.md
docs/HACKATHON_ZERO_GAP_MATRIX.md
docs/IMPACT_CASE.md
docs/J1_GIT_COMMIT_FILE_MANIFEST.md
docs/MASTER_CLOSEOUT_RELEASE_DECISION.md
docs/PHASE_10_REMEDIATION_MATRIX.md
docs/PHASE_10_SECURITY_AND_RELIABILITY_REPORT.md
docs/PHASE_10_SECURITY_FINDINGS_REGISTER.md
docs/PHASE_11_BROWSER_COMPATIBILITY_MATRIX.md
docs/PHASE_11_LOAD_AND_STABILITY_REPORT.md
docs/PHASE_11_PERFORMANCE_VALIDATION_REPORT.md
docs/PHASE_11_RECOVERY_REPORT.md
docs/PHASE_12_FINAL_DEFECT_REGISTER.md
docs/PHASE_12_FINAL_PRODUCT_ACCEPTANCE_REPORT.md
docs/PHASE_12_RELEASE_GATE_MATRIX.md
docs/PHASE_13_ASSET_AND_CODE_PROVENANCE.md
docs/PHASE_13_HACKATHON_READINESS_REPORT.md
docs/PHASE_13_META_AI_CONTRIBUTION_REPORT.md
docs/PHASE_13_NEW_WORK_CONTRIBUTION_REGISTER.md
docs/PHASE_13_RULES_AND_ELIGIBILITY_MATRIX.md
docs/PHASE_13_VIDEO_AND_SUBMISSION_PACKAGE.md
docs/PHASE_14_DEMO_ENVIRONMENT_GUIDE.md
docs/PHASE_14_SUBMISSION_ARCHIVE_MANIFEST.md
docs/PHASE_14_SUBMISSION_PRESERVATION_REPORT.md
docs/PHASE_15_CONTROLLED_PILOT_PLAN.md
docs/PHASE_15_DATA_GOVERNANCE_FRAMEWORK.md
docs/PHASE_15_INSTITUTIONAL_REQUIREMENTS.md
docs/PHASE_15_INTEGRATION_ARCHITECTURE.md
docs/PHASE_15_MODEL_RISK_FRAMEWORK.md
docs/PHASE_15_OPERATIONAL_GOVERNANCE.md
docs/PHASE_15_PRODUCTION_READINESS_MATRIX.md
docs/PHASE_15_REGULATORY_ASSESSMENT.md
docs/PHASE_2B_BROWSER_SMOKE_TEST.md
docs/PHASE_2B_BUILD_VERIFICATION.md
docs/PHASE_2B_REMAINING_GAPS.md
docs/PHASE_2B_TECHNICAL_ACCEPTANCE_REPORT.md
docs/PHASE_3_1_DEMO_READINESS_AUDIT.md
docs/PHASE_3_2_REHEARSAL_REPORT.md
docs/PHASE_3_2_REMEDIATION_AND_RETEST.md
docs/PHASE_3_3_VISUAL_QA.md
docs/PHASE_3_4_LIVE_AI.md
docs/PHASE_9_INTEGRATED_SYSTEM_ACCEPTANCE_REPORT.md
docs/PRODUCT_UIUX_PHASE_4_TO_8_COMPLETION_REPORT.md
docs/REDTEAM_LIVE_AI_REPORT.md
docs/RELEASE_GAP_AUDIT.md
docs/RELEASE_READINESS_A_SUBMISSION.md
docs/RELEASE_READINESS_B_RENDER.md
docs/RENDER_10_RELEASE_GATES.md
docs/RENDER_1_FRONTEND_READINESS.md
docs/RENDER_2_BACKEND_READINESS.md
docs/RENDER_3_DATABASE_DECISION.md
docs/RENDER_4_SECURITY_REMEDIATION.md
docs/RENDER_5_CONFIGURATION_SPEC.md
docs/RENDER_6_ENV_REGISTER.md
docs/RENDER_7_DEPLOYMENT_RUNBOOK.md
docs/RENDER_8_ROLLBACK_RECOVERY.md
docs/RENDER_9_STAGING_ACCEPTANCE.md
docs/SECURITY_GATE_POLICY.md
docs/STAGING_APPROVAL_PREP.md
docs/STAGING_GATE_A_TO_J.md
docs/SUBMIT_A_PARTICIPANT_CHECKLIST.md
docs/SUBMIT_B_RULES_COMPLIANCE.md
docs/SUBMIT_C_CONTRIBUTION_REGISTER.md
docs/SUBMIT_D_METAAI_EVIDENCE.md
docs/SUBMIT_E_IP_LICENCE.md
docs/SUBMIT_FINALISATION_A_TO_J.md
docs/SUBMIT_F_REPO_SECURITY.md
docs/SUBMIT_G_BACKUP_READINESS.md
docs/SUBMIT_H_DEMO_SCRIPT.md
docs/SUBMIT_I_PACKAGE_CHECKLIST.md
docs/SUBMIT_J_REHEARSAL.md
docs/VIDEO_STORYBOARD.md
docs/ZERO_COST_A_TO_J.md
```
