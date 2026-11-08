# CRUISE ORBIT — Satellite Intelligence Feature Inventory

Date: 2026-11-03 · Read-only audit · Statuses: 2 PARTIAL (foundation
reusable), 16 MISSING (greenfield), 0 implemented as specified.

## Current-state honesty

Existing assets often mistaken for satellite capability: `orbital-
explorer.tsx` + `scene/orbital.ts` render the TRANSACTION graph in
rings (explicit visual-metaphor-only comments — NOT orbital
mechanics); `geo_intel.py` handles IP/device geolocation (NOT
satellite); no TLE/SGP4, imagery, AIS, maritime, or provider code
exists anywhere (case-sensitive repo search 11-03).

## ORBIT module inventory

| ID | Module | Status | Reusable foundation |
|---|---|---|---|
| ORBIT-01 | Satellite Intelligence Core | MISSING | `geo_intel.py` contracts (confidence/freshness/NullProvider), `ai_adapter.py` (timeout/retry/cap) |
| ORBIT-02 | Provider Integration Gateway | MISSING | `GeoProvider` Protocol + NullProvider pattern; `MODEL_*` env handling |
| ORBIT-03 | Tracking + Orbital Intel | MISSING | None (needs sgp4 dep + CelesTrak client) |
| ORBIT-04 | Earth Observation Intel | MISSING | None (needs CDSE STAC/OData client) |
| ORBIT-05 | Global Monitoring | MISSING | Notifications/audit patterns |
| ORBIT-06 | Cross-Border Geospatial Intel | PARTIAL | `geo_intel` validation/haversine + graph provenance; needs observation join |
| ORBIT-07 | Maritime + AIS Intel | MISSING | None (needs AISStream client; free-key terms unverified) |
| ORBIT-08 | Port + Infrastructure Intel | MISSING | None (open port datasets conditional) |
| ORBIT-09 | Environmental Observation | MISSING | CDSE/Landsat path (same client as ORBIT-04) |
| ORBIT-10 | Imagery Explorer | MISSING | None (metadata-first; no raster pipeline yet) |
| ORBIT-11 | Geospatial Risk Analysis | PARTIAL | Deterministic risk engine (advisory overlay only — MUST NOT alter scores; invariant + test required) |
| ORBIT-12 | Correlation Engine | MISSING | Evidence-ID grounding validator pattern |
| ORBIT-13 | Investigation Integration | MISSING | Evidence packages + case APIs exist as link targets |
| ORBIT-14 | Provenance + Audit | MISSING | `append_audit` + package-hash chain (extend, don't fork) |
| ORBIT-15 | Freshness + Reliability | MISSING | `FRESHNESS_LEVELS`/stale policy in `geo_intel.py` |
| ORBIT-16 | Alerts + Notifications | MISSING | Alerts model + notifications component exist as targets |
| ORBIT-17 | Security/Permissions/Governance | MISSING | RBAC matrix + session guard (new perms: `orbit_read`, `orbit_manage`) |
| ORBIT-18 | Observability/Resilience | MISSING | Health/ready + rate-limit + caps patterns |

Preservation: all 84 CruiseShield features untouched by this plan
(additive modules only; risk-score immutability is a release gate).
