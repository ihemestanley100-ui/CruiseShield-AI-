# REMAINING 40 — CONFIGURATION AUDIT (READ-ONLY)

Inspected 2026-11-08 @ d82627d. No changes made. For each item:
current → proposed, reason, impact, rollback, authorization.

## 1. GitHub branches & protections

- Current: `feat/*` (d82627d, no upstream), `master` 753a6c5
  (ahead 1 of origin), `production-launch` b4732cb (origin in sync,
  ancestor of HEAD). Branch-protection rules NOT verifiable from
  here (needs authenticated API/owner readout).
- Proposed: confirm required-checks + no-direct-push on
  `production-launch` via PKG-02 readings.
- Reason/impact: prevents unverified merges. Rollback: n/a (readout).
- Authorization: PKG-02 readings (owner supplies).

## 2. CI/CD workflows

- Current: security-gate.yml triggers on push to master/
  production-launch + any PR + weekly audit; PG service +
  SCRATCH_DATABASE_URL wired; backup workflows disabled-by-default
  (manual dispatch + reviewer environment).
- Proposed: no change. Add coverage gates only after D-020 exec.
- Reason: least-change; gates already correct.
- Authorization: D-020 for coverage wiring.

## 3. Netlify (frontend)

- Current: base=frontend, `npm ci && npm run build`, publish=.next,
  OpenNext plugin. Package-lock committed (loud failure otherwise).
- Proposed: no change pre-deploy; set site + NEXT_PUBLIC_API_BASE_URL
  at deploy time per DEPLOY_ORDER.
- Impact/rollback: build-only; redeploy reverts.
- Authorization: deploy approval (item 9).

## 4. Render (backend + frontend) — $0 CONFLICT OPEN

- Current: BOTH services `plan: starter` (paid); backend has 1GB
  disk; STORE_BACKEND=json; MAP_PROVIDER=none; all provider secrets
  sync:false (unset); DEMO_WRITE_TOKEN/SESSION_SECRET sync:false.
- Proposed free variant (NOT applied): plan=free both, disk block
  removed; consequences: cold starts, ephemeral JSON (re-seeds;
  decisions/audits lost across restarts) — document as limitation,
  NOT production-ready storage.
- Reason: $0 lock. Impact: free services sleep; no persistence.
- Rollback: restore starter plan (paid — needs spend approval).
- Authorization: owner must choose free-variant or approve spend.

## 5. Database & persistence

- Current: STORE_BACKEND=json, DATABASE_URL unset, PG code paths
  inert. Scratch PG only in CI service container.
- Proposed: no change (GAP-001 HOLD).
- Authorization: GAP-001 for any cutover.

## 6. Auth callbacks & passkeys

- Current: no OAuth apps exist (nothing to set); RP_ID/RP_ORIGIN
  empty → passkey verification fails closed per D-045.
- Proposed: no change (PKG-09 DEFERRED).
- Authorization: PKG-09 for any federation work.

## 7. CORS / cookies / headers

- Current: single source `cors_options()` (app/config.py),
  FRONTEND_ORIGINS env-driven, default localhost. SESSION_SECRET
  empty → login disabled with honest 503. Cookie fix ed7674d on
  production-launch.
- Proposed: set FRONTEND_ORIGINS to deployed frontend origin at
  deploy time (backend redeploy per DEPLOY_ORDER step 3).
- Impact: cross-origin pages work; mis-set breaks auth visibly.
- Rollback: revert env value + redeploy.
- Authorization: deploy approval.

## 8. Secrets & env exposure

- Current: .env + .env.arming.local exist but gitignored (verified);
  only .env.example (empty values) in scope; secret_scan PASS;
  NEXT_PUBLIC_DEMO_WRITE_TOKEN sync:false (nothing baked to JS).
- Proposed: no change. Owner enters prod secrets directly into host.
- Authorization: none (already correct).

## 9. Health & observability

- Current: /api/v1/health + /api/v1/ready auth-open, rate-limit
  exempt; render healthCheckPath set both services. No external
  APM — in-app audit/metrics only (gap: no paging/alerting).
- Proposed: add uptime/alerting only with a verified-free provider
  (proposal needed; none selected).
- Authorization: owner selects provider first.

## 10. Domain migration readiness

- Current: all origins env-driven (NEXT_PUBLIC_SITE_URL,
  NEXT_PUBLIC_API_BASE_URL, FRONTEND_ORIGINS, RP_ORIGIN); OAuth
  callback URLs N/A (no apps); email-link flows absent (AUTH-09
  deferred). Checklist exists in prior audit.
- Proposed: no change until a domain decision exists.
- Authorization: domain/DNS decision (not requested now).

## Summary

No configuration change is authorized by this audit. Two items need
owner choice before any deploy: (a) Render free-variant vs spend,
(b) uptime/alerting provider. Everything else is already correct
for the current HOLD/DEFER posture.
