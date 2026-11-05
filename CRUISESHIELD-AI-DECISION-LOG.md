# CRUISESHIELD-AI-DECISION-LOG.md

Architectural, product, security, data, infrastructure, and
governance decisions. Dates marked "session record" come from
conversation history whose exact timestamp was not preserved;
dated entries cite dated evidence. Pending items are explicit —
silence is not approval.

## Confirmed decisions

### D-001 — $0 hard ceiling, free-tier only
- Date: session record (standing constraint).
- Owner: project owner.
- Decision: total infra/ops spend capped at $0; free plans only;
  no paid trials, billing changes, or wildcard CORS.
- Alternatives rejected: paid Render/DB tiers, paid Meta quota.
- Consequences: PG scratch-only in CI; Netlify/Render free limits
  bind; features needing paid infra stay BLOCKED.
- Evidence: gate registers, FINAL_ZERO_GAP_MATRIX.md.

### D-002 — R1–R4 demo-token remediation
- Date: session record. Owner: project owner (explicit approval).
- Decision: remove token bypass on admin demo routes (R1);
  server-side actor_id="demo-token" (R2); AI sub-cap/login (R3);
  evidence-package POST authorization (R4). Regression tests per
  fix; 17 green locally.
- Evidence: tests/test_demo_token_remediation.py,
  docs/DEMO_TOKEN_SECURITY_AUDIT.md.

### D-003 — R5 backend token server-side only
- Date: session record. Owner: project owner.
- Decision: DEMO_WRITE_TOKEN is a generated backend secret, never
  in frontend code, bundles, logs, or NEXT_PUBLIC variables.
- Evidence: docs/DEMO_TOKEN_OWNER_CONFIRMATION_REGISTER.md.

### D-004 — R6 frontend token stays empty
- Date: session record. Owner: project owner.
- Decision: NEXT_PUBLIC_DEMO_WRITE_TOKEN remains EMPTY in public
  deploys; writes require login session; no public fallback.
- Evidence: frontend/.env.example, render.yaml wording (B1 PASS).

### D-005 — Fail-safe open-demo preserved
- Date: session record. Owner: project owner (standing rule).
- Decision: unset secret keeps historic open-demo behavior; armed
  mode only when secrets configured. Never silently weaken.
- Consequences: live arming state must be verified, never assumed.

### D-006 — R09 F1–F4 hardening approved as specified
- Date: session record. Owner: project owner.
- Decision: bounded rate-limit buckets + expiry cleanup (F1);
  SESSION_SECRET ≥ 32 chars, fail closed (F2); audit log
  INVALID_CREDENTIALS without secrets (F3); HSTS with
  HTTP-dev/proxy handling (F4). F5 digest pinning prepared only.
- Evidence: app/ratelimit.py, app/config.py, app/auth.py, tests.

### D-007 — Hermetic PG-test fixtures (F-CI-01)
- Date: session record. Owner: agent implementation under owner
  repair authorization; release approval pending with owner.
- Decision: committed canonical fixture + generator; live
  `data/state.json` never a test input; LIVE_SIZE/HASH never
  edited to match drift.
- Evidence: tests/fixtures/canonical-state.json,
  tests/fixtures/canonical_seed.py.

### D-008 — Scratch PG in CI, never production (F-PG-01)
- Date: session record.
- Decision: disposable PostgreSQL service for migration coverage;
  SCRATCH_DATABASE_URL only; explicit skips when unavailable.
- Evidence: .github/workflows/security-gate.yml.

### D-009 — Netlify fix is the NextJS adapter, not a pin
- Date: session record.
- Decision: missing OpenNext adapter is the 404 root cause; no
  manual legacy plugin pin.
- Evidence: netlify.toml (base frontend, publish .next);
  live site still 404 at last check — fix unapplied (ISS-001).

### D-010 — Batch 1.1 scope boundary
- Date: session record.
- Decision: wire 3 routes end-to-end; 6 API-only with reasons;
  listAlerts library-only; zero new i18n keys; read-only GETs.
- Evidence: frontend/lib/api.ts, intel-panels.tsx, route pages.

### D-011 — IP / submission / publication rights
- Date: 2026-11-03 (owner confirmations) + session record (QIP).
- Owner: project owner. Decisions: logo SELF; submission YES;
  public repo YES; deploy YES (all subject to third-party
  licenses/competition terms); organizer/press reuse REVIEW
  (pending); historical .png.png reference RETIRED.
- Evidence: docs/FINAL_QIP1_CONFIRMATION_REGISTER.md.

### D-012 — Track / team / eligibility
- Date: 2026-11-03. Owner: project owner.
- Decision: INDIE DEVELOPER track; SOLO team; age/eligibility
  owner-confirmed.
