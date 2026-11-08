# WORLD ATLAS — FEATURE INVENTORY

Date: 2026-11-03 · Read-only · IDs ATLAS-F01…F28.
Statuses: IMPLEMENTED / PARTIAL / NOT_IMPLEMENTED /
BLOCKED / NOT_VERIFIED. A spec row is NOT proof.

## Globe core

| ID | Feature | Status | Evidence |
|---|---|---|---|
| F01 | 360° horizontal rotation | NOT_IMPLEMENTED | Hero auto-rotates; no user control |
| F02 | Vertical rotation / polar clamp | NOT_IMPLEMENTED | Fixed camera in `GlobalHeroScene.tsx` |
| F03 | Mouse drag rotate | NOT_IMPLEMENTED | Only pointer parallax |
| F04 | Touch drag + pinch | NOT_IMPLEMENTED | No touch handlers on canvas |
| F05 | Wheel zoom + limits | NOT_IMPLEMENTED | No zoom path |
| F06 | Double-click location zoom | NOT_IMPLEMENTED | No picking at all |
| F07 | Auto-rotate on/off + pause/resume | PARTIAL | Pause exists (hero prop); no user toggle, no resume control |
| F08 | Camera reset | NOT_IMPLEMENTED | — |
| F09 | Fullscreen mode | NOT_IMPLEMENTED | No Fullscreen API use |
| F10 | Keyboard navigation | NOT_IMPLEMENTED | Canvas is `role="img"` (correct today, insufficient for atlas) |
| F11 | 2D/3D switching | NOT_IMPLEMENTED | No 2D renderer |
| F12 | Realistic Earth w/ real boundaries | NOT_IMPLEMENTED | Stylized blobs (`scene/earth.ts:18-20`) |
| F13 | Country/region search + select | NOT_IMPLEMENTED | No dataset, no index |
| F14 | Location info panels | NOT_IMPLEMENTED | Region hubs are labels only |
| F15 | Responsive + reduced-motion + fallback | PARTIAL | Patterns exist in hero; atlas must re-apply, not inherit |

## Intelligence layers

| ID | Feature | Status | Evidence |
|---|---|---|---|
| F16 | Transaction/account overlays | NOT_IMPLEMENTED | No coordinate projection of ledger data |
| F17 | Device/IP/geolocation markers | PARTIAL | `geo_intel.py` contracts exist; no map consumer, no provider |
| F18 | Deterministic risk overlays | NOT_IMPLEMENTED | `risk_intel.py` exists; no geospatial view |
| F19 | Cross-border routes + geo-timelines | NOT_IMPLEMENTED | — |
| F20 | Investigation/evidence/case links | NOT_IMPLEMENTED | Deep-link targets exist; no atlas source |
| F21 | Layer toggles + filters | NOT_IMPLEMENTED | — |
| F22 | Provenance labels per item | NOT_IMPLEMENTED | Pattern exists in evidence packages |

## Satellite tracks

| ID | Feature | Status | Evidence |
|---|---|---|---|
| F23 | Track A adapters + imagery metadata | NOT_IMPLEMENTED | No provider code or accounts |
| F24 | Footprints / freshness / licensing | NOT_IMPLEMENTED | — |
| F25 | Historical comparisons | NOT_IMPLEMENTED | — |
| F26 | Track B coverage/status/outages | BLOCKED | No free coverage API identified; needs owner direction |
| F27 | Satcom provider health | BLOCKED | Same as F26 |
| F28 | Privacy/permission controls (sat) | NOT_IMPLEMENTED | RBAC exists; no sat scope defined |

## Totals

IMPLEMENTED 0 · PARTIAL 3 (F07, F15, F17) ·
NOT_IMPLEMENTED 23 · BLOCKED 2 (F26, F27) ·
NOT_VERIFIED 0. No atlas code exists; nothing is claimed.
