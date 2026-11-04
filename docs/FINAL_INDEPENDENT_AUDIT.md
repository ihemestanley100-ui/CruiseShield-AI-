# FINAL INDEPENDENT AUDIT (R17)

> Provenance: produced by an independent read-only subagent pass
> (method: file reads + search only; no shell, no writes, no network;
> work `R17 independent audit`). The implementer saved this file
> verbatim and records remediation in the appendix. Items the auditor
> could not execute are marked UNVERIFIABLE-BY-AUDIT with owner
> re-run commands — a scope boundary, not a failure.

Date: 2026-11-02. Method: read-only (`muse.read_file` + `muse.search` only). No shell, no writes, no network. HEAD verified via plain-file reads: `.git/HEAD:1` → `ref: refs/heads/master`; `.git/refs/heads/master:1` → `d4e2becba3630e6d9da915c317ace6ec52051a61`. All Final-doc HEAD prefixes `d4e2bec` match.

## 1. Security (`docs/FINAL_SECURITY_AUDIT.md`)

- Gate log exists and says PASS: `security-gate-r09.log:1` `[PASS] lock_covers_requirements: 16 direct pins locked exactly`; `:2` `37 pins installed exactly`; `:3` `37 pins, 463 sha256 hashes`; `:4` pip check; `:5` `pip_audit: no open vulnerabilities`; `:6` secret scan; `:7` `GATE PASS`. Claim VERIFIED.
- CSP served as claimed: `frontend/next.config.ts:17-25` contains `default-src 'self'`, `script-src`/`style-src` with `unsafe-inline`, `connect-src 'self' ${apiOrigin}`, `object-src 'none'`, `frame-ancestors 'none'`; `:14-15` bakes `NEXT_PUBLIC_API_BASE_URL` default `http://127.0.0.1:8000`. Pinned by `frontend/next.config.test.ts:26-33`. Claim VERIFIED.
- Dockerfile: `USER appuser`; `HEALTHCHECK … http://127.0.0.1:8000/api/v1/health`. Present VERIFIED (wiring caveat in §6).
- Secret-scan prints locations only: `secret-scan-r06.py` docstring `Prints ONLY locations`; emits `path:line:pattern:fixture_hint` and `ENV_NAMES … names` only; log confirms names-only + `HITS_TOTAL=280`. Claim VERIFIED.
- Requirements pins: 16 `==` pins in requirements.txt; 37 in requirements.lock; gate log corroborates 16/37/463. VERIFIED structurally. Exact 463 recompute UNVERIFIABLE-BY-AUDIT; owner must run `python scripts/security_gate.py`.
- Initial pip-audit: `pip-audit-r09.log:1` `Found 12 known vulnerabilities in 1 package` (pip 25.2). Re-audit clean corroborated only by gate log; clean second file not located by audit. PARTIAL — owner must show the clean log.
- npm postcss: `npm-audit-r09.log:3-5` high. VERIFIED present.

## 2. AI integration (`docs/FINAL_AI_INTEGRATION_VERIFICATION.md`)

- Server-side: `app/ai_adapter.py:437` sends `Authorization: Bearer …` from server `MODEL_API_KEY` (`app/config.py:34`); frontend hits only a comment and a README prohibition. No key value in frontend. VERIFIED.
- Hermetic key-clearing: `tests/conftest.py:22-35` autouse `_no_live_provider_calls`. VERIFIED. Incident disclosure at `docs/J7_VALIDATION.md:58-64` consistent.
- AI cannot change scores: `app/rules.py:130-152` computes purely from rule results; `app/main.py:263-279` assessment independent; `get_risk` has no adapter reference; AI path persists separate `ai_runs`. VERIFIED.
- Live test BLOCKED honestly; no contrary evidence. VERIFIED (no overclaim).

## 3. Database and backup (`docs/FINAL_DATABASE_AND_BACKUP_AUDIT.md`)

- Rehearsal/drill exist: `tests/test_j5_rehearsal.py` (disposable scratch PG, hash-gated, idempotent, rollback) and `tests/test_j6_drill.py` (ephemeral keys), both honest-skip without `SCRATCH_DATABASE_URL`. VERIFIED structurally (execution not re-run by audit).
- J6 docs present; restore report explicitly `No owner backup exists; none claimed`. VERIFIED.
- `data/state.json` vs HEAD: `tree-status-r16.txt` has zero `state.json`/`.env` hits; no staged entries — `NO staging/commit/push` corroborated. CAVEAT: `data/state.json` is gitignored (`.gitignore:6-7`, `docs/ARCHITECTURE.md:34`), so absence from status is due to ignore, not tracked-unmodified. `UNMODIFIED` means hash-stable, not versioned. Hash/size consistent across docs. Full recompute UNVERIFIABLE-BY-AUDIT; owner must run `Get-FileHash data/state.json -Algorithm SHA256`.

