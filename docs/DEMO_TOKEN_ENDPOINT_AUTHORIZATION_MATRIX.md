# DEMO TOKEN — ENDPOINT AUTHORIZATION MATRIX

Date: 2026-11-03 · Auth-armed mode. "Token" = valid
`Authorization: Bearer` demo token, no session.

## Mutating routes (all POST)

| Route | Token | Anon (no creds) | Session non-admin | Session admin | Effect |
|---|---|---|---|---|---|
| `/api/v1/demo/reset` | 403 ADMIN (R1) | 401 | 403 (admin-only) | ALLOW | Wipe interactive state → reseed |
| `/api/v1/demo/scenarios/{id}/start` | 403 ADMIN (R1) | 401 | 403 | ALLOW | Reset + return entry URL |
| `/api/v1/demo/judge-start` | 403 ADMIN (R1) | 401 | 403 | ALLOW | Reset to primary + entry URL |
| `/api/v1/investigations/{id}/ai-analysis` | 403 AI_LOGIN (R3) | 401 | ALLOW (ai_run perm*) | ALLOW | Spends 1 AI call (cap 100/d) |
| `/api/v1/investigations/{id}/ai-followup` | 403 AI_LOGIN (R3) | 401 | ALLOW* | ALLOW | Spends 1 AI call |
| `/api/v1/simulations` | ALLOW | 401 | ALLOW (write) | ALLOW | Persist simulation |
| `/api/v1/cases/{id}/decisions` | ALLOW as demo-token (R2) | 401 | ALLOW (write) | ALLOW | Transition case + audit (actor bound) |
| `/api/v1/events` | ALLOW | 401 | ALLOW (write) | ALLOW | Validated ingest, deduped |
| `/api/v1/investigations/{id}/evidence-package` | ALLOW (gated, R4) | 401 | ALLOW (write) | ALLOW | READ-ONLY alias — no mutation |
| `/api/v1/auth/logout*` | n/a (session ops) | — | own session | own session | No token role |

*Permission depends on role map (`auth_mod.can`); token
skips role checks entirely.

## Read routes (all GET under /api/v1 + legacy pages)

Token: ALLOW (passes login gate; no handler checks role).
Reads are synthetic-demo-data only. No secrets, hashes,
or env readable through any endpoint (verified: no
handler returns config; error bodies are codes only).

## Post-R1–R4 residual (re-audit 11-03)

Token now exceeds NO session anywhere: demo/* admin-only,
AI login-only, decisions attributed. Residual token power:
synthetic reads + validated/rate-limited/attributed writes
(simulations, events, decisions-as-demo-token). Anomaly 3
(unset ⇒ open) stands BY DOCUMENTED DESIGN — deploy
checklist must-set item (R5).

## R6 deployed posture (owner-approved 11-03)

Public frontend ships with NO token value ⇒ the "Token"
column is unreachable from the official UI; all browser
writes arrive as session creds (or 401). The token column
remains valid only for direct-API callers holding a
companion backend value (staging/ops use).

## Anomalies (the original FAIL, now closed except #3)

1. Token > non-admin session on all three demo routes
   (admin gate bypass, `main.py:116-123` scope).
2. Token == write-role session on AI/decisions/sim/events
   with ZERO attribution (no user, forgeable actor).
3. Backend-unset token ⇒ every gated POST world-open
   (fail-open by documented design — deploy MUST set it).
