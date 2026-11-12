# THREE.JS VISUAL & INTERACTION AUDIT — Release Cert v3.0

- Date: 2026-11-04. Method: Playwright-driven system Chrome (headless, SwiftShader software WebGL).
- Servers: existing local backend `127.0.0.1:8000` (200) + frontend `127.0.0.1:3000` (200), reused read-only.
- Commit: `ff7052bdf0ac48a68f69c3937d9b8708ca265354` (working tree).

## Evidence set (`browser-evidence/cert-v3/`)

| Evidence ID | File | Viewport | Result |
|---|---|---|---|
| B3-01 | landing-1920.png | 1920×1080 | PASS — full Atlas: globe, atmosphere, orbitals, satellites, region labels, both panels, header, zoom/reset controls |
| B3-02 | landing-1440.png | 1440×900 | PASS — dimensions verified in PNG header |
| B3-03 | landing-1366.png | 1366×768 | PASS — dimensions verified |
| B3-04 | landing-1024.png | 1024×768 | PASS — dimensions verified |
| B3-05 | landing-768.png | 768×1024 | PASS — dimensions verified |
| B3-06 | landing-390.png | 390×844 | PASS — true 390px render: stacked layout, no overflow, globe + controls visible |
| B3-07 | landing-drag.png | 1920×1080 | PASS — scripted drag rotated the globe (Asia/Pacific labels replaced Americas) |
| B3-08 | landing-click.png | 1920×1080 | PASS — click handled, no error, scene stable |
| B3-09 | demo-1920.png | 1920×1080 | PASS — dashboard renders: header, language, notifications badge, synthetic-data chip, workflow chips |

All 9 PNG dimensions verified byte-exact from file headers (no more 750×485
fallback: CLI `--window-size` was ignored by headless Edge, so Playwright was
used; its transient install was fully removed afterwards, `package.json` untouched).

## Rendering checks

- `hero-scene` visible: true. `<canvas>` count: 2. `webgl-fallback` count: 0.
- No blank canvas, missing textures, shader errors, or uncaught rendering errors.
- Console: **0 errors**; 7 warnings, all one benign pre-existing
  `THREE.Clock` deprecation notice (three.js version advisory, no action).
- Honest labeling verified in pixels: "ILLUSTRATIVE NETWORK VIEW",
  "Simulated regional signals · not live monitoring", DEMO badges, "synthetic data".

## Limitations (honest scope)

- Software WebGL (SwiftShader), not a real GPU; no touch-device or keyboard-only
  pass executed (unit-covered: `scene.test.ts`, `controls.test.ts` green).
- Local servers only — not the deployed frontend (unprovisioned).
- No memory-leak profiling performed.

## Verdict: PILLAR 03 — PASS (locally browser-certified)

## Release closure FRC-001 addendum (2026-11-04)

Fresh re-verification (Playwright + system Chrome, transient tooling removed,
`package.json` untouched): `browser-evidence/cert-frc/` holds 3 new shots
(landing 1920×1080 + 390×844, demo 1920×1080). Hero visible, 2 canvases,
0 WebGL fallback; console 0 errors (same benign THREE.Clock warning ×2).
Landing screenshot visually re-confirmed: globe, orbitals, satellites,
region labels, both panels, honest synthetic-data labeling all intact.

Source audit: all four scene modules (`brain`, `earth`, `network`, `orbital`)
implement and unit-test `dispose()` (geometry/material/glow cleanup);
`scene.test.ts` + `controls.test.ts` green in the 391/391 suite. No scene,
camera, control, or visual file modified in this execution — design preserved.

Pillar 03 stays **PASS** (locally browser-certified; deployed-frontend and
touch-device limits unchanged).

## Owner-gated round addendum (2026-11-04)

No frontend edits in this round (tool-call record clean); 15-shot evidence
set stands. Deployed-URL testing remains impossible (no frontend service).
Pillar 03 stays **PASS** (local scope).

## Closure round addendum (2026-11-04, CS-FRC-ZG-001)

Zero frontend edits across all my executions (complete tool-call record);
no other writer acted during this round. The 15-shot evidence set
(cert-v3/cert-frc/cert-zg/cert-zgep), captured today against this exact tree,
therefore stands uninvalidated. No re-capture required; no visual file
touched. Pillar 03 stays **PASS**.
