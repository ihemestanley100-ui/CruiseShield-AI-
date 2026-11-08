# CruiseShield Fund Recovery & Payment Reversal OS™ — Record

**Status:** Implemented in worktree (uncommitted). Backend verified;
frontend written, execution pending hosted CI (sandbox node EPERM).
No live provider submissions possible: zero VERIFIED recovery
capabilities, all scheme windows NOT_VERIFIED pending D-058.

## 1. Reuse (no duplication)

Taxonomy (`payment_methods`), tracing, detection/signal, industry
registry + adapters, agent kernel + orchestrator, cases, evidence,
reports, connectors registry, tenancy, audit, notifications. New
code is recovery-specific: rules, eligibility, lifecycle,
capabilities, agent tools, UI.

## 2. Components

- `app/recovery_rules.py` — versioned registry: 2 VERIFIED
  structural rules (crypto/cash irreversibility, taxonomy-sourced)
  + 8 NOT_VERIFIED scheme templates. Seeds immutable; admin
  registration requires source + dates + window for VERIFIED.
- `app/recovery.py` — 11-status eligibility engine (rule + reason
  + missing + lawful alternatives) and 17-state audited lifecycle
  with idempotent open (transaction + reason).
- `app/recovery_caps.py` — connector x 12-capability matrix, all
  UNSUPPORTED until an admin declaration with evidence.
- Submission: LIVE requires a VERIFIED capability, else 409 with
  manual guidance; MANUAL is a controlled packet (UNDER_REVIEW +
  external reference tracking). Nothing moves money.
- Approvals: APPROVED/REJECTED need admin sessions; agent writes
  only via approval-gated manifests.
- AI: `fund-recovery` manifest (approval-gated) + 3 read tools;
  orchestrator RECOVERY intent via auto-readable tools.
- Industry: `recovery_config()` for all 45 (shared workflows,
  typologies, templates, connector requirements).
- UI: `RecoverySection` on the investigation page + 4 vitest
  cases (TESTING). Dashboard: `/api/v1/recovery/metrics`.

## 3. Historical recovery (§10)

Eligibility separates scheme windows (verified rules only) from
provider/manual routes; OUT_OF_SCHEME_WINDOW returns lawful
alternatives (provider refund, historical investigation, civil
restitution, LE referral) instead of false reversals. Traces
preserve originals; traceability never implies recoverability.

## 4. Threat assessment (recovery-specific)

- False recovery claims: lifecycle states distinguish prepared /
  submitted / acknowledged / completed; UI renders verbatim.
- Unauthorized submission: live path requires VERIFIED caps;
  approval transitions admin-only + audited.
- Cross-tenant: cases/assessments tenant-scoped; tests prove.
- Duplicate requests: idempotent open key; transitions validated.
- Replay: state-machine guards (no resubmit from terminal states
  except ESCALATED/CLOSED paths); no money movement primitives.
- Evidence: references only (no secret payloads); provider
  responses stored as supplied records with provenance.

## 5. Verification

- `tests/test_recovery_core.py` (11) + `tests/test_recovery_routes.py`
  (9): rules honesty, full eligibility ladder, lifecycle,
  idempotency, live/manual submission gates, caps, agent tools,
  orchestrator intent. Registry count updated 13/16 (deliberate).
- Contract parity extended (recovery imports + paths).
- Full suite + matrix check before close.

## 6. Gates

- D-058 (new): scheme-rule legal verification — no VERIFIED
  windows exist; eligibility cannot confirm until counsel acts.
- D-053: live provider credentials + capability evidence.
- D-056: retention execution. PKG-01: hosted UI execution.
