# CANONICAL FILE MANIFEST — CruiseShield AI™ (Phase 1)

Date: 2026-11-06. Reconciles the L13 Part-17 A–K catalogue
against the actual repository. Nothing was deleted; historical
files keep their place with a HISTORICAL disposition.

Dispositions: CANONICAL (current source of truth) · PARTIAL
(useful but incomplete or scoped) · HISTORICAL (frozen,
preserved) · MISSING (no file; code status noted separately) ·
DUPLICATE (needs content consolidation, Phase 2).
A ✓ means content verified by inspection; ~ means
name-mapped only (content not yet verified).

Consolidation rule: the live line is root
CRUISESHIELD-AI-*.md + docs/ZERO_GAP_MATRIX.json +
docs/PROJECT_EXECUTION_STATE.md + docs/LIVE_EVIDENCE_INDEX.md.
docs/CS_FINAL_* + docs/FINAL_* + docs/PHASE_* + J-series are
HISTORICAL generations; consult, never extend.

## A. Product governance

1. Product Charter → MISSING (README positioning is not a charter).
2. Vision and Strategy → MISSING (L13/L14 directive texts live
   in chat, not in repo; owner to file them if desired).
3. PRD → CRUISESHIELD_AI_*.txt specs (HISTORICAL ✓) +
   live matrix (CANONICAL ✓). PARTIAL.
4. Scope and Boundaries → matrix blockers ✓ +
   docs/KNOWN_LIMITATIONS.md ~. PARTIAL.
5. Roadmap → CRUISESHIELD-AI-IMPLEMENTATION-ROADMAP.md ~.
6. Decision Register → CRUISESHIELD-AI-DECISION-LOG.md ✓.
7. Risk Register → CRUISESHIELD-AI-RAID-LOG.md ✓.
8. Acceptance Criteria → matrix acceptance fields ✓ +
   CRUISESHIELD-AI-ACCEPTANCE-RECORD.md ✓.
9. Change-Control Policy → MISSING (execution-state STOP
   rules act as de-facto control).
10. Release Policy → docs/LEVEL14_OWNER_APPROVAL_PACKAGES.md ✓
    (current); FINAL_DEPLOYMENT_GATE_REGISTER.md (HISTORICAL ✓).

## B. Architecture

11. Universal Architecture Overview → docs/ARCHITECTURE.md ~.
12. Nine-Layer Spec → MISSING as a doc; D-030 mapping in the
    decision log ✓ is the canonical record.
