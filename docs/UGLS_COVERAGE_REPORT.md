# UGLS COVERAGE REPORT (2026-11-02, from test run)

Source keys (en): 165 across nav/auth/workflow/decision/
landing/selector. Registry: 221 entries, 28 families, 19 RTL.

## Per-locale key coverage

| Locale | Keys | Coverage | Status |
|--------|------|----------|--------|
| en, en-GB, en-NG | 165/165 | 100% | translated (source) |
| fr | 165/165 | 100% | PARTIAL — machine-drafted, review pending |
| ar (RTL) | 165/165 | 100% | PARTIAL — machine-drafted, review pending |
| 216 others | 0/165 | 0% | unavailable — English fallback, badged |

No universal-coverage claim is made: 2 of 221 locales have
dictionaries; both need human review before 'translated'.

## Component conversion matrix

| Area | Status |
|------|--------|
| App shell / nav / topbar / drawer | CONVERTED |
| Login gate + auth errors | CONVERTED |
| Workflow strip / section nav | CONVERTED |
| Decision form chrome (labels verbatim) | CONVERTED |
| Landing (nav/hero/panels/strips/footer) | CONVERTED |
| Language selector itself | CONVERTED |
| Demo dashboard content | NOT CONVERTED (keys pending) |
| Investigation / case detail | NOT CONVERTED (keys pending) |
| Network / replay / evidence / audit lists | NOT CONVERTED (keys pending) |
| Notifications / toasts | NOT CONVERTED (keys pending) |
| Data values (IDs/scores/evidence/labels) | INTENTIONALLY UNTRANSLATED |

## Quality gates (all green)

- coverage.test.ts enforces fr/ar key parity (fails on drift).
- locale-switching.test.tsx renders converted surfaces in
  fr+ar asserting zero `[key]` markers and verbatim data.
- Registry, lookup, plural, format, persistence, keyboard,
  screen-reader and RTL-direction tests: 49/49 green.
