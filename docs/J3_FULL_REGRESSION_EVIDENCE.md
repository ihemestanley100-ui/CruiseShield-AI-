# J3 — FULL REGRESSION EVIDENCE

All commands run this turn; counts are observed output, not carried.

## Backend (project `.venv`, sandboxed)

- `.venv/Scripts/python -m pytest tests -p no:cacheprovider -q`
  → **341 passed / 103 skipped / 1 failed-in-sandbox** (445
  collected). The 1 failure is `test_esc_neutralizes_html_fixture`
  (node EPERM `lstat C:\Users\HP` — sandbox forbids node path
  resolution). Re-proven **3/3 green unsandboxed** (approved).
  Skips: socket/loop-gated (direct-handler twins assert every
  behavioral branch) + live-PG-gated (need `SCRATCH_DATABASE_URL`).
- Focused: di03–di09 + events + secret_safety **104 passed**;
  `test_flow_direct.py` **14 passed**; `test_ai_validation.py`
  **24 passed / 15 skipped** (loop-gated halves); auth/CORS/rate/
  body suites all green.

## Frontend (approved unsandboxed; node EPERM in sandbox, environmental)

- `npm run typecheck` → clean. `npm test` → run 1: 260 + 1
  transient failure; run 2: **52 files / 261 tests, all pass**
  (incl. 7 new: site-url ×4, headers ×1, icons ×2).
- `npm run build` → **exit 0**, BUILD_ID `JZCaaZ1gryKKPCfNZLJJI`.

## Security / supply chain

- `security_gate.py` (.venv): lock-covers-requirements PASS (16),
  installed-matches-lock PASS (37 exact), lockfile-hashes PASS
  (37 pins / 463 sha256), pip_check PASS, secret_scan PASS.
  pip_audit: OSV unreachable in sandbox (retry pending — see
  J3_SECURITY doc for final disposition).
- Workflows re-counted: 30 `secrets.*` refs, 0 literals.
- render.yaml parses; backend 10 keys, frontend 4 keys; health
  paths `/api/v1/health`, `/`.

## Coverage map (system × evidence)

Auth/session/roles/CSRF/throttle/CORS → test_auth/cors/rate/gate
suites · AI cap/timeout/retry/fallback/validation/injection/quota →
test_ai_* + P8 · reads/writes/404-400 matrix → flow_direct +
api_flow twins · engine determinism/bands/counts → risk/graph/seed
suites · evidence/audit/provenance → evidence/cases/audit suites ·
migration/loader/parity → pg suites (live parts gated) · backup
crypto/produce/restore → p1/p2 suites · UI routes/states/a11y →
261 vitest · determinism/state → hash checks (below).

## State preservation

`data/state.json`: `BA1D4DB4…3790FE` / 101417 B before, during
(J3), and after closeout. No reseed/reset/migration; tmp_store
isolates every mutating test. Logo: canonical
`cruiseshield-logo-original.png` (1273370 B, `1A0CC66B…`) + 8 icon
assets hashed and recorded; duplicate still absent (D1).
