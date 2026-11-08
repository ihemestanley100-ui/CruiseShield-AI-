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

### D-014 — Tenancy scope (DECIDED MULTI-TENANT, map implemented)
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
- Evidence (new-surface tenant slice, 2026-11-06): legacy
  connection ``tenant`` fallback + canonical ``tenant_id`` stamps on
  connections, SAR/DSR/holds, and agent plans/runs; connector,
  governance, and agent handlers filter/enforce by request context;
  agent graph reads use tenant-visible event edges. +12 tests in
  tests/test_tenant_new_surfaces.py green; touched-surface bundle
  103 passed / 4 skipped. User→tenant map still needs D-014.
- Evidence (txn-evidence tenant slice, 2026-11-06): shared
  tenancy.visible_graph helper (edges inherit owner via source
  events); get_transaction/get_risk/get_graph gate the record and
  evaluate over visible inputs; agent graph tool refactored onto
  the helper; +3 tests (file now 15 green); full backend 908
  passed / 141 skipped with same sandbox-only 1F+2E. D-014 map
  still pending; legacy intelligence endpoints remain unscoped
  follow-ups.
- Evidence (alert tenant slice, 2026-11-06): _visible_alerts
  helper filters alerts/notifications/mark-all by visible
  transaction ids; +3 tests (file now 18 green); full backend
  911 passed / 141 skipped with same sandbox-only 1F+2E.
  D-014 map still pending.
- Evidence (DI-intel tenant slice, 2026-11-06):
  tenancy.visible_state view (visible txns/nodes/edges/events/
  investigations) wired into all 9 derived-intel handlers
  (device/ip/geo/link x3/overlay/risk-intel/intel-evidence);
  +5 tests (file now 23 green); full backend 916 passed / 141
  skipped with same sandbox-only 1F+2E. D-014 map still
  pending; replay/ai-runs remain follow-ups.
- Evidence (replay/AI tenant slice, 2026-11-06):
  get_replay serves visible_state; ai-analysis/followup gate
  investigation+transaction and stamp runs with request
  tenant; get_ai_run enforces reads; followup prior context
  and case summaries filter by tenant; +5 tests (file now
  28 green); full backend 921 passed / 141 skipped with
  same sandbox-only 1F+2E. D-014 map still pending;
  simulations remain follow-up.
- Evidence (simulation tenant slice, 2026-11-06):
  post_simulation gates the target transaction, recomputes
  over tenant-visible inputs, and stamps new records;
  investigation-page simulation context filters by tenant;
  +3 tests (file now 31 green); full backend 924 passed /
  141 skipped with same sandbox-only 1F+2E. All planned
  handler surfaces scoped; D-014 user→tenant map remains
  the only TEN-01 follow-up.
- Evidence (post-push-audit batch): capital-markets,
  insurance-pensions, crypto-assets profiles registered +
  walked to TESTING (+21 tests, 40/40 industry green);
  industry matrix now 5 TESTING / 40 NOT_STARTED. Full suite
  524 passed / 141 skipped / same sandbox-only 1F+2E.
- Evidence (v14.0 batch 2): fx-remittance, government,
  tax-revenue profiles registered + walked to TESTING
  (+21 tests, 61/61 industry green); industry matrix now
  8 TESTING / 37 NOT_STARTED.
- Evidence (v14.0 batch 3): remaining 37 modules registered +
  walked to TESTING (+259 tests, 320/320 industry green);
  industry matrix now 45 TESTING / 0 NOT_STARTED. Existing
  untouched-triple assertions retired (nothing untouched);
  order-dependent registry gates still green.
- Evidence (D-014 map, 2026-11-07): owner recorded MULTI-TENANT
  direction (CS-PRODUCT-CLOSURE-001 review constraints).
  USER_TENANTS map implemented (tenancy.parse_user_tenants /
  tenant_for_user / context_for_user, config.USER_TENANTS,
  _request_ctx wiring, .env.example documented); unknown users
  stay on org_primary. +10 tests/test_tenant_map.py green, 52
  tenancy suites green, 118 auth regression green. TEN-01
  CLOSED_VERIFIED.

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

