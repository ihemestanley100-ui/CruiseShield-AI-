# A-1 Evidence Report — truthful system health

Directive CS-ERD-001, unit 2 of 4. Local commit only (SHA in the
final report). Production LOCKED; no push/merge/deploy.

## Files changed

- `app/main.py`: `_qualified_status()` — unavailable (store
  FAIL) / degraded (blocking FAIL or exempt FAIL) /
  operational_with_gaps (optional service unconfigured;
  unselected pg is N/A, never a gap) / healthy (all
  applicable PASS). Closes the D-1 interim risk: a
  verification FAIL now degrades the headline.
- `frontend/components/system-status.tsx`: headline keys
  off the qualified status — allOk only on healthy, new
  gapsOk headline on operational_with_gaps, no positive
  headline on degraded/unavailable.
- 12 locale files: new `gapsOk` key (machine-drafted,
  parity-checked; reviewer handoff covers human review).
- `tests/test_health_qualified.py`: 6 tests (new file).
- 6 pre-existing backend tests updated with A-1
  justification comments (old "healthy" encoded the
  defect): api_flow (2), e2e_journey_m3, flow_direct,
  homepage_routing, ingest_audit, pg_migration (2).
  pg-unreachable "degraded" assertions untouched.
- `frontend/components/system-status.test.tsx`: gaps
  fixture + 2 new state tests (healthy-reserved,
  unavailable).

## Tests executed

- New backend: `tests/test_health_qualified.py` — 6/6.
- Backend slice (health-asserting files): 43 passed /
  17 socket-skipped (pre-existing skips, unchanged).
- `ruff check` — green.
- Frontend: authored but NOT executed locally — node is
  EPERM-blocked in this sandbox (re-proven this unit).
  Static verification: component re-read, gapsOk present
  exactly once in all 12 locales (mechanical parity
  check). Hosted CI executes vitest/tsc/build.

## Security impact

- Positive: eliminates the false "All systems
  operational" over unconfigured AI/audit; tamper and
  misconfiguration now degrade the headline.
- No weakening: no auth/authz/CSRF change; /ready
  untouched; server template renders the qualified
  status raw (no separate headline logic to drift).

## Regression evidence

- All runnable pre-existing health assertions updated
  intentionally with comments; nothing weakened to
  pass. Socket/PG-gated updates verified by reading
  (they execute in hosted CI).

## Remaining risks

- Frontend execution pending hosted CI (sandbox
  limitation, not a code risk; change is minimal and
  re-read).
- `gapsOk` translations are machine-drafted (established
  precedent; I18N-02 review path applies).
