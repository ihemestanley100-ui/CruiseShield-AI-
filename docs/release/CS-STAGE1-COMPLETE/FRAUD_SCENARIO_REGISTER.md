# CS-FRAUD-002 — Synthetic Fraud Scenario Register (Stage 1)

All data synthetic. Verdicts: COVERED (engine + test),
PARTIAL (taxonomy only / adjacent), NOT_IMPLEMENTED (Stage 2).
No synthetic record is described as real-world intelligence.

## Detector census (CS-FRAUD-001)

IMPLEMENTED_AND_TESTED (10): RULE_MATCH, VELOCITY, DEVICE_REUSE,
PHONE_REUSE, BENEFICIARY_CLUSTER, SHARED_MERCHANT, GRAPH_PATTERN,
NETWORK_PROXIMITY, CROSS_CHANNEL_PATTERN, GEOGRAPHIC_ANOMALY.
Evidence: `tests/test_detection.py`, 99-cell matrix test, R-001..R-008
rule tests. NOT_IMPLEMENTED (1): ML_ANOMALY (registry + matrix +
never-fires test; no model, no change this programme).

## Scenarios

- S-01 account takeover — COVERED. R-003/R-004 device/phone
  reuse + `test_login_risk.py`. Severity high/medium. Evidence:
  sharing signals + login-risk assessment.
- S-02 transaction anomalies — COVERED. R-001 threshold +
  RULE_MATCH (`test_rule_mapped_detectors_fire_on_seed`).
- S-03 payment fraud — COVERED. RULE_MATCH + typologies T-01..T-40
  mapping (`test_typologies` via universal suites).
- S-04 QR payment abuse — COVERED (new). Large QR payment fires
  R-001 with canonical QR attribution:
  `tests/test_fraud_scenarios_stage1.py` (2 tests).
- S-05 identity fraud — PARTIAL. Typologies T-30/T-31 exist;
  no dedicated detector (no identity-proofing rule). Stage 2 (S2-02).
- S-06 money mule networks — COVERED. R-006/R-007 fan-in/out +
  `tests/test_tracing_scenarios.py` (fanin/fanout/multihop).
- S-07 suspicious transaction networks — COVERED. Tracing engine
  + provenance tests (`test_tracing_scenarios.py`, 10 tests).
- S-08 rapid fund movement — COVERED. VELOCITY R-002 (120-min
  window) + rule tests.
- S-09 structuring patterns — NOT_IMPLEMENTED. No
  below-threshold-split rule exists; sub-threshold series do not
  fire. Specified for Stage 2 (S2-02); no pseudo-coverage added.
- S-10 suspicious beneficiary relationships — COVERED. R-005
  beneficiary-cluster + tests.
- S-11 account linking — COVERED. R-003/R-004/R-008 sharing
  signals + drill-down provenance tests.
- S-12 repeated failed transactions — PARTIAL. Lifecycle
  vocabulary + T-19 exist; no rule consumes decline events.
  Stage 2 (S2-02/S2-05 event ingestion).
- S-13 insider abuse — NOT_IMPLEMENTED. No insider-behavior
  rule or actor-anomaly detector. Stage 2 (S2-02/S2-04).
- S-14 cross-tenant access attempts — COVERED (access-control
  plane, not detector plane). `TenantDeniedError` + 403 paths
  (`test_tenant_api.py`, `test_abac.py` incl. F-C test).

## Investigation integrity (CS-FRAUD-003)

Case/investigation lifecycle, evidence attach + provenance,
timeline, assignment, transitions, escalation, audit history,
export, replay, access control: covered by `test_cases_*`,
`test_evidence*`, `test_audit_*`, `test_abac.py`,
`test_access_review.py` (re-run in workstream 8). Evidence
 Canonical bytes + sha256 (`X-Export-SHA256`); tampering with
sealed audits detected via D-1 verification (test-pinned).
