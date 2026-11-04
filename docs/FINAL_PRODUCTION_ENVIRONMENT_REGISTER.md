# FINAL PRODUCTION ENVIRONMENT REGISTER — CruiseShield AI™

Date: 2026-11-03 · NAMES ONLY — no values in this file, ever.
Secret values live in hosting-service prompts (`sync: false` style);
CI-only names live in GitHub environment secrets.

## Backend (Render web service / Docker)

| Name | Required | Notes (behavior, not values) |
|---|---|---|
| SESSION_SECRET | YES (public) | 32+ chars (R09-F2); empty = open demo (FORBIDDEN for public). Render prompt |
| DEMO_USERS | YES (public) | `name:role:pbkdf2$…` CSV; provision via `python -m app.auth provision`. Render prompt |
| DEMO_WRITE_TOKEN | YES (R5, public) | Server-side ONLY; 32+ random via `secrets.token_urlsafe(32)`; empty = open POSTs (FORBIDDEN for public — G-DEPLOY verify: anon write must 401). Render prompt |
| MODEL_API_KEY | For live AI | Server-side only; empty = honest MODEL_NOT_CONFIGURED. Render prompt |
| META_MODEL_ID | With key | Default `muse-spark-1.3` |
| META_BASE_URL | With key | Default `https://api.meta.ai/v1` |
| FRONTEND_ORIGINS | YES | Comma allowlist; MUST equal the deployed frontend origin (deploy order step 3) |
| AI_DAILY_CALL_LIMIT | No | Default 100; 0 = unlimited (not recommended) |
| AI_TIMEOUT_SECONDS | No | Default 30 (keep < 35) |
| DATA_DIR | No | Default repo `data/`; Dockerfile sets `/srv/data` (ephemeral on Free) |
| STORE_BACKEND | No | Default `json`; `pg` = scratch verification only |
| DATABASE_URL | PG path only | NEVER logged/returned; scratch/Neon only until cutover verified |
| PG_CONNECT_TIMEOUT | No | Default 5, fail-safe |
| TRUSTED_PROXIES | No | Display labeling in `app/ip_intel.py` only (NOT the rate-limit trust list) |
| PORT | Platform | Render-provided; local default 8000 |

## Frontend (Render Node service or Vercel Hobby)

| Name | Required | Notes |
|---|---|---|
| NEXT_PUBLIC_API_BASE_URL | YES | MUST equal backend public URL; build-time baked (rebuild after set) |
| NEXT_PUBLIC_DEMO_WRITE_TOKEN | EMPTY (R6, public) | MUST stay empty/unset for public deploy (owner-approved 11-03); writes use login sessions. Any value bakes PUBLIC into browser JS |
| NEXT_PUBLIC_SITE_URL | No | Deployed origin for absolute metadata; empty = relative URLs |
| NODE_VERSION | Render | 20.19.6 per blueprint (engines >= 18.18.0) |
| PORT | Platform | Provided by host |

## CI / backup only (never runtime)

`BACKUP_DATABASE_URL`, `B2_*`, `C3_*`, `CSBK_*`, `BACKUP_ENV` —
GitHub `backup-production-gate` environment; workflows disabled by
default (manual dispatch + required reviewers).

## R5/R6 addendum (owner-approved 2026-11-03)

- R5: backend token mandatory for public deploy (see row);
  rotation = regenerate + backend redeploy only (R6-empty
  frontend needs no rebuild); revocation = replace value
  (unset re-opens gates — never unset in public).
- R6: public frontend ships WITHOUT the var; verified
  clean build + 366/366 with it unset (`DEMO_TOKEN_OWNER_CONFIRMATION_REGISTER.md`).

## Provisioning rule

Generate secrets with `secrets.token_urlsafe(32)` (32+ chars for
SESSION_SECRET), provision users with `python -m app.auth
provision`, paste into hosting prompts directly. No secret value
in chat, files, docs, logs, or git — enforced by the secret-scan
gate and the pre-push history check in the gate register.
