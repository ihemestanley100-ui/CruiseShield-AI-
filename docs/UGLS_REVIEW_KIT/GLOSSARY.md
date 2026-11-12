# UGLS Glossary — verbatim terms + translator rules (§K)

Authoritative English source: `frontend/lib/i18n/locales/en.ts`.
Machine drafts live in `docs/UGLS_REVIEW_KIT/*.tsv`; nothing there is
human-verified. Normative workflow: `docs/UGLS_HUMAN_REVIEW_REGISTER.md`.

## 1. NEVER translate (byte-identical in every locale)

- `CruiseShield AI`, `CruiseShield AI™`
- Product routes and identifiers: `/platform`, `/demo`, case / evidence
  / transaction / audit IDs, trace IDs, run IDs
- Rule + model identifiers: `R-001`, `risk-score-v1`, band codes
  (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`) where shown as data badges
- HTTP/API tokens, status codes, timestamps, hashes, numerals
- Placeholder variables: `{count}`, `{ids}`, `{name}` — keep exact
  spelling; Arabic singulars may drop `{count}` only with sign-off
  (see kit README `vars_ok` rule)

## 2. Translate with domain care

- investigation, evidence, audit trail, risk assessment, alert,
  case, decision, provenance, replay, simulation, watchlist
- Prefer established financial-crime / AML terminology in the target
  language; keep UI labels short enough for badge and table layouts.
- Right-to-left locales (ar, ha): keep embedded IDs/`{vars}` in
  logical order; verify badge rendering per the review register.

## 3. Translator checklist (per locale)

1. Every one of the 575 keys has a reviewed `draft` (0 `fallback`).
2. Every `vars_ok=false` row resolved and signed off.
3. Every `same_as_source` row confirmed verbatim-intended or fixed.
4. Plurals render for 0/1/2/many; RTL layout checked where applicable.
5. Corrected dictionaries shipped + `version` bumped in `meta.ts`;
   named reviewer(s), date, source rev recorded in the review register.
6. `review` flips to `human-reviewed` ONLY after 1–5 with named humans.