### D-022 - MFA via TOTP + recovery codes, opt-in per role (IMPLEMENTED)
- Date: 2026-11-05. Owner: engineering (reversible; inert unless armed).
- Decision: server-enforced TOTP second factor (RFC 6238, ±1 step,
  persisted replay guard, 5-fail/15-min lockout) with single-use login
  tickets and 10 hashed one-time recovery codes per user. Secrets are
  HMAC-derived from SESSION_SECRET per user+enrollment counter — no
  plaintext secret persisted; re-enrollment retires the old secret.
  Required roles (MFA_REQUIRED_ROLES, default empty = opt-in) get
  pending sessions gated to MFA self-service until enrollment
  confirms; enrolled users step up via ticket challenge. Default is
  empty (not admin) so existing armed deployments keep working until
  the owner enrolls, then sets MFA_REQUIRED_ROLES=admin. Tokens
  (non-browser service credential) deliberately carry no MFA.
- Evidence: app/mfa.py + 6 APIs (/auth/mfa/enroll|confirm|status|
  challenge|disable|codes) + 23 tests green incl. RFC 6238 vectors;
  auth/revocation suites green (68 passed); login body unchanged for
  non-required roles.

### D-023 - Industry PILOT promotion requires evaluator + evidence (IMPLEMENTED)
- Date: 2026-11-05. Owner: engineering (reversible; no auto-promote).
- Decision: TESTING→PILOT moves only through the pilot evaluator
  (9 checks against the live rule engine + live routes + honesty
  gates) with a verifiable evidence reference; the promote endpoint
  is write-gated and audited. BLOCKED_EXTERNAL data requirements are
  reported as pilot-scope inputs, never faked. No module is
  auto-promoted; all 45 stay TESTING until an owner-backed pilot.
- Evidence: app/pilot.py + 2 APIs + 10 tests green.

### D-024 - Connector credentials by env reference, never stored (IMPLEMENTED)
- Date: 2026-11-05. Owner: engineering (reversible; additive APIs).
- Decision: connections persist env-var NAMES + non-secret params
  only; the API reports presence booleans, never values. CONNECTED
  requires a successful live handshake; real adapters without partner
  authorization honestly report AWAITING_CREDENTIALS / handshake
  missing. A synthetic-flagged loopback harness proves lifecycle,
  health (3-fail auto-suspend), and audit machinery in tests.
- Evidence: app/connectors.py + 8 APIs + 13 tests green; secret-value
  absence asserted across state, responses, and audit.

### D-025 - Central ABAC policy, new-surface enforcement (IMPLEMENTED)
- Date: 2026-11-05. Owner: engineering (reversible; additive).
- Decision: deny-by-default ABAC (authn + tenant match + role perm +
  session strength for sensitive kinds + legal-hold blocks) enforced
  on new endpoints (policy-check, agents, governance). Legacy
  endpoints keep existing gates; migration is incremental and must
  never weaken them. Token keeps normal read/write, never sensitive
  or manage-level actions.
- Evidence: app/abac.py + policy-check API + 8 tests green.
  Agent/governance subjects now take tenant from _request_ctx and
  their resources are tenant-stamped/filtered (+12 cross-surface
  tests in tests/test_tenant_new_surfaces.py).

### D-026 - Agent tool kernel without model planning (IMPLEMENTED)
- Date: 2026-11-05. Owner: engineering (reversible; additive).
- Decision: ship the governed execution kernel (12 manifests, 6
  read-only real tools, ABAC ai_run/manage, approval flow, run
  recording, audit) with caller-specified tools. Model-driven
  planning is NOT claimed; it arrives with the provider lane.
  Session-only surface (token denied); approval is admin-only.
