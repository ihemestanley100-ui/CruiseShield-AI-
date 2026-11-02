# CRUISESHIELD AI — MASTER REMEDIATION REGISTER (J3)

**Baseline:** `d4e2bec` (published master) + uncommitted J3 worktree (this
programme; NOT committed, NOT pushed — reviewable only).
**Source:** seven-agent audit inventory (165 items: 106 PASS / 30 PARTIAL /
13 FAIL / 16 NOT VERIFIED), 9 contradictions (all resolved in audit),
14 remediation items P1–P14, 5 run-to-verify gaps R1–R5.
**Method:** every P-item re-verified against live code before fixing; no
finding imported on auditor authority alone. Auditor line numbers were
stale in several cases — content verified instead.
**State:** `data/state.json` `BA1D4DB4…3790FE`/101417 B unchanged throughout.

## Closed and verified (code + tests green)

- **J3-P1** `app/config.py:124` — `PG_CONNECT_TIMEOUT` bare `int()` crashed
  boot on garbage env. Fix: `_safe_int` + positive clamp. Tests:
  `tests/test_config_safety.py` (3). Status: CLOSED.
- **J3-P2** `app/main.py:398` — `Secure` dropped behind TLS proxies.
  Fix: honor first-hop `X-Forwarded-Proto:https`. Tests: 3 cookie tests
  in `tests/test_auth.py` (direct-https / proxy / plain-http). CLOSED.
- **J3-P3** `app/rules.py:66` — `next()` leaked `StopIteration` on unknown
  txn. Fix: fail closed with `UNKNOWN_TXN` ValueError (defense-in-depth;
  all API callers pre-404 — verified). Test: 1. CLOSED.
- **J3-P4** `frontend/components/ai-panel.tsx` — follow-up POST had no
  AbortSignal/timeout. Fix: dedicated abort pair + 35 s timer, mirrored
  timeout message. Tests: 1 new (hang → timeout, assessment survives) +
  1 updated assertion (documented contract extension). CLOSED.
- **J3-P5** `app/main.py:latest_ai_run_for_case` — FAILED run (empty result)
  masked latest SUCCEEDED assessment. Fix: skip non-SUCCEEDED runs.
  Test: `test_case_detail_skips_failed_run_for_latest`. Existing
  SUCCEEDED-path tests still green. CLOSED.
- **J3-P6** session UX — no 403 handling, no mid-session re-login. Fix:
  `csai:unauthorized` event on 401/403 data responses (login endpoint
  excluded, SSR-guarded) + gate re-checks `/me` (live session stays,
  expired flips to sign-in). Tests: 1 api-client + 1 gate test. CLOSED.
- **J3-P7** quota visibility — cap message named limit only. Fix: message
  carries `used/limit` + `resets 00:00 UTC` (also in the audit reason).
  Test: message assertions in `tests/test_ai_cost.py`. CLOSED.
- **J3-P10-code** — uplift assertion added (`+49`, command-kpis.test);
  Tabs/Timeline/Toast/Modal suites verified real (23–33 lines each,
  behavioral — critic note refuted with evidence); frontend README
  title fixed; `NEXT_DIST_DIR` override removed (behavior-neutral,
  default `.next`) + RENDER_6/ZERO_COST lines updated. CLOSED
  (openGraph absolute URL stays owner-gated: needs deployment domain).
- **J3-P11** — `tests/test_security_gate.py` (4: `_norm`, `parse_pins`,
  pattern true/false positives with runtime-assembled fixtures,
  live-tree scan PASS). CLOSED.
- **J3-P12** — `.env.example`: dead `AGE_*`/`ALERT_*` (consumed nowhere —
  verified) replaced with the 4 live `CSBK_*` workflow names + runbook
  link (13/13 names now mirror workflows); README Next.js paragraph;
  KNOWN_LIMITATIONS auth + counts refresh; RENDER_6 Neon/timeout rows;
  TEST_EVIDENCE dated addendum (history retained); provenance + GAPS
  dated addenda (history retained). `ENDPOINT_*`/`UNIT_COVERAGE_*`
  targets do NOT exist (verified via `git ls-files`) — recorded as
  auditor stale refs, no-op. SUBMIT_G/PHASE_11 verdict/06-ACCEPTANCE
  verified accurate — no edit. CLOSED.
- **J3-P14** — demo-scale boundaries documented in KNOWN_LIMITATIONS:
  Content-Length-only body cap (chunked unmetered) + single-process
  rate limits. Verified in code first. CLOSED.
- **J3-R1/R2/R3** — suite counts reconciled and green: backend 334 pass /
  102 skip / 0 fail (437; 1 sandbox-node-blocked, proven 3/3 green
  unsandboxed); frontend 49 files / 254 pass; `tsc` clean; `next build`
  exit 0 fresh BUILD_ID. CLOSED.

## Implemented, environment-gated (code complete, runs in CI/user envs)

- **J3-P8** — 6 provider-mapping tests (429-retry→RATE_LIMITED with
  attempt counts, 500/401 single-attempt codes, timeout fail-fast,
  connect-error, non-JSON). Attempt counts verified by reading the
  retry/fallback trigger (`should_retry_without_structured` is
  400-only). Loop-gated: SKIP here, run in CI. STATUS: PARTIAL.
- **J3-P9-transport** — `tests/test_api_flow.py`: original 3 tests
  restored byte-identical after an overwrite incident (see below) +
  10 new transport tests (envelopes, reads, 404/400 matrix, AI
  pre-validation, legacy pages, events 422, auth-mode). Socket-gated:
  SKIP here. Direct-handler twins (`test_flow_direct.py` +4 tests)
  RUN and PASS here. STATUS: PARTIAL (transport half).

## Blocked on owner (no safe local action)

- **J3-P10-openGraph** — absolute image URL needs the deployment domain
  (unknown until Vercel project exists). BLOCKED (owner: domain).
- **J3-P13** — `.gitignore` hardening (D2 proposal + auditor's
  `*.pem/*.key`, `*.csbk1`, `.coverage/htmlcov`). Edits need D2
  approval, never received as an edit authorization. BLOCKED (owner).
- **J3-R4/R5** — live-provider AI call + Neon/Render staging proof.
  External by nature. BLOCKED (owner: quota, deploy approvals).

## Process incident (self-reported)

- During P9 I overwrote tracked `tests/test_api_flow.py` (believed
  missing — `git ls-files` had shown it as TRACKED and I misread).
  Detected via count reconciliation (+29 not +32), restored the
  original 3 tests byte-identical from HEAD, appended my 10. Final
  diff: +101/−0. Full J3 diff then audited: every other deletion is
  an intentional P-fix replacement; both new test files genuinely new.
  No user work lost. Lesson recorded: verify `git status` class
  before `write_file` on any test path.

## Counts

- Actionable J3 set: 14 P-items + 5 R-items = 19.
- Closed-verified: 15 (P1–P7, P10-code, P11, P12, P14, R1–R3).
- Implemented-pending-env: 2 (P8, P9-transport).
- Blocked-owner: 3 (P10-openGraph counted under P10-code split; P13, R4/R5).
  Precise: 15 closed / 2 partial / 2 blocked (P10 splits closed+blocked).
