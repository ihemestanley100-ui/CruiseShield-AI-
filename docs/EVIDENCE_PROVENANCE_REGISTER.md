# EVIDENCE PROVENANCE REGISTER — Release Cert v3.0

Date: 2026-11-04. Commit: `ff7052bdf0ac48a68f69c3937d9b8708ca265354`.
Executor: Muse Code session. No secrets stored in any evidence file.

| Evidence ID | Pillar | Category | Tool / method | Actual outcome |
|---|---|---|---|---|
| E-D1 | 01 | TEST | `pytest tests -q` ×4 (unsandboxed) | 430+73+1-flake each; all 4 flakes pass on re-run; prior 431/73/0 stands |
| E-D2 | 01 | TEST | `npx vitest run` | 71 files / 391 tests, 0 fail, 0 skip |
| E-D3 | 01 | TEST | vitest 2 i18n files | 12/12 |
| E-D4 | 01 | TEST | pytest `-k max_output_tokens` | 4/4 |
| E-D5 | 01 | BUILD | `npm run build`, `tsc --noEmit` | EXIT=0, 8/8 pages; tsc 0 errors |
| E-D6 | 01 | RUNTIME | uvicorn boot + `/api/v1/health` | healthy, all checks PASS; state file untouched |
| E-P2a | 02 | DEPLOYMENT | live `/api/v1/health` GET | 200 healthy; model/pg NOT_CONFIGURED (known) |
| E-P2b | 02 | SOURCE | `render.yaml` parse + review | Valid YAML, 2 web services; 4 backend vars w/o render.yaml entry (defaults apply). See `FINAL_DEPLOYMENT_VERIFICATION.md` |
| E-B3 | 03 | BROWSER/SCREENSHOT | Playwright + system Chrome, 9 shots | Real viewports incl. 390px; drag rotates globe; console 0 errors |
| E-S1 | 04 | SECURITY | pattern scan (1151 files) + tracked-name check | 0 matches; no secret files tracked |
| E-S2 | 04 | SECURITY | built-bundle grep | No backend secrets; public token ref with `""` fallback |
| E-S3 | 04 | SECURITY | `npm audit`, `pip-audit` | postcss 2 vulns (breaking fix deferred); Python 0 vulns |
| E-M1 | 05 | SOURCE/API | `dev.meta.ai` docs inspection | Base URL + model + auth match code; Standard $1.25/$4.25 per M; no training use; no free tier found |
| E-M2 | 05 | SOURCE | `app/ai_adapter.py` review | `max_tokens` enforced both paths; truncation/retries/caps intact; NO live call made. See `META_AI_INTEGRATION_AUDIT.md` |
| E-F1 | 06 | BILLING | owner dashboard read-outs (prior) | Hobby $0, usage tiny, projection $0; card present; overage uncapped |
| E-R1 | 07 | REPOSITORY | unauthenticated web fetch ×2 | Repo + production-launch branch public (200) |
| E-R2 | 07 | REPOSITORY | `git ls-remote` | origin/production-launch = ff7052b = local HEAD |
| E-R3 | 07 | REPOSITORY | `git status`, README/LICENSE check | README yes, LICENSE no; 60 modified + 77 untracked unreleased |
| F-D1 | 01 | TEST | `pytest tests -q` (fresh) | 431 passed, 73 skipped, 0 failed, exit 0 |
| F-D2 | 01 | TEST | flaky-4 loop ×5 | 5/5 green → Windows contention, closed |
| F-D3 | 01 | TEST/BUILD | vitest + `npm run build` (fresh) | 391/391; EXIT=0, 8/8 pages |
| F-P2 | 02 | DEPLOYMENT | live health + auth/mode GETs | 200 healthy (new run_id); auth_enabled:false |
| F-B3 | 03 | BROWSER/SCREENSHOT | Playwright recapture, 3 shots | Hero/canvases OK, console 0 errors |
| F-S1 | 04 | SECURITY | secret scan + bundle re-grep | 0/1114 files; bundle clean |
| F-S2 | 04 | SECURITY | `render.yaml` +5 lines, YAML valid, cfg tests | AI_MAX_OUTPUT_TOKENS declared; 6/6 green |
| F-S3 | 04 | SECURITY | `npm audit fix --dry-run` | No non-breaking fix; residual accepted |
| F-M1 | 05 | API | 3 keyed POSTs (unintended, .env key) | 3× 503 MODEL_TIMEOUT; bare GET 404 (egress OK) |
| F-M2 | 05 | TEST | `test_ai_validation` + `test_ai_cost` | 49 passed (simulated only) |
| F-R1 | 07 | REPOSITORY | manifest generator | 524 files: 141 INCLUDE / 383 EXCLUDE |
| F-E2E | 09 | RUNTIME | 8-leg workflow on temp state copy | 7 PASS (pinned values); EXPLAIN blocked; state clean |