- Evidence: app/agents.py + 4 APIs + 9 tests green.

### D-027 - Governance workflows are technical controls, not legal proof (IMPLEMENTED)
- Date: 2026-11-05. Owner: engineering (reversible; additive).
- Decision: SAR drafts (separation of duties, handoff refs),
  DSR tracker, and legal holds (block case close) ship as
  audited workflows. FILED means internal handoff prepared —
  never a regulator-submission claim. Sensitive ABAC kinds.
- Evidence: app/governance.py + 9 APIs + hold wire-in + 6 tests green.

### D-028 - Login-risk baselines learn post-password, digests-only (IMPLEMENTED)
- Date: 2026-11-06. Owner: engineering (reversible; additive).
- Decision: unknown-location scoring (new network identity 2,
  new UA class 2, unusual hour 1; low 0-1, elevated 2-3,
  high 4+) runs only after the password verifies, so
  unknown users, bad passwords, and rate-limited attempts
  never learn a baseline. Only SHA-256 digests + hour
  buckets persist; low keeps the exact legacy login body,
  MFA tickets carry no risk key.
- Evidence: app/login_risk.py + store accessors + login
  wire-in + 12 tests green.

### D-029 - Per-user security notifications, in-app leg (IMPLEMENTED)
- Date: 2026-11-06. Owner: engineering (reversible; additive).
- Decision: security notices (unusual sign-in, MFA
  enabled/disabled, recovery-code use) persist per user
  (bounded 50, sec_NNNN ids) and merge into GET
  /api/v1/notifications for session callers; POST
  .../notifications/read covers security ids (incl.
  mark-all). Low-risk logins emit nothing; details carry
  no network identifiers or secret material.
- Evidence: app/store.py notify_user/user_notifications_for
  + 4 main.py call sites + merged list/read endpoints +
  tests/test_security_notifications.py 10 green; full
  backend 958 passed / 141 skipped / same sandbox-only
  1F+2E (re-verified 2026-11-06).

### D-030 - L14 14-layer canonical; L13 9-layer mapped (RECORDED)
- Date: 2026-11-06. Owner: engineering (reversible docs
  decision; owner may override).
- Decision: the L14 14-layer model is the canonical frame
  per its supremacy clause. L13 layers map: L01→Layer 01;
  L02→Layers 02+03; L03→Layer 10; L04→Layers 05+13;
  L05→Layer 13; L06→Layers 02+09+12; L07→Layers 06+13;
  L08→EXTENSION (no L14 commercial layer; attaches to
  02+12); L09→Layers 12+14.
- Evidence: Phase 1 reconciliation; mapping in this entry.

### D-031 - Matrix generator is the count authority (RECORDED)
- Date: 2026-11-06. Owner: engineering (reversible).
- Decision: scripts/zero_gap_matrix.py ROWS +
  docs/ZERO_GAP_MATRIX.json are canonical; 78/85 counts
  stale and superseded. New rows only for distinct,
  testable, owned requirements; no status flip without
  quoted evidence.
- Evidence: validator exit 0 at 105 rows (2026-11-06).

### D-032 - JSON as-built authority recorded (RECORDED)
- Date: 2026-11-06. Owner: engineering (records reality;
  does NOT preempt the GAP-001 owner decision).
- Decision: boot pins Store() so JSON is the active
  canonical store; PostgreSQL is scratch-verification
  only. Any cutover still requires the GAP-001 decision
  plus parity/rollback proof.
- Evidence: app/main.py boot; 10-agent audit §5 verdict.

### D-033 - Live evidence index canonical (RECORDED)
- Date: 2026-11-06. Owner: engineering (reversible).
- Decision: docs/LIVE_EVIDENCE_INDEX.md is the canonical
  current-line evidence index. Frozen registers
  (FINAL_EVIDENCE_INDEX, MASTER_EVIDENCE_REGISTER,
  EVIDENCE_PROVENANCE_REGISTER) preserved as history.
