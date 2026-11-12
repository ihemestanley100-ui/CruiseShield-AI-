# Cruise Global Identity & Geointelligence OS™

Implementation record for the master directive (matrix GEO/IDV/ADR/
MAP/PRV/GOV/SEC/AI/LIVE/LEAFLET/DOC rows). Status 2026-11-07:
backend CLOSED_VERIFIED (56 tests green), UI TESTING (written,
unexecuted — sandbox node EPERM, hosted CI pending), live
providers BLOCKED_EXTERNAL, tile binding NOT_STARTED.

## 0. Phase Zero baseline (2026-11-07)

Branch feat/phasezero-foundations @ d82627d; 426 working entries;
136 routes; 96 app modules; 138 backend test files; JSON doc-store
(data/state.json, no ORM — see §12 decision); roles
investigator/admin/auditor/demo_viewer + ABAC; CI = security-gate
+ 3 backup workflows (never observed green on hosted runners);
no map libraries; no lint configs. Backend baseline before
changes: 1147 passed / 141 skipped / same sandbox 1F+2E.

## 1. Reconciliation (what was reused, not duplicated)

| Capability | Existing | Reuse / decision |
|---|---|---|
| KYC tokens | app/verify.py (tokens, not identity) | new identity engine justified |
| Device intel | app/device_intel.py (thin DI-03) | extended with rel/obs endpoints; full Device spec still queued |
| Telecom | app/telecom_* (TEL-01..09) | reused; §11.2 alternate paths rejected |
| IP parsing/class | app/ip_intel.py DI-04 | extended in place |
| Geo contracts | app/geo_intel.py DI-05 | reused providers/validators; orchestrator named investigation_map.py to avoid confusion |
| Graph | 5 rel types + provenance | derived vocabulary capped at OBSERVED; no seed mutation |
| Evidence/audit | immutable packages + append_audit | reused; resolver is read-only; no POST /evidence by design |
| Auth/RBAC/ABAC/MFA | auth/abac/mfa/login_risk | reused; no second system |
| Consent | telecom_consents table | reused + extended fields (one system) |
| Connectors | 24-adapter lifecycle | +9 intel specs, same lifecycle |
| AI gateway | ai_gateway + inv ai endpoints | deterministic summaries only; model PII path NOT_STARTED |
| Notifications | notify.py log driver | reused (no new infra) |
| Background jobs | none in repo | none added; per-request timeouts; rollback = git + JSON |
| Analytics | none | derived live-count metrics only |

## 2. Architecture (§3 layers)

L1 UI: GeointelMap (schematic SVG, zero deps) + IdentitySection +
AddressSection + provider/coverage/metrics panels on
investigation + platform views. L2: 22 endpoints in app/main.py.
L3: deterministic summarize_evidence (no model). L4: JSON keys
identity/address/location/netgeo/authz (+shared telecom_consents).
L5: env-driven config, no migrations (JSON), no new jobs, rollback
via git. L6: _intel_reader/_intel_writer gates, tenant scoping,
HMAC pseudonyms, masked views, quotas, retention purge, audit.
L7: /geointel/metrics derived counts. L8: entitlements/billing
reused as-is (no new billing). L9: unified provider registry +
country coverage.

## 3. API contracts (§11, reconciled)

New: POST/GET /api/v1/identity/verifications(+list);
GET /devices/{id}/relationships|observations;
POST /api/v1/geolocation/ip/lookup; POST/GET
/geolocation/observations(+{id}); POST /api/v1/addresses/verify;
GET /addresses/verifications/{id}; GET /investigations/{id}/
map|locations|relationships; GET /providers(+{id}, +{id}/health);
GET /geointel/coverage|metrics; GET /evidence/{id};
POST/GET /intel/authorizations(+decide); POST
/intel/consents(+withdraw). NOT built: duplicate telecom paths
(existing stand), POST /evidence (immutability).

## 4. Data model + migration decision (§12)

Logical entities map 1:1 to JSON collections (§12.1/12.2/
12.4–12.9; devices stay derived — no intelligence_devices table
until the queued Device spec lands). No ORM exists; PostgreSQL is
scratch-only; PostGIS unjustified. DECISION PACKET: stay on the
JSON doc-store (cost $0, benefit: zero migration risk, risk:
no spatial indexes — mitigated: derived payloads serve current
scale; rollback: git revert). Revisit only with owner-approved
PG cutover (GAP-001).

## 5. Provider contracts + lifecycle (§10)

Adapters implement the connectors contract (capabilities,
config_params, secret_refs; loopback-only handshakes).
Lifecycle mapping DRAFT→DISCOVERED … CONNECTED→ACTIVE (ACTIVE
additionally requires an observed success). Failure policy:
per-request timeouts, no silent substitution (source always
labeled), quotas + 429, health passthrough. No circuit
breaker daemon (no job runner); consecutive-failure disabling
is a documented future row, not silently built.

