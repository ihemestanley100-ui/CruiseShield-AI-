# CRUISE ORBIT — Live Integration Verification Plan

Date: 2026-11-03 · No live calls made in this audit. Every
provider graduates through these steps before ANY live claim.

Per provider (CelesTrak → CDSE → USGS → AISStream → N2YO):

1. ACCOUNT: owner creates account/key (where required); key
   stored in env only. Record capability + quota IN WRITING.
2. PING: one approved request (e.g., CelesTrak stations set /
   CDSE token + one STAC query). Capture raw response (no creds).
3. CONTRACT: response validates against the adapter schema;
   failures produce honest codes (TIMEOUT/QUOTA/MALFORMED).
4. FRESHNESS: retrieved timestamps flow into badges; stale
   fixture renders stale (never LIVE).
5. FROZEN FIXTURE: sanitize one real response into a mock
   fixture; hermetic tests run offline thereafter.
6. UI PROOF: screenshot + DOM capture showing attributed data
   with source/time/confidence/limitations visible.
7. QUOTA LOG: usage vs allowance recorded; alerts on 80%.

Graduation rule: a provider is "LIVE" only after 1–7 with
evidence retained. Until then its UI shows honest
unavailable/synthetic states. No bulk polling before quota
math is proven; no keep-alive hacks on Free hosting.
