# CSG-RELEASE-001 — Findings Register

## F-CSG-001 — Banned demo phrase in new blurb (High) — CLOSED

- Location: `frontend/components/landing/scene/categories.ts`
  (corridor blurb contained "synthetic demonstration" →
  banned substring "synthetic demo").
- Found by: full backend suite (`test_product_identity`),
  2026-11-10 15:1x.
- Root cause: author wording overlooked the product-identity gate.
- Correction: reworded to "synthetic data for demonstration only"
  (meaning + test assertions preserved; full banned-list rechecked).
- Verified: `test_product_identity` 2/2 + atlas suite 12/12 green.
- Owner: engineering. Evidence: this mission's test record.

## F-CSG-002 — npm audit dev-toolchain findings (Medium) — OPEN

- 5 findings (2 moderate, 1 high, 2 critical), all confined to
  vitest/tinypool/postcss: test runner + CSS build tooling. None
  ships in the browser bundle or handles untrusted input.
- Disposition: documented accepted risk (NOT a silent waiver).
- Closure: post-release dependency update + full retest, or reviewer
  directs otherwise. Owner: engineering.

## CF-1 — L-01 numeric coverage absent (Low) — OPEN

- No coverage provider installed; adding one mid-release was
  rejected as tree-perturbing.
- Alternative supplied: `L01_BRANCH_EXECUTION.md` (every failure
  branch mapped to an executing, assertion-bearing test).
- Closure: reviewer accepts the alternative or requests the
  provider addition. Owner: reviewer + engineering.

## CF-2 — Deployed-preview fallback unverified (Medium) — OPEN

- Preview returns 401 to this environment; live fallback proven
  locally (real browser, branded screenshot) but not on the
  deployment.
- Closure: owner-session manual test with screenshots/console.
  Owner: owner.

## CF-3 — Historical evidence scoping (Informational) — CLOSED

- 192-era index and `rc:1`/envelope-less coverage files labeled
  HISTORICAL in `EVIDENCE_PACKAGE.md`; never cited as current
  evidence. Standing classification, no action.

## ENV-1 — Sandbox-only backend items (Informational) — CLOSED

- `test_static_escaping` (node EPERM) + 2× `test_cors` socket-bind
  errors: sandbox restrictions with captured tracebacks, green on
  hosted CI (run 42775901098). Re-verification on the post-push CI
  run closes this for the final tree.
