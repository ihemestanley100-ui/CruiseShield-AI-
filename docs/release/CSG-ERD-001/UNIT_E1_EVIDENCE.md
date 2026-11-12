# E-1 Evidence Report — QR canonical channel

Directive CS-ERD-001, unit 4 of 4. Local commit only (SHA in the
final report). Production LOCKED; no push/merge/deploy.

## Files changed

- `app/channels.py`: QR added as the 9th canonical
  channel (`CANONICAL` + `_RAW_MAP` + docstring).
- `app/payment_methods.py`: QR defaults to the
  registered `qr_checkout` method (inferred-from-channel,
  hint-labelled per module contract); method hints
  extended to ("POS", "WEB", "QR").
- `app/nl_search.py`: "qr" word maps to the QR channel
  filter.
- `tests/test_detection.py`: taxonomy test (QR
  canonical, 9 channels, bogus-rail UNMAPPED preserved),
  seed summary rewritten (zero UNMAPPED + QR row +
  bogus-rail alert control), matrix 88 → 99 cells with
  QR-cell assertions.
- `tests/test_universal_core.py`: QR payment-hint test.
- No frontend change: panels render channels/unmapped
  generically; no cell-count pins exist there.
- No `models.py` change: the ingest `Channel` enum
  already carried QR.

## Tests executed

- E-1 slice: `test_detection` + `test_universal_core` +
  `test_universal_security` — 75 passed / 4 skipped.
- Detector census re-confirmed: 10/11 OPERATIONAL,
  ML_ANOMALY NOT_IMPLEMENTED (untouched, still honest).
- `ruff check` — green (at commit).

## Security impact

- Positive (minor): QR traffic is now attributed to a
  real channel instead of UNMAPPED; detector coverage
  matrix gains 11 honest QR cells.
- No weakening: UNMAPPED fallback preserved and
  re-tested; no auth/authz/audit change.

## Regression evidence

- Swept for channel-count pins: only rule_results (8
  rules), telecom adapters (8), and Atlas categories
  (8) carry the digit — all unrelated surfaces.
- Full backend suite + frontend + hosted gate: final
  battery (next step).

## Remaining risks

- None new. NL "qr" word mapping is additive (no prior
  test covered bare "qr").
