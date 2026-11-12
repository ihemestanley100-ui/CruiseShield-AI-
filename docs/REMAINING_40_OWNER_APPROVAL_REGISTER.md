# REMAINING 40 — OWNER APPROVAL REGISTER

Pending decisions ONLY (2026-11-08 @ d82627d). Already-decided items
(NO-LIVE, DEFER, HOLD as current state) are excluded at the end.

## 1. PKG-01 / D-017 — Push + PR to `production-launch` + hosted CI

- Decision: approve push of `feat/phasezero-foundations`, PR to
  `production-launch`, and hosted security-gate run.
- Why: 12 rows need hosted execution (node EPERM locally); DET-13 is
  the gate itself.
- Alternatives: stay local (default; frontend stays unverified).
- Recommended: approve (manifest reviewed, secrets clean, lockfile ok).
- Free-tier: $0 (github-hosted runners, OSS actions).
- Security/privacy/ops: code leaves the laptop to GitHub; no secrets
  in scope (secret_scan PASS, .env ignored).
- Reversibility: full (close PR, delete remote branch).
- Deferral: 13 rows stay open; no browser/vitest evidence; no release.

## 2. D-018 — Production backup-key ceremony

- Decision: authorize the production key ceremony (custody, access,
  recovery, rotation per prepared procedure).
- Why: AUD-01/BAK-01 need prod-key proof; test-key drills only so far.
- Alternatives: test-keys forever (no proven prod recovery).
- Recommended: approve after reviewing custody procedure.
- Free-tier: $0 (local crypto, no service).
- Reversibility: keys rotatable; ceremony record permanent (by design).
- Deferral: audit/backup stay IN_PROGRESS; recovery unproven.

## 3. GAP-001 — PostgreSQL cutover

- Decision: approve cutover only after hosted PG + parity + rollback
  proof are presented.
- Why: DET-03/DB-01 need durable signal/event persistence.
- Alternatives: JSON forever (accepted: ephemeral, re-seeds, no
  cross-restart durability — NOT production-grade for investigations).
- Recommended: conditional approve (evidence first, then cutover).
- Free-tier: verify free PG allowance + limits before approval.
- Reversibility: rollback drill required BEFORE cutover.
- Deferral: JSON stays; DET-03/DB-01 stay open.

## 4. D-020 execution — Coverage pins + gate wiring

- Decision: execution authorization (in-principle granted) + PKG-01.
- Why: CICD-01 needs enforced thresholds.
- Alternatives: unmeasured coverage (accepted risk).
- Recommended: approve with PKG-01.
- Free-tier: $0. Reversibility: full (revert workflow).
- Deferral: CICD-01 stays open.

## 5. D-019b — Demo-alias removal (post-deploy)

- Decision: approve removal of 4 deprecated `/api/v1/demo/*` aliases
  after a verified deploy.
- Why: REL-02 cleanup; aliases already deprecated + logged.
- Alternatives: retain (tech debt, confusion risk).
- Recommended: approve-when-deployed.
- Free-tier: $0. Reversibility: revert commit.
- Deferral: REL-02 stays open.

## 6. D-056 — Retention/purge authorization

- Decision: authorize retention schedule + production purge execution
  (after backup proven).
- Why: DATA-01 has no purge code and no authorization.
- Alternatives: retain everything (storage + privacy risk).
- Recommended: approve schedule; execution only post-backup-proof.
- Free-tier: $0. Reversibility: NONE for deleted data (backup first).
- Deferral: DATA-01 stays open.

## 7. D-057 — Scratch PostgreSQL for QA-02

- Decision: accept the CI ephemeral PG service (free, no prod data)
  as the QA-02 pass line.
- Why: 73 skips need SCRATCH_DATABASE_URL; sandbox has no PG.
- Alternatives: QA-02 stays skipped-forever.
- Recommended: approve (zero cost, zero prod data, job-scoped).
- Reversibility: full. Deferral: QA-02 stays open.

## 8. D-055 — Map tile policy + MAP_PROVIDER

- Decision: approve tile policy, then set MAP_PROVIDER (else schematic).
- Why: LEAFLET binding needs the policy decision first.
- Alternatives: schematic forever (accepted limitation).
- Recommended: policy-first per LEAFLET_TILE_POLICY_REVIEW.md.
- Free-tier: OSM free within policy; verify attribution + limits.
- Reversibility: full (config value). Deferral: LEAFLET stays NOT_STARTED.

## 9. D-017 deploy — Production deployment

- Decision: approve free-tier deploy (backend + frontend) + smoke capture.
- Why: DET-14/INF-01 need live verification.
- Alternatives: staging-only first (recommended intermediate).
- Recommended: staging first; production only after smoke + billing
  readouts. NOTE: current render.yaml uses starter plans + disk
  (paid) — free variant or explicit spend approval required.
- Free-tier: UNVERIFIED — needs PKG-05 readings first.
- Reversibility: services deletable; data ephemeral on free tier.
- Deferral: DET-14/INF-01/REL-02 stay open; no public URL.

## 10. PKG-02 / PKG-03A / PKG-05 — Owner-supplied readings

- Decision: none to act — owner supplies readouts (deploy identity,
  env-name presence, 7 billing/usage readings).
- Why: gates every deploy/billing claim.
- Deferral: $0 operation unverifiable; deploy stays blocked.

## Excluded — already decided (reopen needs a NEW decision, not asked)

- PKG-09 auth batch: DEFERRED. Licence D-015: DEFERRED.
- PG HOLD as current state (GAP-001 item 3 is the forward path).
- NO-LIVE: AI-01/AI-03 (PKG-04/D-016), TEL-08/LIVE-GEO/UFI-LIVE (D-053).
- D-054 PII lane: DEFERRED. D-058 scheme legal: DEFERRED.
- I18N-02/VIS-01: owner ACTIONS (translators, image), not decisions.
