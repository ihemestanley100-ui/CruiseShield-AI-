# FINAL LIVE ACCEPTANCE TEST PLAN — CruiseShield AI™

Date: 2026-11-03 · Status: PLAN ONLY — every live case is
NOT_VERIFIED until executed against real public URLs in Phase 8.
Placeholders: `BACKEND_URL_TBD`, `FRONTEND_URL_TBD`.

Rules: synthetic data only; risk engine stays authoritative (AI
explains supplied evidence, never scores/decides/accuses);
no PASS without captured evidence (screenshot + response body).

Pre-conditions: deploy order complete (backend → frontend API
base → CORS origins → smoke); P-1/P-2 satisfied; backend warm
(allow ~60 s after idle).

| # | Test | Steps | Expect | Evidence |
|---|---|---|---|---|
| 1 | Frontend availability | GET `FRONTEND_URL_TBD/` + `/demo` | 200, brand + hero render | screenshots |
| 2 | Backend health | GET `/api/v1/health`, `/api/v1/ready` | `healthy`, 200; checks PASS | bodies |
| 3 | Database connectivity | health `store`/`seed_integrity` PASS; GET `/api/v1/alerts` | seeded records served | bodies |
| 4 | Authentication + logout | POST login (bad → 401; good → 200 + HttpOnly cookie); GET `/me`; POST logout → 200; alerts → 401 | exact codes; no session leak | bodies + cookie dump |
| 5 | Session persistence | login → reload app → `/me` still 200 (warm instance) | cookie session holds | screenshot + body |
| 6 | Detect workflow | open alert/investigation inv_84721 | 35/100 MODERATE line, rules R-001… visible | screenshot + DOM |
| 7 | Connect workflow | `/network/txn_84721` graph | 22 nodes / 30 edges, provenance errors 0 | screenshot + API body |
| 8 | Investigate workflow | evidence package read | package + items + IDs resolve | API body |
| 9 | Explain workflow | case AI assessment panel | requires_review + VALIDATED labels | screenshot |
| 10 | Verify workflow | replay `/replay/scn_primary` | 84/100 HIGH immutable baseline, deterministic controls | screenshot |
| 11 | Simulate workflow | POST `/api/v1/simulations` (what-if) | baseline vs simulated scores; audit entry | bodies |
| 12 | Human decision workflow | POST decision TRIAGED + reason | transition allowed list respected; audit entry; no auto-approval | bodies |
| 13 | Audit + provenance | GET case audit; evidence IDs cited resolve to sent IDs | complete trail; 0 unknown IDs | bodies |
| 14 | Meta AI live (needs quota approval) | POST ai-analysis on inv_84721 (ONE call) | SUCCEEDED + VALIDATED/VALIDATED or honest error code; no invented IDs/scores | run artifact (no creds) |
| 15 | Responsive | 390/768/1440 px landing + demo | no clipping/overflow (R-11 stays closed) | 3 screenshots |
| 16 | Headers + CORS | inspect response headers; evil-origin fetch | HSTS/CSP/nosniff/DENY present; evil origin gets no ACAO | header dumps |
| 17 | Error handling | bad txn id, oversized body, bad login | structured codes (404/413/401), no traceback, generic UI text | bodies + screenshot |
| 18 | Logs + recovery | platform logs during 1–17; restart → reseed → health PASS | boot + requests visible; reseed deterministic | log excerpts + health |

Pre-verified locally (carries over, re-confirm live): 8-route
smoke, authed en/fr/ar captures, 354/354 vitest, 403 backend
tests, gate 6/6, local health `healthy`. None of it substitutes
for the live rows above.
