# UGLS Human Review Register

Date: 2026-11-02. Authority: `frontend/lib/i18n/meta.ts`
(`LOCALE_META`, `SOURCE_REV = "2026-11-02-ugls02"`,
`isHumanVerified()`). Rule: a locale is reported human-verified ONLY
when `review` is `source` (English) or `human-reviewed` with named
reviewers. Machine-drafted output is NEVER labeled reviewed — in code,
tests, UI, or reports.

## Register

| Tag | Version | Source rev | Review state | Reviewers | Updated |
| --- | ------- | ---------- | ------------ | --------- | ------- |
| en | 1.2.0 | 2026-11-02-ugls02 | source | — | 2026-11-02 |
| fr | 1.2.0 | 2026-11-02-ugls02 | machine-drafted | — | 2026-11-02 |
| ar | 1.2.0 | 2026-11-02-ugls02 | machine-drafted | — | 2026-11-02 |
| ig | 1.2.0 | 2026-11-02-ugls02 | machine-drafted | — | 2026-11-02 |
| yo | 1.2.0 | 2026-11-02-ugls02 | machine-drafted | — | 2026-11-02 |
| ha | 1.2.0 | 2026-11-02-ugls02 | machine-drafted | — | 2026-11-02 |
| pt | 1.2.0 | 2026-11-02-ugls02 | machine-drafted | — | 2026-11-02 |
| es | 1.2.0 | 2026-11-02-ugls02 | machine-drafted | — | 2026-11-02 |
| zh | 1.2.0 | 2026-11-02-ugls02 | machine-drafted | — | 2026-11-02 |
| hi | 1.2.0 | 2026-11-02-ugls02 | machine-drafted | — | 2026-11-02 |
| sw | 1.2.0 | 2026-11-02-ugls02 | machine-drafted | — | 2026-11-02 |
| ja | 1.2.0 | 2026-11-02-ugls02 | machine-drafted | — | 2026-11-02 |

(Versions corrected 2026-11-02 to match `meta.ts`, the declared
authority: all twelve at 1.2.0. All eleven non-en locales hold FULL
571-key machine drafts — kit-verified, 0 fallback rows — superseding
earlier 66-key figures wherever they describe current state.)

207 remaining registry languages: no dictionary, nothing to review;
any future dictionary starts as `machine-drafted` at 1.0.0 against the
then-current source rev.

## Version history (this programme)

- 1.0.0 — ig/yo/ha/pt/es/zh/hi/sw/ja meta placeholders (no content).
- 1.1.0 — en/fr/ar full extraction (571 keys); nine drafts shipped
  (66 keys each).
- 1.2.0 — en/fr/ar timestamp-template splits for `<bdi>` RTL isolation
  (textContent-identical; see RTL verification report). Drafts unchanged.

## What human review must cover (per locale, in order)

1. Correctness of chrome translations against the English source at the
   recorded source rev (re-draft on rev drift).
2. Placeholder integrity (`{vars}` present, untranslated, un-reordered
   unless grammar requires it — then the component call site must pass
   all vars).
3. Plural forms against `Intl.PluralRules` for the locale (ar: all six
   categories; fr: one/other with French 0/1→one behavior).
4. Script rendering and punctuation in-browser (RTL locales: bidi
   isolation of embedded Latin/data runs).
5. Terminology consistency (risk, evidence, audit, decision vocabulary).
6. No translated data values (IDs/scores/evidence must stay verbatim).

Review completion per locale requires: named reviewer(s), date,
version + source rev reviewed, and the `review` field flipped to
`human-reviewed` in `meta.ts` — a code change, so it ships with the
normal test gate (parity + switching + browser spot-check).

## Review kit (ready 2026-11-02, linguists pending)

`docs/UGLS_REVIEW_KIT/` — one TSV per locale (571 rows each) built
from the production `lookup()` machinery: en source, draft,
direct/fallback origin, same-as-source flag, per-side `{vars}` and
match flag. Freshness pinned by
`frontend/lib/i18n/review-kit.test.ts` (regen:
`UGLS_REGEN_KIT=1 npx vitest run lib/i18n/review-kit.test.ts`).
Integrity snapshot: 0 fallback rows; same-as-source 6–25/locale
(brand/data terms, reviewer to confirm each); placeholder mismatches
0 except ar (8 `.one` singulars dropping `{count}` — grammatically
expected, `{ids}` kept — awaiting sign-off). Kit files are working
reference, not the deliverable: ship corrected dictionaries + meta
bumps.
