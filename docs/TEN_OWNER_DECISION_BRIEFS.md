# TEN OWNER DECISION BRIEFS

2026-11-08 @ d82627d. Each brief: ID, affected rows, blocked now,
authorizes / does-NOT-authorize, alternatives, recommendation, $0,
security/privacy/data, reversibility, deferral cost, exact wording.
Approval-in-principle ≠ execution authorization (flagged per item).

## B1. PKG-01 / D-017 — Push + PR + hosted CI

- Affects: SITE-01 THEME-01 TEL-05 MAP-02 UFI-UI UFI-UI2 AGOS-UI
  REC-UI DET-12 DET-13 FE-01 QA-02 (QA-02 also needs B7).
- Blocked: all hosted execution (node EPERM locally).
- Authorizes: push reviewed branch, open PR to production-launch,
  run gate. NOT: merge, deploy, secrets, spend.
- Alternatives: stay local (default), narrower file subset PR.
- Recommended: approve full reviewed scope (manifest clean).
- $0: yes (free runners; quota readout pending).
- Sec/priv/data: source to GitHub; no secrets (scan PASS, .env out).
- Reversible: yes (close PR / delete remote branch).
- Deferral: 12 rows stay open; frontend never verified.
- Wording: "PKG-01: approve push feat/phasezero-foundations and PR
  to production-launch for hosted CI observation only. No merge,
  deploy, or spend."

## B2. D-018 — Production key ceremony

- Affects: AUD-01 BAK-01.
- Blocked: prod-key audit proof + verified prod restore.
- Authorizes: ceremony with documented custody/rotation. NOT:
  test-key weakening, standing prod access, data export.
- Alternatives: test-keys forever (recovery unproven).
- Recommended: approve after custody-procedure review.
- $0: yes. Sec: keys rotatable; ceremony log permanent by design.
- Reversible: keys yes; ceremony record no (intended).
- Deferral: audit/backup stay IN_PROGRESS; DR unproven.
- Wording: "D-018: authorize the production backup-key ceremony per
  the documented custody procedure. Test drills continue."

## B3. GAP-001 — PG cutover (conditional)

- Affects: DET-03 DB-01.
- Blocked: durable signal/event persistence.
- Authorizes: NOTHING now — approve the condition: cutover only
  after hosted PG + parity + rollback proof presented.
- Alternatives: JSON forever (ephemeral; not production-grade).
- Recommended: approve condition; decide cutover on evidence.
- $0: free PG unverified — needs provider worksheet first.
- Sec/data: tenant isolation + RLS review at migration; backup first.
- Reversible: only via pre-cutover rollback drill (mandatory).
- Deferral: JSON stays; rows stay open.
- Wording: "GAP-001: approve cutover CONDITIONAL on hosted PG,
  parity report, and successful rollback drill. No migration now."

## B4. D-020 execution — Coverage gates

- Affects: CICD-01.
- Blocked: enforced thresholds (in-principle only, needs exec auth).
- Authorizes: pin install + gate wiring + follow-up CI run. NOT:
  threshold lowering to force green.
- Alternatives: unmeasured coverage.
- Recommended: approve alongside PKG-01.
- $0: yes. Reversible: yes (revert workflow).
- Deferral: CICD-01 stays open.
- Wording: "D-020: authorize coverage-pin execution and CI gate
  wiring. Thresholds enforced as prepared."

## B5. D-019b — Alias removal after verified deploy

- Affects: REL-02.
- Blocked: removal of 4 deprecated /api/v1/demo/* aliases.
- Authorizes: removal patch + regression run, post-deploy only.
- Alternatives: retain (documented tech debt).
- Recommended: approve-when-deployed.
- $0: yes. Sec: reduces attack surface. Reversible: revert commit.
- Deferral: REL-02 stays open.
- Wording: "D-019b: after a verified deploy, remove the deprecated
  demo aliases and run regression."

## B6. D-056 — Retention/purge authorization

- Affects: DATA-01.
- Blocked: schedule implementation + any production purge.
- Authorizes: documented schedule; execution only after backup
  proof. NOT: ad-hoc deletes, unlogged purges.
- Alternatives: retain everything (storage + privacy risk).
- Recommended: approve schedule; gate execution on B2 evidence.
- $0: yes. Data: deletions IRREVERSIBLE — backup first.
- Deferral: DATA-01 stays open; data grows unbounded.
- Wording: "D-056: authorize the retention schedule. Production
  purge execution only after verified backup."

## B7. D-057 — Scratch PG acceptance

- Affects: QA-02 (shared with B1).
- Blocked: 73 skipped PG tests.
- Authorizes: treating the CI ephemeral PG service (free, no prod
  data, job-scoped) as the pass line. NOT: production PG.
- Alternatives: QA-02 skipped forever.
- Recommended: approve.
- $0: yes. Reversible: yes. Deferral: QA-02 stays open.
- Wording: "D-057: accept the CI ephemeral PG service as the QA-02
  pass line. No production data."

## B8. D-055 — Tile policy + MAP_PROVIDER

- Affects: LEAFLET.
- Blocked: tile renderer binding (policy-first).
- Authorizes: policy approval + MAP_PROVIDER value. NOT: paid tiles.
- Alternatives: schematic forever (accepted limitation).
- Recommended: approve policy per review doc, then bind.
- $0: OSM free within policy (attribution required).
- Reversible: yes (config value). Deferral: LEAFLET NOT_STARTED.
- Wording: "D-055: approve the OSM tile policy and set MAP_PROVIDER
  accordingly. Schematic until then."

## B9. Deploy — Staging then production (D-017/GAP-009)

- Affects: DET-14 INF-01 (REL-02 follows).
- Blocked: live verification, public URL, smoke evidence.
- Authorizes (staging): free-variant services + smoke capture. NOT:
  production cutover, starter spend, DNS, prod data.
- Alternatives: no deploy (stay local), production-direct (rejected:
  needs staging + readings first).
- Recommended: staging first; production after smoke + PKG-05.
- $0: staging yes IF free variant chosen; starter needs spend OK.
- Sec/data: prod secrets owner-entered; SESSION flows verified.
- Reversible: services deletable; free data ephemeral.
- Deferral: no public URL; rows stay open.
- Wording: "Deploy: approve free-variant STAGING deploy + smoke
  capture. Production and any spend need a separate approval."

## B10. Readings — PKG-02/03A/05 (no action authorized)

- Affects: none directly; enables B9 + billing claims.
- Blocked: protection/quota/plan/overage facts.
- Authorizes: NOTHING except owner supplying readouts.
- Alternatives: proceed blind (rejected).
- Recommended: supply 7 billing + 7 deploy-identity readings.
- $0: n/a (fact-finding). Reversible: n/a.
- Deferral: $0 and deploy claims stay unverifiable.
- Wording: "Readings: owner supplies PKG-02/03A/05 readouts. No
  changes authorized."

## Approval vs execution

B1/B7/B10 execute on approval. B2/B4/B5/B6/B8 authorize bounded
execution as worded. B3/B9 are CONDITIONAL/STAGED: principle now,
execution only after stated evidence or a further approval.
