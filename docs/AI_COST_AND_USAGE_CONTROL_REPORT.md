# AI COST AND USAGE CONTROL REPORT

Controls (all in app/ai_adapter.py + app/config.py):

- AI_DAILY_CALL_LIMIT (default 100): counts persisted run
  attempts per UTC day; restarts cannot reset; cap+1 → 429.
- AI_TIMEOUT_SECONDS (default 30): bounds one call below
  the frontend's 35 s abort; timeouts fail fast, no retry.
- Retry budget: 3 attempts on 429/502/503/504 only.
- Per-run usage capture: prompt/completion/total tokens
  persisted in ai_runs when the provider returns them.
- No background or speculative calls: every call originates
  from an explicit analyst action on one investigation.

Cost position: Meta Model API is metered (secondary source:
$1.25/M in + $4.25/M out). Owner quota/billing NOT_VERIFIED.
$0 HOSTING target does not include AI spend. Demo default:
100 calls/day cap ≈ bounded worst case; exact $ requires
token sizes per call (logged per run for audit).
