# CRUISESHIELD AI — FULL REGRESSION REPORT (J3)

**Suite state at J3 close:** backend 334 pass / 102 skip / 0 fail
(437 collected; 1 sandbox-node-blocked proven green unsandboxed);
frontend 49 files / 254 tests pass; `tsc` clean; `next build` exit 0.
Skips are env-gated (`CAN_SOCKETS`/loop), counted separately, with
socket-free twins asserted for every behavioral branch.

## Coverage map (route → behavior → evidence)

- Auth/gate: login/logout/me/mode, roles, throttle, expiry re-gate,
  CSRF, CORS, Secure cookie → `test_auth`/`test_cors`/gate suites +
  api/login-gate/app-shell suites (frontend).
- AI governance: timeout, cap, retries, fallback, validation,
  injection shield, quota message, stale-skip → `test_ai_*` + P8 loop
  twins (run in CI) + adapter suites.
- Reads: case/audit/scope/decisions/open/alerts/missing/graph/replay
  + unknown-ID 404 matrix + tail/cursor clamps → P9 direct suites
  (11 + 16 + 18 …) with transport twins behind `CAN_SOCKETS`.
- Writes: decisions/simulations/events/analysis idempotent + fenced +
  audited → `test_flow_direct` (11) + `test_api_flow` (13) + existing
  crime/audit suites, scratch-state isolated.
- Engine: 200× determinism, band matrix (6/6), rules 8/8 + unknown-txn
  sentinel (J3-P3) → `test_risk_determinism`, `test_graph_rules_risk`.
- UI states: quota/timeout/401/403/404 honest cards, upload-capped,
  uplift pinned → ai-panel/command-kpis/upload suites.
- Build/type/lint-level: tsc + build + contract/determinism scripts.

## Not covered (named, not hidden)

- Loop+socket twins (CI), real browsers/AT (env), live provider
  (owner), hosted tiers (owner), load-beyond-demo (not claimed).
