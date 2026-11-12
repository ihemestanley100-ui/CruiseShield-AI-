# WORLD ATLAS — IMPLEMENTATION ROADMAP

Date: 2026-11-03 · Plan only · Sizes relative (S/M/L).

## Phase 0 — Audit + plan (THIS TURN, read-only) ✓

Repo audit, preservation re-verification, architecture
assessment, 13 documents. No code, no Git, no spend.

## Phase 1 — Globe prototype (M)

- Add `world-atlas` + `topojson-client` (audit licenses).
- `scene/atlas/geo.ts`: boundary load + rasterizer +
  picking math + unit tests.
- `AtlasCanvas`: earth mesh, OrbitControls profile,
  auto-rotate/pause/reset, resize/DPR, dispose, WebGL
  fallback reuse. Route `/atlas` behind no new auth
  (inherits session). Static boundaries only.
- Gate: interaction tests F01–F09 PASS locally.

## Phase 2 — Geographic foundation (M)

- Search index + AtlasSearch + AtlasInfoPanel.
- 2D plane mode + Globe/Map switch.
- Keyboard map, fullscreen, reduced-motion, 3 viewports.
- i18n strings + a11y audit. Gate: F10–F15 PASS.

## Phase 3 — Financial overlays (L)

- `app/atlas_api.py` + schemas + `atlas_store.py` +
  contract tests (places/layers/overlays/routes/
  timeline). Clustering + PII rules enforced.
- AtlasLayers + filters + overflow honesty.
- Deep links atlas → investigation/case/evidence.
- Gate: F16–F22 PASS, risk engine untouched (diff empty).

## Phase 4 — Track A satellite (M, needs owner ToS approvals)

- Provider adapter(s) for approved candidate(s) only.
- Observation cache + TTL + provenance UI + evidence
  links. `sgp4` only if TLE approved (audit first).
- Gate: per-provider LIVE checklist PASS or layer stays
  PLACEHOLDER (accepted outcome, not failure).

## Phase 5 — Track B satcom (BLOCKED until owner direction)

- Only under option (b)/(c) from Satellite Spec §3.
  Default: ship PLACEHOLDER honestly.

## Phase 6 — Hardening + release (M)

- Security/privacy/licensing review, full regression
  (tsc, 366 vitest + new, pytest + new, build),
  deployment preflight, gap reconciliation, video slice.
- Gate: acceptance matrix green, zero-gap register
  reconciled, owner release approval.

## No-touch list (all phases)

`app/main.py` routes (append-only mount excepted),
risk engine, auth/session, evidence chain, landing,
demo/investigation/network/cases/replay pages,
`data/state.json`, `render.yaml`, Dockerfile.
