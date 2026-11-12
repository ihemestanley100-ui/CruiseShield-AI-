# CRUISE ORBIT — Data Architecture and Database Schema

Date: 2026-11-03 · Design (not implemented).

## Principles

- Observations are immutable records with full attribution;
  NOTHING writes to financial collections (one-way link table).
- Synthetic demo observations carry `synthetic: true` and live
  in a SEPARATE namespace; real and synthetic never mix in one
  query without an explicit flag (mirrors `geo_intel.py`).
- Retention: raw provider payloads 30 d, derived observations
  1 y, audit links permanent. Cache: TLE sets 1 h, AIS snapshots
  60 s, imagery metadata 24 h (no raster caching at launch).

## JSON store extension (Phase 1; PG DDL in Phase 2)

- `orbit_providers`: name, capabilities, quota state, last
  error, `last_ok_at`.
- `orbit_observations`: obs_id, provider, kind
  (pass/imagery_metadata/ais_fix/port_call/environmental),
  lat/lon (+validity per `validate_coordinates`), observed_at,
  retrieved_at, confidence, freshness, license, attribution,
  limitations, payload_ref, synthetic.
- `orbit_links`: investigation_id ↔ obs_id + analyst note +
  created_by/at (append-only; case-visible).
- `orbit_alerts`: rule_id, obs_refs, severity, state
  (open/acked/expired), audited transitions.

## Freshness semantics (extends `geo_intel.FRESHNESS_LEVELS`)

fresh < 24 h (AIS/TLE) or < 14 d (imagery, cloud-limited);
stale to 30 d / 90 d; expired beyond. Expired/stale items
render with badges; NOTHING renders a "LIVE" label unless
retrieved within its freshness window AND provider reachable
(verified at read time, not cached).

## PG cutover (later, same loader discipline)

DDL mirrors the four collections + FK to investigations +
GIN on (kind, observed_at); migration via copy-verify-
reconcile (`migrations/loader.py` pattern). NOT in Phase 1.
