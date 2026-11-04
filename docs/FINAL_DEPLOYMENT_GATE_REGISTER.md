# FINAL DEPLOYMENT GATE REGISTER — CruiseShield AI™

Date: 2026-11-03 · All mutating gates are CLOSED until the owner
approves with the exact scope named. Evidence column names what
must exist before the gate may open.

| Gate | Action | Prerequisites | Owner approval | Status | Evidence required | Next action |
|---|---|---|---|---|---|---|
| G-COMMIT-MANIFEST | Produce commit file list | Manifest §D selection rule; secret-scan PASS | No (prepare only) | READY | This register + manifest doc | Owner reviews manifest §D |
| G-COMMIT | `git commit` on `production-launch` | G-COMMIT-MANIFEST accepted; full tests + gate green on final tree | YES — explicit, this scope | BLOCKED | Green suite evidence; manifest | Ask: approve commit of manifest files |
| G-PUSH | `git push origin production-launch` | G-COMMIT done; pre-push history secret re-scan; Q-IP-1 Q1 SELF + Q2 YES recorded (SATISFIED 2026-11-03) | YES — explicit, this scope | BLOCKED | Commit SHA; clean scan | Ask after G-COMMIT |
| G-PROVISION | Create Render services (+ Vercel if chosen) | G-PUSH done (deploy from branch); $0 plans only; free subdomains | YES — explicit, this scope | BLOCKED | Service plan screenshots ($0); URLs TBD filled | Ask: approve $0 provisioning |
| G-DEPLOY | First deploy + deploy-order env wiring | G-PROVISION; P-1/P-2 secrets provisioned into prompts (never chat) | YES — explicit, this scope | BLOCKED | Health `healthy`; smoke 200s | Ask after G-PROVISION |
| G-CUTOVER | Any PG/database cutover | NOT APPLICABLE at launch (JSON path). Future: scratch parity suite green + review | YES — explicit, future scope | NOT_STARTED | Migration report vs COPY | None at launch |
| G-BACKUP | Execute any backup | NOT APPLICABLE at launch (nothing durable beyond git) | YES — explicit, future scope | NOT_STARTED | Workflow dispatch record | None at launch |
| G-AI-SPEND | ONE live Meta verification call (~10k tokens) | Disposable backend OR post-deploy live backend; cap/fallback verified in code | YES — explicit, this scope | BLOCKED | Run artifact (no creds) + quota note | Ask: approve 1 call |
| G-RELEASE | Declare production release + public URLs official | Acceptance plan rows 1–18 executed with evidence (14 needs G-AI-SPEND); Q3 terms review resolved; Q4 doc reconciliation approved+done | YES — explicit, this scope | BLOCKED | 18-row evidence pack + IP memo | Run Phase 8 after G-DEPLOY |

Rule: a gate opens only for its named scope; opening G-COMMIT
never implies G-PUSH. All approvals recorded here with date
before execution.
