# Architecture (hackathon vertical slice)

Single-process FastAPI application. Domain logic is pure and deterministic;
the store persists state as JSON; the model only interprets evidence.

```text
Synthetic seed (app/seed.py)
  -> Event validation/normalization/idempotency (app/events.py, app/store.py:ingest_event)
  -> Entity resolution = seeded identity map (nodes carry source_record_ids)
  -> Graph + provenance check + features (app/graph.py)
  -> Versioned rules + risk-score-v1 (app/rules.py)
  -> Evidence items + package + hash (app/evidence.py)
  -> Investigation view (app/main.py + templates/investigation.html)
  -> Meta adapter + validators (app/ai_adapter.py)
  -> Replay cursor (app/replay.py) / bounded what-if (app/simulate.py)
  -> Human decision + case machine (app/cases.py) + audit (app/store.py)
```

## Module boundaries

- Domain services (`seed/events/graph/rules/evidence/cases/replay/simulate`)
  compute authoritative facts. No HTTP or model concepts inside them.
- `store.py` owns persistence (atomic JSON writes) and audit sequencing.
- `ai_adapter.py` owns the only external call: server-side httpx POST to the
  OpenAI-compatible Meta endpoint, plus response parsing and validation.
- `main.py` owns routing, error envelope `{error: {code, message, trace_id}}`,
  and page rendering. It never manufactures facts.
- Frontend (`templates/`, `static/`) renders API/store state only. The SVG
  graph is laid out deterministically (BFS layers) from backend data.

## Data

- Money in integer minor units (kobo). IDs stable per blueprint prefixes.
- `data/state.json` (gitignored) holds the active scenario run; reset re-seeds
  deterministically from the versioned manifest.
- No database server, queue, or cache: deliberately the smallest durable
  option (ADR-001). SQLite/Postgres remain a forward option without contract
  changes (store interface is the seam).

## Level 14 platform layers (master directive §3, 2026-11-05)

One platform, 14 logical layers. Each layer names its CANONICAL files;
do not create parallel implementations (§19).

- L01 Experience: `frontend/`, `templates/`, `static/`.
- L02 Identity: `app/auth.py` (sessions/RBAC), `app/mfa.py` (TOTP).
- L03 API gateway: `app/main.py` (routes, guards, error envelope),
  `app/ratelimit.py`, `app/config.py` (CORS/origins).
- L04 Ingestion: `app/events.py`, `app/seed.py`, `app/connectors.py`
  (provider adapters; credentials by env reference only).
- L05 Entity/txn intel: `app/device_intel.py`, `app/ip_intel.py`,
  `app/geo_intel.py`, `app/risk_intel.py`, `app/intel_link.py`,
  `app/intel_evidence.py`.
- L06 Detection: `app/rules.py` (versioned engine), `app/detection.py`
  (derived signals), `app/channels.py` (channel taxonomy).
- L07 Graph: `app/graph.py` (features/provenance),
  `app/graph_intel.py`.
- L08 Investigation: `app/cases.py`, `app/replay.py`,
  `app/simulate.py`.
- L09 Evidence/audit: `app/evidence.py`, `app/store.py` (audit seq),
  `app/audit_chain.py` (hash chain), `backups/`.
- L10 AI: `app/ai_adapter.py` (gateway), `app/intel_ai.py`
  (validators). Deterministic engine stays authoritative.
- L11 Industry: `app/industries.py` (45-ID registry),
  `app/industries_*.py` (profiles), `app/pilot.py` (promotion gate).
- L12 Governance: `app/tenancy.py` (isolation),
  `app/governance.py` (SAR/DSR/legal-hold workflows).
- L13 Operations: `Dockerfile`, `render.yaml`, `netlify.toml`,
  `.github/`, `scripts/backup_drill.py`.
- L14 Evolution: `scripts/zero_gap_matrix.py`,
  `scripts/forensic_inventory.py`, gap/decision/acceptance registers.

Phase-0 duplicate audit (2026-11-05): no identical source files
(app/tests/frontend-lib), no duplicate route+method pairs (79), no
duplicate env names (39/39 unique), every app module referenced.
`industries_law.py` (law-enforcement) vs `industries_legal.py`
(legal) are distinct modules — similar names only, no action.
Canonical inventory: `docs/FORENSIC_INVENTORY.json` (regen via
`scripts/forensic_inventory.py`); directive §12 group→registry
mapping: `app/industries.py::directive_groups` (45 groups, 45 IDs,
zero dropped).

## Telecom Identity (2026-11-07, TEL-01..TEL-09)

Provider-integrated telecom verification reusing Store, connectors
lifecycle, ratelimit, tenancy, and audit. New: app/telecom_registry.py
(13 operators v1.0, provenance-labeled), app/telecom_providers.py
(status + synthetic-only harness), app/telecom_verify.py (11 services,
9 states, sealed evidence). Endpoints /api/v1/telecom/* +
/api/v1/admin/telecom-config. UI: TelecomSection in txn/investigation/
case/platform views. Live integrations: none (TEL-08 blocked).
Full record: docs/TELECOM_IDENTITY.md.

## Geointelligence OS (2026-11-07, GEO/IDV/ADR/MAP/PRV/GOV/SEC/AI rows)

Identity/address/IP/location engines + unified provider registry +
investigation map payloads + schematic zero-dep map UI. Reuses
Store/connectors/ratelimit/tenancy/audit/DI-04/DI-05/telecom.
22 endpoints /api/v1/identity|addresses|geolocation|providers|
evidence|intel|geointel/*. Live providers: none (LIVE-GEO
blocked); tile binding NOT_STARTED. Full record:
docs/GEOINTELLIGENCE_OS.md.

## Universal intel core (UFI, 2026-11-07)

Payment taxonomy (A-I) + traceability + lifecycle mapping,
network/rail registry, party model (masked + resolution),
40-typology registry, alert lifecycle, tracing engine,
crypto/gift/remittance adapters, 15 deterministic reports.
Reuses detection/signal/graph/industry/notify/web3/tenancy/
audit. 18 endpoints (161->179 routes). Live providers: none
(UFI-LIVE blocked); agent-kernel tools NOT_STARTED. Full
record: docs/UNIVERSAL_INTEL_OS.md.

UFI slice 2: monitoring wiring, txn list/events/relationships, 45 industry adapters + readiness, edge-aware tracing, 8 routes (179->187).

UFI slice 3: 5 intel tools in governed kernel (11 tools total), fleet readiness endpoint, report assembly from investigations, trace-investigation links. Routes 188.

SEC slice (2026-11-07): per-client credentials (PBKDF2 store, abac client kind, write-gate + actor wiring), session-secret rotation keyring (primary + previous), trusted-device register (login touch, self-service trust/revoke, deny at 3 issuance sites). 6 routes (188->194).

UFI closeout (2026-11-07): typologies mapped to canonical industry ids (16 refs fixed); E2E + scenario + fleet + perf suites; generated closeout evidence (docs/UFI_CLOSEOUT.md).

Agent OS (2026-11-07): deterministic orchestrator (lifecycle+budgets+traces), NL search, retrieval plane, conversations, 13 kernel tools, 45 industry agent configs, assistant shell. Routes 194->205. No model configured.

Recovery OS (2026-11-07): scheme rules (2 VERIFIED + 8 templates), 11-status eligibility, 17-state lifecycle, 33x12 capability matrix, fund-recovery agent, industry recovery configs, recovery UI. Routes 205->219.
