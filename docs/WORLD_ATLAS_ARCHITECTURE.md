# WORLD ATLAS — ARCHITECTURE

Date: 2026-11-03 · Read-only assessment · No code changed.

## 1. Decision

**Primary: Three.js (already vendored, three@0.187, MIT) +
stdlib OrbitControls + bundled `world-atlas` TopoJSON
(MIT) + `topojson-client` (ISC), rasterized through the
existing canvas-texture pipeline.**

- 2D mode (phase 1): equirectangular plane reusing the SAME
  boundary rasterizer — no second renderer.
- Optional phase 2: MapLibre for a rich 2D basemap IF the
  owner accepts an external tile dependency + CSP edit.

## 2. Evaluation matrix (verified 11-03)

| Criterion | Three.js + data (chosen) | MapLibre GL JS | CesiumJS |
|---|---|---|---|
| License | MIT + MIT/ISC — clean | BSD-3-Clause — clean | Apache-2.0 engine — clean |
| Globe support | Full control (own sphere) | Globe projection since v5 (verified) | Native globe |
| 2D/3D switch | Own plane mode, shared data | Runtime projection switch | 2D/Columbus/globe modes |
| Bundle (order) | ~0 new (three present) + small data | ~253 KB min+gzip (reported) | MB-order + Workers/assets |
| Next.js fit | Already integrated + tested | ESM ok; style/tile plumbing new | Asset-copy config pain, known |
| Data dependency | Bundled TopoJSON, zero network | Vector tiles: self-host or external | ion assets need account/token by default |
| CSP impact | NONE (`self` suffices) | `connect-src` + `img-src` edits for tiles | Same or larger |
| $0 impact | $0, no account | $0 possible (OpenFreeMap, ODbL data) but external reliance | Free tier needs ion account; self-host global terrain infeasible on Render Free |
| Test reuse | Hero patterns + scene tests | New harness | New harness |
| Verdict | **ADOPT** | **PHASE-2 OPTION** | **REJECT** |

CesiumJS rejected: weight, ion-account default path, and
integration cost outweigh its globe maturity for this
mission. MapLibre stays a legitimate future 2D upgrade.

## 3. Why not React Three Fiber / Drei

The scene core is tested, shipped, tuned imperative code.
OrbitControls (three stdlib, no new dep) covers drag,
wheel, touch, pinch, damping, polar/azimuth limits. An
R3F migration rewrites working code for zero new
capability and re-opens all scene tests. NOT recommended;
requires explicit owner override to adopt.

## 4. Additive file plan (no existing file modified)

New: `frontend/app/atlas/page.tsx` (+ `loading.tsx`),
`frontend/components/atlas/AtlasCanvas.tsx`,
`AtlasControls.tsx`, `AtlasLayers.tsx`, `AtlasSearch.tsx`,
`AtlasInfoPanel.tsx`, `frontend/components/landing/scene/atlas/{geo,boundaries,controls2d,layers}.ts`,
`app/atlas_api.py` (versioned router, mounted additively),
`app/atlas_store.py`, `data/atlas.json` (seed: empty +
schema version), tests colocated. ONE config touch IF
MapLibre phase 2 is ever approved: `next.config.ts` CSP.
Nothing else.

## 5. Runtime shape

`/atlas` → `next/dynamic` ssr:false → WebGL probe →
AtlasCanvas (three scene: earth+boundaries, markers,
arcs, layer groups) + side panel + search + layer
toggles. Data via `/api/v1/atlas/*` (same origin, session
cookie, RBAC, rate limits — all inherited).

## 6. Performance budget

First-load atlas chunk ≤ 350 KB gzip excluding three
(shared with hero chunk); 60fps desktop, ≥30fps mobile
tier (DPR ≤1.25, reduced particles — existing pattern);
boundary rasterize once, cached; marker cap with honest
"+N more — refine filters" overflow (no silent drop).