- Evidence: Phase 1 consolidation; no history rewritten.

### D-034 - Credential/actor helpers kept distinct (INVESTIGATED)
- Date: 2026-11-06. Owner: engineering.
- Decision: BATCH-1 found _credential vs
  subject_from_request and the four actor helpers NOT
  safely unifiable: _credential honors tokens unarmed
  while abac subjects are armed-only (migration would
  weaken R2 "platform-token" attribution); actor helpers
  carry distinct contracts (claimed/anonymous/local-default
  + role). Kept as-is with a code note. Unified the
  byte-identical _b64 (auth canonical), removed tests-only
  verify_session, single live validation in the write gate.
- Evidence: BATCH-1 diff; full suite 962 green + same
  sandbox-only 1F+2E (2026-11-06).

### D-035 - Detection skips non-dict rows, surfaces count (IMPLEMENTED)
- Date: 2026-11-06. Owner: engineering (reversible;
  valid inputs unaffected).
- Decision: evaluate_all filters non-dict rows up front
  and records INPUT/NON_DICT_ROWS_SKIPPED:n in
  family_errors; valid rows evaluate normally.
  Malformed-dict rows keep lenient .get behavior (rules
  are defensive by design).
- Evidence: app/detection.py + fault-path test green.

### D-036 - Case creation API with server-side attribution (IMPLEMENTED)
- Date: 2026-11-06. Owner: engineering (reversible; additive).
- Decision: POST /api/v1/cases opens NEW cases (was
  seed-only) with title/priority/assignee/due-date/notes/
  investigation link; validated bounds; tenant stamp +
  visible-link check (no oracle); actor = session user /
  platform-token / anonymous (never client-claimed);
  audited case.opened. IDs case_%04d via persisted seq.
- Evidence: app/cases.py + endpoint + 6 tests green.

### D-037 - Runtime user overlay + flag-off self-register (IMPLEMENTED)
- Date: 2026-11-06. Owner: engineering (reversible; additive).
- Decision: effective users = DEMO_USERS seed + store
  overlay (overlay wins, disabled excluded) so passwords
  rotate and users deprovision without env edits. Admin
  provisioning needs a full admin session; self-register
  is OFF by default (exact "1" enables), throttled like
  login, fixed investigator role, trial auto-opened.
  Runtime passwords need 12+ chars. New identity state
  is JSON-canonical; PG parity follows GAP-001.
- Evidence: app/accounts.py + endpoints + 9 tests green.

### D-038 - Verification tokens, delivery blocked (IMPLEMENTED)
- Date: 2026-11-06. Owner: engineering (reversible; additive).
- Decision: purpose-bound single-use HMAC tokens (24 h)
  for email/phone verification; request is session-bound,
  throttled, audited, and returns delivery BLOCKED_EXTERNAL
  without the token; confirm is session-bound to the same
  user with single-use + contact-match checks. Email/SMS
  delivery needs a provider decision (blocked).
- Evidence: app/verify.py + endpoints + 11 tests green.

### D-039 - Password rotation + session registry + prefs (IMPLEMENTED)
- Date: 2026-11-06. Owner: engineering (reversible; additive).
- Decision: password change needs the current password +
  full session, writes the overlay (uniform for env/seed
  users), bumps the epoch (all sessions die). Logins
  register digest-only session entries; owners list and
  revoke their own; logout prunes. Notification prefs
  persist with security notices locked on; pref flips
  unaudited like mark-read.
- Evidence: store/main/login_risk + 6 tests green.

### D-040 - Trial/sub/founder lifecycle, metering default-off (IMPLEMENTED)
- Date: 2026-11-06. Owner: engineering (reversible; additive).
- Decision: directive trial defaults (14 days, 2 credits);
  metering constrains session users on case creation only
  when TRIAL_ENFORCEMENT=1 (default off; founder/active
  subs bypass; token/anon unattributed). Plans carry no
  prices (owner quote). Founder entitlement derives from
  FOUNDER_USER env at login; no endpoint can grant it.
  Payment events are references only; nothing charges.
