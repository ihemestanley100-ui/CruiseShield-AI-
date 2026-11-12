# CS FINAL — OPERATIONS & ROLLBACK GUIDE (CS-FINAL-EXECUTION-010)

Date: 2026-11-03.

## Normal ops (demo)

- Warm both services before judging (Free sleep ~60 s
  wake): open backend `/api/v1/health`, then frontend `/`.
- Sleep wipes sessions/revocations/audits (F-EPH-1):
  re-login after idle; re-run Judge Start if state looks
  stale. Seed data always recovers via reseed.
- Watch dashboard usage (750 hrs / 5 GB / pipeline mins).

## Rollback

- Backend bad deploy: dashboard → Manual Deploy → select
  `58a3d50` (last-known-good, pre-R1–R4) → deploy. Note:
  rollback re-opens the demo-token gaps until `ff7052b`
  is restored + armed. Prefer forward-fix.
- Backend bad config (env): fix values in dashboard (owner
  only) → auto-redeploy → re-verify health + auth/mode.
- Frontend bad deploy: Manual Deploy → previous commit →
  rebuild. R6: keep token var empty on every redeploy.
- Code revert (needs approvals): `git revert` → G-COMMIT →
  G-PUSH → redeploy. Never force-push, never rewrite.

## Incidents

- Suspected token abuse: rotate backend `DEMO_WRITE_TOKEN`
  (regenerate → save → redeploy). R6-empty frontend needs
  no change. Audit trail shows `demo-token` actor rows.
- Quota burn: AI endpoints are login-gated; check
  `ai_runs` counts; daily cap bounds damage (100/d).
- Full state corruption: admin Judge Start reseeds to
  synthetic baseline in one action.

## Contacts/escalation

Owner holds dashboard + secrets. Muse verifies from
returned evidence only. No standing prod access.
