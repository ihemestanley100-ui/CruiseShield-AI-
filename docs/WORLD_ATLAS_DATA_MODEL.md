# WORLD ATLAS — DATA MODEL

Date: 2026-11-03 · Spec only · No migration performed.

## 1. Storage decision

JSON storage retained. New file `data/atlas.json`
(separate from `data/state.json` — financial state is
never mixed with geospatial cache). F-EPH-1 applies:
Render Free sleep wipes it; atlas data is re-derivable
cache + seed, never authoritative. No PostgreSQL/PostGIS
in this plan; migration needs a separate approval.

## 2. Collections (all additive)

### places (bundled, not stored)
- Source: `world-atlas` TopoJSON shipped in the frontend
  bundle. `{ id (ISO-3166 numeric), name, continent,
  bbox }`. No PII. No network.

### observations (stored cache)
- `{ obs_id, kind (EO_IMAGERY | TLE | AIS |
  PORT | ENV | RISK_GEO | DEMO_SYNTHETIC), provider,
  observed_at, retrieved_at, footprint_geojson,
  centroid {lat,lon}, confidence, licence, terms_url,
  stale_after, synthetic: bool }`
- `synthetic:true` items MUST render with the demo badge;
  the renderer refuses to display them as live.

### layer_state (per-session, client-side only)
- Visible layers, filters, camera preset. Never persisted
  server-side; no tracking implication.

### evidence_links (stored, append-only)
- `{ link_id, obs_id, package_id | case_id |
  investigation_id, linked_by, linked_at, note }`
- Reuses evidence-package hash chain for tamper evidence.

## 3. Validation rules

- Coordinates: lat −90…90, lon −180…180, finite; reject
  NaN/Infinity/strings-that-look-exact (precision cap:
  5 decimals ≈ 1m; IP-derived capped at ~city level and
  labelled APPROXIMATE).
- Timestamps: ISO-8601 UTC; `observed_at ≤ retrieved_at`;
  future-dated observations rejected.
- Every stored observation REQUIRES provider + licence +
  provenance or the write fails closed.

## 4. Retention

Cache TTL 24h default, 7d max; expired items render
STALE or are evicted — never silently presented as
fresh. Purge endpoint guarded (admin, audited).

## 5. What is NOT stored

No user GPS, no precise individual location, no raw
imagery blobs (metadata + footprints only; imagery
viewed at provider under provider terms), no
credentials (server env only).
