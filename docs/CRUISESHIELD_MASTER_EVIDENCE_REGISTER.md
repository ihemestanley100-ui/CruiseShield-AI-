# CRUISESHIELD MASTER EVIDENCE REGISTER — CS-FRC-2026-001 §10

Date: 2026-11-04. Commit: `ff7052bdf0ac48a68f69c3937d9b8708ca265354`.
Consolidates v3.0 E-series + FRC-001 F-series. No secrets stored. Statuses:
PASS / PARTIAL / BLOCKED / NOT VERIFIED only. Historical results are labeled;
nothing historical is presented as fresh.

## v3.0 evidence (prior session, retained)

| Evidence ID | Pillar | Requirement | Test / inspection | Source / service | Command / procedure | Result | Artifact path | Status |
|---|---|---|---|---|---|---|---|---|
| E-D1 | 01 | backend suite | full pytest | repo tests | `pytest tests -q` | 431/73/0 | session log | PASS |
| E-D2 | 01 | frontend suite | full vitest | frontend | `npx vitest run` | 391/391 | session log | PASS |
| E-D3 | 01 | i18n freshness | 2 test files | frontend/lib/i18n | vitest | 12/12 | kit TSVs | PASS |
| E-D4 | 01 | token cap | focused pytest | tests | `-k max_output_tokens` | 4/4 | session log | PASS |
| E-D5 | 01 | build+types | build, tsc | frontend | `npm run build`, `tsc` | EXIT=0, 8/8, 0 errs | session log | PASS |
| E-D6 | 01 | runtime health | boot + GET | local uvicorn | `/api/v1/health` | healthy, all PASS | session log | PASS |
| E-P2a | 02 | live backend | GET health | Render URL | `/api/v1/health` | 200 healthy | session log | PASS |
| E-P2b | 02 | blueprint | parse+review | render.yaml | pyyaml | valid, 2 services | render.yaml | PARTIAL |
| E-B3 | 03 | browser+shots | Playwright/Chrome | :3000 | 9 captures | viewports+drag+0 errors | browser-evidence/cert-v3/ | PASS |
| E-S1 | 04 | secret scan | pattern scan | repo (1151 files) | key-pattern regex | 0 matches | session log | PASS |
| E-S2 | 04 | bundle scan | grep build | .next/static | secret-name grep | clean, empty fallback | session log | PASS |
| E-S3 | 04 | deps | audits | pip+npm | pip-audit, npm audit | 0 py; postcss×2 | session log | PARTIAL |
| E-M1 | 05 | Meta docs | doc inspection | dev.meta.ai | web fetch | config verified, paid-only | session log | PARTIAL |
| E-M2 | 05 | adapter | code review | app/ai_adapter.py | read | capped, complete, no call | app/ai_adapter.py | BLOCKED |
| E-F1 | 06 | billing | dashboard read-outs | Render (owner) | read-only evidence | $0/$0, card present | prior reports | PARTIAL |
| E-R1 | 07 | public access | web fetch ×2 | github.com | unauthenticated GET | 200/200 | session log | PASS |
| E-R2 | 07 | remote SHA | ls-remote | origin | git ls-remote | ff7052b = HEAD | session log | PASS |
| E-R3 | 07 | tree state | status+docs check | repo | git status | 60+77 unreleased, no LICENSE | session log | PARTIAL |

## FRC-001 evidence (fresh this execution)

| Evidence ID | Pillar | Requirement | Test / inspection | Source / service | Command / procedure | Result | Artifact path | Status |
|---|---|---|---|---|---|---|---|---|
| F-D1 | 01 | backend suite | full pytest | repo tests | `pytest tests -q` | 431/73/0 exit 0 | session log | PASS |
| F-D2 | 01 | flake analysis | loop ×5 | 4 tests | pytest subset | 5/5 green, closed | session log | PASS |
| F-D3 | 01 | frontend+build | vitest, build | frontend | `npx vitest run`, `npm run build` | 391/391; EXIT=0 8/8 | session log | PASS |
| F-P2 | 02 | live posture | GETs | Render URL | health + auth/mode | healthy; unarmed | session log | PARTIAL |
| F-B3 | 03 | browser re-verify | Playwright/Chrome | :3000 | 3 captures | green, 0 errors | browser-evidence/cert-frc/ | PASS |
| F-S1 | 04 | scans | pattern+bundle | repo, .next | regex, grep | clean | session log | PASS |
| F-S2 | 04 | config repair | edit+validate+test | render.yaml | +5 lines, pyyaml, pytest | valid, 6/6 | render.yaml | PASS |
| F-S3 | 04 | postcss options | dry-run audit | frontend | `npm audit fix --dry-run` | no non-breaking fix | session log | PARTIAL |
| F-M1 | 05 | live Meta | 3 keyed POSTs (unintended) | api.meta.ai | ai-analysis POST | 3× 503 timeout; egress OK | session log | BLOCKED |
| F-M2 | 05 | offline adapter | pytest | AI test files | 2 files | 49 passed (simulated) | session log | PASS |
| F-R1 | 07 | manifest | generator | git status -uall | classify 524 files | 141 IN / 383 OUT | PUBLIC_REPOSITORY_RELEASE_MANIFEST.md | PARTIAL |
| F-E2E | 09 | workflow | 8-leg HTTP run | temp-DATA_DIR uvicorn | GETs+POSTs | 7 PASS, EXPLAIN blocked | session log | PARTIAL |

