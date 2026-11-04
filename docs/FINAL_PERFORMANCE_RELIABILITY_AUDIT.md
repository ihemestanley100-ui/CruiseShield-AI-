# FINAL PERFORMANCE & RELIABILITY AUDIT (R11)

Date: 2026-11-02. Scope: demo-scale local evidence. No production
traffic claims.

## Measurements (fresh, this programme)

`scripts/perf_smoke.py` (socket-free, tmp store; targets declared
before measuring — J7):

| Op | p50 | Target | Verdict |
| -- | --- | ------ | ------- |
| seed | 14.5 ms | startup < 2 s | PASS |
| health / ready / risk / graph / case / alerts reads | ≤0.02 ms | reads p50 < 50 ms | PASS |
| audit-append write | 3.55 ms | writes p50 < 100 ms | PASS |

Memory (rss): not measured — stdlib-only env, no psutil (NOT_VERIFIED,
low risk at demo scale).

## Reconciled evidence

| Check | Status | Evidence |
| ----- | ------ | -------- |
| Page loads (real browser) | PASS | 954–1317 ms at mobile widths (Phase 11) |
| Bundle size | PASS | 103 kB First Load JS shared (`build-final-r.log`) |
| API latency under server | PASS | Prior J7 validation + health 200s in container/QA runs; no new latency suite (demo scale) |
| Concurrency | PASS | Backend suite: concurrent saves/duplicates/PG races green (live scratch PG) |
| Failure/timeout/recovery | PASS | Suite: DB-unavailable, AI-provider-failure, timeout, retry, restart, restore-failure paths; container `stop` clean; servers restart cleanly across QA runs |
| Logging/monitoring/alerts | PARTIAL | Structured logs + health/ready endpoints verified; no production monitoring/alerting stack (gated on deployment) |
| Graceful degradation | PASS | BACKEND_UNREACHABLE states, AI-unavailable mode, WebGL fallback (live), English fallback (i18n) — all rendered + tested |
| Large graphs / load tests | NOT VERIFIED | Demo graph only (22 nodes/30 edges); no synthetic large-graph or load run in this programme |

## Verdict

R11: PASS_WITH_LIMITATIONS for demo/staging scale. Production
capacity, memory profiling, large-graph, and monitoring/alerting are
explicitly not established.