- Evidence: FINAL_TRACK_AND_TEAM_REGISTER.md.

### D-013 — Framework v1.0 adopted
- Date: 2026-11-05. Owner: project owner (directive) /
  agent-recorded.
- Decision: Universal Zero-Gaps framework governs; existing
  evidence keeps primacy; no re-labeling of verdicts.
- Evidence: CRUISESHIELD-AI-FRAMEWORK-ALIGNMENT.md.

### D-019 — Naming migration: /platform canonical (CONFIRMED)
- Date: 2026-11-05. Owner: directive-confirmed.
- Decision: migrate routes/strings/IDs to platform naming;
  RETAIN env names (DEMO_USERS, DEMO_WRITE_TOKEN,
  NEXT_PUBLIC_DEMO_WRITE_TOKEN), demo_viewer role, and
  deprecated /api/v1/demo/* aliases (deployment-affecting).
  Final alias removal needs separate owner confirm.
- Evidence: removal matrix G1/G10; suite 401 pass.
- 2026-11-05 addendum: G3–G5 done; non-EN locale VALUES stay
  native-review-gated (keys renamed, EN reworded). Frontend
  suites unverifiable in sandbox (node EPERM); hosted CI is
  the behavioral proof gate.

### D-020 — Coverage dependencies (PREPARED, pins verified)
- Date: 2026-11-05. Owner: approval pending.
- Proposal: pin pytest-cov (py3.13/pytest9) + @vitest/coverage
  provider (vitest 3) in locks with hashes; thresholds + CI
  enforcement.
- Evidence (slice-4, PyPI-fetched 2026-11-05): pytest-cov 7.1.0
  py3-none-any `a0461110…d4678`; coverage 7.10.6 win_amd64
  `62805529…79d32` + manylinux_x86_64 `0f3f56e4…d4f27`; lock already
  carries pytest 9.0.3 + pluggy 1.7.0 (satisfy `pytest>=7`,
  `pluggy>=1.2`); py3.13 needs no tomli. Vitest side: provider
  3.2.7 == locked vitest 3.2.7 (zero-conflict; npm hash pending
  networked npm). Lock churn still needs owner approval.

### D-014 — Tenancy scope (PREPARED, dev implementation green)
- Date: 2026-11-05. Owner: approval pending.
- Proposal: multi-tenant (D-014 recommendation in execution order).
- Evidence (slice-4): app/tenancy.py enforcement core + 11
  adversarial tests green (cross-tenant read→None, write→deny,
  enumeration filter, default-tenant back-compat); PG
  MIGRATION_5_2_TENANCY additive prep in app/models_pg.py (scratch
  execution pending GAP-015). API-boundary wiring awaits D-014
  approval; no existing behavior changed.
- Evidence (slice-5): domain + handler enforcement wired
  (cases.record_decision ctx, 7 handler gates, TENANT_DENIED→403
  contract) + 10 adversarial API tests green; all current users
  resolve to the default tenant so behavior is unchanged.
  User→tenant map still needs D-014. Banking pilot: profile +
  status machine + 7 mapping tests green → module TESTING, other 44
  NOT_STARTED.
- Evidence (slice-6): fintech-payments pilot registered + walked to
  TESTING (+7 tests); industry matrix now 2 TESTING / 43 NOT_STARTED.

### D-021 — Detection signals derived, not persisted (IMPLEMENTED)
- Date: 2026-11-05. Owner: engineering (reversible; no prod impact).
- Decision: signal events compute deterministically from stored
  transactions + edges on every read (idempotent IDs, version-pinned,
  history immutable by construction). No new canonical state keys,
  so data/state.json shape + hash are preserved; no second source
  of truth. Persisted signal store with outcomes/audit is deferred
  to the PostgreSQL cutover (GAP-001), which can hold signal_events
  properly.
- Evidence: app/detection.py + app/channels.py + 4 APIs
  (/detectors, /signals/summary, /channels/summary,
  /detection/matrix) + 14 tests green; suite 483 passed.

## Pending decisions (BLOCKED until answered)

| ID | Question | Needed from | Blocks |
|---|---|---|---|
| D-014 | Tenancy scope: single-org or multi-tenant build | Owner | §12 FAIL, stages 12–13 |
| D-015 | License selection | Owner | Public repo certification |
| D-016 | Live Meta call: key + quota approval | Owner | GAP-014, AI lane |
| D-017 | Push/deploy feature branch | Owner | GAP-009, GAP-010 |
| D-018 | Backup keys + ceremony authorization | Owner | GAP-003 |
| D-019b | Remove deprecated /demo/* aliases | Owner | post-deploy |
| D-020 | Approve coverage-dep pins + lock churn | Owner | GAP-005 |
