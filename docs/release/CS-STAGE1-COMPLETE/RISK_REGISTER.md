# Risk & Exception Register (CS-GOV-003)

Scale: severity Critical/High/Medium/Low; likelihood H/M/L.
Owner: project owner unless stated. Status at programme close.

## Technical defects (closed this programme)

- R-SEC-01 F-A session non-dict AttributeError — Low/M —
  fixed + tested (auth.py). Residual: none. CLOSED.
- R-SEC-02 F-B unknown-slug default collapse — Medium/L —
  fixed to isolation + tested (tenancy.py). Residual: none. CLOSED.
- R-SEC-03 F-C ABAC tenant pinning — High/L (multi-tenant only;
  single-org unaffected) — fixed via D-014 + tested (abac.py).
  Residual: token/client subjects remain default-scoped by design
  (documented). CLOSED with note.

## Accepted / documented risks (need signatures)

- R-DEP-01 F-CSG-002 npm dev-toolchain — Low — accepted-risk
  recommendation; upgrade post-release. PENDING signatures.
- R-DEP-02 F-CSG-003 postcss via next (CVSS 6.1) — Moderate —
  residual-risk recommendation; Next major post-release.
  PENDING signatures.
- R-I18N-01 machine-drafted translations (incl. gapsOk) — Low —
  human review via I18N-02 path. PENDING reviewer.

## External / governance blockers

- R-GOV-01 O-05 reviewer not appointed — High/M — package ready;
  owner action. BLOCKED.
- R-GOV-02 no penetration test ever performed — High — scope
  prepared; independent execution external. BLOCKED.
- R-GOV-03 hosted CI on latest tree unconfirmed from here —
  Medium — owner/hosted evidence. BLOCKED.
- R-GOV-04 D-018 ceremony unexecuted; PKG-07 live drill
  unexecuted — Medium — procedures prepared; owner+witness.
  BLOCKED.
- R-GOV-05 dashboard states (Render/Netlify/branch protection)
  owner-reported, not independently verified — Medium. BLOCKED.

## Platform limitations ($0)

- R-PLAT-01 free-tier ephemeral storage (reseed on restart) —
  documented in runbook; accepted shape for launch. ACCEPTED
  pending owner acknowledgement.
- R-PLAT-02 render.yaml starter/disk conflict — must strip
  before any apply. OPEN (owner decision).
- R-PLAT-03 single-worker JSON store (no multi-writer) —
  documented constraint; PG migration criteria defined.
  ACCEPTED pending owner acknowledgement.

## Deferred capabilities (NOT defects)

- ML_ANOMALY, structuring, insider-abuse, decline-driven
  detection, social/enterprise IdP integrations: NOT_IMPLEMENTED
  by scope; routed to Stage 2. No pseudo-coverage claimed.
