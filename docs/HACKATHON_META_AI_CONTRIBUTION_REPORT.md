# HACKATHON META AI CONTRIBUTION REPORT

READ-ONLY audit evidence. Answers: where Meta AI / Muse Spark is genuinely
used in the working product, with file-level references.

## 1. The integration (code, verified by inspection)

- Single integration point: `app/ai_adapter.py` → server-side
  `httpx.AsyncClient(base_url=META_BASE_URL).post("/chat/completions")`
  with `Authorization: Bearer MODEL_API_KEY` (`ai_adapter.py:407-423`).
- Model/endpoint from env with defaults `muse-spark-1.3` and
  `https://api.meta.ai/v1` (`app/config.py:34-36`).
- Request: `{model, temperature: 0, messages, response_format json_object}`
  with a 400-fallback that retries once without `response_format`
  (`ai_adapter.py:216-222, 285-287, 439-445`).
- Served by `POST /api/v1/investigations/{id}/ai-analysis` and
  `.../ai-followup` (`app/main.py`, via `_run_ai`, which persists every run
  and audit event win or lose).
- Secrets: key is server-env-only, never logged/returned/persisted
  (module docstring + `tests/test_secret_safety.py`).

## 2. Live-execution evidence (bounds stated honestly)

| Evidence | Date | Content | Standing |
|---|---|---|---|
| `data/state.json` ai_runs | 10-30 05:03–05:08Z | `agentrun_0001` (prompt v2, 23.6 s, 6275/4632 tok) + `agentrun_0002` (follow-up, 25.3 s, 6617/5331 tok); provider request IDs, `finish_reason stop`, VALIDATED/VALIDATED | PERSISTED run records with live-shaped provenance (latency, usage, provider IDs) |
| `docs/TEST_EVIDENCE.md` G03 | 10-29 | 4 SUCCEEDED runs, 12.9–16.7 s latencies | PROJECT RECORD (attributed; raw responses not retained) |
| `%TEMP%\smoke34\live_run.json` | 11-01 | `agentrun_0003` (prompt v2, 18.8 s, 6275/4030 tok, provider request ID, VALIDATED/VALIDATED, 46/46 citations grounded, conclusion `requires_review`); executed against a disposable backend copy with user approval; full response retained | OBSERVED live call, full artifact (deliberately not persisted; state hash unchanged) |
| Current env | 11-01 | `MODEL_API_KEY` present (name-only check + `model_configured: PASS` + live success; value never read) | Live calls possible; key server-side only |
| No-key path | tests | `MODEL_NOT_CONFIGURED` fail-closed, covered by tests | VERIFIED behavior, not a live call |

What this proves: the product executed real model calls during the
hackathon window (persisted receipts 10-30, fully-observed call 11-01).
What it does NOT prove: video of a live call (not recorded yet).

## 3. Separation: Meta-powered vs deterministic vs human

| Area | Files | Meta AI? | Role |
|---|---|---|---|
| Analysis + follow-up calls | `app/ai_adapter.py` (`analyze`), main routes | YES — the call | Interprets a supplied evidence package; output schema- and ID-validated, advisory only |
| Model-output validators | `ai_adapter.validate_model_output`, `app/intel_ai.validate_di_response` | GUARDS the model | Reject invented scores, enforcement language, unknown IDs, steps lacking human approval |
| DI context builder | `app/intel_ai.build_di_context` | FEEDS the model | Minimized grounded context; itself pure/deterministic, no network |
| Risk scores (35 MODERATE / 84 HIGH) | `app/rules.py` (`risk-score-v1`) | NO | Deterministic versioned rules; model is forbidden by prompt + validator from scoring |
| Graph, provenance, features | `app/graph.py`, DI `*_intel.py` | NO | Deterministic computation over seeded data |
| Evidence package assembly | `app/evidence.py`, `app/seed.py` | NO | Deterministic retrieval/preparation the model consumes |
| Replay / simulation | `app/replay.py`, `app/simulate.py` | NO | Deterministic cursors and bounded what-if (84→72) |
| Human decision + cases + audit | `app/cases.py`, `app/store.py` | NO | Human gate; case machine; append-only audit; NOTHING consequential is model-authorized |
| Frontend (all 138 files) | `frontend/` | NO direct use | Calls backend `/ai-analysis`, `/ai-followup` only; key never in browser (asserted in `lib/api.ts`, `frontend/README.md`; 11-01 tree scan: zero secret hits); `muse-spark-1.3` appears only in test fixtures + API-displayed data |
| Seed data | `app/seed.py`, `data/state.json` | NO | Deterministic synthetic fixtures |

## 4. Contribution summary (for the submission narrative)

Genuinely Meta-powered: evidence-grounded investigation analysis and
analyst follow-ups with fail-closed validation, provenance persistence,
and audit — executed live twice (persisted 10-30), four doc-reported
runs (10-29), and one fully-observed run 11-01 (agentrun_0003).
Genuinely NOT Meta-powered (say so explicitly): risk engine, graph,
evidence retrieval, replay/simulation, cases, audit, seed data, and the
entire frontend except through backend AI endpoints. The architecture's
honest claim is "Meta interprets, deterministic code decides facts,
humans decide actions" — and the code enforces exactly that.
