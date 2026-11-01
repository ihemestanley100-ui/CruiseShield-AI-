# 6. ENVIRONMENT-VARIABLE REGISTER

DATE: 2026-11-01 | NAMES ONLY — no values. († = set in render.yaml; ‡ = Render secret store; § = build-time baked.)

## Backend
- MODEL_API_KEY ‡ — live Meta AI calls; absent → honest NOT_CONFIGURED errors (demo runs without fresh AI).
- META_MODEL_ID † (`muse-spark-1.3`) · META_BASE_URL † (`https://api.meta.ai/v1`).
- DATA_DIR † (`/srv/data`) — persistent disk mount; local default `ROOT/data`.
- FRONTEND_ORIGINS † — comma-separated allowed origins; MUST be the deployed frontend URL (default localhost:3000/127.0.0.1:3000 for local).
- STORE_BACKEND (unset → `json`) — leave unset; `pg` is scratch-only.
- DEMO_WRITE_TOKEN (gap-closure D-002; Render secret prompt) — empty = open demo; set = POSTs require it. Owner-generated (`secrets.token_urlsafe(32)`).
- DATABASE_URL (unset, unused in demo) · PG_CONNECT_TIMEOUT (default 5) · PORT (Render-provided; local default 8000).

## Frontend
- NEXT_PUBLIC_API_BASE_URL †§ — deployed backend URL; BAKED AT BUILD; rebuild required after any change.
- NODE_VERSION † (20.19.6) — build image pin.
- NEXT_PUBLIC_DEMO_WRITE_TOKEN †§ — same value as backend token; PUBLIC once baked; empty = header omitted. Demo-staging only.
- NEXT_DIST_DIR (unset → `.next`) — verification override only; leave unset.
- PORT (Render-provided) — consumed by `npm start -- --port $PORT`.

## Rotation/ handling
MODEL_API_KEY rotation = Render dashboard value change + backend redeploy (no code change). Never commit values; never print values; `.env` stays local-only.
