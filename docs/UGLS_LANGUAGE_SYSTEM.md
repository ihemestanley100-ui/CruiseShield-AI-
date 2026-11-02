# UGLS — UNIVERSAL GLOBAL LANGUAGE SELECTOR

Production-grade language selection + internationalisation for
CruiseShield AI. Zero new dependencies (Intl APIs + React only).

## Architecture

- Registry: `frontend/lib/i18n/registry.ts` — 221 entries, every
  ISO 639-1 language plus BCP 47 regional variants (pt-BR,
  zh-Hans, sr-Latn, ha-Arab, ...) and 639-2/3 indigenous
  additions (Cherokee, Hawaiian, Mohawk, Syriac, ...). Each
  entry: tag, ISO code, native endonym, exonym, family (28),
  RTL flag (19 RTL), translation status.
- Dictionaries: `frontend/lib/i18n/locales/{en,fr,ar}.ts` —
  165 keys in 6 namespaces (nav/auth/workflow/decision/
  landing/selector). English is the source and the fallback.
- Lookup: `dictionaries.ts` — BCP 47 fallback (fr-CA→fr→en),
  {var} interpolation, list lookup, Intl.PluralRules engine,
  missing-key ledger. Keys missing even in English render an
  explicit `[key]` marker so they can never pass silently.
- Provider: `context.tsx` — persisted preference
  (`cruiseshield-locale`), browser detection with explicit
  override, document lang/dir sync, no-flash init script in
  `app/layout.tsx` (RTL set interpolated from the registry:
  single source of truth).
- Formatting: `format.ts` — Intl dates/numbers/money (integer
  minor units, mirrors formatKobo)/relative time, all with
  English fallback on bad input.
- UI: `components/language-selector.tsx` — globe + native
  name + chevron, rounded orange border; searchable listbox
  with full keyboard support, screen-reader labelling,
  44px touch targets, per-language status badges.

## Translated surface (converted components)

App shell + nav, login gate, workflow strip, section nav,
human-decision form chrome, full landing page. Data values
(IDs, risk scores, evidence, server decision labels,
statuses) are NEVER translated — switching locales cannot
corrupt records or scores (pinned by test).

## Deliberate non-goals (honest limits)

- fr/ar are machine-drafted, human review pending (hence
  'partial', never 'translated').
- 216 registry languages have no dictionary: selectable for
  discovery, UI falls back to English with an explicit badge.
- Deep page content (demo dashboard, investigation detail,
  network, replay, evidence, audit, notifications) is not
  yet extracted — namespaces exist, keys pending. See the
  coverage report for the component matrix.
- No settings page exists in the product (omitted: no
  backend); the persistent global selector IS the language
  setting — no fake settings UI was added.
- Grammatical gender: handled at dictionary level (separate
  keys where needed); no engine magic is claimed.
- RTL verified at attribute level (lang/dir, layout
  direction); visual RTL QA needs a real browser (FE-35).
