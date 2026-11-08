# LEVEL 14 OWNER-APPROVAL PACKAGES — CruiseShield AI™

Date: 2026-11-06. Branch: `feat/phasezero-foundations` @ `d82627d`
(11 commits ahead of `production-launch` tip `b4732cb`; worktree
143 modified + 2 deleted + 226 untracked = 371 entries).
Matrix: 85 rows, 72 CLOSED_VERIFIED, 4 IN_PROGRESS, 3 BLOCKED, 6
AWAITING (validator PASS). Full backend: 924 passed / 141 skipped /
same sandbox-only 1F+2E.

How to use: each package names ONE decision, its evidence, the exact
owner action, and what stays blocked without it. Nothing here
authorizes execution — a package opens only on your explicit reply
naming its ID. Provenance tags: LOCAL = verified in this repo on
2026-11-06; OWNER-READOUT = only you can supply it (dashboard);
HISTORICAL = earlier evidence, recheck before relying on it.

Relation to older gates: `docs/FINAL_DEPLOYMENT_GATE_REGISTER.md`
(G-COMMIT … G-RELEASE) belongs to the 2026-11-03 `production-launch`
release (`58a3d50`/`ff7052b`). The packages below belong to the
current `feat/phasezero-foundations` line and do not reopen those
gates. Reconciliation notes at the end list stale rows found while
preparing this file.

## PKG-01 — Push feature branch + open PR + hosted CI (D-017)

Decides: D-017 (push/deploy feature branch). Unblocks: DET-13
(hosted CI), DEP-004, DEP-007, ASM-003.

Background (LOCAL): the branch has no upstream; `origin` is
`https://github.com/ihemestanley100-ui/CRUISESHIELD-AI-.git` (no
embedded credentials). `origin/production-launch` = `b4732cb` per
last fetch; merge-base with HEAD is also `b4732cb`, so the PR is a
clean 11-commit fast-forward with no divergence. CI
(`.github/workflows/security-gate.yml`) triggers on `pull_request`,
so opening the PR fires the Linux run that settles the 3 sandbox-only
signatures and the 31 CAN_LOOP-skipped async tests.

Exact action (your approval text): "Approve PKG-01: push
`feat/phasezero-foundations` as a NEW remote branch and open a PR
against `production-launch`. Do not push to `production-launch` or
`master` directly."

Commands that will run after approval (for the record, not yet run):

```text
git push -u origin feat/phasezero-foundations
gh pr create --base production-launch --head feat/phasezero-foundations \
  --title "Level 14 foundations and detection intelligence"
```

Pre-push checks that will run first: `python
scripts/security_gate.py --skip-audit` (offline: secret scan +
lockfile hashes), `git status` review, `git diff --check`.
Known gate state (HISTORICAL, recheck at push time): secret_scan
PASS, lockfile_hashes PASS; overall FAIL on pre-existing lock-drift
+ shared-interpreter pip_check + Pillow conflict + OSV timeout (no
new deps introduced since).

Cost/risk: $0 (GitHub Free push + Actions free allowance).
Risk if declined: DET-13, DET-12, GAP-010 stay blocked; no hosted
proof exists for any later deploy.

## PKG-02 — Deployment identity, frontend-absent, short-SHA (R02)

Decides: nothing to change — this package asks for READINGS, not
changes. Settles: RSK-005 staleness question, DET-14 evidence base.

Background: RSK-005 says live backend = `ff7052b`, but that note
predates the `b4732cb` tip (LOCAL ref state). The Render deploy was
previously confirmed only by short prefix. Separately, no frontend
service exists (HISTORICAL B3: "Existing frontend: NO").

Exact readings needed (Render dashboard, service `cruiseshield-ai`;
names/values below are non-secret — never paste secret VALUES):

1. Deploys → latest deploy → full 40-char commit SHA.
   Compare against `ff7052bdf0ac48a68f69c3937d9b8708ca265354`
   (LOCAL: the pushed G-COMMIT-2 hash) and against `b4732cb`
   (LOCAL tip; full hash from `git rev-parse production-launch`
   at verification time).
2. Deploys → latest deploy → status + timestamp (LIVE? when?).
3. Services list → confirm exactly one service (`cruiseshield-ai`)
   and that no `cruiseshield-ai-frontend` (or other) service exists.
