# META AI INTEGRATION AUDIT (Category B — 25%)

Audited 2026-11-02 from app/ai_adapter.py, app/intel_ai.py,
app/config.py. Canonical detail: docs/SUBMIT_D_METAAI_EVIDENCE.md.

## B1/B2/B3 — Product, model, endpoint

- Product: Meta Model API (developer API for Muse models).
- Endpoint (default): https://api.meta.ai/v1 + /chat/completions
  (OpenAI-compatible Chat Completions surface). Matches
  multiple 2026 sources incl. ai.developer.meta.com docs.
- Model (default): muse-spark-1.3 — the version Meta
  currently recommends per the same sources.
- Both are env-overridable (META_BASE_URL, META_MODEL_ID);
  no other provider is wired. Single outbound client.
- Pricing (one 2026 source): $1.25/M input + $4.25/M output
  tokens — API use is METERED, not free. Owner's quota/
  billing: NOT_VERIFIED (no account access).

## B4 — Call flow (all server-side)

POST /api/v1/investigations/{id}/analyze (auth + CSRF + rate
limit) → app/main.py builds EvidencePackage → analyze() /
follow-up path → httpx POST {base}/chat/completions with
Bearer MODEL_API_KEY → interpret_provider_body() →
validate_model_output() → persisted ai_runs record →
frontend AiPanel renders. Key never leaves the server (B5).

## B6–B8 — Grounding and validation

SYSTEM_INSTRUCTION + RESPONSE_SCHEMA_SPEC: use ONLY supplied
facts; cite evidence IDs; raw JSON only. Validation rejects:
missing critical fields; invented score fields
(BANNED_SCORE_FIELDS); unknown evidence IDs; enforcement
phrases; bad conclusion enum; next steps lacking
requires_human_approval=true. Follow-up questions are
delimited as UNTRUSTED (<<<ANALYST_QUESTION …) with
sentinel-neutralizing, hostile-injection tested.

## B9–B14 — Reliability and cost

30 s timeout (fail fast, no blind retries); retries only on
429/502/503/504 (3 attempts, 1 s/2 s); response_format
compatibility fallback (single attempt); daily cap
AI_DAILY_CALL_LIMIT=100 counting PERSISTED attempts (restart-
proof); usage tokens recorded per run; logs/diagnostics carry
request_id + excerpts, never the key. Model + prompt version
(cs-prompt-v2) stored per run for attribution (B14).

## B15–B19 — Authority boundaries

AI output CANNOT set risk scores (banned fields + engine
never reads AI results), invent evidence IDs (rejected),
authorize decisions (approval flag enforced; human form is
the only decision path), or pose as verified evidence (AI
panel labelled; VALIDATED/PARTIAL badges shown). AI-down mode
returns explicit 503 codes with deterministic fallback and
last-stored-assessment visibility rules (never stale-as-fresh).

## B20 — Live execution

BLOCKED: quota-spend approval outstanding (this directive
grants no spend authority). Key present (1, value unread).
Prior live evidence stands: 7 historical runs (SUBMIT_D) + 2
incidental live 200s disclosed in J7. Suite is hermetic now.

## Required AI functions (9): all implemented

Summary, rule explanation (findings carry rule refs),
graph interpretation (edges in package), missing/
contradictory evidence, next steps, structured findings +
refs, uncertainty, human-review recommendation, audit
attribution (ai_runs persisted + audit events). PASS.
