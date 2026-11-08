# SECOND UI/UX REDESIGN FORENSIC AUDIT — CruiseShield AI™

Date: 2026-11-03 · Method: READ-ONLY (code + git + public GETs;
no modifications, no git writes, no Render changes).
IMPORTANT: no reference image arrived with the audit request —
pixel-comparison verdicts are NOT_VERIFIED; structural audit
below is evidence-complete.

## Verdict: option E — PASS (structural)

The "Global Intelligence Core" redesign is COMPLETE,
source-implemented, tested, committed in `58a3d50`, and pushed —
but the frontend that contains it was NEVER DEPLOYED. The live
root is the backend's legacy template, not the redesign.

## 1. Current homepage entry points (two apps, one deployed)

- DEPLOYED root (`https://cruiseshield-ai.onrender.com/`, 200):
  backend `app/main.py:321-331` → `templates/command.html`
  (original Command Center). PASS (identified).
- UNDEPLOYED root: `frontend/app/page.tsx:1-4` renders
  `GlobalLandingPage` (the redesign). PASS (identified).
- `frontend/app/layout.tsx`: shell + metadata + icons. PASS.

## 2. Redesign implementation inventory (all real components)

| Element | File | Lines |
|---|---|---|
| Page composition | `frontend/components/landing/GlobalLandingPage.tsx` | 1-90 |
| Nav/brand/hero/CTA | `.../landing/LandingChrome.tsx` | 1-104 |
| Intel/coverage/module panels | `.../landing/LandingPanels.tsx` | 1-119 |
| 10-card strip + metrics | `.../landing/LandingStrips.tsx` | 1-75 |
| 3D hero scene | `.../landing/GlobalHeroScene.tsx` + `scene/{earth,orbital,network,brain,stars,webgl,shared}.ts` | dir |
| Controls/fallback/a11y | `LandingControls.tsx`, `WebGLFallback.tsx`, `skip-link.tsx` | — |
| Strings (12 locales) | `frontend/lib/i18n/locales/*.ts` | en 95-189 |
| Styles | `frontend/app/globals.css`, `frontend/styles/landing.css` | — |
| Tests | `LandingContent.test.tsx`, `GlobalHeroScene.test.tsx`, `scene.test.ts` | — |

Content verified: "Global Intelligence Core" label (page:55-58),
9-item intel panel, 8-region coverage panel, 5 module cards
(incl. Cyber Defense), 10-card capability strip, 4 global
metrics, hero journey, demo CTA, footer honesty lines. No
satellite-coverage claims anywhere in UI strings (deliberate;
see J10 audit). No static "reference image" masquerading as UI:
zero hero/earth/globe image assets in `public/` — all visuals
are code-rendered (WebGL + SVG + CSS).

## 3. Git forensics (no timestamp inference)

- Landing built across `d4e2bec` (J1) → `753a6c5` (UGLS-03) →
  `58a3d50` (release); full file set present in `58a3d50`
  (verified via `git ls-tree`). PASS.
- Worktree vs HEAD: ZERO diffs under `frontend/components/
  landing`, `frontend/app/page.tsx`, `frontend/app/layout.tsx`
  — nothing omitted, nothing half-merged. PASS.
- Old renderer: backend `/` → `command.html` exists in ALL
  commits (legacy surface, never removed — by design for
  no-JS/API-only access). PASS.

## 4. Why live `/` shows the old Command Center — ROOT CAUSE

1. Only ONE Render service exists: the Docker backend
   (`cruiseshield-ai.onrender.com`). Its `/` serves the legacy
   Jinja template — correct behavior for that service.
2. NO frontend service exists: `https://cruiseshield-ai-
   frontend.onrender.com/` returns HTTP 404 (probed 11-03).
   G-PROVISION was never executed (still awaiting approval).
3. The Next.js app (with the redesign as `/`) therefore has
   no public URL. Nothing is disconnected, stale, or missing
   in git — deployment step F was simply never performed.

## 5. Classification of every finding

- Redesign exists asEditable components: PASS (option E proven).
- Reference image available for pixel match: NOT_VERIFIED
  (not attached; structural match to the described elements: PASS).
- Old-UI renderer identified: PASS (`app/main.py:321-331`).
- Frontend service existence: FAIL (404 — absent).
- Git completeness: PASS (committed + pushed in `58a3d50`).
- Omitted/uncommitted redesign work: NONE FOUND (PASS).