## Cross-pillar E2E detail (F-E2E)

DETECT 1 alert + risk 84/HIGH (8 rules) / CONNECT 22n+30e / INVESTIGATE 200 /
EXPLAIN blocked (honest 503s, no spend) / VERIFY 39 items / SIMULATE 84→72 /
DECIDE TRIAGED+audit_0007 / AUDIT 1 event. `data/state.json` untouched.

## ZG-001 evidence (fresh this execution, 2026-11-04)

| Evidence ID | Pillar | Requirement | Test / inspection | Source / service | Command / procedure | Result | Artifact path | Status |
|---|---|---|---|---|---|---|---|---|
| Z-D1 | 01 | backend suite | full pytest | repo tests | `pytest tests -q` | 431/73/0 exit 0 | session log | PASS |
| Z-D2 | 01 | frontend suite | full vitest | frontend | `npx vitest run` | 391/391 | session log | PASS |
| Z-D3 | 01 | build + types | build, tsc | frontend | `npm run build`, `tsc` | EXIT=0 8/8, 0 errs | session log | PASS |
| Z-S1 | 02/04 | Blueprint repair | edit+validate+test | render.yaml | +2 vars, pyyaml, pytest | valid, 6/6 | render.yaml | PASS |
| Z-B1 | 03 | collapse + nav | Playwright clicks | :3000 | click, URL wait | pixels verified, /demo reached | browser-evidence/cert-zg/ | PASS |
| Z-B2 | 03 | region legend | click + source read | :3000, LandingPanels.tsx | click, grep | display-only by design | zg-region-select.png | PASS |
| Z-S2 | 04 | S-04 closure | config review | render.yaml, config.py | default comparison | all declarable vars present | render.yaml | PASS |
| Z-R1 | 07 | reproducibility | fresh clone + smoke | origin/production-launch | clone, pytest 2 files | ff7052b, 7 passed | session log (clone removed) | PASS |
| Z-C1 | — | baseline integrity | checksums | state.json, configs | sha256 | state ba1d4db4… pristine | session log | PASS |

## ZGEP-001 evidence (fresh closed-loop round, 2026-11-04)

| Evidence ID | Pillar | Requirement | Test / inspection | Source / service | Command / procedure | Result | Artifact path | Status |
|---|---|---|---|---|---|---|---|---|
| G-D1 | 01 | backend suite | full pytest | repo tests | `pytest tests -q` | 431/73/0 exit 0 | session log | PASS |
| G-D2 | 01 | frontend suite | full vitest | frontend | `npx vitest run` | 391/391 | session log | PASS |
| G-D3 | 01 | build + types | build, tsc | frontend | `npm run build`, `tsc` | EXIT=0 8/8, 0 errs | session log | PASS |
| G-D4 | 01 | boot + ready + headers | uvicorn boot, GETs | temp-DATA_DIR server | health, ready, header read, log scan | 200/200, headers OK, 0 log errors | session log | PASS |
| G-D5 | 01 | TODO sweep | marker grep | app, frontend, tests | TODO/FIXME/XXX/HACK | 0 actionable (i18n false positives) | session log | PASS |
| G-S1 | 04 | secret scan | pattern scan | repo (1180 files) | key-pattern regex | 0 matches | session log | PASS |
| G-S2 | 04 | bundle scan | fresh-build grep | .next/static | secret-name check | no backend secrets | session log | PASS |
| G-S3 | 04 | deps | audits | pip+npm | pip-audit, npm audit | 0 py; postcss×2 | session log | PARTIAL |
| G-B1 | 03 | browser recapture | Playwright/Chrome | :3000 | capture + console | green, 0 errors | browser-evidence/cert-zgep/ | PASS |
| G-P2 | 02 | live posture | GETs | Render URL | health + auth/mode | healthy; unarmed | session log | PARTIAL |

## Closure-round evidence CS-FRC-ZG-001 (2026-11-04, R01–R09 mapping)

