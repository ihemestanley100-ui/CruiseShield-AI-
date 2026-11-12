# REMAINING 40 — EXTERNAL DEPENDENCY REGISTER

2026-11-08 @ d82627d. Live connections stay DISABLED (NO-LIVE).
No handshake fabricated; all provider rows show ZERO HANDSHAKES.

## P1. Meta AI model lane (AI-01, AI-03, UFI-AIMODEL)

- Provider/capability: Meta API chat/completions for analysis +
  agent planning + PII-lane generation.
- Free option: UNVERIFIED — needs quota/allowance proof + PKG-04.
- Required: named model, API key (owner-entered), quota + cost
  caps, PII redaction rule (D-054), data-flow note, eval set.
- Verification: authenticated call → recorded run + approval +
  audit; deterministic engine stays authoritative until then.
- Adapter: app/ai_adapter.py (mock-transport only). Status: NO-LIVE.

## P2. Telecom CAMARA/MTN/HLR (TEL-08)

- Provider/capability: number verification, SIM/device swap, KYC.
- Free option: none identified (operator agreements required).
- Required: per-operator agreement + creds, consent workflow,
  TELECOM_* thresholds (already configured).
- Verification: sandbox handshake → green requests + evidence log.
- Adapter: exists. Status: NO-LIVE (D-053).

## P3. Identity/address/geo/map intel (LIVE-GEO, LEAFLET)

- Provider/capability: identity, address, IP-geo, geocode,
  location, map tiles.
- Free option: OSM tiles within policy (D-055 pending); other
  providers UNVERIFIED.
- Required: per-provider keys, MAP_PROVIDER decision, privacy review.
- Verification: handshake + quota/error handling + provenance.
- Adapter: exists (schematic ships). Status: NO-LIVE (D-053).

## P4. Financial rails (UFI-LIVE)

- Provider/capability: banks, NIP, POS, cards, mobile, crypto.
- Free option: none (institutional agreements required).
- Required: agreements + certs/keys per rail (CS_CONN_* all unset).
- Verification: sandbox → green requests + settlement proof.
- Adapter: exists. Status: NO-LIVE (D-053).

## P5. Native translators (I18N-02) — owner action

- Need: 11 locales × 17 detection.* keys (+ ar extras triage).
- Pack ready: docs/I18N_NATIVE_REVIEW_PACK.md. Cost: owner-arranged.
- Verification: per-locale sign-off + merged dictionaries + vitest.

## P6. Reference image (VIS-01) — owner action

- Need: exact original image attached to THIS Muse session
  (currently only in ChatGPT conversation).
- Verification: diff register + corrections + real screenshots.

## P7. Hosted PostgreSQL (GAP-001/DB-01/DET-03)

- Need: free-tier PG with PG15+ + 90d+ retention for cutover.
- Free option: UNVERIFIED — Neon/Render/supabase limits must be
  checked against quota, card, expiry, commercial-use terms.
- Required: connection URL (owner-provisioned), parity + rollback.
- Verification: live PG + parity report + rollback drill.

## P8. GitHub Actions + hosting free tiers (DET-13/14, INF-01)

- Need: Actions minutes/quota, Render/Netlify bandwidth/storage/
  overage/card terms — the 7 PKG-05 readings.
- Status: readings pending (owner supplies).

## Reopen rule

Any NO-LIVE/DEFER item reopens ONLY via a new explicit owner
decision + credentials + successful authenticated handshake,
recorded per provider. Preparation above is not permission.
