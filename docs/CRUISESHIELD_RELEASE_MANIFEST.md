# CRUISESHIELD RELEASE MANIFEST — CS-FRC-2026-001 §13.4

Date: 2026-11-04. Branch `production-launch` @ `ff7052bdf0ac48a68f69c3937d9b8708ca265354`.
Per-file record (524 rows): `PUBLIC_REPOSITORY_RELEASE_MANIFEST.md`. This cover
states policy, counts, and the gate; it does not duplicate the row table.

## Counts

544 files total → **157 INCLUDE** / **387 EXCLUDE** (drift-patched closure round). No category-I
sensitive/prohibited file found. Repo-wide secret scan fresh-clean.

## Include policy

- A source, B config, C tests, D docs/kit (incl. 11 review TSVs + inventory,
  required in-tree by the freshness tests). FRC-001-owned changes included:
  token-cap code+tests, regenerated kit, `.gitattributes`, `render.yaml` var.
- Suffix /J marks pre-existing owner work, preserved byte-for-byte.

## Exclude policy (established exclusions, upheld)

- E: QA evidence (screenshots under `browser-evidence/`, etc.).
- F/G/H: scratch/probe dirs (`qa/`, `qa-scratch/`, `.edge-d-probe/`,
  `tmpw_ta9ikh/`), logs, one-off probe scripts, build artifacts.
- Secrets: `.env` is git-ignored and unlisted; no `.env`/keys tracked.

## LICENSE (no selection made)

MIT (simplest permissive) / Apache-2.0 (permissive + patent grant) /
GPL-3.0 (copyleft) / proprietary (conflicts with hackathon public-repo norms).
`LICENSE` prepared only after owner selection.

## Gate — STATUS: PROPOSED

Nothing staged, committed, or pushed. After owner manifest approval: stage
approved paths → final secret scan → final suites → owner-messaged commit →
push ONLY with explicit authorization → verify public tree + record full SHA.

## Telecom Identity (2026-11-07, uncommitted)

New: app/telecom_registry.py, app/telecom_providers.py,
app/telecom_verify.py, frontend/components/telecom-section.tsx (+test),
tests/test_telecom_*.py (5 files, 58 tests), docs/TELECOM_IDENTITY.md.
Extended: app/connectors.py (+8 adapters), app/config.py, app/store.py,
app/main.py (+8 routes), frontend/lib/api.ts, 4 pages, render.yaml,
.env.example, zero-gap matrix (TEL-01..TEL-09). Backend green;
frontend unexecuted (node EPERM); live providers none (TEL-08).

## Geointelligence OS (2026-11-07, uncommitted)

New: app/intel_common.py, app/intel_auth.py,
app/identity_verify.py, app/address_verify.py,
app/location_obs.py, app/intel_providers.py,
app/investigation_map.py, frontend geointel-map +
intel-verify-sections + intel-admin-panels (+2 test files),
tests/test_geointel_*.py (7 files, 56 tests),
docs/GEOINTELLIGENCE_OS.md. Extended: app/ip_intel.py
(geolocation), app/connectors.py (+9 specs), app/config.py,
app/store.py, app/main.py (+22 routes), api.ts, 2 pages,
render.yaml, .env.example, matrix (+13 rows -> 137).
Backend green; frontend unexecuted (node EPERM); live none.

## UFI slice (2026-11-07, uncommitted)

New: app/payment_methods.py, app/institutions.py,
app/parties.py, app/typologies.py, app/alerts.py,
app/tracing.py, app/altpayments.py, app/reports.py,
frontend tracing-section (+test), tests/test_universal_core.py
(30), tests/test_universal_routes.py (9),
docs/UNIVERSAL_INTEL_OS.md. Extended: app/store.py
(fraud alerts + traces), app/main.py (+18 routes), api.ts
(UFI helpers + patchJson), investigations page, matrix
(+15 rows -> 152). Backend green; frontend unexecuted
(node EPERM); live none.

UFI slice 2 (2026-11-07): monitoring.py, industry_adapters.py, tracing edge-upgrade, +8 routes, monitoring/industry UI + tests (7), slice2 tests (15), security tests (8); matrix +5 rows -> 157.

UFI slice 3 (2026-11-07): intel_tools.py, agents.py grants (11 tools), fleet_readiness, related_investigations, +1 route, AI tests (9), integration tests (6), contract tests (2); matrix +4 rows -> 161 (UFI-AI closed).

SEC slice (2026-11-07): api_credentials.py, trusted_devices.py, auth keyring, abac client kind, +6 routes, sec tests (13), render.yaml + .env.example rotation var, PKG-08 packets; matrix 161 rows (133 closed).

UFI closeout (2026-11-07): typology canonical-id fix, e2e + scenarios + fleet + perf tests (20), gen_closeout.py + UFI_CLOSEOUT.md; matrix +2 rows -> 163 (135 closed).

Agent OS (2026-11-07): orchestration/nl_search/retrieval/conversations modules, +2 tools, agent configs, +11 routes, assistant shell + tests, AGOS tests (24); matrix +8 rows -> 171 (142 closed).

Recovery OS (2026-11-07): recovery/rules/caps modules, fund-recovery agent + RECOVERY intent, +14 routes, recovery UI + tests, REC tests (20), D-058 packet; matrix +8 rows -> 179 (149 closed).
