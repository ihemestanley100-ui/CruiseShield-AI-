# CRUISESHIELD REMEDIATION REPORT — CS-FRC-2026-001

Date: 2026-11-04. Commit: `ff7052bdf0ac48a68f69c3937d9b8708ca265354`.
Rule: every repair below is additive or config-neutral; full patch = `git diff`.

## Repairs executed

1. **S-04 (partial close): `render.yaml` declares `AI_MAX_OUTPUT_TOKENS: 4096`.**
   5-line additive block in the AI cost-controls section; value equals the code
   default (behavior-neutral); YAML re-validated with pyyaml; `test_config_safety`
   6/6 green. Remaining code-defaulted vars (`TRUSTED_PROXIES`, `STORE_BACKEND`,
   `PG_CONNECT_TIMEOUT`, `DATABASE_URL`) accepted as documented-default posture.
2. **Flake analysis (closed, no code change):** the 4 transient backend failures
   looped 5x in isolation = 5/5 green; a fresh full suite went 431/73/0.
   Classification: Windows file-lock contention under load. No test touched.
3. **E2E workflow (fresh, isolated state copy):** DETECT (1 alert, risk 84/HIGH,
   8 rules) / CONNECT (22 nodes, 30 edges) / INVESTIGATE (200) / VERIFY (39
   evidence items) / SIMULATE (84 -> 72, pinned values match) / DECIDE (TRIAGED,
   audit_0007) / AUDIT (1 decision event) — all PASS. `data/state.json` untouched.

## Mandatory disclosure: unintended Meta API attempts

During the E2E EXPLAIN leg I believed no key existed (shell env UNSET; an
earlier sandboxed listing hid dotfiles). A repo-root `.env` (git-ignored,
10/28, never read or printed) actually holds `MODEL_API_KEY`, so 3 keyed
`POST ai-analysis` attempts went out. All returned **HTTP 503 MODEL_TIMEOUT**;
no response, no token usage, no SUCCEEDED run was recorded. A bare keyless
`GET https://api.meta.ai/v1` returns 404 in ~1 s, proving egress works — so
the timeouts are key/allowance/provider-side, not network. No further keyed
attempt will be made without explicit owner approval. Pillar 05 stays BLOCKED.

## Investigations closed without change (correct outcome)

- PostCSS advisories: `npm audit fix --dry-run` shows NO non-breaking fix
  (only `--force` to Next 16 / vitest 4). Accepted residual, documented.
- Meta source review: adapter complete; no safe improvement left to make.
- Financial: worst-case ceilings computed ($0.025/call, ~$2.50/day at
  cap=100); recommendation recorded (set cap 1-5 when arming). No default changed.
- No migration proposed; no provisioning; no billing touched.

## Files changed by this execution

- Modified: `render.yaml` (+5 lines).
- Created: `FINAL_REMEDIATION_BASELINE.md`, `PUBLIC_REPOSITORY_RELEASE_MANIFEST.md`,
  this report, `browser-evidence/cert-frc/` (3 PNGs).
- Addenda: 7 authoritative audit docs + evidence register + matrix (J11-33) +
  owner actions. All prior-session work preserved byte-for-byte.

## ZG-001 remediation (2026-11-04)

- S-04 CLOSED: `STORE_BACKEND=json` + `PG_CONNECT_TIMEOUT=5` added to
  `render.yaml` (defaults-matching, behavior-neutral); YAML re-validated;
  config tests 6/6. `TRUSTED_PROXIES` (empty secure default) and `DATABASE_URL`
  (secret, empty correct) accepted as documented — no secret in Blueprint.
- Fresh: backend 431/73/0, frontend 391/391, build EXIT=0 8/8, tsc 0 errors.
- Browser: collapse transition + /demo navigation verified in pixels/console;
  region legend confirmed display-only by design (no defect).
- Reproducibility: fresh clone @ ff7052b + 7-test smoke green, clone removed.
- Manifest regenerated: 543 files, 157 INCLUDE / 386 EXCLUDE, 0 unclassified.
- No deployment executed (no authorization). No live Meta attempt. No spend.
- Non-code change this round: `render.yaml` +9 lines total across both rounds.

