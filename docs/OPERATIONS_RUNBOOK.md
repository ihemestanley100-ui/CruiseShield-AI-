# docs/OPERATIONS_RUNBOOK.md

Consolidated starter runbook (Level 14 §7). Targets are declared
here; MEASUREMENT is not started — no SLO performance is claimed.

## Deploy (owner-authorized only)

Order: backend → verify → frontend → verify. Backend: Render
dashboard manual deploy of the approved full SHA; confirm deploy
ID, timestamp, LIVE status. Verify /api/v1/health, /ready, /,
auth mode. Frontend: Netlify build of same branch; verify root
+ /demo + one dynamic route return 200 (ISS-001 adapter fix
required first). Record all IDs in the evidence register.

## Rollback

Render: redeploy the last-known-good SHA; re-verify health/ready.
Netlify: restore previous production deploy. Rollback itself is
UNTESTED — first authorized deploy must include a rollback drill.

## Backup / restore (GAP-003 state)

Code tested (94 tests); no keys, no schedule, no live drill.
Do not improvise a ceremony. On D-018 approval: generate shares
off-repo, enable workflows, run keyless verify, then read-only
drill, then scratch-load path.

## Incident response

Owner is the only responder with dashboard access. Severity:
SEV-1 (live data breach/exposure) → revoke + rotate + notify;
SEV-2 (auth bypass suspected) → freeze deploys, diagnose;
SEV-3 (broken deploy) → rollback. Never paste secrets into chat;
record timelines in the evidence register.

## Credential rotation

SESSION_SECRET / DEMO_WRITE_TOKEN / DEMO_USERS: owner edits
values in Render dashboard → redeploy → verify auth_mode +
login probes. Frontend token stays EMPTY (R6).

## Access revocation

Sessions: epoch bump / secret rotation invalidates. Demo write
token: rotate value. No per-user remote wipe exists (gap).

## SLO targets (declared, unmeasured)

Availability 99.5% monthly (excludes free-tier sleep);
p95 API latency < 800ms; 5xx rate < 0.5%;
RPO 24h / RTO 4h (after GAP-003 closes).
Instrumentation: NOT_STARTED.

## Telecom Identity operations (TEL)

Thresholds: TELECOM_CONSENT_REQUIRED=0, TELECOM_RETENTION_DAYS=90,
TELECOM_ACTOR_PER_MIN=30, TELECOM_SUBJECT_PER_DAY=20. Provider
secrets unset -> all adapters honestly NOT_CONNECTED. Go-live path:
create connection -> credentials -> handshake -> sandbox requests ->
record evidence in LIVE_EVIDENCE_INDEX -> TEL-08 closes. Purge job:
telecom_purge_expired(now - retention) once DATA-01 authorizes the
schedule. Alerts: PROVIDER_ERROR spike, 429 spike, integrity
MISMATCH (freeze record, escalate). Raw E.164 never in state/logs.

## Geointel operations (GEO/IDV/ADR/MAP)

Thresholds GEO_* mirror telecom; MAP_PROVIDER=none (schematic).
Go-live mirrors telecom path per adapter; OSM tile binding needs
tile-policy review + owner MAP_PROVIDER decision first. Purge:
intel_purge_expired per collection once DATA-01 authorizes the
schedule. Alerts mirror telecom + coordinate/address disclosure
review. Raw identifiers never in state/logs.

## Universal intel operations (UFI)

No new env/quotas. Alerts open from tenant signals; illegal
transitions raise; notify failures degrade to notified:false.
Traces persist bounded (200); fraud alerts bounded (500).
Reports render gaps, never invented content. Party reveal is
write-gated + audited. No live-provider runbooks (UFI-LIVE
blocked); capability doc at /api/v1/altpayments/capabilities.

UFI slice 2: evaluate is idempotent (duplicates reported, never double-opened); readiness never promotes registry status; unstamped rows read as default-tenant.

UFI slice 3: agent tools read-only + tenant-checked; report.build assembles from tenant rows; fleet snapshot read-only; model lane pending PII approval.

SEC operations: rotate by setting SESSION_SECRET_PREVIOUS=old then SESSION_SECRET=new; clear previous after TTL. Client secrets shown once at issue; revoke is immediate. Revoked devices deny login/passkey/step-up with audit.

UFI closeout: regen evidence with python scripts/gen_closeout.py; score = CLOSED/total, gated rows reported separately; NOT PRODUCTION READY stands.

Agent OS ops: executions bounded (8 calls, depth 2); writes only via approval-gated manifests; conversations expire in 90 days (purge); metrics from stored rows.

Recovery ops: cases idempotent per txn+reason; live submit needs VERIFIED caps; approve/reject admin-only; manual packets tracked with external refs; metrics from rows.
