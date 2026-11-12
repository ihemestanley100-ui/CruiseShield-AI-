# CRUISESHIELD-AI-DEMO-REMOVAL-MATRIX.md

§1 terminology audit (2026-11-05). Every `demo` occurrence classed
by disposition. Slices execute in order; no slice lands without
its tests updated and passing.

## Dispositions

- G1 Backend env names (DEMO_USERS, DEMO_WRITE_TOKEN,
  NEXT_PUBLIC_DEMO_WRITE_TOKEN): RETAIN. Deployment contract +
  R5/R6 traceability; not user-facing branding. See D-019.
- G2 Backend routes: IMPLEMENTED 2026-11-05 — /api/v1/platform/*
  canonical + deprecated /demo/* aliases; ADMIN prefixes cover
  both; suite 401 pass. Contract values migrated (platform-token,
  synthetic scope, evt_/trace_ IDs); env names + demo_viewer
  retained per D-019.
- G3 Frontend /demo route + nav hrefs + landing CTAs: PROPOSED
  rename to /platform — same confirm. Files: app/demo/,
  cases/[caseId]/page.tsx:287 + audit/page.tsx:58,
  investigations/[id]/page.tsx:111, network/[txnId]/page.tsx:139,
  not-found.tsx, page.test CTA asserts.
- G4 User-facing strings: "Check the demo server and retry",
  "Fetching the latest demo state", "The demo state is intact",
  "No demo screen lives at this address", "Open the demo":
  PROPOSED reword — same slice as G3.
- G5 i18n "demo" namespace (12 locales + review-kit TSVs):
  rename atomically with G3/G4 (parity tests forbid partial).
- G6 Seed/contract IDs (evt_demo_*, trace_demo_*, synthetic_demo,
  "Deterministic demo risk score"): data-contract change; needs
  fixture regen + loader-gate review. Later slice, owner-visible.
- G7 Tests + mocks mirroring the above: move WITH their slice;
  assertions updated, never weakened or deleted.
- G3–G5 Frontend: IMPLEMENTED 2026-11-05 — /platform route,
  nav/CTAs, api client paths + idents, usePlatformSession, 12
  locales key-renamed, EN values reworded, TSVs + inventory
  regenerated (mechanics calibrated, re-validated). Non-EN
  VALUES gated for native-speaker review (no machine-drafted
  product copy); modeMock/demo_viewer/env retained.
- G8 Frozen history (*-evidence/, qa/, HACKATHON_*, SUBMIT_*,
  blueprints, closed logs): EXEMPT. Rewriting falsifies records.
- G9 Live registers/docs: update references as each slice lands.
- G10 Contract values (action demo.reset, scope "demo", actor
  demo-token): RETAIN (R2 authorization semantics). See D-019.

## Scale (case-insensitive substring ceilings)

Backend src 16 files; frontend src ~36; tests ~46; live docs
~150 (mixed live/frozen); frozen evidence ~70. Line-level
confirmation done for user-facing strings (G3/G4 hits above);
remainder confirmed per-slice before editing.
