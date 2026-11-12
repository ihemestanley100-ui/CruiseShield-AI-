# WORLD ATLAS — ACCEPTANCE TEST MATRIX

Date: 2026-11-03 · All rows currently NOT_VERIFIED (nothing built).

## Interaction (manual + automated where noted)

| ID | Test | Method | Pass criteria |
|---|---|---|---|
| T01 | 360° azimuth | Drag full circle | Seamless wrap, no snap |
| T02 | Polar clamp | Drag past poles | Stops 15°–165°, no flip |
| T03 | Zoom limits | Wheel extremes | Clamps 2.2–12, no clip-through |
| T04 | Dblclick zoom | Dblclick city/ocean | Tweens to point / honest note |
| T05 | Pinch + touch | Mobile gestures | Zoom + rotate, page still scrolls |
| T06 | Auto-rotate override | Drag during rotation | Pauses; toggle resumes |
| T07 | Reset | Reset button | Exact default camera |
| T08 | Fullscreen | F + button | Enters/exits cleanly, layout holds |
| T09 | Keyboard map | Full key set | All actions operable, focus visible |
| T10 | 2D/3D switch | Toggle mid-session | State translated, no data loss |
| T11 | Search + select | Query + Enter/click | Correct country panel, Esc clears |
| T12 | Reduced-motion | OS setting | Static frame, instant moves |
| T13 | No-WebGL | Disabled GPU | Fallback panel, no crash |
| T14 | Viewports 390/768/1440 | Resize suite | No overlap, targets ≥44px |

## Data + integration

| ID | Test | Method | Pass criteria |
|---|---|---|---|
| T15 | Layer honesty | Toggle each | LIVE/STALE/PLACEHOLDER correct |
| T16 | Overlay clustering | Dense bbox | Clusters + "+N more", no PII |
| T17 | Risk overlay parity | vs API | Matches `risk-intelligence` values |
| T18 | Provenance present | Every item | Source/ts/licence shown |
| T19 | Demo labelling | Synthetic on | Badge visible, never live-styled |
| T20 | Deep links | Click-through | Lands on correct inv/case/evidence |
| T21 | Contract tests | pytest/vitest | Auth matrix + validation + 429 |
| T22 | Perf budget | Build + FPS meter | Chunk ≤350KB gzip, fps targets |

## Satellite + regression

| ID | Test | Method | Pass criteria |
|---|---|---|---|
| T23 | Track A LIVE checklist | Per provider | §6 of Satellite Spec green |
| T24 | Track B honesty | Default state | PLACEHOLDER with reason |
| T25 | Full regression | tsc/vitest/pytest/build | All green, risk diff empty |
| T26 | Preservation re-audit | Source diff | 84/84 still preserved |
