# F-CSG-002 / F-CSG-003 — Corrected Acceptance Records (CS-GOV-001)

Version: 2 (2026-11-12). Supersedes the `7b83c7a`-era
`CSG-STAGE1-FINAL/SECURITY_RISK_GATE.md` figures (originals
preserved untouched). Candidate: `3cbbb48` + pending 12-file
translation-sync commit (exact frozen SHA to be re-pinned at
signature time). Status: BOTH PENDING — no signatures below.

## F-CSG-002 — npm dev-toolchain audit findings

- Scope: dev-only vitest toolchain chain (2 critical + 1 moderate
  per prior review). No production runtime path (devDependencies,
  test-time only).
- Disposition: accepted risk; post-release major upgrade
  (vitest 3→4) recommended as a separately assessed change.
- Acceptance condition: reviewer + owner approve, or declare the
  upgrade a release blocker.
- Evidence: `CSG-100/CSG_VULNERABILITY_REGISTER.json`,
  `NPM_RISK_REVIEW.md`, hosted gate dependency steps.

## F-CSG-003 — postcss via next (GHSA-qx2v-qp2m-jg93)

- Scope: build-time CSS processor, CVSS 6.1 (scanner-high);
  stylesheets author-controlled; no user-CSS input path exists.
- Disposition: accepted residual risk; post-release Next major
  upgrade (→16.4.6) recommended as a separately assessed change.
- Acceptance condition: reviewer + owner approve, or declare the
  upgrade a release blocker.
- Evidence: same as F-CSG-002 + `npm audit --omit=dev` output.

## Approval authority and signatures (PENDING)

Required: independent reviewer verdict + owner acceptance, both
attributable with dates. No party may sign for the other.

- [ ] F-CSG-002 APPROVED / REJECTED (+ blocker declaration if rejected)
- [ ] F-CSG-003 APPROVED / REJECTED (+ blocker declaration if rejected)
- [ ] Caveats acknowledged: no pentest ever; machine-drafted
      translations pending human review; Render 503 specifics
      unresolved; session login not for production exposure.

Reviewer: ____ Date: ____  Owner: ____ Date: ____
