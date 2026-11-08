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

## Release cert v3.0 addendum (2026-11-04, commit ff7052b)

- Official docs re-verified (`dev.meta.ai`): base URL `https://api.meta.ai/v1`,
  model `muse-spark-1.3`, token-header auth — all match code defaults. Standard
  pricing $1.25/M in / $4.25/M out; Standard = no training use; Contributor
  variant rejected (grants training permission). No free tier found.
- Cost control implemented (owner-approved, code-only): `AI_MAX_OUTPUT_TOKENS`
  default 4096, fail-safe fallback, enforced as `max_tokens` on analysis AND
  follow-up bodies; 4/4 new tests green; retries/timeout/daily-cap/parsing/
  truncation handling preserved. One live call estimated ~$0.02 (paid).
- Live-call status: NOT EXECUTED. Blocked on: owner-funded key + explicit
  1-call spend approval + R3 backend arming. Pillar 05 verdict: BLOCKED
  under the free-only policy. No quota spent, no key created.

## Release closure FRC-001 addendum (2026-11-04)

Free-allowance check (fresh): `MODEL_API_KEY` UNSET in this environment; no
owner-provided key or allowance exists anywhere in my access; live backend
reports `model_configured: NOT_CONFIGURED`. There is NO authorized free (or
paid) allowance to call against — a live request is impossible without
owner-supplied credentials, independent of the $0.02 estimate. The $0.02 paid
call is NOT executed (financial lock). Contributor mode stays rejected
(training-use terms). No provider substitution, no fabricated response.

Offline verification (fresh): `test_ai_validation` + `test_ai_cost` →
**49 passed** — request/response schemas, `max_tokens` enforcement,
timeouts, bounded retries, truncation/refusal handling, daily cap, and
MockTransport adapter behavior (all clearly simulated, none presented as live).
Historical artifacts re-confirmed read-only: 2 SUCCEEDED `ai_runs` in seed
state (prior live evidence, NOT fresh verification).

Source review: no further safe integration improvement identified — adapter,
validation, grounding, audit provenance, and human-review boundaries are
complete and suite-covered. No code touched in this pillar.

Live-call procedure (prepared, awaiting owner): fund key → confirm Standard
`muse-spark-1.3` → approve 1 call (≤~$0.025 worst case w/ 4096 cap) → execute
via armed backend → record trace/model/usage/validation/audit. Pillar 05
stays **BLOCKED**.

## Closure round addendum (2026-11-04, CS-FRC-ZG-001)

No change: no free entitlement exists, no key/approval/allowance arrived, no
keyed call attempted (any provider API access needs owner approval per §8.4).
Model/endpoint currency stands as verified. R05 acceptance (one authorized
live inference) unmet through no executable path. Pillar 05 stays **BLOCKED**.

## Timeout diagnosis addendum (2026-11-04, zero-spend, zero key use)

Keyless `POST /v1/chat/completions` → instant 401 `invalid_api_key` (0.66 s):
the POST path is fast and healthy. Official error docs confirm invalid keys
fail fast (401) and billing issues fail fast structured (402
`billing_not_configured`) — while our adapter maps 401/403 to the distinct
code MODEL_AUTH_FAILED. The 3 keyed attempts instead raised MODEL_TIMEOUT
(30 s silence). Conclusion: the key passed the fast auth gate; the stall is
downstream (account entitlement/provisioning or provider-side hang) —
diagnosable only via the owner dashboard at `dev.meta.ai/platform` (usage,
keys, billing status) or one approved instrumented call. No inference, no
usage, no spend resulted from any probe.

## Owner-gated round addendum (2026-11-04)

No allowance, approval, or key arrived; no keyed attempt made. Timeout
diagnosis stands (downstream stall; dashboard or approved call required).
Pillar 05 stays **BLOCKED**.