4. Service → Settings → branch (`production-launch`?) and
   auto-deploy ON/OFF.

Report back as: FULL_SHA=<40 chars> / SHORT_ONLY / MISMATCH, plus
the four answers. With FULL_SHA match, R02 closes; with SHORT_ONLY
it stays NOT_VERIFIED by rule (short prefix is never final proof).

Cost/risk: $0, read-only. Risk if declined: DET-14 cannot proceed;
any later deploy would target an unverified base.

## PKG-03 — Backend arming + live R1–R4 security probes (R01/R03)

Decides: authorize entering the three R5 secrets into Render and one
redeploy of the CURRENT live commit (no code change). Unblocks: live
R1–R4 verification, R03.

Background: live `/api/v1/health` historically reports
`auth_enabled:false` with SESSION_SECRET/DEMO_USERS/DEMO_WRITE_TOKEN
MISSING (HISTORICAL R01 readout). Code-side R1–R4 is CLOSED_VERIFIED
(SEC-R1…R4, `tests/test_demo_token_remediation.py` 17 tests).

Phase A — readings (no changes): Environment page → report each of
SESSION_SECRET, DEMO_USERS, DEMO_WRITE_TOKEN as PRESENT / MISSING
(names only, never values). If all PRESENT, skip Phase B.

Phase B — arming (only if something is MISSING): you enter fresh
values directly in the Render Environment prompt (generate with a
password manager; SESSION_SECRET ≥ 32 chars per F2 gate;
DEMO_USERS in the documented `user:role:hash` form; DEMO_WRITE_TOKEN
fresh random, backend-only). Then Manual Deploy → SAME commit the
service already runs (from PKG-02 reading — do NOT advance commits
here). Expected result: `/api/v1/health` still `healthy`, auth
mode endpoint reports armed.

Phase C — probes (run by agent after arming, synthetic data only;
each marked SAFE non-mutating or WRITE-needs-approval):

| Probe | Request | Expected | Mutating? |
|---|---|---|---|
| R1a | POST `/api/v1/platform/reset`, Bearer demo-token, no session | 403 ADMIN_REQUIRED | SAFE (rejected) |
| R1b | POST `/api/v1/platform/judge-start`, token only | 403 ADMIN_REQUIRED | SAFE |
| R1c | GET `/api/v1/platform/scenarios`, token only | 403 | SAFE |
| R1d | POST `/api/v1/platform/reset`, anonymous | 401 | SAFE |
| R1e | POST `/api/v1/platform/reset`, admin session | 200 | WRITE — resets live demo state. SKIP unless you explicitly approve |
| R2 | POST `/api/v1/cases/case_84721/decisions`, token, claimed actor `judge` | 200 with recorded actor `platform-token` | WRITE — one decision + audit on synthetic case. Needs approval |
| R3 | POST `/api/v1/investigations/inv_84721/ai-analysis`, token only | 403 AI_LOGIN_REQUIRED | SAFE (rejected pre-provider; spends no quota) |
| R4a | POST `/api/v1/investigations/inv_84721/evidence-package`, anonymous | 401 | SAFE |
| R4b | GET same path, anonymous | 200 | SAFE (read-only by design) |

Base URL for all probes: `https://cruiseshield-ai.onrender.com`
(LOCAL: `render.yaml` NEXT_PUBLIC_API_BASE_URL value).

Approval text: "Approve PKG-03 Phase A (readings)" first; then, if
needed, "Approve PKG-03 Phase B (arming + same-commit redeploy)" and
"Approve PKG-03 Phase C probes (list: R1a–d, R2, R3, R4a–b; R1e
included/excluded)".

Cost/risk: $0. R1e/R2 mutate shared demo records (documented,
audited, synthetic-only). No probe touches PG (STORE_BACKEND=json),
spends AI quota (R3 is denied pre-provider), or changes billing.

## PKG-04 — Meta live-call decision (D-016, AI-01)

Decides: D-016. Closes AI-01 one way or the other (PASS-with-evidence
or formal NO-LIVE).