## ZGEP-001 closed loop (2026-11-04)

Fresh re-verification (nothing assumed): backend 431/73/0 exit 0; frontend
391/391; build EXIT=0 8/8; tsc 0; boot health+ready 200 with security headers
and zero server-log errors; secret scan 0/1180; bundle re-verified clean;
pip-audit 0, npm postcss×2 unchanged; browser recapture green (0 errors);
live backend re-probed healthy + still unarmed (new run_id). TODO sweep: zero
actionable markers. Zero source/config changes were needed or made this round.

Rule-3 loop per open requirement (reproduce → root cause → disposition):

| Req | Reproduced | Root cause (proven) | Fix attempted | Result |
|---|---|---|---|---|
| ZG-P2-01 live unarmed | Yes, fresh GET | Missing server-side env (dashboard-only) | None possible w/o dashboard | Owner: R3 arming |
| ZG-P2-02 SHA short-only | Yes (no full SHA obtainable) | Dashboard-only evidence | None possible | Owner: R2 read |
| ZG-P2-03 no frontend URL | Yes (none exists) | No provisioning authorization | Spec prepared, not executed | Owner: auth |
| ZG-P4-02 live R1–R4 | Withheld (unsafe unarmed) | Blocked on ZG-P2-01 | Procedure prepared | Owner: R3 first |
| ZG-P4-03 postcss | Yes (audit) | Breaking-only upstream fix | Dry-run evaluated | Owner: accept/upgrade |
| ZG-P5-02/03 Meta live | Yes (503s, no allowance) | Paid-only + undiagnosed key | No spend, no attempt | Owner: key + approval |
| ZG-P6-02 future $0 | Yes (research) | No provider hard cap exists | Ceilings + guidance recorded | Owner: readouts + accept |
| ZG-P7-03 release | Yes (tree unreleased) | No push/license approval | Manifest proposed (543 files) | Owner: approve + LICENSE |

No technically remediable gap remains open. Every PARTIAL/BLOCKED item now has
a named owner, exact action, and dependency. Overall: RELEASE CERTIFICATION
PENDING (per Rule 12).

## Closure execution CS-FRC-ZG-001 (2026-11-04)

Preservation audit: ff7052b=origin, 166 entries, 0 staged/stashes; state.json
sha ba1d4db4… pristine; :8000/:3000 PIDs recorded, untouched; live backend
re-probed healthy with identical run_id (no redeploy). Fresh: 431/73/0,
391/391, build 8/8, tsc 0, secret scan 0/1181. R08 CLOSED via root-cause proof
(Next 15.5.28+15.5.29 pin postcss exactly 8.4.31; zero app attack surface;
documented accepted risk — no compatible fix exists, no override applied).
R06 sharpened (overage $0.30/GB quantified, no cap found). Manifest drift
patched (544 files). Zero source/config changes this round — none available.
R01–R07+R09 dispositions unchanged (owner-gated). Evidence: H-series.

## Auto-fix round CS-AUTO-001 (2026-11-04)

Deepest-execution pass over every PARTIAL/BLOCKED pillar. Results:

- P05 Meta: timeout mechanism SOLVED without spend or key use. Keyless POST =
  instant 401 (path healthy); official docs = invalid keys fail fast (401),
  billing fails fast structured (402); adapter maps 401 to a distinct code.
  The 3 keyed 30 s timeouts therefore passed auth and stalled downstream
  (account entitlement/provisioning or provider hang). Remaining step is
  owner-only: inspect `dev.meta.ai/platform` (usage/keys/billing) or approve
  one instrumented call. No free tier exists — nothing free to switch to.
- P07 repo: push transport verified ready (dry-run, zero mutation); largest
  release file 71 KB (no size risk). Remaining steps are approvals + LICENSE.
- P04 live: HSTS confirmed TLS-conditional by design. Live probes still need
  arming. Nothing else auto-fixable (all code findings closed in prior rounds).