| Evidence ID | R-req | Pillar | Type | Source | Env | Procedure | Result | Integrity note |
|---|---|---|---|---|---|---|---|---|
| H-A1 | — | — | Git | repo | local | branch/HEAD/status/stash/staged | ff7052b=origin, 166 entries, 0/0 | state.json sha ba1d4db4… |
| H-P2 | R01–R03 | 02 | API | Render URL | prod | GET health + auth/mode | 200 healthy, same run_id, unarmed | New timestamp, same deploy |
| H-L1 | — | 02/03 | API | localhost | local | :8000 health, :3000 GET, listeners | healthy/200, PIDs noted | Processes untouched |
| H-D1 | R09 | 01 | Test | repo tests | local | `pytest tests -q` | 431/73/0 exit 0 | Deterministic on tree |
| H-D2 | R09 | 01 | Test | frontend | local | `npx vitest run` | 391/391 | Deterministic on tree |
| H-D3 | R09 | 01 | Build | frontend | local | build + tsc | EXIT=0 8/8, 0 errs | Deterministic on tree |
| H-S1 | R07 | 04/07 | Test | repo (1181 files) | local | key-pattern regex | 0 matches | Covers manifest scope |
| H-S3 | R08 | 04 | Test | npm registry + tree | local | version/pin inspection, attack-surface grep | Exact pin 8.4.31 on 15.5.28+15.5.29; zero app-surface | Registry-fetched |
| H-F1 | R06 | 06 | Dashboard | render.com/pricing | external | Official page fetch (200) | Hobby 5 GB; overage $0.30/GB; no cap found | Saved fetch artifact |
| H-R1 | R07 | 07 | Git | repo | local | Drift check + row patch | 544 files, 157/387, 0 unclassified | Row-level audit |
| H-M1 | R05 | 05 | — | — | — | No keyed call (locked §8.4) | BLOCKED retained, no attempt | Policy boundary |

## Auto-fix round evidence CS-AUTO-001 (2026-11-04)

| Evidence ID | R-req | Pillar | Type | Source | Env | Procedure | Result | Integrity note |
|---|---|---|---|---|---|---|---|---|
| I-M1 | R05 | 05 | API | api.meta.ai | external | Keyless POST (no credentials) | Instant 401 invalid_api_key, 0.66 s | Proves POST path healthy |
| I-M2 | R05 | 05 | Dashboard | dev.meta.ai/docs | external | Error-semantics doc fetch (200) | 401 fast / 402 billing_not_configured documented | Saved fetch artifact |
| I-M3 | R05 | 05 | Test | app/ai_adapter.py | local | Exception-mapping read | Timeout vs 401 codes distinct; stall is downstream | Lines 464–479 |
| I-R1 | R07 | 07 | Git | origin | external | `git push --dry-run` (no mutation) | Transport ready, up-to-date | Non-mutating probe |
| I-R2 | R07 | 07 | Git | manifest | local | Max INCLUDE size | 71,677 B — no push-size risk | Row-level data |
| I-S1 | R03 | 04 | Test | app/main.py | local | HSTS conditional read | TLS-only by design (R09-F4) | Lines 61–69 |

## Owner-gated round evidence (2026-11-04, ACTION 01–07 sweep)

| Evidence ID | R-req | Pillar | Type | Source | Env | Procedure | Result | Integrity note |
|---|---|---|---|---|---|---|---|---|
| J-D1 | R09 | 01 | Test | repo tests | local | `pytest tests -q` | 431/73/0 exit 0 | Deterministic on tree |
| J-D2 | R09 | 01 | Test | frontend | local | `npx vitest run` | 391/391 | Deterministic on tree |
| J-P2 | R01–R03 | 02 | API | Render URL | prod | GET health + auth/mode | 200 healthy, NEW run_id, unarmed | Restart observed, not redeploy |
| J-C1 | R04 | 02 | Test | render.yaml + node | local | Service-block read, version check | plan:starter=paid path; node 20.19.6 match | Blueprint-as-written flagged |
| J-S1 | R07 | 04/07 | Test | repo (1181 files) | local | key-pattern regex | 0 matches | Covers manifest scope |
| J-R1 | R07 | 07 | Git | repo | local | Tree audit, LICENSE/ignore check | 166 entries, no LICENSE, env ignored | No mutation |

## Action-01 intake (2026-11-04, owner evidence pending)

| Evidence ID | R-req | Pillar | Type | Source | Env | Procedure | Result | Integrity note |
|---|---|---|---|---|---|---|---|---|
| K-A1 | R01 | 02 | Git | repo | local | Pre-evidence baseline | ff7052b=origin, 166 entries, state pristine | Intake baseline |
| K-P1 | R01–R03 | 02 | API | Render URL | prod | GET health + auth/mode | 200 healthy, same run_id, unarmed | No change since J-P2 |
| K-D1 | — | — | — | — | — | Awaiting owner | 4 readouts requested, not yet received | STOP boundary held |

## R01 evidence received (2026-11-04, owner dashboard readout)

