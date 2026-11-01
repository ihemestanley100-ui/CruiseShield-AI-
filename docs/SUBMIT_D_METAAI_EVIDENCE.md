# D. META AI INTEGRATION EVIDENCE REPORT

DATE: 2026-11-01 | VERDICT: implemented + live-demonstrated (no planned-only claims).

## Integration facts
- Model/API: muse-spark-1.3 via Meta Model API (`META_MODEL_ID`, `META_BASE_URL` in `app/config.py`; eligible Muse Spark family per S1).
- Code: `app/main.py:513` POST `/api/v1/investigations/{id}/ai-analysis`, `:520` POST `/ai-followup`, `:539` GET `/ai-runs/{run_id}` → `app/ai_adapter.py` (server-side only).
- Call path: UI panel → backend → adapter builds prompt v2 (evidence packages as delimiter-quoted untrusted data, `<<<ANALYST_QUESTION` `app/ai_adapter.py:238`) → `Authorization: Bearer` server-side (`:422`) → response parsed → schema + evidence-ID validators → persisted `ai_runs` → UI.
- Secrets: `MODEL_API_KEY` read server-side (`:42,:367` honest "not configured" error); never in frontend (asserted + tree-scanned); never logged/printed.
- Sampling: `REQUEST_TEMPERATURE = 0` (`:213`); bounded retries + backoff; timeouts; honest error states without key/network (never faked).

## Grounding / safeguards (tested, `tests/test_ai_validation.py` green)
- Findings must cite supplied evidence IDs only; invented IDs/scores/enforcement language rejected by validators + enforcement filter.
- Evidence treated as untrusted data (delimiter quoting); system policy not overridable from content.
- Deterministic risk engine REMAINS AUTHORITATIVE: no score fields in AI I/O; scores byte-identical across all runs; `requires_human_approval` enforced; humans decide, AI advises. No guilt declarations, freezes, or autonomous actions — by construction and policy.

## Live demonstration evidence (7 SUCCEEDED runs)
- 10-29: 4 runs, 12.9–16.7 s (project record). 10-30: `agentrun_0001/0002` persisted (23.6/25.3 s, VALIDATED/VALIDATED, token usage + provider IDs).
- 11-01: `agentrun_0003` fully observed on disposable backend (18,776 ms, 10,305 tokens, 46/46 citations grounded, artifact `%TEMP%\smoke34\live_run.json` — volatile, include in backup).
- Reproducible demo: start backend with `MODEL_API_KEY` → investigation page → Run AI analysis → validated report renders; OR (no key/network) present the retained `agentrun_0003` artifact explicitly labelled "recorded live run 2026-11-01". Both paths in the demo script (H).

## Limits (honest)
Live hostile red-team NOT_RUN (mocked defenses pass; D-005). Each NEW live call needs key + network + owner approval at demo time.
