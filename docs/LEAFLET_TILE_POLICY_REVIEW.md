# Leaflet/OSM Tile Policy Review (D-055 POLICY FIRST prep)

Source: OSMF Tile Usage Policy,
https://operations.osmfoundation.org/policies/tiles/
(fetched 2026-11-07; full text retained in session evidence).
Decision note: this review PREPARES the D-055 call; it does not
approve tile use. Binding the LEAFLET renderer still needs the
owner's explicit policy approval.

## What the policy requires (tile.openstreetmap.org)

Must: exact HTTPS URL
`https://tile.openstreetmap.org/{z}/{x}/{y}.png`; visible
(c) OpenStreetMap contributors attribution on the map, never
hidden; valid identifying User-Agent (library defaults
forbidden); valid Referer from web pages (no restrictive
Referrer-Policy); local caching per HTTP headers (min 7 days);
no bulk download/scrape/prefetch; no no-cache headers by
default; HTTP (non-TLS) URL forbidden.

Should: configurable tile URL (no hard-coding); "report a map
issue" link; published contact email; HTTP/2 or HTTP/3.

Service: best-effort, NO SLA; OSMF may block degrading use
without notice. Heavy use must move to an alternative
OSM-derived service or self-hosted tiles.

## Fit for CruiseShield (investigator map, low volume)

- Attribution: implementable in the map corner (planned
  GeointelMap footer). PASS by design.
- Identification: server-side tile proxy is NOT planned;
  browser tiles carry the browser UA + page Referer, which
  the policy accepts for web use. PASS with default config.
- Caching: Leaflet honors HTTP cache headers; no no-cache
  defaults planned. PASS by design.
- Volume: investigator-only, low-traffic internal tool —
  well under heavy-use thresholds. PASS, with monitoring
  obligation if usage grows.
- No-scrape: no prefetch/offline features planned. PASS.

## Conditions for a D-055 approval recommendation

1. Attribution rendered on every map view (acceptance test).
2. Tile URL configurable via MAP_PROVIDER (no hard-code).
3. No prefetch/bulk features without re-review.
4. Usage stays investigator-scale; revisit if public-facing.
5. Fallback: schematic renderer stays when tiles unreachable.

Recommended D-055 answer (owner decides): POLICY-COMPLIANT
for the planned use; approve binding subject to conditions
1-5. Cost $0. Risk if declined: LEAFLET stays NOT_STARTED,
schematic map remains the only renderer.
