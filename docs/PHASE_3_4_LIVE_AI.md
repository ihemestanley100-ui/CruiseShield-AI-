# PHASE 3.4 — LIVE META AI DEMONSTRATION

Date: 2026-11-01. One (1) live provider call executed with explicit user
approval against a disposable backend copy. Evidence:
`%TEMP%\smoke34\live_run.json` (full run artifact, no credentials).

## A. API configuration — PASS (by inspection + health + live success)

- Endpoint: `META_BASE_URL` + `/chat/completions` (chat-completions
  shape), model `muse-spark-1.3`, greedy decoding (temperature 0),
  structured JSON output with plain-JSON fallback, 30 s timeout,
  bounded retries on 429/502/503/504 only (max 3 attempts).
- Key server-side only (`.env`, gitignored): never in frontend code,
  logs, API responses, or persisted runs (run artifact scanned: the
  single `authorization` regex hit is model prose, not a credential).
- Health `model_configured: PASS` before the call.

## B. Live investigation — PASS (genuine provider response)

- Target: inv_84721 (txn_84721, #84721, NGN 480,000, MOBILE_APP,
  2026-10-27T10:00:00Z, 39 evidence records, R-001..R-008).
- Result: `agentrun_0003`, status SUCCEEDED, 18,776 ms, provider
  `request_id` present, usage 6,275 prompt + 4,030 completion tokens.
- Validation: schema VALIDATED, evidence references VALIDATED.
- Conclusion `requires_review`; 8 key findings, 3 alternative
  explanations, 4 missing-information items, 3 next steps (each
  `requires_human_approval: true`, server-enforced).

## C. AI response requirements — PASS

- 46/46 cited evidence IDs resolve to the 39 sent IDs (0 unknown;
  independently re-checked client-side, not just server-side).
- No invented score fields; no enforcement/guilt language (validator
  rejects both; live output clean); observed-vs-interpreted separation
  and uncertainty are structural in the enforced schema.
- Scores byte-identical before/after on the disposable backend
  (35/MODERATE transaction, 84/HIGH network); `save_ai_run` appends to
  `ai_runs` only and cannot touch risk records.
- Prompt-injection resistance: live hostile test NOT run (only 1 call
  approved); covered by passing mocked tests — delimiter quoting,
  injection-shaped output rejection, enforcement-language rejection,
  hostile-follow-up-changes-nothing (`tests/test_ai_validation.py`).

## D. Demonstration sequence — PASS (API) / panel by same code path

- Live request → genuine response → validated run → persisted with
  audit, all observed on the disposable backend.
- Never a mock, fallback, or stored run relabelled: `agentrun_0003`
  carries a fresh provider request id and token usage; stored
  `agentrun_0002` remains the demo fixture.
- AI-panel display of a live run uses the identical `AgentRun`
  rendering path already proven with stored runs (case-page screenshot
  in 3.3) and unit tests; no separate live-panel browser run was
  performed (would have required a second frontend against the
  disposable backend).

## E. Persistent-data protection — PASS

- `agentrun_0003` absent from the persistent backend (404 on :8000);
  `data/state.json` hash + size identical before/after
  (`BA1D4DB4…3790FE`, 101417 B). Disposable backend destroyed after use.
