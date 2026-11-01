# Test Evidence — 2026-10-28

Command: `.venv/Scripts/python -m pytest tests/ -q`
Result: **48 passed, 8 skipped, 0 failed, 0 warnings** (under 2s).

Update 2026-10-29: **54 passed, 11 skipped, 0 failed** — adds bounded AI
retries, follow-up endpoint + validation, ambiguous scenario, restart
round-trip, 200× determinism benchmark, simulation isolation. The 11
skips are environmental (8 socket-gated, 3 loop-gated), each reasoned.

## G03 synthetic benchmark (measured, local, 2026-10-29)

- 200 rule evaluations over txn_84721: 21.8 ms total, 0.109 ms each;
  all 200 outputs byte-identical (test-enforced, not just observed).
- Live AI latencies: 15065 / 16029 / 12941 / 16733 ms (4 SUCCEEDED runs).
- Suite wall time: ~1.5 s backend; frontend per user runs.
- Synthetic measurements only — no customer savings claimed.

Prompt v2 note (2026-10-28): the live `MODEL_OUTPUT_INVALID: missing critical
fields` failure was traced to the v1 prompt never naming the required schema
fields. Fixed with an explicit in-prompt schema, `response_format json_object`
with fallback, refusal/truncation codes, and bounded failure diagnostics.
Live provider verification still pending (see B-001).

## Coverage by file

| File | Tests | Result |
|---|---|---|
| test_seed_reset.py (T-001) | reset determinism, pinned 22/30 counts, MODERATE/HIGH bands, FP LOW/LOW | pass |
| test_events.py (T-002/T-003) | idempotent duplicate, UNKNOWN channel + warning, alias, schema rejection | pass |
| test_graph_rules_risk.py (T-004..T-008) | provenance, rule boundaries, documented formula, deterministic neighborhood | pass |
| test_evidence.py (T-009) | 39 items, all mapped to real records, sorted, hashed | pass |
| test_flow_direct.py (T-007, T-015..T-019) | full judge flow via handlers, route contract, page renders, no-key AI block | pass |
| test_cases_audit.py | transitions, labels, terminal FP, sequential audit IDs | pass |
| test_ai_validation.py (T-011/T-014) | schema/refs validation, malformed rejection, honest no-key block | pass (1 loop-gated skip) |
| test_secret_safety.py (T-023) | .env absent+ignored, example names-only, no secrets in state | pass |
| test_cors.py | exact origins, no wildcard, allow/reject headers, preflight allow+reject | 7 pass, 1 socket-gated skip |
| test_api_flow.py (transport) | same flow over TestClient | skipped here (no sockets) |

The 4 skips are environmental (WinError 10013: socket creation forbidden in
this sandbox), each with an explicit reason; the same assertions run
socket-free in `test_flow_direct.py`.

## Pinned deterministic values (asserted)

- Seed counts: 22 nodes / 30 edges / 12 accounts / 4 devices / 3 phones /
  2 merchants / 1 beneficiary / 11 txns / 11 events.
- txn_84721: transaction-only 35 MODERATE; network 84 HIGH; all 8 rules fire.
- Simulation ignoring all device-sharing edges: 84 → 72, baseline untouched.
- Evidence package: 39 items, sha256-hashed, sorted by evidence ID.

## Meta Model API verification (docs, not a live call)

Verified 2026-10-28 via public sources (sandbox has no network for direct
doc fetch): base URL `https://api.meta.ai/v1`, model `muse-spark-1.3`,
`MODEL_API_KEY` credential, OpenAI-compatible `POST /chat/completions` with
`{model, messages}` and Bearer auth. The adapter implements exactly this
contract. A live call was NOT made (no key, no network) and is not claimed.

## Not run

- `uvicorn` socket bind (forbidden here); app import + route table verified.
- Real browser session; screenshots; demo video.
- Docker image build (daemon access not attempted).

## Frontend production build (user-verified, 2026-10-30)

The user resolved the `.next/trace` lock (held by their `npm run dev`
process group, verified 2026-10-30) and ran the production build locally
with a full PASS. Earlier agent-side build attempts were environmentally
blocked by that same lock (EPERM, then a hang on `.next\trace`); no code
defect was ever indicated — `tsc --noEmit` exit 0 with 151/151 frontend
tests green (39 files) at the time.

User-reported result (attributed, not agent-observed):
- Next.js 15.5.28, compiled successfully in 12.7 s.
- Linting and type checking passed.
- Static pages generated 4/4; all six application routes generated
  (consistent with the 5 app routes plus the framework not-found route).
- Build traces collected; page optimization finalized.

Phase 2 verification is complete on all gates. Phase 3 remains blocked
pending explicit user approval.
