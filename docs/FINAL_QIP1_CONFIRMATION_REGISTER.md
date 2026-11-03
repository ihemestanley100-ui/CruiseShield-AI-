# Q-IP-1 OWNER CONFIRMATION REGISTER — Logo / IP Rights

Date opened: 2026-11-03 · CORRECTED 2026-11-03 with owner
decisions (verbatim, no invention). The prior "UNANSWERED" status
was a recording error — the owner had already supplied these
decisions. Canonical record:
`docs/Q-IP-1_OWNER_CONFIRMATION_REGISTER.md` (QIP-01…QIP-06);
this file carries the Q1–Q4 working mapping plus forensics.
G-PUSH stays CLOSED until its explicit approval.

## Verified facts (evidence, not decisions)

- Tracked logo: `frontend/public/assets/cruiseshield-logo-original.png`
  (in git at HEAD 753a6c5; ships in product + public repo on push).
- Working-tree file: 1273370 B, SHA-256
  `1A0CC66B6385C38029F326C7B84908DC93B208C3B6191BBAF51EBEC86C32A623`
  — matches the hash recorded in `PHASE_2B_REMAINING_GAPS.md`.
- Code references (single-extension file only):
  `frontend/components/app-shell.tsx:60`,
  `frontend/components/landing/LandingChrome.tsx:11`
  (`OFFICIAL_LOGO_SRC`), plus test assertions. ZERO code
  references to any `.png.png` path.
- Standing assertion (unverified): developer asserts the logo is
  their original brand art (`HACKATHON_ASSET_AND_CODE_PROVENANCE.md`).
- Missing historical file: `frontend/public/assets/
  cruiseshield-logo-original.png.png` does NOT exist in the
  working tree. History: excluded from the J1 commit per D1
  (canonical single-extension file committed instead); proven
  byte-identical + zero-referenced 11-01; ordered KEPT pending
  owner deletion approval — yet now absent. The deletion did NOT
  occur in any Muse session on record. No restore/replace/delete
  performed here, per owner instruction.
- Documents mentioning `.png.png` (16): list in §D below.
- Companion flags (same confirmation round): Q-IP-2 (marks:
  "CruiseShield AI™", "Muse Spark" as integration facts),
  psycopg LGPL-3.0-only dependency (organizer IP confirmation).

## Decisions (OWNER-SUPPLIED — recorded verbatim 2026-11-03)

| # | Decision | Owner answer | Status |
|---|---|---|---|
| Q1 | Logo ownership | SELF — owner created/owns the CruiseShield AI logo (= QIP-01) | OWNER_CONFIRMED |
| Q2 | Submission, public repository and deployment rights | YES — authorized, subject to applicable third-party licenses and competition terms (= QIP-02 + QIP-03 + QIP-04) | OWNER_CONFIRMED |
| Q3 | Organizer/press reuse | REVIEW — NOT granted; silence is not consent (= QIP-05). Relevant official competition terms must be identified for owner review; no such terms exist in-repo — owner must supply them | PENDING_OWNER_REVIEW |
| Q4 | Historical logo reference | RETIRE the obsolete `.png.png` reference (= QIP-06). Do NOT restore the missing asset; do NOT delete or modify the current approved logo `frontend/public/assets/cruiseshield-logo-original.png`. Documentation reconciliation pending separate approval | OWNER_DECISION_CONFIRMED |

## Effect on gates

- G-COMMIT: unaffected (logo file itself is already tracked at
  HEAD; the commit adds no new logo bytes).
- G-PUSH logo-rights precondition: SATISFIED (Q1 SELF + Q2 YES).
  G-PUSH itself stays CLOSED until its explicit approval.
- Q3 (REVIEW): does not block G-PUSH; MUST resolve (terms
  supplied + reviewed) before submission (G-RELEASE). No reuse
  claims until then.
- Q4 (RETIRE): docs-only erratum; must complete before G-RELEASE
  under a separate documentation-change approval.

## D. `.png.png` mentions by document (16 files)

1. `docs/CRUISESHIELD_AI_PHASE_9_TO_15_MASTER_COMPLETION_REPORT.md:86`
2. `docs/HACKATHON_ASSET_AND_CODE_PROVENANCE.md:64,67`
3. `docs/HACKATHON_FINAL_SUBMISSION_READINESS_REPORT.md:60`
4. `docs/J1_COMMIT_VERIFICATION_REPORT.md:25`
5. `docs/J1_GIT_COMMIT_FILE_MANIFEST.md:45,73,220`
6. `docs/J3_165_ITEM_AUDIT_RECONCILIATION_MATRIX.md:198,215`
7. `docs/MASTER_CLOSEOUT_RELEASE_DECISION.md:27,59`
8. `docs/PHASE_12_FINAL_DEFECT_REGISTER.md:29`
9. `docs/PHASE_13_ASSET_AND_CODE_PROVENANCE.md:14`
10. `docs/PHASE_2B_REMAINING_GAPS.md:44`
11. `docs/PHASE_9_INTEGRATED_SYSTEM_ACCEPTANCE_REPORT.md:29`
12. `docs/SUBMIT_E_IP_LICENCE.md:10`
13. `docs/SUBMIT_FINALISATION_A_TO_J.md:26,66`
14. `docs/SUBMIT_G_BACKUP_READINESS.md:15`
15. `docs/FINAL_OWNER_APPROVAL_PACK.md:238` (this programme's flag)
16. This register (record of absence)
