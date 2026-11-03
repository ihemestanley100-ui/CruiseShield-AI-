# UGLS-02 Task 2 — Complete Translation Coverage

Date: 2026-11-02. Registry: 221 entries (`frontend/lib/i18n/registry.ts`,
verified by parse). Dictionaries: 12 (`frontend/lib/i18n/locales/`).
English source: 575 keys. Full per-language table:
[UGLS_LANGUAGE_MATRIX_GENERATED.md](UGLS_LANGUAGE_MATRIX_GENERATED.md).
This document supersedes the UGLS-01 counts in `UGLS_COVERAGE_REPORT.md`
(historical; preserved as-is).

Correction 2026-11-02: the nine drafts were completed to full parity
during UGLS-02 final (code + parity gate pin it; kit-verified at 575
rows, 0 fallbacks — 571 + 3 common error keys + nav.skipToContent);
earlier 66-key / 11.6% figures below are superseded where they
describe current state.

## Tier summary

| Tier | Locales | Keys each | Count |
| ---- | ------- | --------- | ----- |
| translated (source) | en, en-GB, en-NG | 575 (100%) | 3 |
| partial, complete drafts | fr, ar | 575 (100%) | 2 |
| partial, full drafts (review pending) | ig, yo, ha, pt, es, zh, hi, sw, ja | 575 (100%) | 9 |
| unavailable (English fallback + badge) | remaining registry | 0 | 207 |
| TOTAL | | | 221 |

`en-GB` / `en-NG` resolve to the English dictionary through BCP 47
fallback and are therefore honestly `translated`. All eleven
dictionaried locales (fr, ar + nine drafts) hold exact key parity
with English — 575/575 each, gate test fails the suite on any drift
(`coverage.test.ts` → "holds every dictionaried locale at exact key
parity"). Fallback/ledger machinery stays tested via undictionaried
locales. Tier `partial` denotes review state (machine-drafted,
unreviewed), not key count.

## Priority order (directive §Task 2)

1. English — source, 100%. 2. French — complete draft, 100%.
3. Arabic — complete draft, 100%, six-category plurals.
4.–12. Igbo, Yoruba, Hausa, Portuguese, Spanish, Chinese, Hindi,
Swahili, Japanese — full machine drafts, 100% each, review pending. 13. Remaining 207
registered languages — available for selection, English fallback,
truthfully badged `unavailable` in the selector.

## Draft quality controls (all locales)

- Placeholders preserved 1:1 (`{role}`, `{a}`, `{b}`, `{count}`,
  `{ids}`, `{id}`, `{n}` …): a locale-switching integration test renders
  four components in fr/ar with zero `[key]` markers and an empty
  missing-key ledger; a dedicated test pins `{count}` interpolation in
  every shipped fr/ar plural template.
- Plurals validated per locale via `Intl.PluralRules`: en/fr two-form,
  ar six-form (zero/one/two/few/many/other). All 12 dictionaries ship
  complete plural maps (kit-verified; Arabic singulars drop `{count}`
  grammatically — flagged for linguist sign-off).
- Punctuation and script rendering verified in a real browser (Arabic
  RTL screenshots at 3 breakpoints + ha-Arab script-subtag page; French
  desktop page) — see `UGLS_RTL_BROWSER_VERIFICATION.md`.
- Terminology is machine-drafted throughout (including fr/ar): NOTHING
  outside English source is human-verified. See
  `UGLS_HUMAN_REVIEW_REGISTER.md`.

## What is NOT translated (by design, verified)

IDs, evidence values, risk scores/bands, server rule text, model IDs,
timestamps, brand name, tagline. English tagline/brand render verbatim
in all 12 dictionaries (convention, matching fr/ar UGLS-01 behavior).

## Honesty guarantees (tested, not claimed)

- `coverage.test.ts`: en key set non-trivial; all eleven
  dictionaried locales at exact parity (zero missing, coverage 1);
  undictionaried locale (`zu`) reports 0 with 100+ missing; full
  drafts pinned machine-drafted / never human-verified; summary
  counts 3 / 11 / 207+.
- `registry.test.ts`: unique BCP 47 tags (`Intl.Locale`-valid), status
  pins per tier, dictionary-tag fallback, browser-list matching.
- `dictionaries.test.ts`: variant fallback (fr-CA→fr, ar-EG→ar,
  en-NG→en), undictionaried fallback flagged with quiet ledger,
  `[key]` marker + ledger for keys missing even in English,
  interpolation, list fallback, plural selection, `{count}` template
  audit, flatten correctness.