- Evidence: app/billing.py + endpoints + 11 tests green.

### D-041 - Payments stub + Web3 isolated, live disabled (IMPLEMENTED)
- Date: 2026-11-06. Owner: engineering (reversible; additive).
- Decision: provider-neutral intents (minor units) via a
  manual stub only; live_charge() always raises so charging
  is impossible by construction. Isolated Web3 records
  stablecoin intents + operator tx hashes with shape-only
  validation, zero confirmations claimed, no custody, no
  chain client. Named providers need owner + legal choice.
- Evidence: app/payments.py + app/web3.py + 9 tests green.

### D-042 - Org admin + invitations (IMPLEMENTED)
- Date: 2026-11-06. Owner: engineering (reversible; additive).
- Decision: single-org profile, membership view (hashes
  never included), runtime disable/enable with self and
  founder guards, token invitations redeemable even when
  self-registration is off (invitation authorizes; email
  still unverified until the verify flow). Cross-tenant
  semantics stay with D-014.
- Evidence: app/orgs.py + endpoints + 8 tests green.

### D-043 - Delivery interface + templates + log driver (IMPLEMENTED)
- Date: 2026-11-06. Owner: engineering (reversible; additive).
- Decision: versioned templates for six security events;
  security always dispatches, other kinds honor prefs
  (suppressions recorded); only the log test driver
  exists, so provider drivers need a vendor decision.
  Emitters wired at login-risk, password, MFA ×3, verify.
- Evidence: app/notify.py + emitters + 11 tests green.

### D-044 - Provider interface + webhook framework (IMPLEMENTED)
- Date: 2026-11-06. Owner: engineering (reversible; additive).
- Decision: interface v1 (capability keys + conformance
  check; stub conforms), HMAC-SHA256 webhook verification
  with a 300 s replay window, reference idempotency
  lookup. No webhook endpoint until a named provider
  exists (URL/header shape must not be guessed).
- Evidence: app/payments.py + 5 tests green.

### D-045 - Passkey ceremonies, review-gated interop (IMPLEMENTED)
- Date: 2026-11-06. Owner: engineering (reversible; additive).
- Decision: flag-off WebAuthn with none + packed
  self-attestation registration and ES256/EdDSA assertion
  verification (real signatures, clone detection,
  single-use challenges). CA attestation, authenticator
  interop, lock regen, and review stay pending; crypto
  absence fails closed. Passkeys replace passwords, never
  pending MFA policy.
- Evidence: app/passkeys.py + endpoints + 15 tests green.

### D-046 - Session kill-all revokes tracked nonces (IMPLEMENTED)
- Date: 2026-11-06. Owner: engineering (reversible; additive).
- Decision: logout-all + password change revoke tracked
  session nonces and drop the registry; the epoch bump stays
  as the backstop for untracked tokens. Root cause fixed:
  second-resolution epoch comparison missed same-second
  tokens. Exact epoch-value contracts untouched.
- Evidence: app/main.py + 2 regression tests green.

### D-047 - Provider-neutral AI gateway + routing (IMPLEMENTED)
- Date: 2026-11-06. Owner: engineering (reversible; additive).
- Decision: app/ai_gateway.py routes analysis/followup tasks
  across registered lanes (Meta first; further lanes join
  without gateway changes). Lanes are authoritative on
  credentials: MODEL_NOT_CONFIGURED falls through, quota and
  task-fit skip with reasons, validation/refusal fail fast.
  Per-provider daily quota (default off; global cap
  governs), token-only usage accounting, observed-only lane
  stats, prompt-version digest registry. Live calls still
  need D-016 credential + PKG-04 approval.
- Evidence: app/ai_gateway.py + 13 tests green.

