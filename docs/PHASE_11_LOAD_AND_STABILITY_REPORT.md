# PHASE 11 — LOAD AND STABILITY REPORT

PROGRAMME: CSAI-MASTER-RELEASE-001 | PHASE: 11 | DATE: 2026-11-01
BACKEND: disposable :8006 (current code, post PERF-001 fix for race section; pre-fix race documented the bug).

## Load (controlled, localhost, synthetic data)
| Scenario | Result |
|---|---|
| 4 endpoints × 50 sequential (risk, graph, case, POST sim) | 200/200 OK; IWR p50 115–131 ms / p95 134–156 ms (incl. ~115 ms harness overhead); tight HttpClient p50 3 ms |
| 20-way concurrent GET × 200 | 0 non-200 |
| 10-way concurrent POST simulations (pre-fix) | 4×200 + 6×500 → PERF-001 diagnosed (WinError 32 on shared state.tmp) |
| 10-way concurrent POST simulations (post-fix) | 10/10 200; state JSON valid, sim count consistent |
| p50/p95/p99 (n=50, IWR): risk 117/135/364, graph 131/156/158, case 115/134/150, sim 122/146/149 ms | Single p99 outlier (364 ms, first-hit warmup) |

Targets: demo needs are single-user interactive (<2 s page, <500 ms API client-observed). All met. No multi-user saturation, soak, or external-service load test performed — capacity beyond this envelope NOT claimed.

## Stability
- 200 mixed sequential requests (5 endpoints): 0 errors; RSS flat 56.2 MB; CPU 3.1 s.
- Repeated navigation/rendering: covered by CDP matrix re-run 69/69 (see compatibility matrix) — 0 console errors, 0 failed requests across routes/viewports.
- provider interruption / session expiry / long-running sessions: NOT_VERIFIED (no live-provider chaos run; no sessions exist — SEC-004).
- Timers/handlers: animation code uses rAF with visibility + reduced-motion guards (`ambient-background.tsx`, `orbital-explorer.tsx`, covered by unit tests); no runaway-timer evidence observed.

## Verdict
Load/stability at demo scale: PASS_VERIFIED (with PERF-001 fixed and regression-pinned). Soak/multi-user/provider-chaos: NOT_VERIFIED.
