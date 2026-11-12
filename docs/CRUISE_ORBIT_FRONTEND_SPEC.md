# CRUISE ORBIT — Frontend UI/UX Specification

Date: 2026-11-03 · Design (not implemented). Route: `/orbit`
+ deep links; shell/nav/landing integration (no removals).

## Screens

1. **Orbit overview** — provider health cards, freshness ages,
   synthetic-vs-live banner, quick links. Honest empty states.
2. **Pass predictor** — sat selector + observer lat/lon + hours
   → pass table (AOS/LOS, max elevation). Server-computed.
3. **Imagery explorer (metadata-first)** — bbox + date range →
   scene table (mission, date, cloud %, license, attribution) +
   deep link-out to provider browser. NO raster viewer at
   launch (keeps licensing + bandwidth honest).
4. **Vessel view** — AIS snapshot table + SVG plot (reuse
   orbital-explorer SVG discipline: NO meaning in styling),
   "coastal receivers, not for navigation" label.
5. **Ports/infra** — reference table + region filter.
6. **Observation detail** — full provenance card: source, obs +
   retrieval times, coords, confidence, freshness badge,
   license, limitations, synthetic flag.
7. **Link-to-investigation** — picker + note → audited link;
   visible from the investigation studio.

## UX rules (binding)

- No `LIVE` label unless freshness-verified at read time.
- Maps: server-side SVG/static first (zero new deps, CSP-safe).
  Leaflet/CDN maps are Phase 2 ONLY with a CSP carve-out review
  (connect/img-src) + privacy review. Never silently upgrade.
- i18n keys for all strings (12-locale pattern); RTL-safe SVG;
  keyboard/a11y parity with existing explorers; reduced-motion
  path for any animation.
- Reuse: AppShell, Breadcrumbs, RiskBadge-style dots,
  AuditList, decision-form patterns, `userErrorMessage`.
