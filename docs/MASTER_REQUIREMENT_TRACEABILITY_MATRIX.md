# MASTER REQUIREMENT TRACEABILITY MATRIX

Generated 2026-11-08 from docs/ZERO_GAP_MATRIX.json (matrix untouched). 192 rows.

| ID | Canonical status | Implementation | Test | Evidence | Campaign |
|---|---|---|---|---|---|
| ABAC-01 | CLOSED_VERIFIED | app/abac.py | tests/test_abac.py | 8 tests green; deny-by-default; tenant+hold+sensitivity | - |
| ADR-01 | CLOSED_VERIFIED | app/address_verify.py | tests/test_geointel_address.py | 9 tests green; structure!=proof; geocode caps UNVERIFIED; role-tiered  | - |
| AGENT-01 | CLOSED_VERIFIED | app/agents.py | tests/test_agents.py | 9 tests green; 12 manifests; 6 read-only real tools; approval | - |
| AGOS-CONV | CLOSED_VERIFIED | app/conversations.py app/store.py | tests/test_agent_os.py tests/test_agent_os_routes.py | tenant+owner scope; credential redaction; 90-day expiry + purge | - |
| AGOS-DOC | CLOSED_VERIFIED | docs/AGENT_OS.md | tests/test_agent_os.py | reuse matrix + A01-A20 mapping + approvals + threat model + degraded m | - |
| AGOS-IND | CLOSED_VERIFIED | app/industry_adapters.py | tests/test_agent_os.py | all 45 resolve; shared runtime; terminology only from profiles (none i | - |
| AGOS-NL | CLOSED_VERIFIED | app/nl_search.py | tests/test_agent_os.py tests/test_agent_os_routes.py | amount/currency/date/channel/ref parsing; clarification on ambiguity;  | - |
| AGOS-ORCH | CLOSED_VERIFIED | app/orchestration.py app/store.py | tests/test_agent_os.py tests/test_agent_os_routes.py | 11-state lifecycle; 8 intents; pipelines depth<=2; 8-call budget; resu | - |
| AGOS-RAG | CLOSED_VERIFIED | app/agent_retrieval.py | tests/test_agent_os.py tests/test_agent_os_routes.py | keyword+structured over 5 sources; attribution + freshness; embeddings | - |
| AGOS-TOOLS | CLOSED_VERIFIED | app/intel_tools.py app/agents.py | tests/test_agent_os.py tests/test_agents.py | 13 tools; masked accounts; writes only on approval-gated manifests; re | - |
| AGOS-UI | TESTING | frontend/components/assistant-shell.tsx frontend/lib/api.ts frontend/a | frontend/components/assistant-shell.test.tsx | 1 reusable shell + 3 tests written; verbatim states; no executed run ( | EVIDENCE_READY |
| AI-01 | BLOCKED_EXTERNAL_DEPENDENCY | app/ai_adapter.py | tests/test_ai_eval.py tests/test_ai_validation.py tests/test_ai_cost.p | mock-transport only; PKG-04 NO-LIVE recorded 2026-11-07 (D-016); local | BLOCKED_OWNER_APPROVAL |
| AI-02 | CLOSED_VERIFIED | app/ai_gateway.py app/main.py app/config.py | tests/test_ai_gateway.py | 13 tests green; meta registered; 2nd lane addable (test double); fallb | - |
| AI-03 | BLOCKED_EXTERNAL_DEPENDENCY |  |  | none — caller-specified per D-026 | BLOCKED_OWNER_APPROVAL |
| AI-GEO | CLOSED_VERIFIED | app/investigation_map.py | tests/test_geointel_map.py | discrepancy/uncertainty/missing covered; model_used null; model path N | - |
| AUD-01 | IN_PROGRESS | app/audit_chain.py app/store.py migrations/loader.py | tests/test_audit_chain.py tests/test_audit_store.py tests/test_loader_ | chain/store/CLI-keyring tests green; D-018 TEST DRILL ONLY 2026-11-07  | IN_PROGRESS |
| AUD-02 | CLOSED_VERIFIED | app/audit_chain.py scripts/audit_export.py | tests/test_audit_export.py | 10 CLI/report tests green; key-safe output asserted | - |
| AUD-03 | CLOSED_VERIFIED | app/main.py | tests/test_ingest_audit.py | event.ingested audit (accepted+duplicate) + 4 tests green | - |
| AUD-04 | CLOSED_VERIFIED | app/main.py | tests/test_ingest_audit.py | presence check (counts only, exempt) + 3 tests green | - |
| AUTH-01 | NOT_STARTED |  |  | planned; awaits go + PKG-09 (no OAuth app/creds) | BLOCKED_OWNER_APPROVAL |
| AUTH-02 | NOT_STARTED |  |  | planned; awaits go + PKG-09 (no OAuth app/creds) | BLOCKED_OWNER_APPROVAL |
| AUTH-03 | NOT_STARTED |  |  | planned; awaits go + PKG-09 (no OAuth app/creds) | BLOCKED_OWNER_APPROVAL |
| AUTH-04 | NOT_STARTED |  |  | planned; awaits go + PKG-09 (no OAuth app/creds) | BLOCKED_OWNER_APPROVAL |
| AUTH-05 | NOT_STARTED |  |  | planned; awaits go + PKG-09 (delivery stays blocked) | BLOCKED_OWNER_APPROVAL |
| AUTH-06 | NOT_STARTED |  |  | planned; awaits go + PKG-09 (delivery stays blocked) | BLOCKED_OWNER_APPROVAL |
| AUTH-07 | NOT_STARTED |  |  | planned; awaits go + PKG-09 (no IdP metadata) | BLOCKED_OWNER_APPROVAL |
| AUTH-08 | NOT_STARTED |  |  | planned; awaits go + PKG-09 | BLOCKED_OWNER_APPROVAL |
| AUTH-09 | NOT_STARTED |  |  | no reset flow exists; delivery stays blocked | BLOCKED_OWNER_APPROVAL |
| AUTH-ACCOUNT | CLOSED_VERIFIED | app/store.py app/main.py app/login_risk.py | tests/test_account_security.py | 7 tests green; nonce-revoke+epoch/drop/registry/prefs-locked | - |
| AUTH-REG | CLOSED_VERIFIED | app/accounts.py app/store.py app/main.py | tests/test_accounts.py | 9 tests green; overlay/admin/flag-off/throttle/audit | - |
| AUTH-VERIFY | CLOSED_VERIFIED | app/verify.py app/store.py app/main.py | tests/test_verify.py | 10 tests green; single-use/session-bound/audit; no delivery | - |
| BAK-01 | IN_PROGRESS | backups/local_target.py | tests/test_local_target.py scripts/backup_drill.py | scratch drill parity PASS (re-verified 2026-11-07: verified/signature/ | IN_PROGRESS |
| CAP-01 | CLOSED_VERIFIED | app/capabilities.py | tests/test_capabilities.py | 4 tests green; 8 HAVE/6 PARTIAL/1 MISSING, refs resolve | - |
| CASE-01 | CLOSED_VERIFIED | app/cases.py app/main.py | tests/test_cases_create.py | POST /cases + 6 tests; bounds/tenant/audit green | - |
| CICD-01 | AWAITING_OWNER_APPROVAL | docs/COVERAGE_LOCK_PREP.md |  | pins prepared; D-020 APPROVED IN PRINCIPLE 2026-11-07, execution needs | BLOCKED_OWNER_APPROVAL |
| CONN-01 | CLOSED_VERIFIED | app/connectors.py | tests/test_connectors.py | 13 tests green; secrets-by-reference; honest FAILED states | - |
| DATA-01 | AWAITING_OWNER_APPROVAL |  |  | none - tracker-only; no purge code; D-056 DEFERRED 2026-11-07 | BLOCKED_OWNER_APPROVAL |
| DB-01 | AWAITING_OWNER_APPROVAL | app/db.py | tests/test_pg_migration.py tests/test_pg_parity.py tests/test_pg_atomi | scratch parity only; GAP-001 HOLD confirmed 2026-11-07 | BLOCKED_OWNER_APPROVAL |
| DET-01 | CLOSED_VERIFIED | app/detection.py | tests/test_detection.py tests/test_detect_tranche_s09_s12.py tests/test_detect_r011_mule.py | registry test 14 families | - |
| DET-02 | CLOSED_VERIFIED | app/channels.py | tests/test_detection.py | taxonomy mapping test | - |
| DET-03 | IN_PROGRESS | app/store.py | tests/test_detection.py | outcome/link history tests; events derived per D-021; GAP-001 HOLD con | BLOCKED_OWNER_APPROVAL |
| DET-04 | CLOSED_VERIFIED | app/detection.py | tests/test_detection.py | reconciliation + bucket tests | - |
| DET-05 | CLOSED_VERIFIED | app/channels.py | tests/test_detection.py | channel summary test | - |
| DET-06 | CLOSED_VERIFIED | app/main.py | tests/test_detection.py | 88-cell honest-status test | - |
| DET-07 | CLOSED_VERIFIED | app/tenancy.py | tests/test_detection.py | foreign-read 404 tests (6 endpoints) | - |
| DET-08 | CLOSED_VERIFIED | app/main.py | tests/test_detection.py | chain + consistency tests | - |
| DET-09 | CLOSED_VERIFIED | app/store.py | tests/test_detection.py | idempotent link + audit tests | - |
| DET-10 | CLOSED_VERIFIED | app/store.py | tests/test_detection.py | outcome/link audit-entry tests | - |
| DET-11 | CLOSED_VERIFIED |  | tests/test_detection.py | 34 passed + 4 socket-gated | - |
| DET-12 | BLOCKED_EXTERNAL_DEPENDENCY |  | frontend/components/detection-panels.test.tsx | sandbox node EPERM (3 paths proven); PKG-01 DEFERRED 2026-11-07 - no h | EVIDENCE_READY |
| DET-13 | AWAITING_OWNER_APPROVAL | .github/workflows/security-gate.yml |  | PKG-01 DEFERRED 2026-11-07; push unauthorized | EVIDENCE_READY |
| DET-14 | AWAITING_OWNER_APPROVAL | render.yaml netlify.toml |  | GAP-009; PKG-01 DEFERRED 2026-11-07 (CI first) | BLOCKED_OWNER_APPROVAL |
| DET-15 | CLOSED_VERIFIED | app/detection.py app/channels.py | tests/test_detection.py | zero/SEED_FEED/NOT_IMPLEMENTED asserts | - |
| DET-16 | CLOSED_VERIFIED | app/detection.py | tests/test_detection.py | INPUT skip + fault test green; valid inputs unchanged | - |
| DOC-GEO | CLOSED_VERIFIED | docs/GEOINTELLIGENCE_OS.md | tests/test_geointel_api.py | doc + manifest/index/exec-state/env/render updated | - |
| EVD-01 | CLOSED_VERIFIED | scripts/evidence_manifest.py docs/EVIDENCE_MANIFEST.json | tests/test_evidence_manifest.py | manifest verifies; tripwire test green | - |
| EVID-01 | CLOSED_VERIFIED | app/evidence.py | tests/test_evidence_export.py | canonical bytes + sha256 header + 4 tests green | - |
| FE-01 | AWAITING_OWNER_APPROVAL |  |  | suites exist; PKG-01 DEFERRED 2026-11-07 - no CI run | EVIDENCE_READY |
| GEO-01 | CLOSED_VERIFIED | app/ip_intel.py | tests/test_geointel_ip.py | 5 tests green; INVALID/NOT_APPLICABLE fenced; null-shape honest; maske | - |
| GEO-02 | CLOSED_VERIFIED | app/location_obs.py | tests/test_geointel_location.py | 5 tests green; allowlisted sources; authz+consent gates; unknown accur | - |
| GOV-01 | CLOSED_VERIFIED | app/governance.py | tests/test_governance.py | 6 tests green; separation of duties; hold blocks close | - |
| GOV-02 | CLOSED_VERIFIED | app/intel_auth.py | tests/test_geointel_api.py | lifecycle + withdraw + expiry covered; one consent system (telecom tab | - |
| I18N-01 | CLOSED_VERIFIED | frontend/lib/i18n/locales |  | 12/12 locales + 11 TSVs zero demo residue | - |
| I18N-02 | BLOCKED_EXTERNAL_DEPENDENCY | docs/UGLS_REVIEW_KIT |  | kit rows fallback-marked, review pending; stdin parity 2026-11-07: 17  | BLOCKED_EXTERNAL_DEPENDENCY |
| IDV-01 | CLOSED_VERIFIED | app/identity_verify.py | tests/test_geointel_identity.py | 12 tests green; factor-based (no score); provider-only UNAVAILABLE; no | - |
| IND-accounting | CLOSED_VERIFIED | app/industries_accounting.py | tests/test_industry_accounting.py | profile + 7 mapping tests green; tests/test_industry_accounting.py | - |
| IND-agriculture | CLOSED_VERIFIED | app/industries_agriculture.py | tests/test_industry_agriculture.py | profile + 7 mapping tests green; tests/test_industry_agriculture.py | - |
| IND-automotive | CLOSED_VERIFIED | app/industries_automotive.py | tests/test_industry_automotive.py | profile + 7 mapping tests green; tests/test_industry_automotive.py | - |
| IND-aviation | CLOSED_VERIFIED | app/industries_aviation.py | tests/test_industry_aviation.py | profile + 7 mapping tests green; tests/test_industry_aviation.py | - |
| IND-banking | CLOSED_VERIFIED | app/industries_banking.py | tests/test_industry_banking.py | profile + 7 mapping tests green; tests/test_industry_banking.py | - |
| IND-capital-markets | CLOSED_VERIFIED | app/industries_capital_markets.py | tests/test_industry_capital_markets.py | profile + 7 mapping tests green; tests/test_industry_capital_markets.p | - |
| IND-charities | CLOSED_VERIFIED | app/industries_charities.py | tests/test_industry_charities.py | profile + 7 mapping tests green; tests/test_industry_charities.py | - |
| IND-construction | CLOSED_VERIFIED | app/industries_construction.py | tests/test_industry_construction.py | profile + 7 mapping tests green; tests/test_industry_construction.py | - |
| IND-consulting | CLOSED_VERIFIED | app/industries_consulting.py | tests/test_industry_consulting.py | profile + 7 mapping tests green; tests/test_industry_consulting.py | - |
| IND-crypto-assets | CLOSED_VERIFIED | app/industries_crypto.py | tests/test_industry_crypto.py | profile + 7 mapping tests green; tests/test_industry_crypto.py | - |
| IND-customs-border | CLOSED_VERIFIED | app/industries_customs.py | tests/test_industry_customs.py | profile + 7 mapping tests green; tests/test_industry_customs.py | - |
| IND-defence-security | CLOSED_VERIFIED | app/industries_defence.py | tests/test_industry_defence.py | profile + 7 mapping tests green; tests/test_industry_defence.py | - |
| IND-ecommerce | CLOSED_VERIFIED | app/industries_ecommerce.py | tests/test_industry_ecommerce.py | profile + 7 mapping tests green; tests/test_industry_ecommerce.py | - |
| IND-education | CLOSED_VERIFIED | app/industries_education.py | tests/test_industry_education.py | profile + 7 mapping tests green; tests/test_industry_education.py | - |
| IND-energy-utilities | CLOSED_VERIFIED | app/industries_energy.py | tests/test_industry_energy.py | profile + 7 mapping tests green; tests/test_industry_energy.py | - |
| IND-environmental | CLOSED_VERIFIED | app/industries_environment.py | tests/test_industry_environment.py | profile + 7 mapping tests green; tests/test_industry_environment.py | - |
| IND-fintech-payments | CLOSED_VERIFIED | app/industries_fintech.py | tests/test_industry_fintech.py | profile + 7 mapping tests green; tests/test_industry_fintech.py | - |
| IND-fx-remittance | CLOSED_VERIFIED | app/industries_fx.py | tests/test_industry_fx.py | profile + 7 mapping tests green; tests/test_industry_fx.py | - |
| IND-gambling | CLOSED_VERIFIED | app/industries_gambling.py | tests/test_industry_gambling.py | profile + 7 mapping tests green; tests/test_industry_gambling.py | - |
| IND-gaming-esports | CLOSED_VERIFIED | app/industries_gaming.py | tests/test_industry_gaming.py | profile + 7 mapping tests green; tests/test_industry_gaming.py | - |
| IND-government | CLOSED_VERIFIED | app/industries_government.py | tests/test_industry_government.py | profile + 7 mapping tests green; tests/test_industry_government.py | - |
| IND-healthcare | CLOSED_VERIFIED | app/industries_healthcare.py | tests/test_industry_healthcare.py | profile + 7 mapping tests green; tests/test_industry_healthcare.py | - |
| IND-hospitality | CLOSED_VERIFIED | app/industries_hospitality.py | tests/test_industry_hospitality.py | profile + 7 mapping tests green; tests/test_industry_hospitality.py | - |
| IND-import-export | CLOSED_VERIFIED | app/industries_trade.py | tests/test_industry_trade.py | profile + 7 mapping tests green; tests/test_industry_trade.py | - |
| IND-insurance-pensions | CLOSED_VERIFIED | app/industries_insurance.py | tests/test_industry_insurance.py | profile + 7 mapping tests green; tests/test_industry_insurance.py | - |
| IND-law-enforcement | CLOSED_VERIFIED | app/industries_law.py | tests/test_industry_law.py | profile + 7 mapping tests green; tests/test_industry_law.py | - |
| IND-legal | CLOSED_VERIFIED | app/industries_legal.py | tests/test_industry_legal.py | profile + 7 mapping tests green; tests/test_industry_legal.py | - |
| IND-luxury-goods | CLOSED_VERIFIED | app/industries_luxury.py | tests/test_industry_luxury.py | profile + 7 mapping tests green; tests/test_industry_luxury.py | - |
| IND-manufacturing | CLOSED_VERIFIED | app/industries_manufacturing.py | tests/test_industry_manufacturing.py | profile + 7 mapping tests green; tests/test_industry_manufacturing.py | - |
| IND-maritime | CLOSED_VERIFIED | app/industries_maritime.py | tests/test_industry_maritime.py | profile + 7 mapping tests green; tests/test_industry_maritime.py | - |
| IND-media | CLOSED_VERIFIED | app/industries_media.py | tests/test_industry_media.py | profile + 7 mapping tests green; tests/test_industry_media.py | - |
| IND-mining-resources | CLOSED_VERIFIED | app/industries_mining.py | tests/test_industry_mining.py | profile + 7 mapping tests green; tests/test_industry_mining.py | - |
| IND-ngo | CLOSED_VERIFIED | app/industries_ngo.py | tests/test_industry_ngo.py | profile + 7 mapping tests green; tests/test_industry_ngo.py | - |
| IND-oil-gas | CLOSED_VERIFIED | app/industries_oilgas.py | tests/test_industry_oilgas.py | profile + 7 mapping tests green; tests/test_industry_oilgas.py | - |
| IND-pharma-biotech | CLOSED_VERIFIED | app/industries_pharma.py | tests/test_industry_pharma.py | profile + 7 mapping tests green; tests/test_industry_pharma.py | - |
| IND-procurement-infra | CLOSED_VERIFIED | app/industries_procurement.py | tests/test_industry_procurement.py | profile + 7 mapping tests green; tests/test_industry_procurement.py | - |
| IND-real-estate | CLOSED_VERIFIED | app/industries_property.py | tests/test_industry_property.py | profile + 7 mapping tests green; tests/test_industry_property.py | - |
| IND-retail | CLOSED_VERIFIED | app/industries_retail.py | tests/test_industry_retail.py | profile + 7 mapping tests green; tests/test_industry_retail.py | - |
| IND-social-platforms | CLOSED_VERIFIED | app/industries_social.py | tests/test_industry_social.py | profile + 7 mapping tests green; tests/test_industry_social.py | - |
| IND-supply-chain | CLOSED_VERIFIED | app/industries_supply.py | tests/test_industry_supply.py | profile + 7 mapping tests green; tests/test_industry_supply.py | - |
| IND-tax-revenue | CLOSED_VERIFIED | app/industries_tax.py | tests/test_industry_tax.py | profile + 7 mapping tests green; tests/test_industry_tax.py | - |
| IND-technology | CLOSED_VERIFIED | app/industries_technology.py | tests/test_industry_technology.py | profile + 7 mapping tests green; tests/test_industry_technology.py | - |
| IND-telecom | CLOSED_VERIFIED | app/industries_telecom.py | tests/test_industry_telecom.py | profile + 7 mapping tests green; tests/test_industry_telecom.py | - |
| IND-transport | CLOSED_VERIFIED | app/industries_transport.py | tests/test_industry_transport.py | profile + 7 mapping tests green; tests/test_industry_transport.py | - |
| IND-wholesale | CLOSED_VERIFIED | app/industries_wholesale.py | tests/test_industry_wholesale.py | profile + 7 mapping tests green; tests/test_industry_wholesale.py | - |
| INF-01 | AWAITING_OWNER_APPROVAL |  |  | configs written, never executed; PKG-01 DEFERRED | BLOCKED_OWNER_APPROVAL |
| LEAFLET | NOT_STARTED |  |  | schematic ships; policy REVIEWED 2026-11-07 (docs/LEAFLET_TILE_POLICY_ | BLOCKED_OWNER_APPROVAL |
| LIVE-GEO | BLOCKED_EXTERNAL_DEPENDENCY |  |  | NO-LIVE recorded 2026-11-07 (D-053); adapters exist, no credentials/ha | BLOCKED_EXTERNAL_DEPENDENCY |
| MAP-01 | CLOSED_VERIFIED | app/investigation_map.py | tests/test_geointel_map.py | 6 tests green; 12 layers honest-empty; derived links cap OBSERVED; mas | - |
| MAP-02 | TESTING | frontend/components/geointel-map.tsx frontend/components/intel-verify- | frontend/components/geointel-map.test.tsx frontend/components/intel-ve | 3 components + 8 tests written; zero-dep schematic; distinct marker sh | EVIDENCE_READY |
| NOTIFY-01 | CLOSED_VERIFIED | app/notify.py app/store.py app/main.py | tests/test_notify.py | 11 tests green; templates+emitters+log driver; email/SMS need a provid | - |
| OPS-01 | CLOSED_VERIFIED | scripts/forensic_inventory.py |  | FORENSIC_INVENTORY.json generated | - |
| OPS-02 | CLOSED_VERIFIED | scripts/rollback_rehearsal.py | tests/test_rollback_rehearsal.py | 2 tests green; target+state+import verified, nothing changed | - |
| ORG-01 | CLOSED_VERIFIED | app/orgs.py app/store.py app/main.py | tests/test_orgs.py | 8 tests green; single-org/members/disable/invite/redeem/audit | - |
| PAY-01 | CLOSED_VERIFIED | app/payments.py app/web3.py app/store.py app/main.py | tests/test_payments.py | 9 tests green; intents/refunds/no-custody; live raises | - |
| PAY-02 | CLOSED_VERIFIED | app/payments.py app/store.py | tests/test_provider_webhooks.py | 5 tests green; interface v1; HMAC 300s window; schema-agnostic (no ven | - |
| PDI-01 | CLOSED_VERIFIED | README.md tests/test_product_identity.py | tests/test_product_identity.py | 2 hygiene tests green; Phase 0 search + dispositions | - |
| PILOT-01 | CLOSED_VERIFIED | app/pilot.py | tests/test_pilot.py | 10 tests green; 9 checks vs live engine/routes; audited promote | - |
| PRV-01 | CLOSED_VERIFIED | app/intel_providers.py | tests/test_geointel_providers.py | 6 tests green; 33 adapters all DISCOVERED; 7 countries PROVIDER_UNAVAI | - |
| QA-02 | AWAITING_OWNER_APPROVAL |  |  | suites skip without SCRATCH_DATABASE_URL; PKG-01 DEFERRED + D-057 DEFE | BLOCKED_OWNER_APPROVAL |
| QG-01 | CLOSED_VERIFIED | tests/test_quality_gates.py | tests/test_quality_gates.py | 3 tests green; 0 dupe groups; 118/118 /api routes; 24/24 codes logged | - |
| REC-AI | CLOSED_VERIFIED | app/intel_tools.py app/agents.py app/orchestration.py | tests/test_recovery_routes.py | fund-recovery manifest (approval-gated) + 3 read tools; RECOVERY inten | - |
| REC-CAPS | CLOSED_VERIFIED | app/recovery_caps.py | tests/test_recovery_core.py tests/test_recovery_routes.py | 33x12 all UNSUPPORTED; declarations need evidence; live submit require | - |
| REC-DOC | CLOSED_VERIFIED | docs/RECOVERY_OS.md | tests/test_recovery_core.py | reuse map + gates + historical routes + threat model | - |
| REC-ELIG | CLOSED_VERIFIED | app/recovery.py | tests/test_recovery_core.py | full ladder proven incl. window expiry + alternatives; coded-reason ga | - |
| REC-IND | CLOSED_VERIFIED | app/industry_adapters.py | tests/test_recovery_routes.py | shared workflows; per-industry typologies + templates; live count comp | - |
| REC-LIFE | CLOSED_VERIFIED | app/recovery.py app/store.py | tests/test_recovery_core.py tests/test_recovery_routes.py | idempotent open; illegal moves raise; admin-only approve/reject; evide | - |
| REC-RULES | CLOSED_VERIFIED | app/recovery_rules.py | tests/test_recovery_core.py | 2 VERIFIED structural + 8 NOT_VERIFIED templates; seeds immutable; adm | - |
| REC-UI | TESTING | frontend/components/recovery-section.tsx frontend/lib/api.ts frontend/ | frontend/components/recovery-section.test.tsx | 1 section + 4 tests written; verbatim states; no executed run (node EP | EVIDENCE_READY |
| REL-01 | AWAITING_OWNER_APPROVAL |  |  | no LICENSE; PKG-06 DEFERRED 2026-11-07 | BLOCKED_OWNER_APPROVAL |
| REL-02 | AWAITING_OWNER_APPROVAL | app/main.py |  | aliases deprecated, retained; D-019b HOLD 2026-11-07 | BLOCKED_OWNER_APPROVAL |
| SEC-CRED | CLOSED_VERIFIED | app/api_credentials.py app/abac.py app/main.py app/store.py | tests/test_sec_cred.py | issue/verify/revoke on PBKDF2 store; abac client kind; write-gate + ac | - |
| SEC-DEV | CLOSED_VERIFIED | app/trusted_devices.py app/main.py app/store.py | tests/test_sec_dev.py | register on login; trust/revoke self-service; revoked denied at 3 issu | - |
| SEC-GEO | CLOSED_VERIFIED | app/main.py app/config.py app/store.py | tests/test_geointel_api.py | 13 tests green; reader/writer gates; viewer 403; auditor masked; armed | - |
| SEC-MFA | CLOSED_VERIFIED | app/mfa.py | tests/test_mfa.py | 23 tests green incl RFC6238 vectors; replay+lockout+recovery+audit | - |
| SEC-NOTIF | CLOSED_VERIFIED | app/store.py app/main.py | tests/test_security_notifications.py | 10 tests green; risk/mfa notices merged per-user; 50-cap; no network/s | - |
| SEC-PASSKEY | CLOSED_VERIFIED | app/passkeys.py app/store.py app/main.py | tests/test_passkeys.py | 15 tests green; none+packed self-attestation; ES256/EdDSA real verify; | - |
| SEC-PROD | CLOSED_VERIFIED | app/config.py app/store.py app/main.py .env.example | tests/test_production_guard.py | 6 tests green; CS_ENV parsing; reset 403; boot fail-closed | - |
| SEC-R1 | CLOSED_VERIFIED | app/main.py | tests/test_demo_token_remediation.py | R1 4-way matrix green | - |
| SEC-R2 | CLOSED_VERIFIED | app/main.py | tests/test_demo_token_remediation.py | R2 forced-actor tests | - |
| SEC-R3 | CLOSED_VERIFIED | app/main.py | tests/test_demo_token_remediation.py | R3 denial tests | - |
| SEC-R4 | CLOSED_VERIFIED | app/main.py | tests/test_demo_token_remediation.py | R4 gate tests | - |
| SEC-R5 | CLOSED_VERIFIED | app/config.py | tests/test_write_token.py | owner-confirmed register | - |
| SEC-R6 | CLOSED_VERIFIED | frontend/.env.example | tests/test_secret_safety.py | owner-confirmed register | - |
| SEC-REV | CLOSED_VERIFIED | app/main.py | tests/test_access_review.py | grant deltas + snapshot + 4 tests green | - |
| SEC-RISK | CLOSED_VERIFIED | app/login_risk.py | tests/test_login_risk.py | 12 tests green; low/elevated/high; digests-only baseline | - |
| SEC-ROT | CLOSED_VERIFIED | app/auth.py app/config.py app/main.py app/abac.py | tests/test_sec_rot.py | keyring parse (primary + previous); overlap then cutover proven; 3 tes | - |
| SITE-01 | TESTING | frontend/app/help/page.tsx frontend/app/support/page.tsx frontend/app/ | frontend/app/static-pages.test.tsx | 4 pages + shared renderer + 4 tests written; no invented claims; no ex | EVIDENCE_READY |
| SUB-01 | CLOSED_VERIFIED | app/billing.py app/store.py app/main.py | tests/test_billing.py | 11 tests green; trial/sub/founder/meter/402/audit | - |
| TEL-01 | CLOSED_VERIFIED | app/telecom_registry.py | tests/test_telecom_registry.py | 11 tests green; 13 operators v1.0; provenance+coverage+explicit API re | - |
| TEL-02 | CLOSED_VERIFIED | app/telecom_verify.py | tests/test_telecom_verify.py | 20 tests green; derived paths honest; provider-only UNAVAILABLE w/o li | - |
| TEL-03 | CLOSED_VERIFIED | app/telecom_providers.py app/connectors.py | tests/test_telecom_providers.py | 8 tests green; 8 adapters registered; all NOT_CONNECTED; harness synth | - |
| TEL-04 | CLOSED_VERIFIED | app/telecom_verify.py app/store.py | tests/test_telecom_contract.py | 10 tests green; masked+hash only; sha256 integrity; stale-on-read; ten | - |
| TEL-05 | TESTING | frontend/components/telecom-section.tsx frontend/app/network/[txnId]/p | frontend/components/telecom-section.test.tsx | section + 6 tests written; lazy closed-by-default; masked subjects; no | EVIDENCE_READY |
| TEL-06 | CLOSED_VERIFIED | app/main.py app/config.py app/store.py | tests/test_telecom_security.py | 9 tests green; RBAC/consent/quotas/retention/tenant/PII minimization;  | - |
| TEL-07 | CLOSED_VERIFIED | app/telecom_registry.py | tests/test_telecom_registry.py | E.164/NG-local/7-country parse; allocation-not-current; unknown market | - |
| TEL-08 | BLOCKED_EXTERNAL_DEPENDENCY |  |  | NO-LIVE recorded 2026-11-07 (D-053); adapters exist, no credentials/ha | BLOCKED_EXTERNAL_DEPENDENCY |
| TEL-09 | CLOSED_VERIFIED | docs/TELECOM_IDENTITY.md | tests/test_telecom_contract.py | doc written + inspected; matrix/manifest/runbook/env updated | - |
| TEN-01 | CLOSED_VERIFIED | app/tenancy.py app/main.py app/agents.py app/governance.py app/connect | tests/test_tenancy.py tests/test_tenant_api.py tests/test_tenant_new_s | request-seam adversarial + 52 surface tests green (incl. txn/graph/ris | - |
| THEME-01 | TESTING | frontend/components/theme-provider.tsx frontend/components/theme-selec | frontend/components/theme-provider.test.tsx frontend/lib/theme.test.ts | provider mounted in layout; selector in app-shell x2; tests written, n | EVIDENCE_READY |
| UFI-ADAPT | CLOSED_VERIFIED | app/industry_adapters.py | tests/test_universal_slice2.py | all 45 ids resolve; slugs reuse matrix map; readiness never mutates re | - |
| UFI-AI | CLOSED_VERIFIED | app/intel_tools.py app/agents.py | tests/test_universal_ai.py | 5 read-only tools; 12 existing manifests granted; propose/approve/exec | - |
| UFI-AIMODEL | NOT_STARTED |  |  | deterministic only; D-054 DEFERRED 2026-11-07 | BLOCKED_OWNER_APPROVAL |
| UFI-ALERT | CLOSED_VERIFIED | app/alerts.py app/store.py | tests/test_universal_core.py tests/test_universal_routes.py | 8-state lifecycle; illegal transitions raise; idempotent open; real-ro | - |
| UFI-ALT | CLOSED_VERIFIED | app/altpayments.py | tests/test_universal_core.py tests/test_universal_routes.py | format validation reuse; chain/issuer/provider lookups PROVIDER_UNAVAI | - |
| UFI-API | CLOSED_VERIFIED | app/main.py | tests/test_universal_routes.py | 9 tests green; writes gated + audited; tenant 404s; sensitive reveal a | - |
| UFI-CLOSE | CLOSED_VERIFIED | docs/UFI_CLOSEOUT.md | tests/test_ufi_e2e.py | discovery + reconciliation + 45-industry matrix + score methodology +  | - |
| UFI-DOC | CLOSED_VERIFIED | docs/UNIVERSAL_INTEL_OS.md | tests/test_universal_core.py | doc + manifest/index/exec-state updated | - |
| UFI-E2E | CLOSED_VERIFIED | app/main.py app/tracing.py app/industry_adapters.py | tests/test_ufi_e2e.py tests/test_tracing_scenarios.py tests/test_indus | 2 e2e + 10 scenarios + 6 fleet + 2 perf green, 1 hosted skip; ingest-t | - |
| UFI-FLEET | CLOSED_VERIFIED | app/industry_adapters.py | tests/test_universal_integration.py | 45-row snapshot from live signals; totals; read-only | - |
| UFI-IND | CLOSED_VERIFIED | app/industries.py app/typologies.py | tests/test_universal_routes.py | 45 ids verified; no rename; shared-core reuse kept; typology cross-map | - |
| UFI-INST | CLOSED_VERIFIED | app/institutions.py | tests/test_universal_core.py tests/test_universal_routes.py | 8 networks seeded public-knowledge; status from connector registry; al | - |
| UFI-INT | CLOSED_VERIFIED | app/intel_tools.py app/tracing.py app/main.py | tests/test_universal_integration.py | bundle assembles from tenant rows; traces carry related investigations | - |
| UFI-LIVE | BLOCKED_EXTERNAL_DEPENDENCY |  |  | NO-LIVE recorded 2026-11-07 (D-053); adapters exist, no credentials/ha | BLOCKED_EXTERNAL_DEPENDENCY |
| UFI-MON | CLOSED_VERIFIED | app/monitoring.py | tests/test_universal_slice2.py | on-demand mode labelled; freshness from rows; evaluate idempotent; run | - |
| UFI-PARTY | CLOSED_VERIFIED | app/parties.py | tests/test_universal_core.py tests/test_universal_routes.py | 17 roles; mask-by-default; exact-id RESOLVE; shared signals SUPPORT on | - |
| UFI-PAY | CLOSED_VERIFIED | app/payment_methods.py | tests/test_universal_core.py tests/test_universal_routes.py | 13 methods; per-method sender/recipient/history/reversal limits; cash- | - |
| UFI-REP | CLOSED_VERIFIED | app/reports.py | tests/test_universal_core.py tests/test_universal_routes.py | all 15 types build; missing sections render gaps; unknown types raise | - |
| UFI-SEC | CLOSED_VERIFIED | app/main.py app/monitoring.py app/alerts.py | tests/test_universal_security.py | 8 tests green; cross-tenant 404s; armed 401s; audits; validation; mask | - |
| UFI-TRACE | CLOSED_VERIFIED | app/tracing.py app/store.py | tests/test_universal_core.py tests/test_universal_routes.py | 8-link ladder; provenanced edges upgrade; hop cap + cash limits surfac | - |
| UFI-TXN | CLOSED_VERIFIED | app/payment_methods.py | tests/test_universal_core.py | 6 tests green; provider-reported/hint/UNKNOWN; lifecycle preserves unm | - |
| UFI-TXNAPI | CLOSED_VERIFIED | app/main.py | tests/test_universal_slice2.py | filters + clamped paging; lifecycle per event; links + neighborhood; i | - |
| UFI-TYPO | CLOSED_VERIFIED | app/typologies.py | tests/test_universal_core.py tests/test_universal_routes.py | 40 typologies; all families/rules validated; canonical industry ids; g | - |
| UFI-UI | TESTING | frontend/components/tracing-section.tsx frontend/lib/api.ts frontend/a | frontend/components/tracing-section.test.tsx | 1 component + 5 tests written; closed-by-default; no executed run (nod | EVIDENCE_READY |
| UFI-UI2 | TESTING | frontend/components/monitoring-section.tsx frontend/components/industr | frontend/components/monitoring-section.test.tsx frontend/components/in | 2 components + 7 tests written; closed-by-default; legal transitions o | EVIDENCE_READY |
| UFI-UI3 | CLOSED_VERIFIED | frontend/components/tracing-section.tsx frontend/components/monitoring | tests/test_ufi_contract.py | imports resolve; helper paths exist in route table; vitest/build still | - |
| VIS-01 | BLOCKED_EXTERNAL_DEPENDENCY |  |  | no image attached in session; nothing compared | BLOCKED_EXTERNAL_DEPENDENCY |
