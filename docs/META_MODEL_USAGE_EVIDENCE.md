# META MODEL USAGE EVIDENCE — CruiseShield AI™

Date: 2026-11-03 · No live calls made in this audit (quota untouched).

## Integration (code — VERIFIED)

- Model: `muse-spark-1.3` (`META_MODEL_ID`; endpoint
  `META_BASE_URL` + `/chat/completions`).
- Source: `app/ai_adapter.py` (created in-window, f75c3fb
  10-28): temperature 0, structured-JSON output with plain-JSON
  fallback, 30 s timeout, 3-attempt retry (429/502/503/504),
  daily cap 100 with audited rejections, FAILED-run persistence.
- Credentials: `MODEL_API_KEY` server-side only (`.env`,
  gitignored); never logged, returned, or persisted — verified
  by grep + secret-scan gate + run-artifact scan.
- Validation (fail-closed): required-field schema check, banned
  numeric-score fields, enforcement-language rejection,
  evidence-ID reference check against sent IDs, mandatory
  `requires_human_approval: true` on next steps
  (`test_ai_validation.py`, 33+ tests incl. red-team cases).

## Live evidence (VERIFIED from artifact, firsthand 11-03)

- `%TEMP%\smoke34\live_run.json` (17464 B, approved 11-01 call):
  `agentrun_0003`, status SUCCEEDED, provider `meta`, model
  `muse-spark-1.3`, latency 18776 ms, fresh provider
  `request_id` (`chatcmpl-01a…`), token usage recorded,
  schema VALIDATED + evidence-refs VALIDATED, conclusion
  `requires_review`, 8 findings / 46 cited IDs resolving to 39
  sent (0 unknown — independently re-checked).
- Persistent store holds 2 SUCCEEDED runs (10-30,
  `agentrun_0001/0002`).

## Current status (honest boundary)

- NOT_VERIFIED: present-day key validity and model
  accessibility — requires the one approved G-AI-SPEND call.
  No successful-use claim is made beyond the artifacts above.
- Participant API credits: secondary sources report $150 Meta
  Model API credits per participant — REPORTED, not verified
  against our account. Supports plausibility only.

## Deterministic vs AI-generated (workflow truth)

- DETERMINISTIC (code, always): risk scores/bands, rule
  triggers, graph assembly, evidence packaging, case
  transitions, replay baselines, audit entries.
- AI-GENERATED (model, advisory): investigation summary, key
  findings prose, alternative explanations, missing-info notes,
  suggested next steps, conclusion label — every item validated
  against supplied evidence IDs; the model can NEVER change a
  score, transition a case, or approve an action (server-enforced).