Background (LOCAL): provider adapter + cost controls are code-complete
and mock-tested (`tests/test_ai_eval.py`, `test_ai_validation.py`,
`test_ai_cost.py`); live call never executed. Config names:
MODEL_API_KEY (empty = honest NOT_CONFIGURED), META_MODEL_ID
(default `muse-spark-1.3`), META_BASE_URL (default
`https://api.meta.ai/v1`), AI_DAILY_CALL_LIMIT (100),
AI_TIMEOUT_SECONDS (30), AI_MAX_OUTPUT_TOKENS (4096).

Option A — one live verification call. You supply: (1) a
MODEL_API_KEY value entered by YOU into Render (never chat), (2)
evidence the key carries a free allowance covering ~1 bounded call
(≤4096 output tokens + prompt; screenshot or plan page), (3) explicit
spend approval capped at that call. Agent then runs exactly one
synthetic investigation analysis via the armed backend, records
model/timestamp/request-id/redacted result, and stops.

Option B — formal NO-LIVE. You reply "Record NO-LIVE for AI-01".
AI-01 stays BLOCKED_EXTERNAL_DEPENDENCY with a settled disposition;
no code changes; the deterministic engine remains authoritative and
the UI keeps its honest NOT_CONFIGURED state.

Approval text: "Approve PKG-04 Option A (one capped live call)" or
"Approve PKG-04 Option B (formal NO-LIVE)".

Cost/risk: Option A costs at most one small metered call (or $0 on a
true free allowance — verified from YOUR evidence, never assumed).
No key is ever committed, logged, or echoed.

## PKG-05 — Financial readouts + overage risk acceptance (R11/R12)

Decides: whether the $0 posture is evidenced, and whether you accept
the documented residual exposure. Covers: RSK-001, ASM-004, DEP-005.

Background (LOCAL/HISTORICAL): `render.yaml` as written declares
TWO Starter (paid) services — backend `plan: starter` + 1 GB disk,
frontend `plan: starter`. The file itself documents the $0
alternative (backend Free without disk = ephemeral: decisions, runs,
audits do not survive restarts; frontend Free = sleeps on idle).
RSK-001: $0.30/GB bandwidth overage, no verified hard cap, card on
file. No Blueprint deploy, plan change, or purchase is authorized by
this package.

Exact readings needed (Render Billing + Services pages; non-secret):

1. Workspace plan + displayed monthly price.
2. Backend service plan + displayed monthly price.
3. Payment method present: YES/NO (no card details).
4. Usage vs included allowances (instance hours, bandwidth, build
   minutes) + current/projected charges.
5. Spend limit / overage settings (exact control names + values, or
   NONE FOUND).
6. Paid resources active: disks / databases / add-ons — YES/NO each.
7. Frontend service exists: YES/NO.

Decision after readings: (A) accept residual overage exposure for
demo-scale traffic with monitoring (RSK-001 → MITIGATED-accepted,
duly recorded), or (B) direct a $0-enforcing change (e.g. remove
payment method, or pick a host with hard caps — separate proposal,
no action taken here).

Approval text: "PKG-05 readings supplied" (paste the 7 answers),
then "Accept RSK-001 residual exposure" or "Request $0-enforcing
alternative".

Cost/risk: $0 to decide. Plain-language risk: a traffic spike can
bill the card on file; NOTHING in code can cap provider billing —
this is an owner risk call, not an engineering fix.

## PKG-06 — Public repo: license + release manifest (D-015, REL-01)

Decides: D-015 (license), REL-01, and the manifest rule for any
future release commit. Covers: RSK-007, DEP-003, ISS-003.

Background (LOCAL): no LICENSE/LICENCE file exists. Worktree is
143 modified + 2 deleted + 226 untracked = 371 status lines; the
matrix/forensic validators pass on this tree. Nothing is staged and
no commit is proposed by this package.

Decision 1 — license. Options (one-line implications; your counsel
wins on legal questions):

| Option | Effect |
|---|---|
| MIT | Permissive; anyone can reuse with attribution. Hackathon-friendly. |
| Apache-2.0 | Like MIT plus explicit patent grant. |
| GPL-3.0 | Copyleft; derivatives must stay open. |
| All rights reserved (no open license) | No reuse rights granted; repo is view-only. |

