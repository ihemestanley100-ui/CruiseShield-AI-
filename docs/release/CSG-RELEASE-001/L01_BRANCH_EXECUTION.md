# CSG-RELEASE-001 — L-01 Branch-Execution Evidence

## Coverage-tool limitation (honest)

No coverage provider is installed (`@vitest/coverage-v8` and
`-istanbul` both absent) and no coverage gate exists in CI
(`security-gate.yml` runs `vitest run` without coverage). Adding a
dependency mid-release to manufacture a percentage would perturb the
verified tree; it was deliberately not done. A numeric coverage
artifact therefore does not exist. Reviewer-approved alternative
below: every L-01 failure branch is executed by a named,
assertion-bearing test — branch execution proven, percentage not
claimed.

## Branch → test map (`GlobalHeroScene.tsx`, target `e099b7a`)

| Failure branch | Executing test | Assertion proving execution |
|---|---|---|
| Renderer `try` throws (80–85) | `GlobalHeroScene.test.tsx` — WebGL unavailable | `webgl-fallback` rendered |
| Setup `try` throws (115–132) | `GlobalHeroScene.failure.test.tsx` | `dispose` called + fallback + canvas absent |
| Catch disposes renderer (134) | failure test + `strictmode.test.tsx` | dispose counter 1 / 2-for-2 |
| Catch removes canvas (135) | failure test + Playwright harness | DOM absent + `remove()` call observed |
| Catch activates fallback (136) | failure test + harness + live WebGL-off shot | fallback visible in all three |
| Cleanup mirror (319–338) | StrictMode test (unmount empty) + suite | zero outstanding resources |
| Success path preserved | `atlas-categories.test.tsx` reduced-motion render + control runs | canvas present, no fallback |

## Verdict

Branch execution: PROVEN for every L-01 line above via independent,
re-runnable tests. Numeric coverage: NOT AVAILABLE (tooling absent).
Closure requires reviewer acceptance of this alternative or a
post-release coverage-provider addition with full retest.