### D-048 - LocalDirTarget resolves its root (IMPLEMENTED)
- Date: 2026-11-06. Owner: engineering (reversible; additive).
- Decision: resolve the backup-target root at construction.
  Root cause: containment compared resolved candidates
  against an unresolved root, so every relative root
  self-reported PATH_ESCAPE (scratch drill failed).
  Absolute-root behavior unchanged; containment still
  rejects .. and absolute payload paths.
- Evidence: backups/local_target.py + regression test green.

### D-049 - Ingest endpoint audited (IMPLEMENTED)
- Date: 2026-11-07. Owner: engineering (reversible; additive).
- Decision: POST /api/v1/events appends event.ingested for
  every validated ingest (accepted + idempotent duplicates,
  mirroring the signal-link precedent); schema rejections
  raise before any audit. Actor follows the promote-handler
  contract (session user / platform-token / anonymous);
  detail carries transaction/channel routing only.
- Evidence: app/main.py ingest_event + 4 tests green
  (tests/test_ingest_audit.py).

### D-050 - Health reports chain presence, exempt (IMPLEMENTED)
- Date: 2026-11-07. Owner: engineering (reversible; additive).
- Decision: /api/v1/health gains an audit_chain check reporting
  sealed/total counts (PASS) or legacy presence
  (NOT_CONFIGURED), exempt from the blocking set. No keys
  created, no keyring loaded, no signatures verified, no
  digests exposed — counts only. Verification still needs
  the D-018 ceremony keyring.
- Evidence: app/main.py _audit_chain_check + 3 tests green
  (tests/test_ingest_audit.py).

### D-051 - Evidence-package export with hash proof (IMPLEMENTED)
- Date: 2026-11-07. Owner: engineering (reversible; additive).
- Decision: canonical export bytes (sorted keys, compact
  separators, versioned envelope) + sha256, served by GET
  .../evidence-package/export as raw application/json with
  an X-Export-SHA256 header. Read-only mirror of the package
  read (same visibility, no new auth surface).
- Evidence: app/evidence.py + app/main.py + 4 tests green
  (tests/test_evidence_export.py).

### D-052 - Admin access-review report (IMPLEMENTED)
- Date: 2026-11-07. Owner: engineering (reversible; additive).
- Decision: GET /api/v1/admin/access-review (admin session
  only) returns grant/revoke/invitation/MFA deltas in audit
  order plus the current membership snapshot. Logins,
  ingests, decisions, and runs are out of scope; hashes
  and secrets never included.
- Evidence: app/main.py access_review + 4 tests green
  (tests/test_access_review.py).

### D-016 — Live Meta call (NO-LIVE recorded)
- Date: 2026-11-07. Owner: PKG-04 Option B direction recorded via
  CS-PRODUCT-CLOSURE-001 review constraints (NO-LIVE).
- Disposition: local .env holds a key-shaped value (presence-only
  verified 2026-11-07; value never read, validity untested).
  NO-LIVE recorded: no live call executed, no quota consumed.
  Deterministic engine remains authoritative;
  UI keeps honest NOT_CONFIGURED state. AI-01 stays
  BLOCKED_EXTERNAL_DEPENDENCY with settled disposition; reopen
  needs new owner approval + key.
### D-053 — Live provider credentials (NO-LIVE recorded)
- Date: 2026-11-07. Owner: D-053 NO-LIVE direction recorded via
  CS-PRODUCT-CLOSURE-001 review constraints.
- Disposition: per-provider NO-LIVE for telecom (TEL-08), intel
  (LIVE-GEO), financial (UFI-LIVE). Adapters exist; no
  credentials, handshakes, or requests. Reopen per provider
  needs creds + handshake + approval.
## CS-OWNER-DECISIONS-UPDATE-002 (2026-11-08, review records only)
### PR target — `production-launch` proposed
- Date: 2026-11-08. Owner: PR target for the PKG-01 publication
  is `production-launch` (verified: exists locally + origin, both
  b4732cb, in sync; ancestor of HEAD d82627d; committed diff
  51 files +5846/-553; no codified branch-policy doc located —
  gate workflow enforces checks on push/PR to master and
  production-launch).
