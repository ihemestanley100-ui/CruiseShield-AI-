# PHASE 15 — INTEGRATION ARCHITECTURE (design only — DO NOT CONNECT)

STATUS: DESIGNED, not built, not connected. Every connection below requires separate written institutional authorisation + security review. No integration code was added in this programme.

## Target systems (per institution need)
Core banking / payment processors / transaction-monitoring (alert feed in) / KYC + identity services / institutional AML case management (decisions/outcomes back) / fraud-intel + sanctions/watchlist sources (reference data in) / data warehouse (reporting extracts out).

## Contract pattern (per integration)
- Transport: mTLS or signed API keys over TLS; IP allowlists; per-client rate limits + quotas (closes D-001 at the edge).
- Auth: OAuth2 client-credentials or institution SSO (SAML/OIDC) for users; service accounts least-privilege (closes D-002).
- Ingest API: idempotency keys (first-wins, mirroring current `seen_event_ids` semantics), schema validation with 4xx envelopes (current `code/message/trace_id` shape), max body sizes (extends SEC-001 caps), async acknowledgement for bursts.
- Egress: signed webhooks with retry + dead-letter queue; reconciliation jobs (daily counts + hash spot-checks against source).
- Failure handling: circuit breakers, bounded retries with backoff (already the pattern for the Meta API path), safe degradation (queue + alert, never silent drop), replay from idempotent log.
- Data mapping: explicit field maps per source version; unknown-field policy = reject-with-reason (never coerce silently); PII fields tagged RESTRICTED at the boundary.
- Observability: structured logs (no PII/secrets), trace IDs end-to-end (current `_trace` pattern extended), latency/error/queue dashboards, tamper-evident audit sink (current audit log hardened: hash-chained or WORM-backed).

## Non-goals for pilot
No direct core-banking write access. No automated fund actions. No bulk PII export. No multi-tenant commingling (single-institution pilot database).