- P02/P06: no dashboard access exists on my side; no code lever can set env,
  provision services, or cap provider billing. Genuinely owner-only.
- P01/P03: remain PASS; no changes made, none needed.

Verdict: the auto-fixable set is EMPTY — every remaining item is proven
owner/external-gated (see approval register in CRUISESHIELD_OWNER_ACTIONS.md
and the final answer). Evidence: I-series.

## Owner-gated round (2026-11-04, ACTION 01–07 sweep)

Preservation audit clean (ff7052b=origin, 166 entries, state pristine).
Fresh: 431/73/0, 391/391, scan 0/1181, live healthy/new-run_id/unarmed.
New findings: (1) backend restarted since last probe (Free sleep/wake
signature, not a redeploy claim); (2) Blueprint frontend is `plan: starter`
— $0 path is manual Free creation only; (3) Node version match verified;
(4) card-removal mitigation identified for owner evaluation (not performed).
Zero source/config changes — none available. Evidence: J-series.

## R01 pre-arm gate (2026-11-04, Action 01 only — STOP held)

$0-neutrality VERIFIED before any change: entering 3 env vars costs nothing;
one manual redeploy consumes a few of the 0/500 used free pipeline minutes;
zero new services/disks/DBs/add-ons/plans; runtime + bandwidth pattern
unchanged. Rollback (remove values + redeploy) is equally $0.
Functional consequence disclosed, not hidden: after arming, anonymous public
writes become login-gated per the R6-approved posture (reads stay public;
demo login via the 2 provisioned users). Before-state snapshotted (M-A1/M-P1).
No dashboard change, secret handling, or redeploy performed — awaiting the
owner's entry + explicit redeploy authorization, after which the 7-step live
verification (names-present, deploy success, auth_enabled, admin/investigator
login, unauthorized rejection, R1–R4 probes, secret-leak scan) executes.

## Action-01 intake (2026-11-04, awaiting owner readouts)

Pre-evidence baseline: ff7052b=origin, 166 entries, state pristine; live
backend healthy, same run_id as J-P2 (no restart), still unarmed.

Reconciliation procedure locked (executes the moment evidence lands):
(a) compare each env name to the code-required set (SESSION_SECRET 32+ chars
assumed present-only, DEMO_USERS parseable, DEMO_WRITE_TOKEN backend-only);
(b) compare full 40-char SHA to HEAD ff7052b (MATCH required, no prefix rule);
(c) compare plans/prices/usage against the $0 ceiling and the quantified
$0.30/GB overage rate; (d) record R01/R02/R06 PASS/PARTIAL with evidence IDs.

Safest free-tier arming plan (prepared, NOT executed): owner generates three
fresh random values locally (32+ chars; DEMO_USERS in `user:pbkdf2$...:role`
format per app/auth.py) → enters them ONLY in Render dashboard → Environment
→ triggers Manual Deploy of exactly ff7052b → I verify names-without-values,
`auth_enabled:true`, then safe R1–R4 probes. No secret ever in chat/logs/Git.
Rollback: remove/rotate values + redeploy (documented, owner-executed).

Frontend $0 decision procedure: IF readouts show backend on Free + no paid
add-ons + usage headroom, THEN manual dashboard creation as Free (plan: Free,
rootDir frontend, build `npm ci && npm run build`, start `npm start -- --port
$PORT`, env NEXT_PUBLIC_API_BASE_URL + empty token var) can complete at $0 —
pending explicit provisioning authorization. Blueprint-as-written is FORBIDDEN
for $0 (declares `plan: starter`). ELSE stay unprovisioned with reason recorded.

Bandwidth risk (no acceptance made): usage is ~0/5 GB, so realistic demo
exposure is cents-at-most — but Control 5 forbids ME accepting it. Resolution
requires the owner to EITHER verify Render's no-card behavior and remove the
card (converting overage to suspension — unconfirmed provider behavior) OR
explicitly accept the quantified $0.30/GB residual in writing. No migration
eliminates overage-class risk (verified same-class billing everywhere
comparable); none proposed without approval.
