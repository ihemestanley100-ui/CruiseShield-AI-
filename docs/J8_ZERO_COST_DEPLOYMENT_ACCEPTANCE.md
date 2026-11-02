# J8 ZERO-COST DEPLOYMENT ACCEPTANCE (20-point)

Canonical report: docs/J8_DEPLOYMENT_ACCEPTANCE.md (terms
evidence). This file is the acceptance checklist.

| # | Check | Status |
|---|-------|--------|
| 1 | Provider eligibility + permitted use | PASS (Pages/Render/Neon eligible; Vercel rejected) |
| 2 | Free-tier limits recorded | PASS (quotas + conflicts noted) |
| 3 | Runtime compatibility | PASS (Next.js, Python Docker, PG) |
| 4 | Build config | PASS (build exit 0; Dockerfile unbuilt — PARTIAL) |
| 5 | Env-var requirements | PASS (RENDER_6 register + J4 additions) |
| 6 | Backend /health | PASS (endpoint + tests) |
| 7 | Frontend/backend connectivity | PASS (design; live NOT_VERIFIED) |
| 8 | CORS | PASS (allowlist, credentialed when armed) |
| 9 | Neon connectivity | PASS (pattern proven on scratch PG; Neon URL NOT_VERIFIED) |
| 10 | Migrations | PASS (atomic loader, rehearsed) |
| 11 | Authentication | PASS (J4, local) |
| 12 | Secrets server-side | PASS (scans + architecture) |
| 13 | Logging | PASS (redacted, trace IDs) |
| 14 | Rate limits | PASS (600/min, login 10/min) |
| 15 | Sleep/wake | DOCUMENTED (Render 15 min; Neon 5 min) |
| 16 | Ephemeral FS | DOCUMENTED (no disk; PG is the store) |
| 17 | Storage/bandwidth | DOCUMENTED (fits; overage vectors open) |
| 18 | AI costs/quotas | PARTIAL (controls PASS; billing NOT_VERIFIED) |
| 19 | Usage monitoring | PARTIAL (per-run logs; no hosted dashboard) |
| 20 | Suspension/recovery | DOCUMENTED (cold-start + quota-exhaustion behavior) |

ACCEPTANCE: configuration PASS_WITH_LIMITATIONS; live
deployment NOT DONE (owner gates; no provisioning performed).
