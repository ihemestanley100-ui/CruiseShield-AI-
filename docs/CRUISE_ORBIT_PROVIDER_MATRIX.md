# CRUISE ORBIT — Provider and API Integration Matrix

Date: 2026-11-03 · Evidence: primary pages inspected 11-03
(CelesTrak home, CDSE docs); aggregator snippets are discovery
only. Quotas subject to owner-account verification.

| Provider | Data | Access | Cost | Terms/notes | Feeds |
|---|---|---|---|---|---|
| CelesTrak | TLE/GP orbital elements (20k+ objects) | Free, no key (usage policy applies) | $0 | MUST use new GP formats for 6-digit catalog numbers (TLE capped at 5-digit since 2026-07-11 — inspected notice). Obey request-rate policy | ORBIT-03 |
| Copernicus CDSE | Sentinel-1/2/3 products; STAC/OData/S3/openEO APIs | Free account + access token | $0 (reported 10k req + 10k PU/mo, 300/min — VERIFY at signup) | Legal Notice on Sentinel use; attribution required | ORBIT-04/09/10 |
| USGS (Landsat/M2M/STAC) | Landsat C2 archive, STAC COGs | Free ERS account | $0 | Public domain (US federal); no license review | ORBIT-09/10 (archive depth) |
| AISStream | Live AIS vessel positions (websocket) | Free API key (reported; VERIFY) | $0 tier reported | Attribution; coastal receivers; key server-side only | ORBIT-07 |
| N2YO | Per-satellite lookups | Free tier ~1k/hr (reported; VERIFY) | $0 tier reported | Backup to CelesTrak only | ORBIT-03 (fallback) |
| Digitraffic (Finland) | Regional AIS | Free, no key (reported) | $0 | Regional coverage only — demo-safe example | ORBIT-07 (demo) |
| World Port Index / open port data | Port locations | Public sources (conditional) | $0 | Verify license per dataset before use | ORBIT-08 |
| Commercial AIS / VHR imagery (exactEarth, Spire, Maxar…) | Dense AIS, sub-meter imagery | Paid contracts | $$$ — BLOCKED under $0 | NOT selected; revisit only with budget approval | None |

Adapter architecture (mirrors `GeoProvider` + `ai_adapter.py`):
`OrbitProvider` Protocol (name, capabilities, fetch with
timeout/retry/caps) + `NullOrbitProvider` default (unknown,
zero network) + per-provider server-side clients. All keys in
env, never logged/persisted; provider outages degrade to
honest stale/unavailable states (never silent, never live).
New dependency: `sgp4` (propagation) — needs lock + license
audit at implementation.
