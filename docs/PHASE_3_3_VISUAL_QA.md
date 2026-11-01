# PHASE 3.3 — VISUAL QUALITY ASSURANCE

Date: 2026-11-01. Method: production servers + headless Edge (CDP):
44 automated checks + human inspection of 8 screenshots. Evidence:
`%TEMP%\smoke33\vqa.ps1`, `%TEMP%\smoke33\shots\vqa_*.png`,
`%TEMP%\smoke33\vqa-checks.json`, plus `%TEMP%\smoke33\probe.ps1`
(audit re-verify, 5/5). 14 screenshots captured; all routes × viewports
listed below were rendered for real — nothing claimed from code alone.

## Result: 44/44 automated checks PASS, 0 console errors, 0 failed requests

## A. Brand identity — PASS

- Title: "CruiseShield AI™ | The Financial Crime Immune System™" on
  every route (transport shows ™ as T; the served bytes are correct).
- Logo: `img[src*=cruiseshield-logo]` naturalWidth 1219 (authentic
  high-res asset, proportionally contained), brand anchor → `/`.
  Original file untouched (no logo edits in this programme).
- Favicon: 5/5 icon links resolve 200 with real byte sizes
  (favicon.ico 7690 B; 16/32/48 px PNGs; apple-touch-icon 47656 B).
- theme-color + og:title metas present.
- "Synthetic demo data" badge visible in the shell on every route.

## B. Landing page — PASS

- Desktop 1440: hero, value proposition, Detect→Protect strip,
  capability panel (9 DEMO modules), regions panel with
  "ILLUSTRATIVE NETWORK VIEW" + "Simulated regional signals · not live
  monitoring" disclosure, capability cards, CTA, footer below fold.
- R-04 region labels: small overlay tags (North America, Europe, South
  America…), not oversized. R-05 audio toggle: "Sound: Off" + Volume
  slider fully visible, off by default. R-11 mobile hero (390 px):
  stacks cleanly, globe prominent, readable, 0 px overflow.
- Reduce motion + Pause scene controls present and visible.

## C. Three.js experience — PASS (one live item NOT VERIFIED)

- Live: canvas renders; two frames 1.5 s apart differ (animating).
- Earth ~125.7 s/rev (spec 90–150), brain ~69.8 s/rev (spec 45–75),
  independent rotations, independent orbital rings/objects — all
  delta-time driven (`THREE.Clock`, dt capped 0.05) and unit-pinned in
  `scene.test.ts`.
- Hidden tabs skip render work; reduced/paused renders a static frame;
  full cleanup on unmount (rAF cancel, listener removal, part/renderer
  dispose). No misleading surveillance claims anywhere.
- WebGL failure fallback: `WebGLFallback` component + detection/
  try-catch wiring verified by code inspection
  (`GlobalHeroScene.tsx`, `scene/webgl.ts`, `WebGLFallback.tsx`).
  Live fallback trigger NOT VERIFIED (headless Edge always provides
  WebGL via SwiftShader; no mechanism to force failure was available).
- Observation (not a defect): the rAF loop keeps re-rendering the
  static frame while reduced/paused instead of stopping; negligible
  cost, left as is.

## D. Application shell — PASS

- Sidebar, topbar, theme radio group, notifications, breadcrumbs,
  system status, profile all render on every demo route; drawer +
  hamburger verified at 390 px; sidebar active states correct
  (multi-active on sub-routes, e.g. Cases + Audit Trail, is the
  established pattern).

## E. Product screens — PASS (7/7 routes)

All at 1440 px, 0 px horizontal overflow, exactly one h1 each:
`/` home, `/demo`, `/investigations/inv_84721` (badge settles 84/100
HIGH, section pills, triggered rules R-001+ with evidence ids),
`/network/txn_84721` (orbital explorer, 22 nodes / 30 edges, honest
layout-only disclaimer), `/replay/scn_primary`, `/cases/case_84721`
(AI assessment `requires_review`, muse-spark-1.3, VALIDATED refs),
`/cases/case_84721/audit` (real event `audit_0002`, clean `›`
breadcrumbs). Tablet 768 + mobile 390 verified for home/demo/
investigation: 0 px overflow everywhere.

## F. Visual + accessibility testing — PASS

- Dark mode end to end: clicking Dark sets `data-theme="dark"`,
  full dark render verified by screenshot; back to System after.
- Reduced motion (emulated): badge renders final 84 immediately.
- Keyboard: Tab chain moves focus (brand link → theme radio →
  menu button → nav links); global `:focus-visible` covers indicators.
- Semantic headings (single h1 per route), labelled sections,
  labelled form controls, table captions, `aria-current` on
  breadcrumbs/section nav — all observed live.
- Screen-reader pass with assistive technology NOT VERIFIED (no AT
  available); automated proxies above all pass.

## G. Fixes applied during 3.3 (safe, minimal)

- Audit table: `Event`, `Time`, `Actor`, `Action` cells `nowrap`
  (mid-token wrapping eliminated; verified 5/5 by targeted probe +
  screenshot). Files: `frontend/components/audit-list.tsx`,
  `frontend/app/globals.css` (rule added in 3.2F cycle).
- Frontend rebuilt (exit 0) and re-verified after each fix.

## Data integrity

No POSTs executed in 3.3. `data/state.json` untouched (hash
re-verified in the final assessment).
