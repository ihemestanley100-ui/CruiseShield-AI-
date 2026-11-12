# CruiseShield AI™ — Universal Financial Crime Intelligence & Investigation OS™

**Status:** Core slice implemented in worktree (uncommitted). Backend verified by
automated tests; frontend written, execution pending hosted CI (sandbox node EPERM).
No live financial providers. No production deployment.

## 1. What this is

The universal layer unifies transaction, payment-method, party, institution,
typology, alert, tracing, crypto/gift/remittance, report, and industry
intelligence on top of the existing platform core. It reuses authentication,
tenancy, detection families, signals, graph, industry registry, evidence/audit,
and notifications. It creates no duplicate engines.

## 2. Modules (new)

| Module | Purpose |
|---|---|
| `app/payment_methods.py` | Canonical taxonomy (families A–I, 13 methods), traceability registry, `classify()`, `map_lifecycle()` |
| `app/institutions.py` | Network/rail registry (8 public-knowledge entries), status from connector registry |
| `app/parties.py` | 17 roles, masked extraction, conservative `resolve()` |
| `app/typologies.py` | 40 typologies mapped to real families/rules; gap-flagged |
| `app/alerts.py` | 8-state lifecycle over signals, idempotent open, real-row metrics |
| `app/tracing.py` | 8-strength link ladder, BFS trace builder, limitations |
| `app/altpayments.py` | Crypto/gift/remittance adapters; validation + honest capability doc |
| `app/reports.py` | 15 deterministic report types from evidence bundles; gaps explicit |

Extended: `app/store.py` (`fraud_alert_save`, `fraud_alerts`, `trace_save`,
`traces`), `app/main.py` (18 routes, 161 → 179), `frontend/lib/api.ts`
(UFI types + helpers incl. `patchJson`), investigation page wiring.

## 3. Honesty contracts

- Classification: provider-reported ids must exist in the registry; channel
  defaults are labelled `inferred-from-channel`; everything else is UNKNOWN.
- Lifecycle: unmapped provider statuses pass through verbatim (`mapped:false`).
- Institutions: networks/rails only; per-bank records withheld (no data);
  integration status resolves against the live connector registry.
- Parties: masked by default; reveal is write-gated and audited; exact
  authorized-identifier matches RESOLVE; shared signals only SUPPORT.
- Typologies: gap typologies match zero signals; mapping errors fail loudly.
- Alerts: open from tenant-visible signals only; illegal transitions raise.
- Tracing: cash legs end deterministic tracing; hop caps surface unknown
  downstream; no freeze/reverse/recover claims — ever.
- Alt payments: chain/issuer/provider lookups are PROVIDER_UNAVAILABLE;
  wallet attribution defaults to UNKNOWN_ENTITY; gift secrets rejected.
- Reports: missing sections render `not_available` gaps, never invented content.

## 4. API surface

Reads: `GET /api/v1/payment-methods{,/{id}}`, `GET /api/v1/payment-networks`,
`GET /api/v1/institutions`, `GET /api/v1/transactions/{id}/parties[?reveal=1]`,
`GET /api/v1/fraud/typologies[?industry=|/{id}]`,
`GET /api/v1/industries/{id}/typologies`, `GET /api/v1/fraud/alerts[?status=|/metrics|/{id}]`,
`GET /api/v1/tracing/{id}[/movements]`, `GET /api/v1/altpayments/capabilities`.

Writes (write-gated, audited, tenant-scoped): `POST /api/v1/fraud/alerts`,
`PATCH /api/v1/fraud/alerts/{id}`, `POST /api/v1/tracing/transactions`
(max_hops clamped 0–8), `POST /api/v1/reports` (bundle ≤ 40 keys).

## 5. Frontend

`TracingSection` (closed-by-default): fund-trace builder with verbatim
movements/evidence/limitations, masked party summary, typology browser with
gap flags. Wired into the investigation page. 5 vitest cases written;
execution pending hosted CI.

## 6. Verification

- `tests/test_universal_core.py`: 30 passed.
- `tests/test_universal_routes.py`: 9 passed (socket-free direct handlers).
- Full suite: 1242 passed / 141 skipped / same sandbox-only 1F+2E
  (node EPERM + 2× WinError 10013), unchanged pre-existing failures.
- Matrix: `python scripts/zero_gap_matrix.py --check` exit 0.

## 7. Coverage and limits

- 45-industry registry verified intact (no renames); per-industry typology
  cross-map served live; module statuses unchanged (evidence-gated).
- No live providers: UFI-LIVE is BLOCKED_EXTERNAL_DEPENDENCY.
- Agent-kernel intel tools (14 roles): NOT_STARTED, needs proposal + approval.
- Reused, not duplicated: detection families, signal APIs + outcomes,
  graph + provenance, industry registry + profiles, notify, web3 validators,
  tenancy, audit, evidence immutability.
- Free-tier: no new services, credentials, or billable usage. $0 held.

## 8. Slice 2 (2026-11-07): monitoring, transactions, adapters, security

New: app/monitoring.py (on-demand status + idempotent evaluate),
app/industry_adapters.py (45 configs + evidence readiness),
frontend monitoring-section + industry-section (+2 test files).
Extended: app/tracing.py (provenanced account-edge upgrades;
fixed inverted populate condition), app/main.py (+8 routes ->
187), api.ts (monitoring + industry helpers), network + platform
pages. Reuse decisions: intake stays POST /api/v1/events (no
POST /transactions dup); providers stay /api/v1/providers (no
payment-providers dup); ratelimit via global middleware.
Security: cross-tenant 404s, armed-write 401s, audited writes,
clamped paging, masked-by-default (tests/test_universal_
security.py 8/8). Slice-2 tests: 15 module/route + 8 security.
Frontend: 7 new vitest cases, unexecuted (node EPERM; D-017).

## 9. Slice 3 (2026-11-07): AI tools, fleet readiness, integration

New: app/intel_tools.py (trace.read, typology.match,
monitoring.status, industry.coverage, report.build -
read-only, tenant-checked, evidence-grounded). Extended:
app/agents.py (6->11 tools; grants to 9 of 12 manifests;
registry test count updated), app/industry_adapters.py
(fleet_readiness), app/tracing.py (related_investigations),
app/main.py (+1 route -> 188; reports assemble from
investigation). Fleet snapshot (live seed signals): 45
industries, 0 READY, 7 with measured typologies, 136
signals - evidence only, statuses untouched. Model-backed
generation stays NOT_STARTED (UFI-AIMODEL; owner
PII-processing approval required). Slice-3 tests: 9 AI +
6 integration + 2 contract parity. Frontend: fresh vitest
+ build attempt both fail sandbox node EPERM (reconfirmed);
contract parity test green as substitute static evidence.
