# Q-IP-1 OWNER CONFIRMATION REGISTER

REGISTER ID: Q-IP-1 · PROJECT: CruiseShield AI™
PURPOSE: Resolve intellectual-property and branding approval
requirements before public release.
Recorded: 2026-11-03 · Source: owner decisions supplied verbatim
(no interpretation, no invented answers).

## 1. OWNER DECISIONS (verbatim record)

### QIP-01 — LOGO OWNERSHIP
- Owner decision: SELF.
- The project owner confirms that they created/own the
  CruiseShield AI logo.
- Status: OWNER_CONFIRMED.
- Evidence: tracked asset
  `frontend/public/assets/cruiseshield-logo-original.png`
  (1273370 B, SHA-256
  `1A0CC66B6385C38029F326C7B84908DC93B208C3B6191BBAF51EBEC86C32A623`,
  verified 2026-11-03; matches hash recorded in
  `docs/PHASE_2B_REMAINING_GAPS.md`).

### QIP-02 — HACKATHON SUBMISSION RIGHTS
- Owner decision: YES.
- The project owner confirms authorization to submit the
  CruiseShield AI project to the hackathon, subject to
  applicable competition rules.
- Status: OWNER_CONFIRMED.

### QIP-03 — PUBLIC REPOSITORY RIGHTS
- Owner decision: YES.
- The project owner confirms authorization to publish the
  project repository, subject to existing third-party licenses,
  privacy requirements and secret-exclusion controls.
- Status: OWNER_CONFIRMED.
- Evidence: secret-clean tree + history (security gate
  `secret_scan` PASS 2026-11-03; 11-01 history audit CLEAN);
  6-entry exclusion list + ignored secrets in
  `docs/FINAL_OWNER_APPROVAL_PACK.md` §1e.

### QIP-04 — DEPLOYMENT RIGHTS
- Owner decision: YES.
- The project owner confirms authorization to deploy the
  project, subject to applicable third-party licenses, service
  terms and security controls.
- Status: OWNER_CONFIRMED.

### QIP-05 — ORGANIZER AND PRESS REUSE
- Owner decision: REVIEW.
- The project owner has NOT yet granted additional
  organizer/press reuse permission. Silence is not consent.
- Status: PENDING_OWNER_REVIEW.
- Required action: inspect the applicable official hackathon
  terms for provisions governing project names, logos,
  screenshots, recordings, promotional material and press use.
- BLOCKER: no official rules text exists in this repository
  (`docs/HACKATHON_OFFICIAL_RULES_COMPLIANCE.md:3-9`, still
  true 2026-11-03); event/waiver pages are JS-gated and the
  submission portal is auth-gated (fetch attempts 11-03
  returned no terms). The inspection CANNOT be performed until
  the owner supplies the official terms (portal text or file).
- SECONDARY REPORT (single blog source, NOT verified): "you
  keep ownership; grant organisers a perpetual, worldwide,
  royalty-free, non-exclusive licence to use, modify and
  publish, including marketing." Treat as UNCONFIRMED until the
  owner confirms it against the actual waiver.
- Consequence: do NOT claim organizer/press reuse rights have
  been granted; do NOT claim hackathon IP terms fully cleared.
  QIP-05 does not block G-PUSH (publishing grants no reuse to
  organizers by itself) but MUST resolve before submission
  (G-RELEASE).

### QIP-06 — HISTORICAL LOGO ASSET
- Owner decision: RETIRE.
- The obsolete historical `.png.png` logo reference is to be
  retired. Do NOT restore the missing asset. Do NOT delete or
  overwrite other logo files.
- Status: OWNER_DECISION_CONFIRMED;
  DOCUMENTATION_RECONCILIATION_PENDING.
- Scope of THIS authorization: record the decision in the four
  outputs named below. A broader erratum pass over the 16
  documents mentioning `.png.png` is NOT authorized here and
  remains pending a separate documentation-change approval.
- Current approved asset (preserved, untouched):
  `frontend/public/assets/cruiseshield-logo-original.png`.

## 2. RELEASE CONDITIONS (recorded)

- QIP-01 through QIP-04: owner decisions recorded (all confirmed).
- QIP-05: PENDING until the owner reviews the actual competition
  terms (terms must be supplied; none in repo).
- QIP-06: retire reference; preserve current approved logo asset.
- No claim of granted organizer/press reuse rights.
- No claim of fully cleared hackathon IP terms.

## 3. GATE EFFECTS (recorded — gates NOT executed)

- G-PUSH logo-rights precondition: SATISFIED by QIP-01…QIP-04.
  G-PUSH itself stays CLOSED until its explicit approval.
- G-RELEASE/submission additionally requires QIP-05 resolved
  (terms supplied + reviewed) and the QIP-06 doc reconciliation
  (separate approval).
- This register authorizes NO staging, commit, push,
  provisioning, deployment, quota spend, release, or submission.
  All gates remain CLOSED.

## 4. File references

- Prior working register (forensics + 16-doc mention list):
  `docs/FINAL_QIP1_CONFIRMATION_REGISTER.md` (retained as
  evidence; decisions live HERE).
- Approval pack §7, gate register, zero-gap matrix J11: updated
  alongside this register 2026-11-03.
- Provenance: `docs/HACKATHON_ASSET_AND_CODE_PROVENANCE.md`,
  `docs/HACKATHON_SUBMISSION_ELIGIBILITY_REPORT.md` (Q-IP-1
  definition), `docs/SUBMIT_E_IP_LICENCE.md`.
