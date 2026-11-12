# B3 — RENDER ACCOUNT & FREE-TIER VERIFICATION

Date: 2026-11-03 · Sources: official Render pricing page
and free-instances docs (fetched 11-03). No dashboard
access; no account changes.

## B3.1 Official terms — PASS (researched)

Workspace plans (list): Hobby $0/mo + compute · Pro
$25/mo + compute · Scale $499/mo + compute · Enterprise
custom. Render charges three things: workspace plan +
metered bandwidth + compute usage.

Free web services (official limitations):
- Spin down after 15 min without inbound traffic; wake
  on next request (cold-start delay).
- 750 free instance hours per workspace/month; exhausted
  ⇒ all Free services SUSPENDED until next month (no
  rollover).
- Ephemeral filesystem: ALL local changes lost on
  redeploy/restart/spin-down. Free services CANNOT attach
  persistent disks (paid-only, SSDs $0.25/GB/mo).
- Count against monthly bandwidth + build-pipeline
  minutes. Overage with payment method ⇒ billed
  supplementary amount; WITHOUT payment method ⇒ Free
  services suspended (bandwidth) or new builds disabled
  (pipeline; existing artifacts keep serving).
- Hobby includes 5 GB bandwidth, up to 25 services.
  Unusually high outbound traffic may trigger suspension
  (restore by moving to paid).
- Spend limits exist for build pipeline (dashboard).

## B3.2 Account-specific — NOT_VERIFIED (no dashboard)

Workspace plan, backend service plan, payment-method
presence, usage/consumed hours, spend limits: ALL
NOT_VERIFIED. Nothing inferred. Owner must read these
from dashboard → Billing before provisioning.

## B3.3 Pricing assessment (list vs actual)

1. Existing backend: list $0 IF Free compute + within
   750 hrs + 5 GB bandwidth; ACTUAL unknown (plan +
   usage NOT_VERIFIED). If the existing service is
   Starter/paid, it bills per-minute rates.
2. Proposed frontend: list $0 on Free (same conditions).
3. Combined: list $0 compute; shared 750 hrs + 5 GB pool.
4. Bandwidth overage: billed if card on file, else
   month-long suspension. Demo traffic is KB-order —
   negligible under normal judging use.
5. Build overage: same mechanics; each deploy consumes
   pipeline minutes (Docker backend builds cost more
   than Node).
6. Workspace fee: $0 on Hobby (assumed, NOT_VERIFIED).

$0 TOTAL is NOT claimed: it holds only if (a) Hobby
workspace, (b) both services Free, (c) usage within
750 hrs + 5 GB + pipeline minutes, (d) no paid add-ons.
(b)–(d) need dashboard confirmation.

## B3.4 Suitability

- Hackathon demo / evaluation / prototype: SUITABLE with
  caveats (cold starts ~60 s — warm before filming;
  ephemeral state — reseed/re-login after sleep; monitor
  usage dashboard).
- Production financial-crime platform: NOT SUITABLE on
  Free (no persistence, no SLA, suspension risk, sleep
  gaps). Production needs paid plans + managed Postgres +
  disks — a separate, funded decision.

## B3.5 Provisioning boundary — RESPECTED

No service created, no control clicked, no plan/billing
touched. Provisioning spec: `G_PROVISION_FRONTEND_PREFLIGHT.md`
§9 (Option B manual Free service). Awaiting owner approval.

## Verdict: B3 research PASS · account facts NOT_VERIFIED

## Round 2 (2026-11-03 — dashboard still unavailable)

- No authenticated Render dashboard is reachable from this
  session (no browser control, no API token, and using
  either would exceed authorization). All §C
  account-specific items remain NOT_VERIFIED.
- Owner must inspect and report (read-only, values never
  pasted): workspace plan · backend service plan ·
  monthly cost shown · payment method yes/no · used vs
  included instance-hours/bandwidth/pipeline minutes ·
  spend limit/overage settings. Official-pricing half of
  B3 stands as researched in Round 1.

## Round 3 (final-readiness directive — no owner evidence supplied)

- No dashboard observations supplied. Workspace plan,
  backend service plan, billing/spend, and frontend-cost
  support stay NOT_VERIFIED. No estimates invented.
  Owner read-out from dashboard → Billing still due
  (plan · service plan · cost · card yes/no · usage vs
  allowances · spend limits).

## Round 4 (CS-B2-B3-FINAL-003)

- Checklist §F + evidence register §C define the exact
  read-out. Nothing received yet — account items stay
  NOT_VERIFIED, no estimates invented.

## Round 5 (billing evidence arrived 11-03)

- Evidenced: Hobby $0 · card YES (details withheld) ·
  usage 1.82/750 hrs, 0/5 GB, 0/500 pipe-min, 1/25 svcs ·
  $0.00 MTD + projected · Oct $0 paid · frontend NONE.
- Current-$0 ≠ guaranteed-$0: card on file means overage
  WOULD bill (Render's stated policy) instead of
  suspending. Recorded as FINANCIAL RISK R-$1.
- Capacity: 748.18 hrs remain; burn rate ~0.6 hrs/day →
  backend+frontend projected ~40–50 hrs/mo — comfortable
  IF sleep behavior holds and no always-on change.
- Still due: spend-limit/overage settings · Services page
  (all plans) · paid-resources confirmation. Gate stays
  BLOCKED until overage exposure is controlled + verified.
