# MS-DETECT-003 — R-011 Threshold & Version Register

Mule pass-through detection (MULE_PASSTHROUGH). Synthetic data only.
No ML claims. Follows the MS-DETECT-001 detector-layer pattern;
engine RULES and R-009/R-010 behavior are unchanged.

## R-011 — MULE_PASSTHROUGH (v1.1, remediation pending independent review; v1.0 owner-authorized)

Detects accounts receiving value from 3+ distinct senders and
forwarding 80%+ of it within a 24h window.

| Parameter | Value | Source |
|---|---|---|
| Rule version | 1.1 | `app/detection.py` RULE_VERSIONS |
| Window | ±1440 minutes, centered on target | `app/graph.py` MULE_WINDOW_MINUTES |
| Timestamp contract | aware UTC normalization before window/sort/compare; naive or unparseable excluded, no TZ assumed | `app/graph.py` _aware_ts + `_mule_signals` (RV-01/RV-02) |
| Chronological guard | OUT legs count only at/after earliest eligible IN leg | `_mule_signals` (UTC ordering, same as window sort) |
| Min distinct senders | ≥ 3 | MULE_MIN_SENDERS |
| Min incoming | ≥ 10,000,000 kobo eligible | MULE_MIN_INCOMING |
| Min forwarded ratio | ≥ 0.80, uncapped | MULE_MIN_RATIO |
| Grouping | (tenant_id, account), IN/OUT directional legs, deduped by ID | `app/graph.py` account_window_legs |
| Self-transfers | excluded from both legs | account_window_legs |
| Target membership | required (target must be an eligible IN or chronological OUT leg) | `_mule_signals` |
| Severity | high | signal field |
| Kill switch | DETECTOR_MULE_ENABLED (default ON; "0" disables) | `app/config.py` |
| Operator note | Grammar (exact, tested): OFF = literal `0` with surrounding whitespace tolerated; ON = `1` (default), empty, unset, or any other value. Always verify the resulting DISABLED state. Availability-biased fail-open by design. | `app/config.py` detector_flag_enabled (RV-04) |

## Lifecycle eligibility (verified against `map_lifecycle`)

| Canonical state | Treatment |
|---|---|
| SETTLED | INCLUDE (confirmed movement) |
| AUTHORIZED | EXCLUDE (approved, not settled; avoids double-count) |
| PENDING | EXCLUDE (explicitly incomplete) |
| DECLINED / FAILED | EXCLUDE (no movement) |
| CHARGEBACK | EXCLUDE both legs (funds clawed back) |
| UNKNOWN, no provider info | INCLUDE as LEGACY, flagged unattested (R-009 precedent) |
| UNKNOWN, unmapped pair | EXCLUDE |

## Ratio semantics and limits

- forwarded_ratio = total_out / total_in over eligible legs;
  total_in ≤ 0 yields no evaluation (denominator protection).
- The ratio is an account-level co-occurrence indicator. It does
  not trace individual funds and does not prove criminal proceeds.
- Ratios above 1.0 fire but are flagged OVER_FORWARD /
  BALANCE_CONFOUNDED (pre-existing balances unseen).
- Unrelated OUT legs inflate the ratio (false-positive
  direction); all OUT leg IDs are disclosed in evidence.
- No REFUND/REVERSAL canonical states exist in the mapper;
  v1.1 remains reversal/refund-blind by documented limitation.
- Windows are centered, not trailing; the chronological guard
  (OUT at/after earliest IN) enforces receive-before-forward.
- Amounts must be non-negative integer kobo at the detector
  boundary; negatives, bools, floats, strings, and missing
  values are excluded; zero is a valid leg (RV-03).
- Exclusion accounting splits `lifecycle_excluded` from
  `chronology_excluded`; `ineligible_excluded` is their sum
  and is kept for compatibility (RV-05).
- Thresholds are code constants in v1.1; changes need a
  version bump and re-test.

## Version history

- v1.0 (owner-authorized): initial MULE_PASSTHROUGH release.
- v1.1 (remediation, PENDING independent review): RV-01/RV-02
  UTC timestamp normalization with naive-exclusion contract;
  RV-03 non-negative integer amount boundary; RV-04 explicit
  kill-switch grammar (behavior preserved); RV-05 split
  exclusion counts. Thresholds unchanged. R-009/R-010 untouched.

## False positives (designed behavior)

Escrow, payroll disbursement, marketplace settlement and
payment-processor accounts structurally match this pattern.
Every signal carries the mandatory limitation sentence,
names these legitimate explanations, and requires
investigator review before any action. No automated adverse
consequences are authorized.

## False negatives (documented limits)

Slow-drip forwarding beyond 24h, sub-floor micro-muling,
multi-hop chains through several mules, cross-tenant rings,
single-sender funnels, and lifecycle-excluded legs are missed
by design.

## Registry / matrix

- 14th family: OPERATIONAL by default, DISABLED when killed.
- Matrix: 14 × 9 = 126 cells; SUPPORTED_BUT_DISABLED when
  killed (pre-declared vocab).
- Killed runs record family_runs 0 with the group key kept.

## Rollback

- Immediate: set DETECTOR_MULE_ENABLED=0; verify zero
  MULE_PASSTHROUGH signals and DISABLED registry status.
- Full source revert: reverse the R-011 file changes
  (app/graph.py legs+constants, app/detection.py family,
  app/config.py flag, tests/test_detect_r011_mule.py,
  pin updates, this register, DET-01 sync); registry
  returns to 13 families. MS-DETECT-001 history untouched.

## Evidence

- Implementation: app/graph.py, app/config.py,
  app/detection.py (no app/main.py change; registry and
  matrix consume the existing family_enabled hooks).
- Tests: tests/test_detect_r011_mule.py (43 tests) +
  updated pins (14 families, 126 cells).
