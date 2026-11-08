# B2/B3 — OWNER ACTION CHECKLIST (CS-B2-B3-FINAL-003)

Date: 2026-11-03 · All actions below are OWNER dashboard steps.
Muse has no dashboard access and will verify from returned evidence.

## A. Service identity

- Service: `cruiseshield-ai` (EXISTING — do not create another)
- URL: `https://cruiseshield-ai.onrender.com`

## B. Branch

- `production-launch`

## C. Approved commit (exact, full SHA)

- `ff7052bdf0ac48a68f69c3937d9b8708ca265354`
- Parent must be `58a3d50d126edf05c8900c9edc00724d2220d45e`

## D. Manual deployment steps

1. Open dashboard → existing `cruiseshield-ai` service.
2. Open Manual Deploy → select SPECIFIC commit (not Latest).
3. Verify the full SHA character-by-character against §C.
4. Trigger deployment; wait for LIVE/success.
5. Record: deployed SHA, status, timestamp (screenshot OK).

## E. Environment presence checklist (names only, never values)

- [ ] `SESSION_SECRET` — PRESENT / MISSING?
- [ ] `DEMO_USERS` — PRESENT / MISSING?
- [ ] `DEMO_WRITE_TOKEN` — PRESENT / MISSING? (R5: must be
      a fresh 32+ random value; set it now if missing, per
      the already-approved R5/G-DEPLOY prerequisite)

## F. Billing/account checklist (read-only)

- [ ] Workspace plan (Hobby/Pro/…?)
- [ ] Backend service plan + monthly price shown
- [ ] Payment method present? YES / NO (no details)
- [ ] Usage vs allowances (instance-hrs, bandwidth, builds)
- [ ] Spend limit + overage settings
- [ ] Existing frontend service? (expect NONE — confirm)
- [ ] Paid resources present? disks / databases / add-ons /
      subscriptions (list names only, expect NONE)

## G. Evidence to return to Muse

Paste/type (never secret values or card details):
deployed SHA · status · time · env-name presence (3×) ·
workspace plan · service plan + price · card YES/NO ·
usage/allowances · spend limits.

## H. Stop conditions (stop + report, do not improvise)

- Service/branch/SHA mismatch · deploy failure · health
  non-200 after deploy · any required secret missing and
  you do not approve setting it · any purchase/plan/billing
  change demanded · any unexpected permission prompt.

## I. Muse verification after evidence arrives

SHA match → service identity → deploy success → health
re-probe → env presence log → safe R1–R4 probes (only if
armed + safe) → pricing/account reconciliation → report
updates → G-PROVISION re-evaluation.
