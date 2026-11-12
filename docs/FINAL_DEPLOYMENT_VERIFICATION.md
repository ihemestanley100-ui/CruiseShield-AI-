# FINAL DEPLOYMENT VERIFICATION (R02)

Date: 2026-11-02.

## Verdicts

| Check | Status | Evidence |
| ----- | ------ | -------- |
| Frontend prod build reproducibility | PASS | `npm run build` exit 0 (default env + QA envs), 8/8 pages, 103 kB shared JS. Logs: `build-final-r.log`, `build-csp-r07.log` |
| Backend container build + runtime | PASS | `docker build` exit 0; runs healthy as non-root; clean shutdown (R08). Log: `docker-build-r08.log` |
| Health/ready endpoints | PASS | `/api/v1/health` + `/api/v1/ready` 200 locally, in-container, and in QA runs |
| Env completeness + per-env correctness | PASS | `.env.example` canonical; CSP `connect-src` + API base bake per-env (verified :8000 default + :8100 QA); secrets server-side only |
| Staging blueprint | PASS (config) | `render.yaml` + service definitions exist (J8 programme); NOT provisioned |
| **Staging deployment + public URL + TLS** | BLOCKED | Requires owner approval (service creation, possible plan/billing implications). Nothing provisioned |
| **Deployment rollback (live)** | BLOCKED | Same gate; runbook exists (`DEPLOYMENT_ROLLBACK_RUNBOOK`-era docs), never executed live |
| **Restart recovery (hosted)** | BLOCKED | Same gate; local restart recovery verified repeatedly |

## Standing approval request (unchanged)

Provision staging (exact services/plan/URLs) + execute deploy and
rollback drill, or defer to a later programme. A local container run
is explicitly NOT deployment evidence.

## Release cert v3.0 addendum (2026-11-04, commit ff7052b)

- `render.yaml` re-validated: parses clean (pyyaml), declares `cruiseshield-ai`
  + `cruiseshield-ai-frontend` web services. Gap noted: `AI_MAX_OUTPUT_TOKENS`,
  `TRUSTED_PROXIES`, `STORE_BACKEND`, `DATABASE_URL`/`PG_CONNECT_TIMEOUT` are
  read by the backend but absent from the env list — harmless (code defaults
  apply), to add on the next config touch.
- Live backend `https://cruiseshield-ai.onrender.com/api/v1/health` re-probed:
  200 healthy, store/seed/graph/storage PASS, model + pg NOT_CONFIGURED
  (known). Posture unchanged: UNARMED (`auth_enabled:false`), short-SHA-only
  deploy identity (owner full-SHA read-out still pending).
- Frontend service: still NOT provisioned (no owner authorization); local
  production build verified EXIT=0, 8/8 pages; browser-certified locally
  (`THREE_JS_VISUAL_INTERACTION_AUDIT.md`).
- Pillar 02 verdict: PARTIAL. Nothing provisioned, deployed, or billed.

## Release closure FRC-001 addendum (2026-11-04)

Fresh live evidence (read-only GETs, new server `run_id` proves liveness):

- `GET /api/v1/health` → 200 `healthy`; store/seed/graph/storage PASS;
  model + pg NOT_CONFIGURED (unchanged, known).
- `GET /api/v1/auth/mode` → `{"auth_enabled":false}` — backend still UNARMED;
  no safe live write/arming action taken (owner-gated R3).

Deployment manifest (verified, no changes made):

| Item | Value |
|---|---|
| Backend URL | `https://cruiseshield-ai.onrender.com` (200, healthy) |
| Intended source | `production-launch @ ff7052b…65354` (= origin) |
| Deployed SHA | short `ff7052b` matches; full 40-char still needs owner source-link read |
| Frontend URL | NONE — service not provisioned (authorization outstanding) |
| Local frontend | production build EXIT=0, 8/8; served :3000 (200) for browser evidence |
| CORS | exact-origin allowlist in code; live origins need dashboard confirm |
| Storage | JSON active; pg NOT_CONFIGURED; no disks/databases evidenced |

Discrepancy live-vs-certified-local: live lacks `AI_MAX_OUTPUT_TOKENS` code
(deployed pre-cap commit lineage is `ff7052b` short-match; cap is uncommitted
local) and all working-tree source. No deployment executed — Pillar 02 stays
PARTIAL. Standing approval request unchanged.

## Owner-gated round addendum (2026-11-04)

Live re-probed: 200 healthy with NEW run_id (service restarted since last
probe — consistent with Free sleep/wake; NOT claimed as redeploy). Posture
unchanged: unarmed, model/pg NOT_CONFIGURED, SHA short-only. Frontend
Blueprint block re-read: `plan: starter` (paid) with explicit owner-decides
comment — the $0 path is manual dashboard creation as Free, never
Blueprint-as-written. Node 20.19.6 matches local runtime. Evidence: J-P2, J-C1.
No authorization arrived. Pillar 02 stays **PARTIAL**.

## Closure round addendum (2026-11-04, CS-FRC-ZG-001)

Live re-probed: 200 healthy, identical `run_id` (no redeploy occurred between
rounds, as expected without authorization). Local :8000/:3000 healthy (PIDs
recorded, processes untouched). No authorization arrived; no deployment
executed. Evidence: H-P2. Pillar 02 stays **PARTIAL** (R01–R04 owner-gated).
