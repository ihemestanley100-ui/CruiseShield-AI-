# CRUISE ORBIT — Backend Endpoint Matrix

Date: 2026-11-03 · Design (not implemented). All under
`/api/v1/orbit/*`, guarded by session/token auth + new
`orbit_read` / `orbit_manage` perms; rate-limited; 1 MB bodies.

| Method + path | Purpose | Status |
|---|---|---|
| `GET /api/v1/orbit/providers` | Provider health/quota/freshness | MISSING |
| `GET /api/v1/orbit/passes?satId=&lat=&lon=&hours=` | SGP4 pass predictions (server-computed) | MISSING |
| `GET /api/v1/orbit/objects?bbox=` | Catalog objects in view (CelesTrak cache) | MISSING |
| `GET /api/v1/orbit/imagery/search?bbox=&from=&to=` | Scene METADATA only (no rasters at launch) | MISSING |
| `GET /api/v1/orbit/vessels?bbox=` | AIS snapshot (freshness-labelled) | MISSING |
| `GET /api/v1/orbit/ports?bbox=` | Port/infra reference data | MISSING |
| `GET /api/v1/orbit/observations/{obsId}` | Single observation + provenance | MISSING |
| `POST /api/v1/orbit/links` | Link obs→investigation (audited) | MISSING |
| `GET /api/v1/orbit/alerts` + `POST .../ack` | Alert list + acknowledge | MISSING |
| `GET /api/v1/orbit/freshness` | Feed ages + reliability panel data | MISSING |

Conventions (match existing API): structured error envelopes
(`ORBIT_*` codes: NOT_CONFIGURED, PROVIDER_TIMEOUT,
QUOTA_EXHAUSTED, STALE_FEED, LICENSE_BLOCKED), trace IDs,
validation-first (bbox/coords via `validate_coordinates`),
audited mutations, synthetic namespace flag on every read.