Recommendation: MIT (matches public-demo + competition posture; a
dependency-license review stays due before any commercial use).
Reply with the exact choice; the file is added only after your
wording approval.

Decision 2 — manifest rule. Any future release commit follows: (a)
agent produces the exact path list + per-path reason, (b) secret scan
PASS on the staged set, (c) you approve the exact list, (d) commit
message fixed in advance. No `git add -A`, no `.env`/key/log/DB
files, no `pytest-of-HP/` or `tmp*/` scratch. ISS-003's "162"
count is superseded by the LOCAL 143/2/226 breakdown above.

Approval text: "Approve PKG-06 license = <MIT|Apache-2.0|GPL-3.0|
closed>" and "Approve PKG-06 manifest rule". Neither stages nor
commits anything.

Cost/risk: $0. Risk if declined: RSK-007 stays OPEN; no publishable
release commit can be cut.

## PKG-07 — Remaining decision batch (one reply per line)

Each line is independent; approve, defer, or decide per line.

| ID | Decision | Recommendation | Blocks |
|---|---|---|---|
| D-014 | Tenancy scope: single-org forever vs multi-tenant build | Multi-tenant (boundary code + 31 adversarial tests already green; map is the only remainder) | TEN-01 → CLOSED, RSK-002 |
| D-018 | Backup keys + ceremony authorization | Authorize test-key scratch drill procedure first; production ceremony separately with its own key handling | AUD-01, BAK-01, GAP-003, RSK-003 |
| GAP-001 | PG cutover | NO CUTOVER now — JSON stays active; cutover only after hosted PG + parity + rollback proof (DB-01 stays AWAITING) | DET-03, DB-01 |
| D-020 | Coverage-dep pins + lock churn (pytest-cov 7.1.0 etc., PyPI hashes on file in GAP-005) | Approve pins; agent wires CI gates after PKG-01 | GAP-005, CICD-01 |
| D-019b | Remove deprecated `/demo/*` aliases | Remove only after a verified deploy (aliases stay until then) | REL-02 |

Reply format: "PKG-07: D-014=<multi|single|defer>, D-018=<...>,
GAP-001=<hold|proceed>, D-020=<approve|defer>, D-019b=<hold|approve>".

## PKG-08 -- UFI + security follow-up decision batch (2026-11-07)

Each line is independent; approve, defer, or decide per line. Nothing
below self-executes; first step after any approval is the named
reading or handshake -- never a mutation, purchase, or deployment.

| ID | Decision | Recommendation | Blocks |
|---|---|---|---|
| D-053 | Live provider credentials: telecom (TEL-08), intel (LIVE-GEO), financial (UFI-LIVE) | Per-provider choice: supply sandbox creds + handshake evidence, or record formal NO-LIVE per provider; no shared secrets in chat -- owner enters creds into the host directly | TEL-08, LIVE-GEO, UFI-LIVE |
| D-054 | Model PII-processing approval for the AI lane (UFI-AIMODEL) alongside PKG-04 | Approve only with a named model, data-flow note, and redaction rule; otherwise the deterministic engine stays authoritative and the lane stays NOT_STARTED | UFI-AIMODEL, AI-03 |
| D-055 | Map tile policy + MAP_PROVIDER value (LEAFLET) | Approve OSM tile policy review first; set MAP_PROVIDER only after the policy resolves; schematic stays until then | LEAFLET |
| D-056 | Retention/archival/purge execution authorization (DATA-01) | Authorize the documented schedule per collection; purges already run in tests via expires_at but production execution needs this line | DATA-01 |
| D-057 | Scratch Postgres for QA-02 pass line | Approve a free-tier scratch instance (no production data) or defer QA-02; GAP-001 cutover stays separate per PKG-07 | QA-02 |
| D-058 | Scheme-rule legal verification (REC-RULES) | Counsel verifies windows/deadlines per scheme, or defer; eligibility stays RULES_NOT_VERIFIED until then | REC function |

Covered elsewhere (no new decision needed): UFI-UI, UFI-UI2,
TEL-05, MAP-02, THEME-01, DET-12, FE-01 ride PKG-01 (hosted CI);
INF-01/DET-14 ride PKG-02/PKG-03; REL-02 rides D-019b;
DET-03/DB-01 ride GAP-001; TEN-01/AUD-01/BAK-01 ride D-014/D-018.
I18N-02 is an owner action (find native reviewers), not an
approval -- no packet line.

