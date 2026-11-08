# PROPOSED ZERO-COST RENDER CONFIG (NOT APPLIED — AWAITS APPROVAL)

Date: 2026-11-03 · Status: PROPOSAL ONLY. Production
`render.yaml` untouched. Do not apply without explicit
owner approval + a G-COMMIT for the change.

## Why a proposal exists

Committed `render.yaml` declares `plan: starter` (backend
+ frontend) + a 1 GB paid disk. It was never applied
(all declarations INACTIVE), but one Blueprint click
would provision paid resources. This proposal is the
$0-safe equivalent. Alternatively keep Option B manual
Free creation and leave the blueprint as paid-tier
documentation — owner decides.

## Proposed diff (if blueprint route is chosen)

- Backend: `plan: starter` → `plan: free`; DELETE the
  `disk:` block; DELETE `DATA_DIR=/srv/data` (app falls
  back to ephemeral `ROOT/data`, reseeds deterministically).
- Frontend: `plan: starter` → `plan: free`. All commands,
  env keys, and R6-EMPTY token posture unchanged.
- Keep: health checks, `sync: false` secret prompts,
  DEPLOY_ORDER comments, all non-plan values.

## Resulting exposure (proposed)

- Compute: $0 (Free ×2, shared 750 hrs/mo).
- Storage: $0 (ephemeral; F-EPH-1 wipe-on-sleep accepted).
- Bandwidth/build: $0 within Hobby 5 GB + pipeline minutes;
  without a card, overage SUSPENDS instead of billing.
- Condition: Hobby workspace + no card + usage within
  allowances — all still need dashboard proof before any
  $0 claim (see zero-cost gate).

## Explicit non-goals

No disk, no database, no paid tier, no card requirement,
no blueprint apply, no push. This file proposes; it does
not configure anything.
