# WORLD ATLAS — SECURITY, PRIVACY & GOVERNANCE

Date: 2026-11-03 · Binding on all atlas phases.

## 1. Access control

Atlas inherits session auth + 4-role RBAC. Read layers:
any authenticated user. Evidence links: `write`.
Purge/admin: `admin`. Every denial is backend-enforced
(never UI-only) and audited.

## 2. Credentials

Provider keys in server env only, never in bundle,
URL, logs or error bodies. `GET /layers` exposes
availability, never key presence details. No atlas
secret may enter Git (secret-scan gate per phase).

## 3. Privacy red lines

- No user GPS collection; no precise-individual
  location storage (see Data Model §5).
- IP-derived positions are APPROXIMATE and labelled;
  never used as proof of presence.
- Coverage ≠ location: satcom data must never imply a
  user's physical position (mandatory UI disclaimer).
- Aggregation minimums: clusters only below
  country-pair granularity for flows; no single-txn
  pins with PII.

## 4. Retention + audit

Observation cache TTL 24h/7d max; purge is audited.
Evidence links are append-only and hash-chained with
their package. Atlas reads of sensitive overlays are
audit-logged (who/what/when, no payload secrets).

## 5. Licensing

- Code/data deps: three (MIT), world-atlas (MIT),
  topojson-client (ISC) — commercial-safe, no
  attribution burden beyond notices.
- OSM-derived context (if ever used): ODbL —
  attribution + share-alike on the DATA; isolate from
  proprietary layers.
- Imagery/observation licences per provider (Track A):
  stored per item; UI shows licence + terms URL.
- `sgp4` (if TLE approved): audit license + vulns
  before install; no silent adds.

## 6. CSP + network

Phase 1–4 need NO CSP change (same-origin API +
bundled data). Any future external tile/imagery host
requires an explicit CSP amendment review + owner
approval. `connect-src` stays minimal by default.

## 7. AI + risk governance (unchanged)

Deterministic scores authoritative; atlas never
recomputes risk client-side; AI explains supplied
items only; humans decide; correlation ≠ proof —
mandatory caption on cross-border views.
