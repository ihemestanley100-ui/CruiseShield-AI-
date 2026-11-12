# FINAL DEPLOYMENT GATE REGISTER — CruiseShield AI™

Date: 2026-11-03 · All mutating gates are CLOSED until the owner
approves with the exact scope named. Evidence column names what
must exist before the gate may open.

| Gate | Action | Prerequisites | Owner approval | Status | Evidence required | Next action |
|---|---|---|---|---|---|---|
| G-COMMIT-MANIFEST | Produce commit file list | Manifest §D selection rule; secret-scan PASS | No (prepare only) | READY | This register + manifest doc | Owner reviews manifest §D |
| G-COMMIT | `git commit` on `production-launch` | G-COMMIT-MANIFEST accepted; full tests + gate green on final tree | YES — explicit, this scope | EXECUTED 2026-11-03 | Commit `58a3d50d126edf05c8900c9edc00724d2220d45e` (133 paths, exact approved message); staged-verified; secret-scan PASS; 8 worktree leftovers as approved | Done — await G-PUSH approval |
| G-PUSH | `git push origin production-launch` | G-COMMIT done; pre-push history secret re-scan; Q-IP-1 Q1 SELF + Q2 YES recorded (SATISFIED 2026-11-03) | YES — explicit, this scope | EXECUTED 2026-11-03 | Remote branch created @ `58a3d50` (verified via ls-remote); upstream tracking set; no force/merge. NOTE: CI runs on push-to-master/PR only, so no Actions run fired on this push — needs a PR or master merge to exercise CI remotely (separate approval) | Done — await G-PROVISION approval |
| G-PROVISION | Create Render services (+ Vercel if chosen) | G-PUSH done (deploy from branch); $0 plans only; free subdomains | YES — explicit, this scope | BLOCKED | Service plan screenshots ($0); URLs TBD filled | Ask: approve $0 provisioning |
| G-DEPLOY | First deploy + deploy-order env wiring | G-PROVISION; P-1/P-2 secrets provisioned into prompts (never chat) | YES — explicit, this scope | BLOCKED | Health `healthy`; smoke 200s | Ask after G-PROVISION |
| G-CUTOVER | Any PG/database cutover | NOT APPLICABLE at launch (JSON path). Future: scratch parity suite green + review | YES — explicit, future scope | NOT_STARTED | Migration report vs COPY | None at launch |
| G-BACKUP | Execute any backup | NOT APPLICABLE at launch (nothing durable beyond git) | YES — explicit, future scope | NOT_STARTED | Workflow dispatch record | None at launch |
| G-AI-SPEND | ONE live Meta verification call (~10k tokens) | Disposable backend OR post-deploy live backend; cap/fallback verified in code | YES — explicit, this scope | BLOCKED | Run artifact (no creds) + quota note | Ask: approve 1 call |
| G-RELEASE | Declare production release + public URLs official | Acceptance plan rows 1–18 executed with evidence (14 needs G-AI-SPEND); Q3 terms review resolved; Q4 doc reconciliation approved+done | YES — explicit, this scope | BLOCKED | 18-row evidence pack + IP memo | Run Phase 8 after G-DEPLOY |

Rule: a gate opens only for its named scope; opening G-COMMIT
never implies G-PUSH. All approvals recorded here with date
before execution.

## R5/R6 addendum (owner-approved 2026-11-03, recorded — gates unchanged)

- R5 and R6 recorded in `DEMO_TOKEN_OWNER_CONFIRMATION_REGISTER.md`.
- G-DEPLOY prerequisites EXTENDED (additive): backend
  `DEMO_WRITE_TOKEN` set to a fresh 32+ random value in the
  Render prompt; pre-release verify = anonymous POST to a
  gated endpoint returns 401; public frontend has NO
  `NEXT_PUBLIC_DEMO_WRITE_TOKEN` value.
- No gate opened by this record. G-COMMIT-2 (for the
  uncommitted R1–R4 code) still needs its own approval.
