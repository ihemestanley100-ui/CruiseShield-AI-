# B2/B3 — OWNER EVIDENCE REGISTER (CS-B2-B3-FINAL-003)

Date: 2026-11-03 · Fields stay PENDING_OWNER_INPUT until
the owner supplies them. Never enter secret values or
card details here.

## A. Deployment evidence

- Service name: cruiseshield-ai (owner-reported 11-03)
- Branch: production-launch (owner-reported 11-03)
- Full deployed SHA: PENDING (short `ff7052b` reported;
  unambiguous locally → approved commit; full 40-char
  dashboard confirmation still due)
- Deployment status: Deploy succeeded / Live (owner-reported)
- Deployment time: 2026-11-03 10:31:53 AM GMT+1, 33.3 s,
  manual dashboard trigger (owner-reported)
- Evidence reference: chat description 11-03 (no screenshot
  file attached)

## D. Post-deployment health evidence (owner-viewed 11-03)

- Source: owner opened `/api/v1/health` directly.
- Reported: healthy, 1.0.0-p0, scn_primary, store PASS,
  seed_integrity PASS, graph_provenance PASS,
  storage_backend PASS (json/json).
- `model_configured: NOT_CONFIGURED` and `pg: NOT_CONFIGURED`
  recorded as CONFIGURATION LIMITATIONS (no key by design;
  JSON store by design) — NOT health failures.
- Corroboration: independently byte-identical to Muse's
  fresh probe (200, new run_id). Verdict: backend healthy
  post-report; says nothing about deployed SHA (static
  version string).

## B. Environment presence

- SESSION_SECRET: PENDING_OWNER_INPUT
- DEMO_USERS: PENDING_OWNER_INPUT
- DEMO_WRITE_TOKEN: PENDING_OWNER_INPUT

## C. Billing evidence (owner-supplied 11-03)

- Workspace plan: Hobby, displayed $0.
- Backend service plan: PENDING (Services page read-out due).
- Monthly service cost: $0.00 MTD; $0.00 projected November;
  Oct 2026 invoice paid at $0.00.
- Payment method present: YES (card details withheld from
  records by policy).
- Usage and allowances: 1.82/750 instance-hrs · 0/5 GB
  bandwidth · 0/500 pipeline min · 1/25 services ·
  0/2 custom domains. Credit balance $0.00.
- Spend limit: PENDING (Spend-limits page read-out due).
- Overage configuration: PENDING (same).
- Paid resources: PENDING (Services page confirmation due).
- Existing frontend service: NO (confirmed).

## Intake log

- Round 4 (11-03): register created; all fields pending.
  No deployment, env, or billing evidence received yet.
- Round 5 (11-03): blank evidence template received (all
  fields empty). No verifiable values — all fields remain
  PENDING_OWNER_INPUT; no status changed.
- Round 6 (11-03): deployment description received (§A
  filled except full SHA + env + billing). Health
  re-probed 200 with FRESH run_id (consistent with a new
  boot; not SHA proof). auth/mode still false — live
  backend UNARMED, R1–R4 prerequisites unmet, no probes
  run.
