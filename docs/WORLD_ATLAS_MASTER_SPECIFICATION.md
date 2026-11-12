# WORLD ATLAS — MASTER SPECIFICATION (CruiseShield AI™)

Date: 2026-11-03 · Status: READ-ONLY AUDIT + PLAN · Code changes: NONE.

## 1. Mission

Add an enterprise-grade geospatial intelligence subsystem to
CruiseShield AI™: an interactive 360° Earth globe, geographic
foundation data, financial-intelligence map overlays, and two
separate satellite tracks (Earth observation, satellite
communications) — fully integrated with the existing
investigation, evidence, risk, case, AI and audit architecture.

## 2. Absolute preservation rule

- All 84 inventoried features preserved (80 IMPLEMENTED,
  4 PARTIAL reverified 11-03 — see
  `WORLD_ATLAS_FEATURE_PRESERVATION_AUDIT.md`).
- Second UI/UX redesign (`frontend/app/page.tsx` →
  `GlobalLandingPage`) untouched.
- No route replacement, no file deletion, no mock-data
  substitution, no duplicate components.
- Atlas is ADDITIVE: one new page (`/atlas`), new scene
  modules, new versioned APIs. Nothing existing is moved.

## 3. Capability summary with honest status

| # | Capability | Status | Evidence / note |
|---|---|---|---|
| 1 | Interactive 360° globe | NOT_IMPLEMENTED | Hero scene is non-interactive (parallax only) |
| 2 | Drag / zoom / pan / reset / touch | NOT_IMPLEMENTED | No OrbitControls or equivalent in tree |
| 3 | 2D/3D switching | NOT_IMPLEMENTED | No 2D map renderer exists |
| 4 | Country/region search + selection | NOT_IMPLEMENTED | No boundary dataset; hero Earth is stylized blobs |
| 5 | Financial overlays (txn/acct/device/IP) | NOT_IMPLEMENTED | Backend geo signals exist (see §4), no map consumer |
| 6 | Deterministic risk overlays | NOT_IMPLEMENTED | Risk engine exists; no geospatial projection |
| 7 | Cross-border routes + timelines | NOT_IMPLEMENTED | No temporal geo view |
| 8 | Track A: EO/satellite intelligence | NOT_IMPLEMENTED | No providers, no adapters, no accounts |
| 9 | Track B: satcom coverage/status | NOT_IMPLEMENTED | No providers; no free coverage API identified |
| 10 | Provenance/licensing/audit for geo | NOT_IMPLEMENTED | Patterns exist (evidence packages), not extended |

## 4. Existing foundations (PARTIAL, reusable)

- `frontend/components/landing/scene/*`: tested Three.js core
  (three@0.187), WebGL fallback, reduced-motion, DPR tiers.
- `app/geo_intel.py`: vendor-neutral IP-geolocation contracts
  (offline-safe, approximate-only).
- `app/risk_intel.py` + `/api/v1/risk-intelligence/{id}`:
  deterministic candidate signals incl. GEO-* rules.
- `app/intel_link.py`: device/IP/geolocation linking with
  honest insufficient-evidence states.
- Evidence packages (hash-chained), RBAC, audit trail,
  rate limiting: reusable governance as-is.

## 5. Architecture decision (summary)

Primary: **Three.js (already vendored) + stdlib
OrbitControls + bundled `world-atlas` boundaries + canvas
rasterizer**. No new runtime dependency except two small
OSS data packages (MIT/ISC). No CDN, no CSP change, no
account, $0 preserved. Full evaluation (CesiumJS, MapLibre)
in `WORLD_ATLAS_ARCHITECTURE.md`. R3F/Drei NOT recommended
(rewrite of tested code, no capability gain).

## 6. Data posture

- JSON storage retained; atlas data in new `data/atlas.json`
  (never mixed with financial state). No PostgreSQL/PostGIS
  migration in this plan (F-EPH-1 ephemeral limits apply).
- Real geography from `world-atlas` (Natural Earth derived).
- Satellite data: CANDIDATE open programs only
  (Landsat, Sentinel, CelesTrak TLE) — each NOT_VERIFIED
  pending owner ToS review; no accounts created.
- Synthetic demo overlays clearly labelled; never live.

## 7. Governance (binding)

Deterministic risk stays authoritative; AI explains verified
evidence only; humans decide; correlation ≠ proof; every
observation carries source/timestamp/licence/provenance;
stale/missing feeds labelled; credentials server-side only.

## 8. Document index

Master (this file) · Feature Inventory · Architecture ·
Data Model · API Specification · Satellite Integration ·
Interaction Design · Roadmap · Zero-Gap Register ·
Acceptance Matrix · Security/Privacy/Governance ·
Deployment & Release Gate · Preservation Audit.

## 9. Stop state

No code written, no Git mutation, no provisioning, no spend.
Owner approvals required: architecture choice (§5),
candidate-provider ToS review, `go` for implementation.
See `WORLD_ATLAS_DEPLOYMENT_AND_RELEASE_GATE.md`.
