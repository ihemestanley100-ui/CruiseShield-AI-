# WORLD ATLAS — SATELLITE INTEGRATION SPEC (Tracks A + B)

Date: 2026-11-03 · Spec only · No accounts, no keys, no calls.

## 1. Adapter architecture (to build, not built)

`app/sat_providers/base.py`: `fetch_observations(kind,
bbox, since) → Observation[]`, `health() →
{state,latency,quota}`, `licence() → {name,terms_url}`.
One module per provider, fail-closed, timeout 8s, retry
2× backoff, quota counters, all credentials from server
env. No provider code exists today.

## 2. Track A — Earth observation (CANDIDATES, all NOT_VERIFIED)

| Candidate | Data | Cost posture | Owner must verify |
|---|---|---|---|
| USGS Landsat (EarthExplorer) | Multispectral imagery metadata | U.S. public domain data; account for API | Current API terms + key process |
| Copernicus Sentinel (CDSE) | SAR + optical metadata | Free with account | Current ToS + quota |
| CelesTrak | TLE orbital elements | Free public | Current query policy |
| OpenStreetMap-derived | Ports/infra context | ODbL, attribution | Tile/data policy for use |

First integration (if approved): TLE-only orbital layer
(positions computed client-side from elements via `sgp4`
— new dep needs license+security audit) + Landsat/
Sentinel METADATA + footprints. No raw imagery blobs
stored; full scenes viewed at provider under its terms.

## 3. Track B — Satellite communications

Status: BLOCKED. No free public API for coverage maps,
outage events or satcom health was identified. Options
for owner direction: (a) defer Track B to PLACEHOLDER
(openly labelled), (b) owner supplies an authorized
provider + credentials + terms, (c) manual coverage
dataset with provenance (low freshness, honestly dated).
No fabrication under any option.

## 4. Provenance contract (binding, both tracks)

Every observation: provider, `observed_at`,
`retrieved_at`, footprint/centroid, confidence,
licence + terms URL, limitations. Missing/stale =
labelled STALE/UNAVAILABLE, never live-styled. Synthetic
demo items carry `synthetic:true` + badge.

## 5. Governance red lines

No inferring financial activity of an individual from
imagery; no altering risk scores from unverified
observations; no presenting coverage as location proof;
AI explains supplied items only; retention TTLs apply;
access logged to the audit trail.

## 6. Verification before LIVE label (per provider)

Account + terms recorded → test call succeeds → licence
stored → freshness measured → UI shows provider name +
timestamps → acceptance row PASS. Until then the layer
stays PLACEHOLDER. Evidence plan mirrors
`CRUISE_ORBIT_LIVE_VERIFICATION_PLAN.md`.
