# MASTER PRODUCTION GAP REGISTER

Campaign 2026-11-08. 40 open rows; canonical statuses verbatim.

| ID | Canonical | Campaign | Statement | Basis |
|---|---|---|---|---|
| AGOS-UI | TESTING | EVIDENCE_READY | Assistant shell + copilot wiring | Hosted green (42501376167/42515350200); matrix-owner transition pending (planning-only). |
| AI-01 | BLOCKED_EXTERNAL_DEPENDENCY | BLOCKED_OWNER_APPROVAL | Live Meta provider integration verified | D-053 NO-LIVE; adapter offline-verified, live call forbidden. |
| AI-03 | BLOCKED_EXTERNAL_DEPENDENCY | BLOCKED_OWNER_APPROVAL | Model-driven agent planning | D-053 NO-LIVE. |
| AUD-01 | IN_PROGRESS | IN_PROGRESS | Tamper-evident audit hash chain | Hash-chain code present; prod key ceremony needs D-018 approval. |
| AUTH-01 | NOT_STARTED | BLOCKED_OWNER_APPROVAL | Google OIDC federation | PKG-09 DEFER. |
| AUTH-02 | NOT_STARTED | BLOCKED_OWNER_APPROVAL | Apple OIDC federation | PKG-09 DEFER. |
| AUTH-03 | NOT_STARTED | BLOCKED_OWNER_APPROVAL | Microsoft OIDC federation | PKG-09 DEFER. |
| AUTH-04 | NOT_STARTED | BLOCKED_OWNER_APPROVAL | Yahoo OIDC federation | PKG-09 DEFER. |
| AUTH-05 | NOT_STARTED | BLOCKED_OWNER_APPROVAL | Email OTP login | PKG-09 DEFER. |
| AUTH-06 | NOT_STARTED | BLOCKED_OWNER_APPROVAL | Passwordless magic links | PKG-09 DEFER. |
| AUTH-07 | NOT_STARTED | BLOCKED_OWNER_APPROVAL | Enterprise SSO (OIDC + SAML 2.0) | PKG-09 DEFER. |
| AUTH-08 | NOT_STARTED | BLOCKED_OWNER_APPROVAL | Safe federated account linking | PKG-09 DEFER. |
| AUTH-09 | NOT_STARTED | BLOCKED_OWNER_APPROVAL | Password recovery (forgot/reset) | PKG-09 DEFER. |
| BAK-01 | IN_PROGRESS | IN_PROGRESS | Encrypted backup + verified restore drill | D-018 TEST DRILL ONLY; drill exists at test grade + campaign durability tests. |
| CICD-01 | AWAITING_OWNER_APPROVAL | BLOCKED_OWNER_APPROVAL | Coverage measurement + thresholds enforced | Coverage thresholds need owner gate decision. |
| DATA-01 | AWAITING_OWNER_APPROVAL | BLOCKED_OWNER_APPROVAL | Retention/archival/purge execution | D-056 DEFER. |
| DB-01 | AWAITING_OWNER_APPROVAL | BLOCKED_OWNER_APPROVAL | PostgreSQL operational cutover | GAP-001 HOLD. |
| DET-03 | IN_PROGRESS | BLOCKED_OWNER_APPROVAL | Signal events persist with history and outcomes | Depends on DB-01/GAP-001. |
| DET-12 | BLOCKED_EXTERNAL_DEPENDENCY | EVIDENCE_READY | Frontend detection tests green | Hosted green (42501376167/42515350200); matrix-owner transition pending (planning-only). |
| DET-13 | AWAITING_OWNER_APPROVAL | EVIDENCE_READY | Hosted CI green | Hosted green (42501376167/42515350200); matrix-owner transition pending (planning-only). |
| DET-14 | AWAITING_OWNER_APPROVAL | BLOCKED_OWNER_APPROVAL | Production deployment verified | No deployment authorized; production branch is production-launch. |
| FE-01 | AWAITING_OWNER_APPROVAL | EVIDENCE_READY | Frontend executed-test evidence on current tree | Hosted green (42501376167/42515350200); matrix-owner transition pending (planning-only). |
| I18N-02 | BLOCKED_EXTERNAL_DEPENDENCY | BLOCKED_EXTERNAL_DEPENDENCY | Native human review of non-EN values | Native human review outstanding. |
| INF-01 | AWAITING_OWNER_APPROVAL | BLOCKED_OWNER_APPROVAL | Deploy verification (logs + smoke) | Deploy verification needs an authorized deployment. |
| LEAFLET | NOT_STARTED | BLOCKED_OWNER_APPROVAL | OSM/Leaflet tile renderer binding | D-055 POLICY FIRST; MAP_PROVIDER=none. |
| LIVE-GEO | BLOCKED_EXTERNAL_DEPENDENCY | BLOCKED_EXTERNAL_DEPENDENCY | Live intel providers (identity/address/geo/map) | NO-LIVE + no provider credentials/agreements. |
| MAP-02 | TESTING | EVIDENCE_READY | Geointel UI: map + verify + admin panels | Hosted green (42501376167/42515350200); matrix-owner transition pending (planning-only). |
| QA-02 | AWAITING_OWNER_APPROVAL | BLOCKED_OWNER_APPROVAL | Scratch-PG pass line (migration/parity/J6) | B7 approval outstanding; 73 scratch-PG tests NOT executed. |
| REC-UI | TESTING | EVIDENCE_READY | Recovery section + dashboard wiring | Hosted green (42501376167/42515350200); matrix-owner transition pending (planning-only). |
| REL-01 | AWAITING_OWNER_APPROVAL | BLOCKED_OWNER_APPROVAL | Public repository license selected | D-015 DEFER. |
| REL-02 | AWAITING_OWNER_APPROVAL | BLOCKED_OWNER_APPROVAL | Demo API aliases removed after migration | D-019b HOLD. |
| SITE-01 | TESTING | EVIDENCE_READY | Help/support/legal/privacy pages | Hosted green (42501376167/42515350200); matrix-owner transition pending (planning-only). |
| TEL-05 | TESTING | EVIDENCE_READY | Telecom investigation UI (4 views + admin panel) | Hosted green (42501376167/42515350200); matrix-owner transition pending (planning-only). |
| TEL-08 | BLOCKED_EXTERNAL_DEPENDENCY | BLOCKED_EXTERNAL_DEPENDENCY | Live telecom provider integrations | NO-LIVE + no operator agreements. |
| THEME-01 | TESTING | EVIDENCE_READY | Dark/light/system themes | Hosted green (42501376167/42515350200); matrix-owner transition pending (planning-only). |
| UFI-AIMODEL | NOT_STARTED | BLOCKED_OWNER_APPROVAL | Model-backed AI generation (PII lane) | D-054 DEFER (PII lane). |
| UFI-LIVE | BLOCKED_EXTERNAL_DEPENDENCY | BLOCKED_EXTERNAL_DEPENDENCY | Live financial providers (banks/rails/crypto) | NO-LIVE + no bank/rail agreements. |
| UFI-UI | TESTING | EVIDENCE_READY | Tracing UI: trace + parties + typologies | Hosted green (42501376167/42515350200); matrix-owner transition pending (planning-only). |
| UFI-UI2 | TESTING | EVIDENCE_READY | Monitoring + industry UI sections | Hosted green (42501376167/42515350200); matrix-owner transition pending (planning-only). |
| VIS-01 | BLOCKED_EXTERNAL_DEPENDENCY | BLOCKED_EXTERNAL_DEPENDENCY | Visual fidelity to reference image | Reference image never supplied. |

Counts: EVIDENCE_READY 11, BLOCKED_OWNER_APPROVAL 22, BLOCKED_EXTERNAL_DEPENDENCY 5, IN_PROGRESS 2.
