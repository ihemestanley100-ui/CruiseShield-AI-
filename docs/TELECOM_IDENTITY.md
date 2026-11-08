# Telecom Identity & Operator Verification Engine™

Canonical design + operating record for the telecom subsystem
(matrix TEL-01…TEL-09). Status 2026-11-07: backend
CLOSED_VERIFIED (58 tests green), UI TESTING (written,
unexecuted — sandbox node EPERM, hosted CI pending),
live integrations BLOCKED_EXTERNAL (TEL-08, no credentials).

## 1. Architecture

```
caller ──► FastAPI (app/main.py §telecom) ──► engine (telecom_verify.py)
              │                                  ├── registry (telecom_registry.py)
              │                                  ├── providers (telecom_providers.py)
              │                                  └── store (telecom_* methods)
              ├── guards: _require_write_token, role gate, ratelimit
              ├── tenant: _request_ctx + enforce_read/filter_visible
              └── audit: telecom.verify / telecom.consent / telecom.config.read
```

No new persistence engine, auth system, or connector lifecycle:
storage reuses `Store._save`, secrets reuse the connectors
`secret_refs` by-reference pattern, quotas reuse
`app/ratelimit.py`, lifecycle reuses the connection
DRAFT→…→CONNECTED state machine. New code is confined to three
`app/telecom_*` modules + store methods + endpoints.

## 2. API specification (delta)

| Method | Path | Gate | Notes |
|---|---|---|---|
| GET | /api/v1/telecom/operators?country= | open | registry v1.0, no PII |
| GET | /api/v1/telecom/operators/{id} | open | 404 UNKNOWN_OPERATOR |
| GET | /api/v1/telecom/numbers/parse?e164= | open | derived, never persisted |
| POST | /api/v1/telecom/verifications | write + role + quotas | persists masked+hash only |
| GET | /api/v1/telecom/verifications/{id} | tenant read | stale + integrity on read |
| GET | /api/v1/telecom/summary?subject=&phone_label= | tenant read | history + co-signals, no verdicts |
| POST | /api/v1/telecom/consents | write + role | audited |
| GET | /api/v1/admin/telecom-config | admin | audited read, no secrets |

Roles allowed for verification/consent writes: admin,
investigator, auditor. `demo_viewer` → 403 PERMISSION_DENIED.
Error codes: INVALID_E164, VERIFY_TYPE_UNKNOWN,
PURPOSE_REQUIRED, TELECOM_RATE_LIMITED (429),
UNKNOWN_OPERATOR / UNKNOWN_VERIFICATION (404, tenant-safe).

## 3. Data dictionary (delta)

- `telecom_verifications` (dict tvrf_NNNNNN → record): §4 fields —
  verification_id, subject_masked, subject_hash,
  operator_id/country, provider/provider_ref, api/api_version,
  verify_type, state/previous_state, confidence, source,
  verified_at/verified_ts, freshness_ttl_hours, limitations,
  consent_id, purpose, org, user, tenant_id, synthetic,
  evidence, record_hash. Raw E.164 is never a field.
- `telecom_consents` (dict tcon_NNNNNN → record): consent_id,
  subject_hash, subject_masked, purpose, org, granted_by,
  granted_at, expires_ts, revoked, tenant_id.
- `telecom_seq`: integer evidence counter.
- Registry (code, not state): 13 operators, `registry_version`
  1.0, per-record provenance + per-API availability.

## 4. Integration registry (delta)

Adapters (all NOT_CONNECTED, none LIVE): camara-number-verification,
camara-sim-swap, camara-device-swap, camara-kyc-match,
camara-number-recycling, camara-device-identifier,
mtn-sim-verification, hlr-lookup. Secrets by env-var reference
only: CS_CONN_CAMARA_SECRET, CS_CONN_MTN_KEY, CS_CONN_HLR_KEY.
MTN-only API is NOT_APPLICABLE on non-MTN operators.
Test double: TelecomHarness behind CONNECTED loopback only,
synthetic-labeled, tenant-scoped, fault-injectable.

## 5. Threat model (delta)

| Threat | Control | Test |
|---|---|---|
| PII disclosure (E.164) | never persisted/returned; masked+hash | test_raw_e164_never_persisted |
| Unauthorized lookup | role gate; viewer 403; tenant 404 | security/contract suites |
| Consent bypass (KYC/ownership) | ALWAYS_CONSENT + expiry + global mode | consent tests |
| Quota abuse / enumeration | actor 30/min + subject 20/day | 429 tests |
| Stale verdict reuse | TTL per type; STALE on read; stored immutable | stale tests |
| Fake-live provider | CONNECTED+success required; harness synthetic | providers suite |
| Evidence tampering | sha256 record_hash verified on read + audit | mismatch test |
| Secret leak | refs only; redact(); presence-not-value API | registry/config tests |
| Replay of consent | expiry + purpose binding; revoke flag | consent tests |

Residual: boot-random subject key in open mode loses
cross-restart correlation (fail-safe, documented); full HMAC
audit-chain sealing follows the D-018 ceremony like audits.

## 6. Privacy assessment (delta)

Lawful basis: per-request `purpose` (1–200 chars, mandatory,
audited) + explicit consent records for KYC/ownership (and all
types when TELECOM_CONSENT_REQUIRED=1). Minimization: masked
display + HMAC hash; provider raw payloads mapped to
result+ref then dropped. Retention: TELECOM_RETENTION_DAYS
(default 90) enforced by `telecom_purge_expired`
(service-scoped; DATA-01 still governs platform-wide
retention). Access: tenant isolation + role gate; raw
identifiers are available to nobody (not stored). No
hardware identifiers collected; no covert tracking (all
lookups are investigator-initiated, purpose-bound, audited).

## 7. Deployment & runbook (delta)

Env (see .env.example + render.yaml): TELECOM_CONSENT_REQUIRED
(default 0), TELECOM_RETENTION_DAYS (90),
TELECOM_ACTOR_PER_MIN (30), TELECOM_SUBJECT_PER_DAY (20);
provider secrets CS_CONN_CAMARA_SECRET / CS_CONN_MTN_KEY /
CS_CONN_HLR_KEY (sync:false, unset = all NOT_CONNECTED).
Operate: configure thresholds → create connection (DRAFT→…)
→ credentials → verify handshake → sandbox requests →
evidence in LIVE_EVIDENCE_INDEX → mark LIVE (TEL-08).
Purge: call `telecom_purge_expired(now - retention)` from the
retention job once DATA-01 authorizes the schedule.
Incidents: PROVIDER_ERROR spike → inspect provider_status;
429 spike → review quotas; integrity MISMATCH → freeze
record, escalate (evidence tamper).

## 8. Evidence & provenance

Backend: 58 tests green (registry 11, engine 20, providers 8,
contracts 10, security 9) + connectors 13 + gates green —
`pytest tests/test_telecom_*.py tests/test_connectors.py
tests/test_quality_gates.py tests/test_di03_device.py` →
88 passed, 2026-11-07. Frontend: telecom-section.tsx +
6 vitest cases written; unexecuted (sandbox node EPERM;
hosted CI per D-017). No live provider evidence exists;
TEL-08 stays BLOCKED_EXTERNAL. Matrix: TEL-01…TEL-09 in
scripts/zero_gap_matrix.py; `zero_gap_matrix.py --check`
exit 0.
