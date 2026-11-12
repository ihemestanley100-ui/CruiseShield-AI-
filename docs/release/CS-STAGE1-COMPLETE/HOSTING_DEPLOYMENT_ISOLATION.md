# Hosting & Deployment Isolation Assessment (CS-DEPLOY-001/002/003)

Status: ASSESSED from repository + owner-reported configuration.
No dashboard access from here; no service created/modified.

## Render (CS-DEPLOY-001)

Owner-reported: Free service, Auto-Deploy OFF, PR Previews OFF,
health check `/api/v1/health`, existing preview service. The
`plan: starter` + 1 GB disk block in `render.yaml` (lines 17–28)
CONFLICTS with $0: disks require a paid instance type. The file
itself documents the free-tier removal (reseed on restart, no
persistence). DO NOT apply `render.yaml` as-is: applying the
starter plan would create a billable resource. Required before
any blueprint apply: owner decision to (a) strip plan+disk for a
free ephemeral launch, or (b) separately authorize paid spend
(forbidden by current policy). DATA_DIR `/srv/data` assumes the
disk; free-tier uses ephemeral container storage.

## Netlify (CS-DEPLOY-002, O-03 record)

Owner-reported: production branch `production-launch`, Auto
Publishing Locked, existing PR Deploy Preview + preview config.
`netlify.toml` builds `frontend/` via OpenNext adapter. O-03
evidence record: see O03_EVIDENCE_RECORD.md (this directory) —
links candidate commit → preview URL → production SHA. No
unlock or deploy performed or authorized here.

## Branch protection (CS-DEPLOY-003, recommended, not applied)

For `production-launch`: require PR + independent review (O-05),
require security-gate status checks, no direct pushes, no bypass
without written governance exception, merge-commit strategy only
(never squash — preserves SHA/evidence traceability). GitHub
settings CANNOT be changed from here; owner applies in dashboard.

## Isolation verdict

Preview and production are separated by branch + locks per
owner report; repo evidence cannot independently confirm
dashboard state (BLOCKED item for owner evidence, as in
CS-ERD-004B). No repo-controlled path deploys on push.