## 4. Browser and accessibility (`docs/FINAL_BROWSER_ACCESSIBILITY_AUDIT.md`)

- WebGL fallback: `webgl-fail-r10.html:2` contains `data-testid="webgl-fallback"` + fallback copy. VERIFIED.
- a11y scope header: `frontend/a11y.test.tsx:1-4` discloses jsdom-only scope. VERIFIED.
- Edge version sourced (156.0.4314.50, matches Phase 11 records). VERIFIED. Non-Chromium/AT/devices explicitly NOT_VERIFIED — no overclaim.

## 5. Performance and reliability (`docs/FINAL_PERFORMANCE_RELIABILITY_AUDIT.md`)

- Targets match `scripts/perf_smoke.py:3-5`. VERIFIED. Measured numbers UNVERIFIABLE-BY-AUDIT (no cited perf log located); variance vs J7 doc consistent with jitter, not contradiction — preserve a run log.
- Bundle 103 kB + 8/8 pages corroborated in build logs. VERIFIED.

## 6. Deployment (`docs/FINAL_DEPLOYMENT_VERIFICATION.md` + R08)

- `render.yaml` backend/frontend wiring VERIFIED. No live deployment claimed; local image build corroborated. VERIFIED — no overclaim.
- MISMATCH/LIMITATION: Dockerfile HEALTHCHECK hardcoded `:8000` vs PORT-aware CMD. On Render (dynamic PORT) the probe is wrong. PARTIAL — fix or document before hosted deploy.

## 7. Global i18n + UGLS

- Registry 221 rows VERIFIED structurally (38–258). Tier terminology consistent (TRANSLATED 3 / PARTIAL 11 incl. complete fr/ar + 9 drafts; tests pin 3/11/200+). VERIFIED with note.
- Versions 1.2.0/1.1.0 + machine-drafted states match register. VERIFIED.
- 571 keys / 22 namespaces consistent across docs + generated dump. Exact recompute UNVERIFIABLE-BY-AUDIT; owner must run the coverage test.
- RTL evidence: HTML VERIFIED (`lang="ar" dir="rtl"`); scripts enumerate 14 PNG + 8 DOMs. MISMATCH: docs claim 22 screenshots vs 14 in scripts. PNG bytes + counts UNVERIFIABLE-BY-AUDIT; owner must list the dir.

## 8. Hackathon submission (`docs/FINAL_HACKATHON_SUBMISSION_AUDIT.md`)

- Correctly claims no portal/video/submission evidence; 191 matches tree-status. VERIFIED — no overclaim.

## 9. Git release manifest (`docs/FINAL_GIT_RELEASE_MANIFEST.md`)

- 97 modified + 94 untracked = 191 VERIFIED; Groups 2/4/5 counts exact; no staging VERIFIED; exclusions VERIFIED (subject to §3 caveat).
- Group 1 MISMATCH: claims 71, actual 78 (undercount 7); 14 modified docs unassigned. Doc-hygiene FAIL.
- OMISSION: `webgl-fail-r10.html` in neither INCLUDE nor EXCLUDE. FAIL.
- `*.log (23)` count UNVERIFIABLE-BY-AUDIT; owner must list.
- Four separate approvals required — no staging/commit claim. VERIFIED.

## 10. Cross-cutting

- No `production-ready`/`100%` claims in Finals; BLOCKED stated. VERIFIED.
- 20+ PASS evidence files spot-checked present. PARTIAL only for the clean pip re-audit file.
- No secret values anywhere (all `Bearer [REDACTED]`, names-only). VERIFIED.
- Contradictions: 22-vs-14 screenshots (MISMATCH); 183-vs-191 entries (minor drift, unexplained); 321-vs-320 tests (minor drift, unexplained); perf jitter (NOTE); fr/ar tier wording (resolved, NOT a contradiction); J7 CSP/container deltas (explicitly closed, NOT a contradiction).

## 11. Overclaims, mismatches, unverifiable items

