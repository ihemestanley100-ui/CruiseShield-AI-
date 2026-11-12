# WORLD ATLAS — API SPECIFICATION (proposed, versioned)

Date: 2026-11-03 · Spec only · NONE implemented.
Base: `/api/v1/atlas`. Auth: session cookie + RBAC
(read: any authenticated; link/purge: write/admin).
Rate limits + audit inherited from existing middleware.
All responses carry `provenance` + `as_of`.

## 1. Geographic foundation

- `GET /places/search?q=&limit=` → `{id,name,continent,
  bbox}` — local index over bundled boundaries. No fetch.
- `GET /places/{id}` → boundary bbox + hub info.
- `GET /layers` → layer registry with availability:
  `{key,label,state: LIVE|STALE|PLACEHOLDER|DISABLED,
  reason}` — honest states, never fake LIVE.

## 2. Financial-intelligence overlays (read-only projections)

- `GET /overlays/transactions?bbox=&since=&risk_min=`
  → clustered markers `{cluster_id,centroid,count,
  max_risk,txn_ids[]}`. Clustering mandatory (no
  thousand-pin dumps); amounts rounded; no PII.
- `GET /overlays/geo-signals` → GEO-* rule outcomes
  from `risk_intel.py` projected to regions (approximate,
  labelled).
- `GET /routes/cross-border?window=` → aggregated
  country-pair flows `{from,to,count,risk_p95}` — counts
  only, never individual attribution.
- `GET /timeline/geo?window=` → time-bucketed
  `{bucket,region_id,count,alerts}` for the geo-timeline.

## 3. Satellite (Track A / Track B)

- `GET /observations?kind=&bbox=&since=` → stored
  observation cache (see Data Model). Empty + honest
  `source_status` until a provider is authorized.
- `GET /observations/{id}` → full metadata + licence +
  evidence links.
- `POST /evidence-links` (write) → link observation to
  package/case/investigation (validated IDs only).
- `GET /coverage` → Track B status. Until a provider
  exists: `{state:"PLACEHOLDER", reason}` — 200 with
  honest body, NOT 404, NOT fake data.

## 4. Error model (existing convention)

`{detail, code, trace_id?}`; 401 unauthenticated, 403
role-denied, 422 validation, 429 limited, 503 provider
unreachable (with `source_status`). No stacks, no secrets.

## 5. OpenAPI + contracts

Router mounted additively in `app/main.py` (append-only
`include_router`); schemas in `app/atlas_schemas.py`;
contract tests per endpoint (auth matrix + validation +
provenance fields) before any frontend wiring.

## 6. Existing touchpoints reused (no changes)

`/api/v1/risk-intelligence/{id}`,
device/IP intel, graph, alerts, cases, evidence, audit —
atlas reads through service functions, never forks them.
