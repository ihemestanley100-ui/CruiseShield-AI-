# UGLS Review Kit — linguist working files

One TSV per machine-drafted locale (fr, ar, ig, yo, ha, pt, es, zh,
hi, sw, ja). Each row is one English source key with its draft.
All 11 locales currently ship FULL 575-key drafts (see counts
below); nothing here is human-verified.

## Columns

- `key` — dotted source path (`namespace.key`, plural forms as
  `key.category`, list items as `key.index`).
- `en_source` — the English template (authoritative).
- `draft` — the machine draft under review.
- `origin` — `direct` (draft exists) or `fallback` (English shown;
  must be 0 rows unless a key was added without drafts).
- `same_as_source` — draft byte-identical to English. Expected for
  brand/data terms (`CruiseShield AI`, IDs); anything else needs a
  reviewer decision.
- `en_vars` / `draft_vars` — `{placeholders}` found in each side.
- `vars_ok` — placeholders identical on both sides. `false` rows
  need linguist sign-off (e.g. Arabic singulars legitimately drop
  `{count}` — "one audit event" needs no numeral — but confirm).

Cell escaping: tabs → space, newlines → literal `\n`.

## Current integrity snapshot (2026-11-05)

- Rows per locale: 602 (591 prior + 11 `detection.*` fallback).
  Fallback rows: 11 (detection namespace, machine drafts pending).
- `same_as_source`: prior counts + 11 detection fallback rows per
  locale — brand/data terms plus untranslated English, reviewer to
  confirm each.
- `vars_ok=false`: 0 everywhere except ar (8 rows, all `.one`
  plural forms dropping `{count}`; `{ids}` correctly kept —
  grammatically expected, awaiting sign-off).

## Workflow (normative: `docs/UGLS_HUMAN_REVIEW_REGISTER.md`)

1. Review per the register's 6-point checklist (correctness,
   placeholders, plurals, rendering, terminology, verbatim data).
2. Record named reviewer(s), date, version + source rev in the
   register. Do NOT edit these TSVs as the deliverable — ship
   corrected dictionaries + bump `version` in `meta.ts`.
3. Flip `review` to `human-reviewed` ONLY with named reviewers; the
   `isHumanVerified()` gate + full test suite enforce the rest.
4. Regenerate after any catalog change:
   `UGLS_REGEN_KIT=1 npx vitest run lib/i18n/review-kit.test.ts`
   (frontend/). Default test mode fails on a stale kit.

Machine-drafted output is NEVER labeled reviewed — in code, tests,
UI, kits, or reports.
