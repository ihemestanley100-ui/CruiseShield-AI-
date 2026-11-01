# 8. ROLLBACK AND RECOVERY PLAN

DATE: 2026-11-01 | PRECONDITION: owner-approved backup executed (D-008) — no rollback claim is valid without it.

## Service rollback (code/config)
- Render keeps deploy history per service: dashboard → service → Deploys → Redeploy a prior SHA. Frontend is stateless (safe). Backend redeploy restarts uvicorn; in-flight requests drain per Render defaults.
- Order on rollback: backend first, then frontend ONLY if its baked API URL still matches (it will, same backend URL) — else rebuild frontend.

## Data rollback (state — the hard part)
- The persistent disk is NOT versioned with deploys: rolling back code does NOT roll back `/srv/data/state.json`.
- Procedure: (1) stop writes (restrict URL/shut service if needed), (2) copy current state.json to `state.json.pre-rollback-<ts>` ON THE DISK (via Render shell), (3) restore the approved backup copy over `state.json`, (4) verify byte count + spot-check (case status, decisions count, risk scores 35/84 via /api/v1/risk/txn_84721), (5) restart backend, confirm /api/v1/health healthy, (6) record the incident + register a D-item.
- Corruption/disaster: same procedure from the off-Render archive (closeout backup procedure) + full smoke (runbook step 7).

## Recovery time expectations (staging, unmeasured — do NOT promise)
Target practice drill (not yet run): service rollback < 15 min; data restore < 30 min. First staging deploy SHOULD include a rollback drill to replace these with measurements.

## What is NOT covered
Free-tier (no disk): nothing persists — "rollback" = redeploy; staging data loss is by design there. Multi-instance: unsupported (single-instance store).
