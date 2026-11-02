# J6 — DISASTER RECOVERY PLAN

## Scenarios and responses

| # | Scenario | Detection | Response | RTO |
|---|----------|-----------|----------|-----|
| D1 | state.json deleted/corrupt | health FAIL / hash mismatch | restore last verified JSON bytes; re-hash; restart | < 15 min |
| D2 | Neon project lost/quota-killed | PG unreachable + dashboard | re-provision; load last verified snapshot; re-run J5 reconcile; or fall back to JSON (one env change) | < 30 min |
| D3 | Render service broken deploy | health checks red | instant rollback to prior revision (Render dashboard) | < 10 min |
| D4 | bad migration / reseed | reconcile FAIL / counts off | loader rolls back automatically (single txn); fix source; re-run; live JSON never touched | < 15 min |
| D5 | secret exposure suspected | report/scan | rotate at provider; update secret store + Render; redeploy; revoke sessions (epoch bump); audit | < 1 h |
| D6 | workstation loss | — | clone GitHub + secret store + latest B2/C3 generation; full J7 gate before demo | < 2 h |

## Escalation

Owner is the only escalation point (solo project): detect → assess
against this table → execute → verify per
`docs/J6_DATA_INTEGRITY_VALIDATION.md` → record in the restore
report. No step proceeds on a failed verification.

## Drill record

Disposable roundtrip drill green 2026-11-01
(`tests/test_j6_drill.py`): snapshot → seal → 2 targets → verify →
decrypt → byte-equality. No owner backup exists yet (D-008).
