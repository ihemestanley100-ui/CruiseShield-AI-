# CRUISE ORBIT — Test and Acceptance Matrix

Date: 2026-11-03 · Design (not implemented).

## Backend (pytest, hermetic: mock-transport fixtures, no live calls)

- Provider contract tests (NullProvider honesty; each adapter's
  timeout/retry/quota paths; malformed-payload rejection).
- Coordinate/bbox validation incl. antimeridian + poles.
- SGP4 determinism: fixed TLE + epoch → fixed position (golden).
- Score-immutability regression: orbit writes CANNOT alter any
  risk/decision field (attempt → 403 + audit).
- Synthetic-separation: mixed-namespace query without flag → 400.
- Freshness-labelling: stale/expired fixtures render badges, never LIVE.
- Auth/RBAC: `orbit_read`/`orbit_manage` matrix incl. 401/403/503 paths.
- Audit: links/acks/config-changes produce entries with trace IDs.

## Frontend (vitest + browser)

- Component tests per screen (fetch mocks; empty/error/stale states).
- Honesty tests: stale feed shows badge; no LIVE label on cached data.
- i18n key coverage for new strings; RTL snapshot; a11y pass;
  keyboard + reduced-motion checks.
- 8-route-style smoke extension: `/orbit` + deep links with DOM capture.

## Acceptance gates

- All suites green (existing + new); secret-scan + pip-audit clean.
- Live verification plan executed (separate doc) before ANY
  live-data claim. No PASS without captured provider evidence.
