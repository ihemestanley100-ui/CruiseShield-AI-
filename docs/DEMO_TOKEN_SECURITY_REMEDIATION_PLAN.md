# DEMO TOKEN — SECURITY REMEDIATION PLAN

Date: 2026-11-03 · Spec only — NO code changed (read-only audit).
Re-audit required after implementation; verdict stays FAIL until then.

## Implementation record (2026-11-03)

R1–R4 IMPLEMENTED in `app/main.py` (+`_decision_actor`,
`_require_login`, `_evidence_package` helpers) with 17
regression tests in `tests/test_demo_token_remediation.py`
(failing-first observed: 9 failed pre-fix, all green
post-fix). `tests/test_flow_direct.py`: 2 call-site
updates (request arg; assertions untouched). Full suite:
420 passed / 73 skipped. Re-audit verdict: PASS WITH
LIMITATIONS (see Audit §7). R5 (must-set + rotation
runbook) and R6 (empty-frontend option) remain OWNER
decisions at deploy time — no code. No commit/push/deploy
performed.

## R1 — REQUIRED: close the admin bypass (F-PRIV-1)

Problem: `kind=="token"` skips the admin-prefix check.
Fix (minimal): in `session_guard`, enforce
`AUTH_ADMIN_PREFIXES` for token creds too — deny token
on `/api/v1/demo/*` (403) OR treat token as exactly
{write} on non-admin paths. Demo reset/start then needs
a logged-in admin (judges log in; public cannot reset).
Tests: token→demo/* 403; admin session→200; matrix row
update. Size: S.

## R2 — REQUIRED: bind decision actor to credential (F-AUDIT-1)

Problem: `actor_id` is body-controlled.
Fix: when `auth_kind=="token"`, force
`actor_id="demo-token"` (ignore body); sessions keep
their login username (prefer cookie identity over body
for sessions too). Tests: forged "judge" becomes
"demo-token" in record + audit. Size: S.

## R3 — RECOMMENDED: token AI sub-cap (F-QUOTA-1)

Problem: token can burn the full 100/day budget.
Fix options: (a) token-credential AI calls capped at
e.g. 20/day (separate counter); (b) AI endpoints
require login session (token denied). (b) is simpler
and matches "AI is the crown demo" posture. Tests:
token→ai-analysis 403/429-per-policy. Size: S-M.

## R4 — RECOMMENDED: gate evidence-package POST (F-CONSIST-1)

Add `_require_write_token` for consistency (defense in
depth; no behavior change while it stays read-only).
Size: XS. Tests: anon 401.

## R5 — DEPLOY CONTROL (no code): must-set + rotation

- Backend `DEMO_WRITE_TOKEN` MUST be set (32+ random)
  or all gates stand open — add to Render checklist as
  blocking item with verify step (anon POST → 401).
- Frontend value MUST equal backend value; any change
  needs frontend rebuild.
- Rotation on abuse: regenerate backend + frontend,
  rebuild frontend, redeploy both (~10 min). Document
  the runbook before demo day.

## R6 — SAFEST-POSTURE OPTION (owner decision, no code)

Leave `NEXT_PUBLIC_DEMO_WRITE_TOKEN` EMPTY in Render:
public visitors read + view; ALL writes require a
logged-in session (judges get demo logins). Zero
public-write risk, zero code change. Trade-off: drive-
by visitors cannot click write buttons (they 401 with
a login prompt). RECOMMENDED if R1–R3 cannot land
before the deadline.

## Acceptance to lift FAIL → PASS WITH LIMITATIONS

R1 + R2 implemented + tests green + matrix re-verified
(token ≤ write-role session everywhere, actor bound).
R3/R4/R6 decide the residual: with R6-empty, residual
is read-only-public (lowest); with token set, residual
is T2-monitored + T1-accepted (documented).
