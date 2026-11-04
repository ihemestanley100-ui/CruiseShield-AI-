# DEPLOYMENT ROLLBACK RUNBOOK (Part 5 — J8 stack)

Canonical base: docs/RENDER_8_ROLLBACK_RECOVERY.md (service
redeploy order, data-restore discipline, drill targets).
This file adapts it to the SELECTED J8 stack — it does not
replace the base procedure's incident discipline.

## J8 deltas (supersede the disk-centric lines of RENDER_8)

1. No persistent disk exists on Render Free: the RENDER_8
   §"Data rollback" disk procedure DOES NOT APPLY. The
   database of record is Neon PostgreSQL.
2. Service rollback: Render dashboard → Deploys → redeploy
   prior SHA (backend); Cloudflare Pages → Deployments →
   rollback (frontend). Order: backend first, then frontend
   only if its baked API URL still matches.
3. Data rollback (Neon): use Neon's instant-restore / point-
   in-time recovery to a pre-deploy snapshot (Free: 6-hour
   history window per secondary sources — verify in console),
   then run the J5 reconcile (record counts, IDs, 35/84
   scores, audit continuity) before reopening writes.
4. Quota-exhaustion rollback: if Neon compute suspends or
   Render hours exhaust mid-demo, the recovery is
   wait-for-reset or owner-approved upgrade — there is no
   code rollback for a quota event. See fallback plan.
5. Migration rollback: migrations/loader.py is single-
   transaction (interrupted = rolled back); post-cutover
   reversal = Neon restore per (3) + STORE_BACKEND=json
   fallback ONLY with owner approval (file store kept
   recoverable until PG acceptance per J5).

## Preconditions (unchanged from base)

No rollback claim is valid without an owner-approved backup
(G5 open). First staging deploy MUST include a rollback
drill to replace the <15/<30 min targets with measurements.
