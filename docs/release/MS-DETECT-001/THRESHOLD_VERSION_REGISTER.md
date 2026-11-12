# MS-DETECT-001 — Rule Threshold & Version Register

Tranche S09–S12: structuring detection (GAP-08) + decline-repetition
detection (GAP-10). Synthetic data only. No ML claims.

## R-009 — STRUCTURING_PATTERN (v1.0)

Detects repeated sub-threshold transfers from one sender whose
combined value reaches the large-transfer reporting line.

| Parameter | Value | Source |
|---|---|---|
| Rule version | 1.0 | `app/detection.py` RULE_VERSIONS |
| Window | ±1440 minutes (24h), centered on target | `app/graph.py` STRUCTURING_WINDOW_MINUTES |
| Amount line | strictly below 40,000,000 kobo | STRUCTURING_AMOUNT_LINE (= R-001 line) |
| Min count | ≥ 3 qualifying transfers | STRUCTURING_MIN_COUNT |
| Min total | ≥ 40,000,000 kobo combined | STRUCTURING_MIN_TOTAL |
| Grouping | (tenant_id, sender_account_id), deduped by transaction_id | `app/graph.py` sender_window_peers |
| Target membership | required (target must be one of the qualifying transfers) | `app/detection.py` _structuring_signals |
| Severity | high | signal field |
| Kill switch | DETECTOR_STRUCTURING_ENABLED (default ON; "0" disables) | `app/config.py` |

## R-010 — DECLINE_REPETITION (v1.0)

Detects repeated DECLINED authorizations from one sender, consuming
the existing canonical lifecycle (`payment_methods.map_lifecycle`).

| Parameter | Value | Source |
|---|---|---|
| Rule version | 1.0 | `app/detection.py` RULE_VERSIONS |
| Window | ±1440 minutes (24h), centered on target | `app/graph.py` DECLINE_WINDOW_MINUTES |
| Decline definition | canonical lifecycle == "DECLINED" | `app/payment_methods.py` map_lifecycle |
| Min count | ≥ 3 declined events | DECLINE_MIN_COUNT |
| Grouping | (tenant_id, sender_account_id), deduped by transaction_id | `app/graph.py` sender_window_peers |
| Target membership | required (target must itself be DECLINED) | `app/detection.py` _decline_signals |
| Severity | medium | signal field |
| Provenance | provider_status values preserved in evidence; provider names recoverable via transaction_ids | signal evidence |
| Kill switch | DETECTOR_DECLINE_REPETITION_ENABLED (default ON) | `app/config.py` |

## Architecture decision: detector layer, not engine rules

R-009/R-010 fire as detector families (CUSTOM group), not as
`app/rules.py` engine rules. Rationale:

1. Both rules aggregate multi-transaction windows; the detector
   layer already owns aggregate detectors (NETWORK_PROXIMITY,
   CROSS_CHANNEL_PATTERN, GEOGRAPHIC_ANOMALY precedent).
2. Engine membership would rewrite pinned cross-system contracts:
   risk-score rule_result lengths, the byte-pinned canonical
   fixture, migration loader counts, and evidence-package counts.
   That blast radius is disproportionate to a detection tranche.
3. Rule governance (§7) is preserved: unique IDs (R-009/R-010),
   versioned configs (RULE_VERSIONS), documented thresholds
   (this register), independent kill switches, deterministic
   outputs, explicit provenance, and full test coverage.

## Registry / matrix status vocabulary

- Registry (`/api/v1/detectors`): OPERATIONAL by default;
  DISABLED when the family's kill switch is "0";
  ML_ANOMALY stays NOT_IMPLEMENTED.
- Matrix (`/api/v1/detection/matrix`): SUPPORTED_AND_ACTIVE by
  default; SUPPORTED_BUT_DISABLED when killed (a status the
  matrix contract already declared).
- Meta (`evaluate_all`): a killed family records family_runs 0
  and no signals; the group key stays present for observability.

## False-positive considerations

- R-009: legitimate repeated transfers (payroll batches, rent
  installments, marketplace payouts) below 40M kobo can trip
  the count+total gate. The total gate (combined value must
  reach the reporting line) and target-membership requirement
  reduce noise, but every alert still needs investigator review;
  repeated small transfers are not fraud by themselves.
- R-010: legitimate retry bursts (expired card re-attempts,
  intermittent issuer outages) can trip the count gate. The
  24h window and same-sender grouping bound the blast radius;
  correlation with account-takeover signals is recommended
  before escalation.

## Limitations

- Windows are centered (±1440m), not trailing; a burst split
  across the window edge of every member may not fire.
- R-009 v1.0 groups by a single sender_account_id and does not
  detect multi-account smurfing spread across different sender
  identities (related-account linkage is out of scope).
- Amounts must be integer kobo; non-integer amounts are
  excluded, never coerced.
- Rows with unparseable timestamps are excluded from windows;
  an unparseable target timestamp yields no peers.
- Lifecycle coverage is limited to provider statuses the
  canonical mapper knows; unmapped statuses are preserved
  verbatim and never counted as DECLINED.
- Thresholds are code constants in v1.0 (no runtime tuning
  API); changes require a version bump and re-test.

## Evidence

- Implementation: app/graph.py, app/config.py,
  app/detection.py, app/main.py (registry/matrix status only).
- Tests: tests/test_detect_tranche_s09_s12.py (25 tests) +
  updated pins in tests/test_detection.py and
  tests/test_fraud_scenarios_stage1.py.
- Full backend regression: 1485 passed / 145 skipped /
  1 failed + 2 errors (pre-documented sandbox-only
  environmental blockers, unchanged from Stage 1).
