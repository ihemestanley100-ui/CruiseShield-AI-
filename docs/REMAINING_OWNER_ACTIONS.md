# REMAINING OWNER ACTIONS — CruiseShield AI™ (2026-11-03)

Everything executable locally is DONE and green. The items below need
the owner (dashboard access, secrets, recording, portal). Do them in
order; after each batch, paste the evidence back for verification.

## Batch 1 — Read-only dashboard reads (~5 min, zero risk)

1. Backend service → **Environment**: report per NAME only —
   `SESSION_SECRET`, `DEMO_USERS`, `DEMO_WRITE_TOKEN` → PRESENT/MISSING.
   Never paste values. (Live evidence predicts all MISSING.)
2. Backend → **Deploys** → top Live deploy → **Source** commit link →
   paste full 40-char SHA (expect `ff7052b…65354`). Do not redeploy.
3. **Billing** + service list: each service name/plan/price; bandwidth
   used vs 5 GB; instance hrs vs 750; pipeline min vs 500 + spend-cap
   value; disks/databases/add-ons YES/NO; unbilled + projected totals.

## Batch 2 — Arming + frontend deployment (needs Batch 1)

4. If any Batch-1 var is MISSING: generate strong values, set them in
   backend Environment, redeploy. Then I verify `auth_enabled:true`
   and run the R1–R4 live security probes (safe, synthetic).
5. Create frontend service (Free): repo `CRUISESHIELD-AI-`, branch
   `production-launch`, root `frontend`, Node, build
   `npm ci && npm run build`, start `npm start -- --port $PORT`,
   health `/`. Paste the live URL + deployed SHA.
6. Frontend env: set `NEXT_PUBLIC_API_BASE_URL` to the backend URL;
   leave `NEXT_PUBLIC_DEMO_WRITE_TOKEN` UNSET. Rebuild if prompted.
7. Backend env: append the frontend URL to `FRONTEND_ORIGINS`
   (exact origin, comma-separated, no wildcard). Redeploy backend.
8. I then run the 7 live landing acceptance checks + responsive pass.

## Batch 3 — AI, video, submission

9. Meta live call: set `MODEL_API_KEY` (+ URL/model if different) in
   backend env and explicitly approve ONE live call (~10k tokens).
   I execute, record evidence, and confirm spend.
10. Record the 3-minute video (`docs/FINAL_THREE_MINUTE_DEMO_PLAN.md`:
    8 timed scenes, captions, 1080p) and submit at the portal.
    Recording + submission cannot be delegated.

## Standing decisions (no action needed unless you disagree)

- `$0` ceiling: current/projected charges are $0, but bandwidth
  overage has no provider cap while a card is on file — acknowledged
  residual risk; say so explicitly before Batch 2 if you accept it.
- Frontend `postcss` advisories (build-time only): fix needs breaking
  Next 16 upgrade — deferred post-submission unless you say otherwise.
- No LICENSE file exists: adding one is your legal call (MIT /
  Apache-2.0 / other) — I will not choose unilaterally.
- Uncommitted worktree (~130 entries) stays uncommitted until you
  approve a G-COMMIT manifest; nothing will be pushed or published.

## What I do after each batch

Reconcile evidence → update the zero-gap matrix → run the next
verification gate → report PASS/PARTIAL/BLOCKED with proof. R3–R10
stay closed until you approve each gate.

## Release cert v3.0 owner actions (2026-11-04)

Still gated, in dependency order:

1. R1/R2/R11/R12 dashboard read-outs (env names, full SHA, services + billing).
2. R3 arming: set the 3 backend secrets in Render, redeploy, then I verify +
   run safe R1–R4 probes.
3. Frontend provisioning authorization (only after the $0 gate passes).
4. Meta: funded key + explicit 1-call approval (~$0.02), or accept P05 BLOCKED.
5. LICENSE choice + G-COMMIT manifest approval (60 modified + 77 untracked).
6. Postcss Next-16 breaking upgrade: accept residual risk or approve upgrade.
7. Video recording + portal submission.

## Release closure FRC-001 notes (2026-11-04)

- Release manifest (`PUBLIC_REPOSITORY_RELEASE_MANIFEST.md`) is PROPOSED:
  review the 141 INCLUDE / 383 EXCLUDE split, then approve the G-COMMIT set.
- A repo-root `.env` holds a Meta API key (git-ignored, never printed). Three
  keyed test POSTs timed out (503, no usage). To diagnose live Meta, approve
  ONE explicit diagnostic call, or rotate/revoke the key if it is stale.
- When arming Meta in Render, set `AI_DAILY_CALL_LIMIT` to 1-5 initially
  (worst-case ceiling ≈ $2.50/day at the default 100).