13. Maturity Spec → MISSING (directive text in chat only).
14. System Context → docs/ARCHITECTURE.md ~. PARTIAL.
15. Container Architecture → Dockerfile ✓ + render.yaml ✓.
16. Component Architecture → docs/ARCHITECTURE.md ~ + app/* ✓.
17. Service Catalogue → MISSING (app/main.py route table ✓
    is the de-facto catalogue).
18. ADRs → decision-log D-entries ✓ (consolidated form; no
    separate ADR files by design).
19. Data Flow Architecture → MISSING (CRUISE_ORBIT_DATA_
    ARCHITECTURE.md is orbit-scoped ~).
20. Integration Architecture → CRUISESHIELD-AI-DEPENDENCY-AND-
    INTEGRATION-REGISTER.md ~ + PHASE_15_INTEGRATION_
    ARCHITECTURE.md ~. PARTIAL.
21. Deployment Architecture → RENDER_1..10 series ~ +
    docs/DEPLOYMENT.md ~. PARTIAL.
22. Conformance Rules → tests/test_quality_gates.py ✓
    (gates 1/9/16) + matrix QG-01 ✓.

## C. Frontend

23. Design System → MISSING. 24. UI Component Catalogue →
    MISSING. 25. Navigation Specification → MISSING.
26. Dashboard Specification → WORLD_ATLAS_FRONTEND_SPEC.md ~
    (atlas scope). PARTIAL.
27. User Settings Spec → MISSING. 28. Organization Settings
    Spec → MISSING. 29. Administration Spec → MISSING.
30. Accessibility Spec → a11y-audit.mjs ✓ script +
    FINAL_BROWSER_ACCESSIBILITY_AUDIT.md ~. PARTIAL.
31. Localization Spec → UGLS_LANGUAGE_SYSTEM.md ~ + i18n
    registry ✓. PARTIAL.
32. Theme Specification → MISSING. 33. Frontend Test
    Strategy → MISSING (vitest config exists, no strategy doc).

## D. Backend and APIs

34. Backend Service Catalogue → MISSING (route table de-facto).
35. API Standards → MISSING (conventions live in code).
36. API Contracts → route table + tests ✓ PARTIAL
    (no standalone contract doc; WORLD_ATLAS_API_SPECIFICATION
    is atlas-scoped ~).
37. API Versioning → app/main.py v1 ✓ code; doc MISSING.
38. Authentication Spec → J4_AUTHENTICATION.md HISTORICAL;
    no current-line spec. PARTIAL.
39. Authorization Spec → DEMO_TOKEN_ENDPOINT_AUTHORIZATION_
    MATRIX.md ✓ (token scope). PARTIAL.
40. Tenant Management Spec → MISSING (tenancy.py code ✓,
    D-014 pending).
41. Workflow Spec → MISSING (governance.py code ✓).
42. Notification Spec → MISSING (D-029 code ✓).
43. Billing API Spec → MISSING (no code).
44. Integration API Spec → MISSING as a doc (connectors.py ✓).
45. Webhook Specification → MISSING (no receiver code).

## E. Data

46. Data Architecture → MISSING as a platform doc
    (orbit doc is scoped ~).
47.–55. Entity/Transaction/Signal/Investigation/Case/
    Evidence/Audit models, Industry Contracts, DB Schema →
    code-canonical (models.py, detection.py, cases.py,
    evidence.py, industries_*.py, models_pg.py ✓); all
    standalone docs MISSING.
56. Migration Registry → migrations/loader.py ✓ code;
    J5_MIGRATION_MANIFEST.md HISTORICAL.
57. Retention Policy → MISSING (DATA-01).
58. Data Lineage Spec → MISSING (trace_id code only).
59. Backup/Restore Spec → BACKUP_RECOVERY_RUNBOOK.md ✓ +
    J6_* ✓. PARTIAL (code-ready, no live evidence).

## F. AI and detection

60. AI Gateway Spec → MISSING (AI-02; single-lane code).
61. Model Registry → MISSING (config trio only).
62. Agent Registry → app/agents.py _MANIFESTS ✓ code;
    doc MISSING.
63. Prompt Registry → in-code versions ✓; doc MISSING.
64. Detection Engine Spec → MISSING as a doc
    (detection.py/rules.py code ✓).
65. Detection Rule Registry → RULES R-001..R-008 ✓ code;
    doc MISSING.
66. Risk Scoring Spec → risk-score-v1 code ✓; doc MISSING.
67. Entity Resolution Spec → MISSING (no code).
68. Graph Intelligence Spec → MISSING as a doc (graph.py ✓).
69. Anomaly Detection Spec → MISSING (ML NOT_IMPLEMENTED).
70. Model Evaluation Spec → tests/test_ai_eval.py ✓ code;
    AI_COST_AND_USAGE_CONTROL_REPORT.md ~. PARTIAL.
71. AI Governance Spec → adapter guards ✓ code;
    PHASE_15_MODEL_RISK_FRAMEWORK.md ~. PARTIAL.
72. Human Review Spec → MISSING as a doc (cases.py code ✓).

## G. Industry modules (73–118)

Registry app/industries.py ✓ + matrix IND rows ✓ + 45
profile modules + 45 walk tests ✓ are canonical for code
and status. All 46 per-industry DOC counterparts MISSING.
No per-industry doc exists; do not invent coverage.

## H. Security and compliance

119. Security Architecture → SECURITY_GOVERNANCE_AUDIT.md ~.
     PARTIAL.
120. Threat Model → DEMO_TOKEN_PUBLIC_EXPOSURE_THREAT_MODEL.md ✓
     (token scope). PARTIAL; platform model MISSING.
121. Security Control Registry → MISSING (scattered
     across gate/headers/tests).
122. Identity and Access Policy → MISSING (code + D-entries).
123. MFA Specification → MISSING as a doc (mfa.py ✓).
124. Session Security Policy → MISSING as a doc (code ✓).
125. Encryption Policy → MISSING.
126. Key Management Policy → MISSING (D-018 pending;
     audit_chain.py code ✓).
127. Secrets Management Policy → RENDER_6_ENV_REGISTER.md ✓ +
     FRONTEND_PUBLIC_ENVIRONMENT_SECURITY_REGISTER.md ✓ +
     secret_safety tests ✓. PARTIAL (no platform policy doc).
128. Privacy Policy → WORLD_ATLAS_SECURITY_PRIVACY_GOVERNANCE.md
     ~ (atlas scope). PARTIAL.
129. DPIA → MISSING. 130. Retention/Deletion Policy →
     MISSING (DATA-01).
131. Incident Response Plan → MISSING (OPERATIONS_RUNBOOK.md
     covers ops only). PARTIAL.
132. Vulnerability Management → SECURITY_GATE_POLICY.md ~ +
     audit evidence ✓. PARTIAL.
133. Compliance Mapping → PHASE_15_REGULATORY_ASSESSMENT.md ~.
     PARTIAL (name-mapped).
134. Security Test Report → CS_FINAL_BACKEND_SECURITY_REPORT.md
     ~ + SECURITY_ACCEPTANCE_REPORT.md ~. PARTIAL.

## I. Business and billing (135–148)

ALL MISSING (no code, no docs): strategy, pricing research,
plans, entitlements, trial policy, founder policy, billing
architecture, payments, Web3, invoices, refunds, tax,
metering, lifecycle. Exception: PROVIDER_ELIGIBILITY_MATRIX.md
~ PARTIAL by name (unverified scope). Commercial platform is
entirely future work gated on owner decisions.

## J. Operations and deployment

149. Environment Spec → ENVIRONMENT_BASELINE.md ~ +
     RENDER_5_CONFIGURATION_SPEC.md ~. PARTIAL.
150. Infrastructure Spec → ZERO_COST_INFRASTRUCTURE_REGISTER.md ✓
     (old line; re-verify at deploy). PARTIAL.
151. CI/CD Spec → security-gate.yml ✓ code (never ran);
     spec doc MISSING. PARTIAL.
152. Dependency Policy → requirements.lock ✓ +
     SECURITY_GATE_POLICY.md ~. PARTIAL.
153. SBOM → MISSING (lock files de-facto).
154. Deployment Runbook → RENDER_7_DEPLOYMENT_RUNBOOK.md ~.
     PARTIAL.
155. Rollback Runbook → RENDER_8_ROLLBACK_RECOVERY.md ~ +
     DEPLOYMENT_ROLLBACK_RUNBOOK.md ~. PARTIAL (never drilled).
156./157. Backup/Restore Runbooks → BACKUP_RECOVERY_RUNBOOK.md ✓.
     PARTIAL (disposable/read-only drills only).
158. Disaster Recovery → J6_DISASTER_RECOVERY_PLAN.md
     HISTORICAL; current-line plan MISSING. PARTIAL.
159. Monitoring Spec → MISSING (endpoints only; runbook
     declares measurement NOT_STARTED).
160. SLO Register → OPERATIONS_RUNBOOK.md targets ✓ declared;
     measurement NOT_STARTED. PARTIAL.
161. Incident Communications → MISSING.
162. Capacity Plan → MISSING on current line (J8_ZERO_COST*
     HISTORICAL).
163. Release Manifest → DUPLICATE: CRUISESHIELD-AI-RELEASE-
     MANIFEST.md (root) vs CRUISESHIELD_RELEASE_MANIFEST.md
     (docs) — content consolidation required in Phase 2
     before either is canonical. FINAL_GIT_RELEASE_MANIFEST.md
     and PUBLIC_REPOSITORY_RELEASE_MANIFEST.md HISTORICAL/~.
164. Production Acceptance → ACCEPTANCE-RECORD ✓ PARTIAL
     (no customer acceptance exists).

## K. Quality and evidence

165. Master Requirements Matrix → ZERO_GAP_MATRIX.json ✓.
166. Master File Manifest → this doc + FORENSIC_INVENTORY.json ✓.
167./168. Req→code / Req→test traceability → matrix
     implementation/test fields ✓ PARTIAL (new rows honestly
     empty until implemented).
169. Contract Test Report → gate-9 reference test ✓ PARTIAL
     (full contract suite MISSING).
170. Backend Test Report → gap-register GAP-006 lines ✓ +
     TEST_EVIDENCE.md ~. PARTIAL.
171. Frontend Test Report → TEST_RESULTS.md ~ + historical
     vitest logs. PARTIAL.
172. Integration Test Report → MISSING (no live integrations).
173. Security Test Report → CS_FINAL_BACKEND_SECURITY_REPORT.md
     ~. PARTIAL.
174. Tenant Isolation Report → tenant tests ✓ code; report
     doc MISSING. PARTIAL.
175. Performance Report → PHASE_11_* HISTORICAL +
     scripts/perf_smoke.py ✓. PARTIAL (no current measures).
176. Accessibility Report → a11y-audit.mjs ✓ +
     FINAL_BROWSER_ACCESSIBILITY_AUDIT.md ~. PARTIAL.
177. Localization Review → UGLS_* suite ✓ machine review;
     human review pending (I18N-02). PARTIAL.
178./179. Backup/Restore Drill Evidence → backup_drill.py ✓ +
     runbook ✓. PARTIAL (disposable/read-only only).
180. Rollback Drill Evidence → rehearsal read-only ✓.
     PARTIAL (never executed).
181. Hosted CI Evidence → MISSING (DET-13; never ran).
182. Deployment Evidence → MISSING (INF-01).
183. Production Smoke Evidence → MISSING (INF-01).
184. Customer Acceptance → MISSING (no customer).
185. Final Release Assessment → CRUISESHIELD-AI-RELEASE-
     ASSESSMENT.md ~. PARTIAL (name-mapped).

## Consolidation backlog (Phase 2, controlled)

- REL-M1: unify the two release manifests (item 163).
- REL-M2: gap registers — PRODUCTION-GAP-REGISTER.md is live;
  MASTER_REMAINING_GAP_REGISTER.md, CLOSEOUT_PILOT_GAP_REGISTER.md,
  HACKATHON_CRITICAL_GAP_REGISTER.md are HISTORICAL (verify
  no unique open item, then mark superseded — never delete).
- REL-M3: FINAL_ZERO_GAP_MATRIX.md (HISTORICAL) vs
  ZERO_GAP_MATRIX.json (CANONICAL) — already separated; keep.
- REL-M4: TEST_EVIDENCE.md vs TEST_RESULTS.md — read both,
  designate test-report canonical.
- REL-M5: L13/L14 directive texts live in chat only; owner
  may file them under docs/DIRECTIVES/ (optional).

## Addendum 2026-11-07 (Telecom Identity, CANONICAL)

app/telecom_registry.py, app/telecom_providers.py,
app/telecom_verify.py, frontend/components/telecom-section.tsx,
frontend/components/telecom-section.test.tsx,
tests/test_telecom_registry.py, tests/test_telecom_verify.py,
tests/test_telecom_providers.py, tests/test_telecom_contract.py,
tests/test_telecom_security.py, docs/TELECOM_IDENTITY.md.
Provenance: implemented 2026-11-07 against telecom spec; backend
evidence in LIVE_EVIDENCE_INDEX.md; matrix TEL-01..TEL-09.

## Addendum 2026-11-07 (Geointelligence OS, CANONICAL)

app/intel_common.py, app/intel_auth.py, app/identity_verify.py,
app/address_verify.py, app/location_obs.py,
app/intel_providers.py, app/investigation_map.py,
frontend/components/geointel-map.tsx (+test),
frontend/components/intel-verify-sections.tsx (+test),
frontend/components/intel-admin-panels.tsx,
tests/test_geointel_identity.py, tests/test_geointel_address.py,
tests/test_geointel_location.py, tests/test_geointel_ip.py,
tests/test_geointel_providers.py, tests/test_geointel_map.py,
tests/test_geointel_api.py, docs/GEOINTELLIGENCE_OS.md.
Matrix GEO/IDV/ADR/MAP/PRV/GOV/SEC/AI/LIVE/LEAFLET/DOC rows.
