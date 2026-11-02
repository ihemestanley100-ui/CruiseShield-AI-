# 6. ENVIRONMENT-VARIABLE REGISTER

DATE: 2026-11-01 | NAMES ONLY — no values. († = set in render.yaml; ‡ = Render secret store; § = build-time baked.)

## Backend
- MODEL_API_KEY ‡ — live Meta AI calls; absent → honest NOT_CONFIGURED errors (demo runs without fresh AI).
- META_MODEL_ID † (`muse-spark-1.3`) · META_BASE_URL † (`https://api.meta.ai/v1`).
- DATA_DIR † (`/srv/data`) — persistent disk mount; local default `ROOT/data`.
- FRONTEND_ORIGINS † — comma-separated allowed origins; MUST be the deployed frontend URL (default localhost:3000/127.0.0.1:3000 for local).
- STORE_BACKEND (unset → `json`) — leave unset; `pg` is scratch-only.
- DEMO_WRITE_TOKEN (gap-closure D-002; Render secret prompt) — empty = open demo; set = POSTs require it. Owner-generated (`secrets.token_urlsafe(32)`).
- SESSION_SECRET ‡ — HMAC session signing; empty = demo login disabled (open demo, honest 503 on /auth/login).
- DEMO_USERS ‡ — `user:role:pbkdf2-hash` CSV for demo login (investigator/admin roles).
- AI_DAILY_CALL_LIMIT † (default 100) · AI_TIMEOUT_SECONDS † (default 30) — AI cost controls; enforced pre-call with audited rejections.
- DATABASE_URL (unset until Neon cutover, §E-gated) · PG_CONNECT_TIMEOUT (default 5, fail-safe on garbage per J3-P1) · PORT (Render-provided; local default 8000).

## Backup workflows (CI/manual only — never Render runtime)
- CSBK_RECIPIENT_PUBKEYS · CSBK_SIGNING_SEED · CSBK_SIGNING_VERIFY_KEY · CSBK_RESTORE_PRIVATE_KEY — GitHub environment secrets for the backup-produce/restore-drill/verify workflows (see `.env.example`). Names only; values live in the `backup-production-gate` environment.

## Frontend
- NEXT_PUBLIC_API_BASE_URL †§ — deployed backend URL; BAKED AT BUILD; rebuild required after any change.
- NODE_VERSION † (20.19.6) — build image pin.
- NEXT_PUBLIC_DEMO_WRITE_TOKEN †§ — same value as backend token; PUBLIC once baked; empty = header omitted. Demo-staging only.
- NEXT_DIST_DIR — REMOVED 2026-11-01 (J3-P10): the Phase 2B temporary `distDir` override is deleted from `next.config.ts`; builds use default `.next`. This variable no longer exists.
- PORT (Render-provided) — consumed by `npm start -- --port $PORT`.

## Rotation/ handling
MODEL_API_KEY rotation = Render dashboard value change + backend redeploy (no code change). Never commit values; never print values; `.env` stays local-only.