## 6. Country coverage (§17)

7 assessed countries (NG/US/UK/FR/KE/ZW/ZA), all categories
PROVIDER_UNAVAILABLE, legal NOT_ASSESSED. All others
NOT_ASSESSED (implicit — never listed as covered).

## 7. Methodologies (§4.3, §7, §8, §9)

Identity: factor lists + missing + limitations; no numeric
score. IP: ESTIMATED-only, nulls for unknowns, IP≠address
limitations on every response. Address: structure ≠ proof;
geocode caps at UNVERIFIED; occupancy never claimed. Map:
schematic renderer; marker shapes differ by evidence class
(square verified/authorized, circle estimated, triangle
partial/telecom, hollow unverified); masked payloads carry
no coordinates.

## 8. Authorization, consent, privacy (§15)

Allowlisted purposes (§15.3) enforced on new engines;
authorization records (PENDING→APPROVED/REVOKED, admin
decides, country-specific basis strings, scope, expiry);
consent shared table + method/withdrawal; auditor masked,
viewer denied, armed-anonymous 401; tenant 404s; quotas;
90-day purge; masked+HMAC storage (raw identifiers to
nobody); every mutation audited. Jurisdiction review:
NOT_ASSESSED everywhere — legal signoff is an owner gate.

## 9. Security (§15, §19.7)

Threats/controls mirror TELECOM_IDENTITY.md §5 plus:
coordinate disclosure (role-tiered + masked views),
address harvesting (subject-scoped lists only, no bulk),
IP retention (masked+hash, TTL purge), evidence tamper
(sha256 + audit), SSRF (no server-side fetch of map tiles;
schematic renderer), XSS (React escaping + verbatim-state
rendering), IDOR (tenant enforce on every read).

## 10. Evidence, audit, retention (§13, §15.7, §21)

Records sealed (sha256, verified on read); reads evaluate
expiry (EXPIRED_EVIDENCE/EXPIRED/STALE views, stored bytes
immutable); audits capture who/org/investigation/purpose/
subject/masked result/decision; retention via
intel_purge_expired (service TTLs; platform schedule still
DATA-01).

## 11. Deployment (§20, free-tier)

New env: GEO_ACTOR_PER_MIN/GEO_SUBJECT_PER_DAY/
GEO_RETENTION_DAYS (values), MAP_PROVIDER (none),
CS_CONN_IDENTITY_KEY/ADDRESS/IPGEO/GEOCODE/LOCATION_SECRET
(sync:false, unset). No paid service touched; map is
dependency-free schematic; OSM/Leaflet binding explicitly
NOT_STARTED pending tile-policy + owner review. Quota
exhaustion → 429/UNAVAILABLE, never fabricated data.

## 12. Testing (§19)

Backend 56 green (identity 12, address 9, location 5, IP 5,
providers 6, map 6, API/security 13); regression: full suite
(post-change count recorded in LIVE_EVIDENCE_INDEX).
Frontend: 3 components + 8 vitest cases written, unexecuted
(node EPERM; D-017). Skips reported, never counted as passed.

## 13. Known limitations + owner gates (§23)

No live providers (LIVE-GEO blocked); no tile renderer
(LEAFLET NOT_STARTED); model-backed summaries NOT_STARTED
(PII-processing approval); legal review NOT_ASSESSED;
Device spec still queued (device endpoints derived-only);
hosted CI/deploy/smoke/rollback-drill all owner-gated
(PKG-01…07); NO production-readiness claim (§25 unmet).

## 14. Requirement map (§21/§24)

G01 Phase Zero: this §0 + matrix rows → CLOSED_VERIFIED.
G02 identity: IDV-01. G03 telecom: TEL rows (reused).
G04 device: derived endpoints (in SEC-GEO) + queued spec.
G05 IP: GEO-01. G06 location: GEO-02. G07 address: ADR-01.
G08 maps: MAP-01 (data) CLOSED, MAP-02 (UI) TESTING,
LEAFLET NOT_STARTED. G09 providers: PRV-01. G10 APIs:
SEC-GEO. G11 DB: §4 decision (in DOC-GEO). G12 graph:
MAP-01 relationships. G13 provenance: SEC-GEO. G14
auth: SEC-GEO. G15 privacy: SEC-GEO. G16 audit: SEC-GEO.
G17 screens: MAP-02 TESTING. G18 AI: AI-GEO (deterministic
closed; model NOT_STARTED). G19 coverage: PRV-01. G20
observability: metrics in SEC-GEO. G21 tests: §12. G22
security: SEC-GEO. G23 docs: DOC-GEO. G24 free-tier: §11.
G25/26/27: owner-gated (PKG-01…07). G28 evolution: §15.
Completion: backend 9/9 applicable rows closed; UI 0/1
executed; live 0/1; overall ≠ production-ready by §25.