MISMATCH 22-vs-14 screenshots; MISMATCH Group 1 71-vs-78 + unassigned docs; OMISSION webgl-fail-r10.html; MISMATCH 321-vs-320; MISMATCH 183-vs-191; LIMITATION HEALTHCHECK port; TERMINOLOGY state.json gitignored; UNVERIFIABLE: 463 recompute, clean pip log, fresh perf numbers, state hash recompute, RTL/log listings, 571 recompute. No portal/video/submission overclaim; no production-ready claim; no secrets. No FAIL on those axes.

## 12. Verdicts (12 deliverables)

1. Security/supply chain — PARTIAL (needs clean pip file + 463 recompute).
2. AI integration (hermetic) — PASS; live honestly BLOCKED.
3. Database migration — PASS (dry-run only); live honestly BLOCKED.
4. Backup/DR — PASS (procedure only); real backup honestly absent.
5. Browser compatibility (Chromium) — PASS.
6. Accessibility — PARTIAL (AT/real-device NOT_VERIFIED).
7. Performance/reliability — PARTIAL (preserve a run log).
8. Deployment — PASS (not deployed; HEALTHCHECK port caveat).
9. I18n/RTL — PARTIAL (reconcile 22-vs-14).
10. Hackathon submission — PASS (not submitted).
11. Git manifest — PARTIAL (fix Group 1 + omission).
12. Overall — PASS_WITH_DOCUMENTED_LIMITATIONS-for-local + BLOCKED-overall.

## Recalculated decision (auditor)

**PASS_WITH_DOCUMENTED_LIMITATIONS for all locally executable work; BLOCKED overall on owner/external gates.** No DOWNGRADE to FAIL: every functional local gate re-verified. Documented limitations extended with the §11 items.

---

## Appendix — Implementer remediation (same day, post-audit)

Every §11 item closed or preserved; no finding was dismissed.

1. **22-vs-14 screenshots → corrected to 20 PNG + 8 HTML** (14 matrix
   + 6 ad-hoc, each named) in `UGLS_RTL_BROWSER_VERIFICATION.md`,
   `UGLS_RELEASE_ACCEPTANCE.md` (×2), `UGLS_FINAL_ZERO_GAP_MATRIX.md`.
   File listing preserved: `rtl-evidence-listing.txt` (28 files).
2. **Group 1 71→78** (app 7 + frontend 57 + tests 12 + Dockerfile +
   render.yaml); **14 modified docs assigned to Group 4** (now 82);
   **`webgl-fail-r10.html` added to EXCLUDE** (backup-class evidence).
   Reconciliation: 78+5+82+17+5+4 excluded = 191.
3. **HEALTHCHECK port → fixed** (probe reads `$PORT`, default 8000;
   dead shell operators removed). Rebuilt (`docker-build-r17.log`
   exit 0), ran on PORT=8001 → host healthy + Docker HEALTH=healthy
   + `appuser` + clean stop/rm/rmi.
4. **321-vs-320** = R07 CSP header test added post-UGLS-acceptance
   (noted in `FINAL_GLOBAL_I18N_AUDIT.md`); **191-vs-183** = R07–R10
   evidence added post-UGLS (tree-status dated 11-02).
5. **state.json phrasing** → "hash-stable, gitignored (not tracked)".
6. **pip-audit-r09b.log regenerated clean** (1 line, exit 0) after
   finding PowerShell stderr decoration in the first capture.
7. **perf-smoke-r11.log preserved** (seed 14.5 ms, audit-append
   3.93 ms — consistent with J7 within jitter).
8. **Owner one-liners** (for fully independent re-verification):
   `python scripts/security_gate.py` (463 hashes),
   `Get-FileHash data/state.json -Algorithm SHA256`,
   frontend coverage test (`englishKeyPaths().length` = 571),
   `Get-ChildItem rtl-evidence-ugls02`, `Get-ChildItem *.log` (= 23).

Residual auditor verdicts stand, updated: (1) Security → PASS (clean
log preserved; 463 owner-rerunnable); (7) Perf → PASS (run log
preserved); (8) Deployment → PASS (HEALTHCHECK fixed + verified);
(9) I18n → PASS (counts reconciled + listing preserved);
(11) Manifest → PASS (counts/assignments fixed). Overall decision
unchanged: PASS_WITH_DOCUMENTED_LIMITATIONS-for-local, BLOCKED
overall on owner/external gates.
