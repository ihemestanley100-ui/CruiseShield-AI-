# PHASE 15 — DATA GOVERNANCE FRAMEWORK

SCOPE: requirements for any pilot handling non-synthetic data. NO real customer data has been imported; none may be without owner + institutional + legal approvals and the agreements below.

## Principles
1. Lawful basis first: pilot data flows only under signed data-sharing/processing agreements naming purposes, retention, and return/destruction.
2. Minimisation: ingest only fields the use case needs; drop or tokenise direct identifiers where analysis permits.
3. Classification: PUBLIC (marketing) / INTERNAL (runbooks) / CONFIDENTIAL (investigation content, model keys) / RESTRICTED (customer PII, STR material). Current repo holds PUBLIC+INTERNAL only.
4. Retention/deletion: schedule per LQ-02; cryptographic deletion procedure for backups; no silent persistence of demo data into pilot stores.
5. Encryption: TLS 1.2+ in transit; AES-256-GCM-class at rest (keys in a managed KMS/HSM, never in repo/env files); the existing backup crypto design (P1/P2) is a starting point, not a certified control.
6. Access: authenticated, role-based, least-privilege; every read of RESTRICTED data audit-logged (extends current audit log with viewer identity — D-002 dependency).
7. Privacy: DPIA before pilot (LQ-01); data-subject rights procedure (access/correction/deletion) owned by the institution; no model training on customer data without explicit consent + agreement terms.
8. Incident response: suspected breach → contain, notify institution DPO + owner within agreed clocks (LQ-06), preserve forensic copies, post-incident review. Current product has no breach-detection instrumentation — a pilot gap.

## Data-flow map (pilot, to be validated with the institution)
Source systems → authenticated ingest API (validated, rate-limited) → case store (encrypted) → risk engine (versioned, deterministic) → evidence packages → Meta Model API (transfer-governed, logged, no training) → AI explanations (validated, advisory-only) → human decision → audit record (tamper-evident) → retention/deletion.
Each arrow needs: contract basis, encryption state, logging, and owner.

## Prohibitions (carry forward from demo governance)
No real-data imports without written authorisation. No AI-authored guilt determinations, fund freezes, or punitive actions — ever. No secrets in code/logs/docs. No silent score changes.
