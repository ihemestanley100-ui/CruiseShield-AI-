# CSG-RELEASE-001 — Test Report (final candidate tree)

Source: `e099b7a` + 15-file candidate. Node v20.19.6, Python 3.13,
Windows. Times local (UTC+1).

| Suite | Command | Result | Exit |
|---|---|---|---|
| Backend full | `pytest tests/ -q` | 1,431 passed, 144 skipped, 1 env-fail, 2 env-errors, 224s | recorded non-zero (env-only) |
| Backend gate recheck | `pytest tests/test_product_identity.py` | 2 passed (F-CSG-001 fix verified) | 0 |
| Frontend full | `npx vitest run` | 473 passed / 85 files, 72s | 0 |
| L-01 slice | 5 hero/scene/controls files | 34 passed | 0 |
| StrictMode lifecycle | `GlobalHeroScene.strictmode.test.tsx` | 1 passed (2/2 dispose, 0 leaks) | 0 |
| TypeScript | `npx tsc --noEmit` | clean | 0 |
| Ruff | `ruff check .` | clean | 0 |
| Matrix / manifest | `--check` both | 213 valid / 11 ok | 0 |
| Build (×3 trees) | `npm run build` | green (pristine, GAT-008, final) | 0 |
| Dependency audit | `npm audit` | 5 dev-only findings (F-CSG-002) | 1 (findings) |
| Browser regression | Playwright (local builds) | rotation, digits 1/5/8 select, reset, fallback shot, console baseline | 0 |
| L-01 harness | control + poison on `e099b7a` build | both PASS per criteria | 0 |

Environmental (non-blocking, green hosted): `test_static_escaping`
(node EPERM in sandbox), 2× `test_cors` (socket-bind WinError 10013
in sandbox). Product-identity failure was a genuine defect
(F-CSG-001, fixed and re-verified). No passing result is reported
for a non-zero command: the backend exit reflects the 3 sandbox-only
items, each classified with trace evidence in the mission record.
