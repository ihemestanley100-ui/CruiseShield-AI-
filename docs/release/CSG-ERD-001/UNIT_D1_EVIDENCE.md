# D-1 Evidence Report — audit-chain integrity

Directive CS-ERD-001, unit 1 of 4. Local commit only (SHA in the
final report). Production LOCKED; no push/merge/deploy.

## Files changed

- `app/config.py`: `AUDIT_CHAIN_KEY*` config, 32-byte
  minimum, hex/base64/raw decoding, key-id validation,
  `audit_chain_armed()` / `audit_chain_misconfigured()` /
  `audit_chain_keyring()` (current + previous epoch).
- `app/store.py`: arming in `__init__` before load/seed
  (fail-closed `ValueError` on invalid config),
  `arm_audit_chain()`, `audit_verification_report()`
  (config ring + live key; counts/ids/digests/codes only).
- `app/main.py`: `audit_chain_verified` health check —
  PASS / NOT_CONFIGURED / FAIL + position; added to the
  exempt set (A-1 owns status semantics; interim state
  documented in the findings matrix).
- `.env.example`, `docs/RENDER_6_ENV_REGISTER.md`: new
  variable names + generation/rotation notes (names only).
- `tests/test_audit_arming.py`: 16 tests (new file).

## Tests executed

- New: `tests/test_audit_arming.py` — 16 passed.
- Focused slice: arming + audit_chain + ingest_audit +
  config_safety + audit_store + audit_export — 52 passed
  (16 new + 36 pre-existing, zero pre-existing changed).
- `ruff check app tests` — green.
- Full backend suite + frontend + hosted gate: final
  battery after E-1 (per directive §5).

## Security impact

- Positive: sealing is now configurable and active when
  armed; invalid config fails closed at construction
  (cannot boot silently unsealed); tamper is detected via
  the verification report and health check.
- No weakening: auth/authz/CSRF/audit-append paths
  untouched; legacy entries never gain false integrity.
- No secrets: all test key material is synthetic
  (`b"e" * 32` class); reports leak-tested (key hex and
  digests asserted absent from health JSON).

## Regression evidence

- Pre-existing audit/health assertions unchanged and
  green (`PASS sealed=1 total=N` string, `never_fails`
  check, `status in (healthy, degraded)` all hold).
- New check key is additive; no route added/removed;
  no frontend change in this unit.

## Remaining risks

- Interim: verification FAIL does not flip `status`
  (closes in A-1).
- Health verification is O(sealed) per call — noted
  for the C-1 runbook; negligible at current scale.
- Real key ceremony still owes D-018; operator-managed
  keys are procedural discipline, not code.