- Disposition: target recorded. NOT an authorization: no push,
  commit, PR creation, or deployment approved.
### qa-scratch/data/state.json — REMAINS TRACKED
- Date: 2026-11-08. Owner: file stays tracked with current
  release status.
- Disposition: no untrack/delete/overwrite/modify. Exclusion
  from publication only via separate owner approval. Prior
  untrack recommendation superseded.
### D-015 — Licence DEFERRED
- Date: 2026-11-08. Owner: licence selection deferred.
- Disposition: no MIT/Apache-2.0/BSD-3-Clause/proprietary
  selection, creation, or application. REL-01 stays
  AWAITING_OWNER_APPROVAL.
### PKG-09 — Social/federated auth batch DEFERRED
- Date: 2026-11-08. Owner: AUTH-01..AUTH-09 batch deferred.
- Disposition: no implementation or activation. Existing
  authentication preserved untouched. Rows stay NOT_STARTED.
### GAP-001 — PostgreSQL HOLD reaffirmed
- Date: 2026-11-08. Owner: JSON store stays active.
- Disposition: no provision/migrate/cutover/config change.
  DET-03 stays IN_PROGRESS, DB-01 stays AWAITING_OWNER_APPROVAL.
## Pending decisions (BLOCKED until answered)

| ID | Question | Needed from | Blocks |
|---|---|---|---|
| D-014 | Tenancy scope: single-org or multi-tenant build | Owner | §12 FAIL, stages 12–13 |
| D-015 | License selection — DEFERRED 2026-11-08 (see UPDATE-002) | Owner | Public repo certification |
| D-016 | Live Meta call: key + quota approval | Owner | GAP-014, AI lane |
| D-017 | Push/deploy feature branch | Owner | GAP-009, GAP-010 |
| D-018 | Backup keys + ceremony authorization | Owner | GAP-003 |
| D-019b | Remove deprecated /demo/* aliases | Owner | post-deploy |
| D-020 | Approve coverage-dep pins + lock churn | Owner | GAP-005 |
| D-058 | Scheme-rule legal verification (windows/deadlines) | Owner/Counsel | REC eligibility confirmation |
## M1 OWNER DECISION RECORD — B10 text-based evidence acceptance (APPROVED 2026-11-08)
- Date: 2026-11-08. Owner: explicit approval granted; review record only.
- Decision: accept the previously supplied November 8, 2026 B10
  dashboard readings as OWNER_TRANSCRIBED / OWNER_REPORTED
  evidence, covering GitHub Billing, GitHub Licensing, Netlify
  Usage and Billing, Render Workspace Billing, Render Pipeline
  Spending Cap, GitHub Budgets, Render Observability, Render
  Webhooks, and Render Notifications (readings reconciled in
  PRA-002 and M1; historical sources: PRA-002 §D–E, M1
  reconciliation, docs/B10_READING_WORKSHEET.md R1 + addendum
  B10-ADD-2026-11-08-R2).
- Permanent limitations (must not be reclassified): nine
  original screenshot files NOT transferred into the Muse
  workspace; zero screenshot files archived in the repository;
  zero screenshot hashes generated; readings stay
  OWNER_TRANSCRIBED or OWNER_REPORTED as applicable; no
  screenshot-level independent verification occurred;
  unresolved account limits, billing details, service settings,
  and provider restrictions stay UNVERIFIED. Never relabel as
  SCREENSHOT_VERIFIED, HOSTED_VERIFIED, or independently
  confirmed.
- Disposition: M1 evidence accepted as text-grade with stated
  limitations. NOT an authorization: no push, PR, hosted CI,
  external resources, billing/provider changes, deployment,
  service activation, database provisioning/migration, or any
  other deferred/restricted action approved. Canonical 192-row
  matrix unchanged by this record.