Reply format: "PKG-08: D-053=<creds:<provider>|no-live:<provider>|defer>,
D-054=<approve:<model>|defer>, D-055=<policy-first|defer>,
D-056=<approve|defer>, D-057=<approve|defer>, D-058=<approve|defer>".

## Reconciliation notes (found while preparing this file)

- RSK-005 detail ("live backend = ff7052b") predates the `b4732cb`
  tip; LOCAL refs show `origin/production-launch` = `b4732cb` per
  last fetch. Treat live identity as UNCONFIRMED until the PKG-02
  dashboard SHA lands. No register rewritten — this note governs.
- ISS-003 count ("162 entries, no manifest") is superseded by the
  LOCAL 2026-11-06 breakdown: 143 modified + 2 deleted + 226
  untracked. Manifest rule proposed in PKG-06.
- RSK-002 detail lists scoped surfaces through agents; LOCAL code
  now also covers txn/graph/risk/alert/notification/DI-intel/
  replay/ai-run/simulation (31 tests). The risk (single-org until
  D-014 map) is unchanged.
- Remote state above `b4732cb` is NOT verified: `git ls-remote`
  needs credentials the agent does not hold (HISTORICAL
  SEC_E_NO_CREDENTIALS). PKG-01's push will surface any remote
  movement safely (new branch; no force; no writes to existing
  branches).

## PKG-09 (DRAFT) — Federated auth + account recovery batch

Status: DRAFT prepared 2026-11-07 from the approved federation plan
(go still required to implement). It becomes a live package only
after the owner says `go` AND reviews this text. Nothing below
self-executes; first step after any approval is the named reading,
never a mutation, purchase, or deployment.

Decides: AUTH-01..09 (Google/Apple/Microsoft/Yahoo OIDC, email OTP,
magic links, enterprise SSO via OIDC + SAML 2.0, safe account
linking, password recovery). Each line is independent: approve,
defer, or record no-live per line.

Per social provider (Google/Apple/Microsoft/Yahoo): you create the
OAuth application in the provider console, enter the client ID and
secret (Apple: Services ID + ES256 private key) into the host
directly — never in chat — and register the callback URL exactly.
Planned callback path: /api/v1/auth/federation/callback (exact
absolute URL confirmed at implementation against the deployment).
Verify at creation that the sign-in flow sits on a genuinely free
tier with no card requirement; stop and report if any flow needs a
paid tier. No provider app, credential entry, or live login happens
without this line's approval.

Enterprise SSO: you supply IdP metadata (OIDC discovery URL or
SAML 2.0 metadata XML) or defer. No metadata is guessed.

OTP/magic-link/recovery: flows are implemented up to issuance with
rate limits; email/SMS delivery stays BLOCKED_EXTERNAL (no delivery
provider configured or approved).

Safe linking (AUTH-08) ships inside the batch: unverified-email
links rejected, no privilege from IdP claims (local roles only).

Approval wording: "Approve PKG-09: <per-line go|no-live|defer>,
callback URL <exact URL>, SSO metadata <supplied|defer>".

Cost/risk: $0 to decide; implementation is local code + mocked
tests. Live logins need each provider handshake recorded; mocked
sign-in is never presented as live.

## Package status summary

| Package | Subject | Status |
|---|---|---|
| PKG-01 | Push + PR + hosted CI | AWAITING OWNER |
| PKG-02 | Deploy identity readings | AWAITING OWNER |
| PKG-03 | Arming + live R1–R4 | AWAITING OWNER (phase-gated) |
| PKG-04 | Meta live-call decision | AWAITING OWNER |
| PKG-05 | Financial readings + risk call | AWAITING OWNER |
| PKG-06 | License + manifest rule | AWAITING OWNER |
| PKG-07 | Decision batch | AWAITING OWNER |
| PKG-08 | UFI + security follow-up batch | AWAITING OWNER |
| PKG-09 | Federated auth batch (DRAFT, needs go + review) | DRAFT |

No package self-executes. First safe step after any approval is
always the named reading or check — never a mutation.
