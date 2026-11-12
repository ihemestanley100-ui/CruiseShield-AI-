# Operational Readiness Checklist (Stage 1)

Candidate line: `3cbbb48` + pending commits (12-file sync +
this programme's changes). Check = verified this programme
unless marked OWNER (external).

## Service

- [x] Health contract: 4 qualified states, honest headlines.
- [x] Readiness endpoint distinct from health (`/ready`).
- [x] Synthetic-only data; no PII; masking verified by tests.
- [x] Audit chain: seal/verify/report + tamper tests.
- [ ] OWNER: D-018 ceremony executed; live health PASS sealed.
- [ ] OWNER: production backup generation + restore drill.

## Security

- [x] AuthN/Z regression green (F-A/B/C closed, F-D/E verified).
- [x] Secret hygiene (no values in tree; safety tests green).
- [ ] OWNER: SESSION_SECRET + DEMO_USERS provisioned in hosting.
- [ ] OWNER: render.yaml $0 decision (strip plan+disk) before apply.
- [ ] OWNER: branch protection applied per recommendation.

## Release

- [x] Evidence package complete (this directory + ERD-001).
- [x] Risk register current; F-CSG records corrected.
- [ ] OWNER: hosted CI green on final candidate.
- [ ] OWNER: O-05 verdict received + dispositioned.
- [ ] OWNER: F-CSG-002/003 signatures.
- [ ] OWNER: Stage 1 acceptance decision signed.
