# PHASE 11 — PERFORMANCE VALIDATION REPORT

PROGRAMME: CSAI-MASTER-RELEASE-001 | PHASE: 11 | DATE: 2026-11-01 | HEAD: 0eaaaf5 (no commit/push)
STATE: persistent `data/state.json` BA1D4DB4…3790FE (101417 B) — unchanged. All write/load probes used disposable TEMP stores.

## Test conditions
- HW/OS: Intel i7-8565U (4C/8T), 31.8 GB RAM, Windows 10 Pro 21H2.
- Runtime: Python 3.13.7 (uvicorn single worker), Node v20.19.6, production `next start`.
- Browsers: Edge 156.0.4314.50 + Chrome 156.0.4314.50 (same Chromium), headless CDP.
- Harness note: PowerShell `Invoke-WebRequest` adds ~115 ms overhead per call; tight figures use .NET HttpClient. Both reported honestly.

## 11.1 Baseline measurements
| Metric | Value | Method |
|---|---|---|
| Backend ready (spawn→first 200) | 2544 ms | :8006 disposable, 0.5 s poll |
| Backend RSS / private (after 200+ reqs) | 56.2 / 46.3 MB, 3 threads | listener child PID (uvicorn spawns a server child; launcher PID stats are NOT the server) |
| Backend CPU (400+ reqs) | 3.1 s total | Get-Process |
| GET /api/v1/risk (tight, n=20) | min 2, p50 3, p95 5, max 39 ms | HttpClient |
| GET risk/graph/case + POST sim (IWR, n=50 each) | p50 115–131, p95 134–156 ms, 0 errors | IWR incl. ~115 ms harness overhead |
| Frontend prod build | 49.7 s, exit 0 | timed `npm run build` |
| Static bundle (`.next/static`) | 1.61 MB total; largest chunk 357 KB | measured (`.next` total 223 MB incl. build cache — not shipped) |
| Prod route medians (n=5, HttpClient) | / 8, /demo 7, /cases 38, /investigations 31, /network 21, /replay 24 ms; all 200 | `next start` + :8000 backend |
| Real-browser page loads | 954–1317 ms at 320/360 px widths | CDP matrix (Edge headless) |
| Live Meta AI explanation | 18,776 ms (`agentrun_0003`, SUCCEEDED) | prior recorded evidence, Phase 3.4 — no new live call made |

## Findings
- PERF-001 (HIGH, FIXED+VERIFIED): concurrent POST /api/v1/simulations → 6/10 HTTP 500. Cause: `Store._save()` shared one fixed `state.tmp` path (WinError 32). Fix: per-store `threading.Lock` in `app/store.py` (+ comment). Regression test `test_concurrent_saves_do_not_collide` (16 threads × 5 saves) failed pre-fix, passes post-fix. Live re-race: 10/10 200, state valid. Residual: lock is per-process (single worker verified); multi-worker would need unique tmp names or external store — flagged for pilot.
- No memory growth across 400 sequential + 210 concurrent requests (RSS flat 56.2 MB) — no leak signal.
- GET race 20-way × 200: 0 failures.

## Verdict
Performance baseline: PASS_VERIFIED for demo scale (single-user judge walkthrough, tens of concurrent reads, serialized writes). Load capacity beyond the tested envelope (sustained multi-user, multi-worker) is NOT claimed.