| Evidence ID | R-req | Pillar | Type | Source | Env | Procedure | Result | Integrity note |
|---|---|---|---|---|---|---|---|---|
| L-R1 | R01 | 02 | Dashboard | Render (owner) | prod | Env names read-out | 3/3 MISSING, 0 env groups, section empty | Owner-supplied, non-secret |
| L-A1 | R01 | 02/04 | Test | app/auth.py + app/config.py | local | Fail-safe + format verification | Unset→open demo by design; no default creds; formats parsed | Code-read + round-trip |
| L-A2 | R03 | 04 | Git | repo | local | Arming values generated (owner-authorized) | 64-char secrets, 2 users verified, file git-invisible | Values never printed |

## R01 pre-arm gate (2026-11-04, no dashboard change made)

| Evidence ID | R-req | Pillar | Type | Source | Env | Procedure | Result | Integrity note |
|---|---|---|---|---|---|---|---|---|
| M-A1 | R01 | 02 | Git | repo | local | Tree + HEAD + arming-file audit | 166 entries, ff7052b, file present+ignored | Pre-change baseline |
| M-P1 | R01 | 02 | API | Render URL | prod | GET health + auth/mode | 200 healthy, same run_id, unarmed | Before-state snapshot |
| M-F1 | R01 | 06 | Dashboard | Prior billing evidence + Blueprint | external | $0-neutrality analysis | Env=$0; redeploy≈minutes of 0/500 free; 0 new resources | No charge path |
| N-P1 | R01 | 02 | API | Render URL | prod | Post-entry probe after owner reported 3 names present (read-only GET) | 200 healthy, SAME full run_id 0b2ffbc6…, auth_enabled:false → no redeploy completed; values not yet live | Names per owner only, not independently visible |
| O-P1 | R01 | 02 | API | Render URL | prod | Rollout-watch after owner reported deploy LIVE (3 fresh cache-busted GETs, ~2.5 min apart) | All: 200 healthy, SAME run_id 0b2ffbc6…, auth_enabled:false → serving process predates env entry; no POSTs run | Dashboard LIVE unreconciled; Deploy-log readout needed |
| P-D1 | R01 | 04 | API+Code | Render URL + repo | prod+local | Auth diagnostic: guarded GETs open (cases+demo/scenarios 200, state born 07:27Z), code trace (no dotenv override, flag=len>=32, single worker, no disk on Free, silent-by-design boot), artifact struct audit (64/64/2-valid, bools only) | No code fault; SESSION_SECRET empty in process; DEMO_USERS/TOKEN not externally readable; rollout-vs-delivery needs deploy-log timestamps | Zero POSTs, zero values printed, probe deleted |
| Q-R1 | R01 | 04 | Code+Test | repo + live URL | local+prod | Recovery sweep: no start scripts, import order clean, 58a3d50-ff7052b not GET-fingerprintable, real-parser round-trip 2/2 OK + wrong-pw rejected, 5th live round unchanged, backend 431/73 + frontend 391/391 fresh green | All 8 code suspects eliminated; all 12 test cases pre-covered; zero code/test changes required | Probes deleted; data/ pristine |
| R-A1 | R01 | 04 | Test | repo (TestClient, tmp store) | local | Armed-boot proof v4: real app + real generated values, isolated client per condition | 20/20 as designed: armed, both logins 200, anon 401s, R1 403 ADMIN_REQUIRED, R2 actor demo-token, R3 403 AI_LOGIN_REQUIRED, R4 200s | Values never printed; probe+tmp deleted |
| T-V1 | R01 | 02 | API | Render URL | prod | Post-redeploy triage (fresh GETs): NEW run_id 5f416dfd…, seed 08:51Z, but auth false + cases 200-open | Fresh post-save process lacks secret → DELIVERY failure isolated; stale-process ruled out; twin-service now prime suspect | Zero POSTs; URL-vs-name mismatch flagged |
| U-V1 | R01 | 02 | API+Test | Render URL + repo | prod+local | Post-confirmation triage: same 5f416dfd boot, still unarmed; suites rerun (backend 430+1-flake-pass/73, frontend 391/391) | Twin weakened by owner ID+URL match; ordering (deploy<save) now prime; timestamps still needed to prove it | Zero POSTs; no code changes |
| W-V1 | R01 | 02/04 | API | Render URL (dep-dblfc03) | prod | Full live suite on armed boot 827c142a (seed 09:08:39Z): auth true, anon 401s, token 200, bad-token 401, R1 403 ADMIN_REQUIRED, R3 403 AI_LOGIN_REQUIRED, R4 200+equals-GET, R2 decision_0001 actor demo-token, 22 responses leak-free | G05/G08 PASS; G06/G09/G10 FAIL (both logins 401 vs locally-proven creds → saved DEMO_USERS differs from file); R2 audit-echo unverified (probe field bug, follow-up declined) | One documented synthetic write; values never printed |
