# DEMO ENVIRONMENT CONFIGURATION

Target (not provisioned): Pages + Render + Neon, synthetic
data, protected login.

## Backend (Render Free)

- Root: repo root (Dockerfile); start: uvicorn on $PORT.
- Health: GET /health (also readiness semantics).
- Required env (names only): SESSION_SECRET, DEMO_USERS
  (provisioned hashes — never defaults), FRONTEND_ORIGINS,
  DATABASE_URL (Neon pooler URL), MODEL_API_KEY,
  AI_DAILY_CALL_LIMIT, AI_TIMEOUT_SECONDS, STORE_BACKEND=pg.
- Forbidden: DEMO_WRITE_TOKEN reliance (low-assurance;
  J4 login is the control), NEXT_PUBLIC_* secrets (none exist).

## Frontend (Cloudflare Pages)

- Build: npm run build; output: Next.js (needs next-on-pages
  adapter — NOT yet configured, owner-gated work item).
- Required env: NEXT_PUBLIC_API_BASE_URL (Render URL),
  NEXT_PUBLIC_SITE_URL (Pages URL).
- No secrets in bundle (verified: no NEXT_PUBLIC key).

## Database (Neon Free)

- Schema via migrations/loader.py (atomic, hash-gated).
- Pool via Neon pooler endpoint (client is URL-agnostic).
- Cutover + rollback: J5 runbook; live cutover owner-gated.

## Demo operation

- Cold start: expect ≤60 s first hit (Render) + ~1 s (Neon).
- Credentials: provisioned per-event, rotated after; audit
  on; synthetic banner on every money screen.
