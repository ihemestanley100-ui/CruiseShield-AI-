# I18N-02 REVIEWER HANDOFF PACKAGE (Batch 0)

Owner gives one TSV + these instructions to each nominated reviewer.
No reviewer contact by the agent. Kit: docs/UGLS_REVIEW_KIT/
(11 TSVs + GLOSSARY.md + README.md — 13 files).

## Per-locale assignment

| Locale | File | Reviewer (owner fills) | Status |
|---|---|---|---|
| ar | ar.tsv | ___ | pending |
| es | es.tsv | ___ | pending |
| fr | fr.tsv | ___ | pending |
| ha | ha.tsv | ___ | pending |
| hi | hi.tsv | ___ | pending |
| ig | ig.tsv | ___ | pending |
| ja | ja.tsv | ___ | pending |
| pt | pt.tsv | ___ | pending |
| sw | sw.tsv | ___ | pending |
| yo | yo.tsv | ___ | pending |
| zh | zh.tsv | ___ | pending |

One reviewer may cover 2+ locales they command natively.

## Reviewer instructions (send verbatim)

1. Open your locale TSV. Columns: key | en_source | draft |
   origin | same_as_source | en_vars | draft_vars | vars_ok.
2. Correct the `draft` column where the machine draft is wrong,
   unnatural, or inconsistent with GLOSSARY.md.
3. Translate the 17 missing `detection.*` keys (listed in
   docs/I18N_NATIVE_REVIEW_PACK.md; your TSV shows English fallback).
4. Keep every `{placeholder}` EXACTLY as in en_source
   ({count}, {role}, {ids}). Never translate IDs, scores, evidence
   values, decision labels, or the brand `CruiseShield AI`.
5. ar reviewer only: triage the 32 extra keys (mark keep/drop).
6. Return the edited TSV + one sign-off line:
   "Reviewed <locale> on <date> — <name>."

## Maintainer merge procedure (after owner delivers TSVs)

1. Validate: vars match en per row; no empty drafts; UTF-8 intact.
2. Merge into frontend/lib/i18n/locales/<locale>.ts.
3. Run locale-diff parser (expect 0 missing) + hosted vitest
   dictionaries suite (needs PKG-01) → file log as evidence.
4. I18N-02 → CLOSED_VERIFIED only after sign-offs + green run.

## Acceptance criteria

- All 11 TSVs returned with sign-off lines.
- vars_ok true on every row (mechanical check).
- No machine-drafted row left unreviewed (origin column audit).
- Hosted vitest dictionaries tests green on merged files.

## Current state

Reviewers: NONE nominated. TSVs returned: 0/11. I18N-02 stays
BLOCKED_EXTERNAL_DEPENDENCY. Nothing marked complete.
