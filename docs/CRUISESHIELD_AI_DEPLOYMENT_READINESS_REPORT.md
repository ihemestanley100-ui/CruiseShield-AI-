# CRUISESHIELD AI — DEPLOYMENT READINESS REPORT (J3)

**Verdict:** STAGING-READY ON APPROVAL (specs verified, no services
provisioned, no deploy performed).

## Target ($0 hosting)

- Frontend: Vercel Hobby *eligibility gated* (personal/non-commercial
  interpretation for a judged demo = NOT_VERIFIED in the record; needs
  owner ToS check or eligible alternative) — build/runbook otherwise
  ready, openGraph URL needs the chosen domain.
- Backend: Render Free (Docker, HEALTHCHECK, PORT honored, cold-start
  ≤60 s allowed; 512 MB / sleep / ephemeral FS documented —
  sufficiency NOT_VERIFIED until staging).
- Database: JSON-on-disk first (legal on paid Render disk / any
  persistent host FS), Neon Free PG via `STORE_BACKEND=postgres`
  cutover (owner-gated); no migration performed.

## Blocking policy

- Protected login + rate limiting + credentialed CORS enforced in code
  before any public URL (owner requirement — implemented and tested).
- Secrets by name only (`MODEL_API_KEY` etc.); no live values in repo,
  logs, or evidence. AI quota/price NOT_VERIFIED — tripwires in place.

## Deployment/rollback order (spec, not executed)

1. Owner approves backup destination + Neon project + frontend host.
2. Provision DB → rehearse migration → provision backend → wire CORS/
   API base → provision frontend with demo credentials → run staging
   acceptance (workflow + login + rate-limit + persistence proofs).
3. Rollback: unset `STORE_BACKEND` (JSON), previous service revisions;
   no data mutation in staging beyond disposable rehearsal records.
