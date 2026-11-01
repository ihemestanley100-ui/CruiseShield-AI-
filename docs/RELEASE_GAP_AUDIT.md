# Release Gap Audit — G01–G27 (master mandate, 2026-10-29)

> R18 addendum 2026-10-30: this audit is a dated snapshot; its baseline
> counts are superseded, not rewritten. Current evidence: backend suite
> 250 passed / 0 skipped / 0 failed with disposable scratch PostgreSQL
> (P2.2H/P2.2J); frontend 165/165 + `tsc --noEmit` exit 0 + `next build`
> exit 0, all observed agent-side (P2.2J); security gate 6/6 PASS.
> Sandbox npm/socket restrictions were lifted via approved escalated
> execution for these runs. G02/G07–G09/G14–G18/G22/G25/G26 PASS standing
> re-confirmed by that evidence; G10/G12/G13 closed by the mandate
> implementation below. Still open: G24 hosted behavior (BLOCKED, no
> deploy approval), G20 browser/a11y checks (PARTIAL), G27 recording
> (PARTIAL), first GitHub Actions run (NOT VERIFIED, push forbidden).

Baseline: branch `master` @ `0eaaaf5`; tracked mods = approved CORS batch +
gate tests only; `frontend/`, matrix, COMMAND_EXPERIENCE untracked; no stash.
Backend suite: 49 passed, 8 skipped (fresh). Frontend: 73/73 + typecheck +
build green (user-confirmed; npm unrunnable in this sandbox — standing EPERM).
Live state preserved: case_84721 ESCALATED, decisions 0001–0004, audits
through audit_0012, ai_runs 0001–0004 (all SUCCEEDED/VALIDATED), sims 0001–0002.
Risk 84 HIGH / 35 MODERATE, 22/30 graph, 39-item package. No reset performed.

Status: PASS (implemented + evidenced), PARTIAL (exists, incomplete),
FAIL (missing/failing), BLOCKED (external/approval).

| ID | Area | Status | Evidence / gap |
|----|------|--------|----------------|
| G01 | Problem/user/rubric mapping | PARTIAL | README + matrix exist; demo script missing → write docs/DEMO_SCRIPT.md |
| G02 | Full workflow DETECT→AUDIT | PASS | All stages verified locally 2026-10-29 |
| G03 | Efficiency indicators | PASS | 200× determinism test + measured 21.8 ms benchmark in TEST_EVIDENCE; AI latencies recorded |
| G04 | Explainable risk | PASS | 8 rules + 39 evidence + limitations text |
| G05 | Scenario variety | PASS | scn_primary (suspicious) + scn_ambiguous (38 MODERATE) + scn_false_positive; pinned tests |
| G06 | Messaging/onboarding | PASS | Workflow nav + onboarding copy + homepage tests; demo script covers the rest |
| G07 | AI integration config | PASS | Server-side key, muse-spark-1.3, real endpoint, 4 live SUCCEEDED runs |
| G08 | Evidence grounding | PASS | ID validation + tests + live VALIDATED refs |
| G09 | Structured schema | PASS | Prompt v2 + response_format + validation + failure codes |
| G10 | Investigative depth | PARTIAL | Single-shot only; follow-ups MISSING → implement ai-followup endpoint + UI |
| G11 | Trust boundary | PASS | Persistence + non-interference tests; runs never mutate scores |
| G12 | Resilience/retries | PARTIAL | Timeout/auth/refusal/truncation coded; no bounded retry, no 429 code → implement + test |
| G13 | AI observability | PARTIAL | Latency/validation/usage/audit recorded; retry tests land with G12 |
| G14 | API contracts | PASS | 24→25 routes tested; error envelope uniform |
| G15 | Graph explorer | PASS | Flat verified; orbital Batch B implemented, user gate pending |
| G16 | Replay/simulation | PASS | Isolation tested; SIMULATED labels + limitations |
| G17 | Decisions/audit | PASS | State machine + 1:1 decision:audit + append-only chain |
| G18 | Persistence/deploy store | PASS | Restart round-trip tested locally (decisions/audit/scores survive re-init); hosted restart still BLOCKED on deploy |
| G19 | Security review | PARTIAL | CORS exact-origin, server secrets, validation done; see findings below |
| G20 | A11y/responsive | PARTIAL | Keyboard/focus/reduced-motion/theme implemented + tested; no axe/lighthouse runner here |
| G21 | Quality gates | PARTIAL | pytest + vitest + tsc + build green; no lint script (no runner to verify one) |
| G22 | Production build | PASS | User-confirmed green; no project-caused failures open |
| G23 | Browser smoke | PARTIAL | User-verified surfaces; full script lands with G27 |
| G24 | Hosted behavior | BLOCKED | No approval to deploy; artifacts ready, live check NOT VERIFIED |
| G25 | Demo setup/reset | PASS | Explicit two-step reset; existing records never wiped by tests |
| G26 | Recovery paths | PASS | Honest error/timeout/invalid states + retry; no fake fallback |
| G27 | Submission evidence | PARTIAL | Matrix exists; demo script + this audit close it |

## G19 static findings (no secrets printed)

- Secrets: MODEL_API_KEY header-only, never logged/returned/persisted;
  secret-safety tests pass; `.env` ignored. No issue.
- CORS: exact origins, no credentials, minimal methods/headers. No issue.
- Input: Pydantic models + explicit ValueError→AppError mapping; decision/
  transition allowlists server-side. No issue.
- Error disclosure: envelope `{code,message,trace_id}` only; AI
  diagnostics bounded (2000-char excerpt, no credentials). No issue.
- Deps: frontend `npm audit` reported 1 moderate + 1 high (user run);
  cannot re-audit here (no npm/network). Action: user runs `npm audit`
  and pastes output before submission; no `--force` fixes.
- AuthN/Z: demo has none beyond CORS + server validation (documented
  threat model: local demo + trusted analyst). No change without approval.

## Implementation actions (this mandate)

1. G12: bounded retry (429/503, max 2, backoff) + MODEL_RATE_LIMITED +
   tests in `tests/test_ai_validation.py`.
2. G10: `POST /api/v1/investigations/{id}/ai-followup` + tests +
   AiPanel follow-up UI + tests (same schema validation).
3. G27/G01/G03/G23: `docs/DEMO_SCRIPT.md` (script + recovery + measured
   numbers + smoke checklist).
4. Re-run backend suite; confirm state intact; final report.
