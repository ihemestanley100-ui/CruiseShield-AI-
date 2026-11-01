# 9. STAGING ACCEPTANCE CHECKLIST

DATE: 2026-11-01 | RUN AFTER DEPLOY (owner-approved staging only). All checks against STAGING URLs; local `data/state.json` must remain BA1D4DB4…3790FE throughout.

## Infrastructure
- [ ] Backend /api/v1/health 200, status healthy, checks all PASS (model NOT_CONFIGURED acceptable only if no key set).
- [ ] Frontend / 200, CSS 200, SEC-010 headers present on both surfaces.
- [ ] All 6 routes 200 with live data (/, /demo, /cases/case_84721, /investigations/inv_84721, /network/txn_84721, /replay/scn_primary).
- [ ] Browser console: 0 errors; network: 0 failed (one walkthrough).

## Workflow (DETECT→AUDIT on staging store)
- [ ] DETECT: txn_84721, ₦480,000, MOBILE_APP shown.
- [ ] CONNECT: graph 22n/30e, 0 provenance errors.
- [ ] INVESTIGATE: 39 evidence records with provenance.
- [ ] EXPLAIN: AI analysis runs (with key) or honest error (without); EITHER is a pass if labelled.
- [ ] VERIFY: evidence IDs cited exist in the package.
- [ ] SIMULATE: sim runs, baseline 84 preserved, result labelled simulated.
- [ ] HUMAN DECISION: submit on staging → decision recorded + case transitions.
- [ ] AUDIT: decision event present with actor/reason; ordering sane.

## Invariants (fail the acceptance if any break)
- [ ] Risk: txn 35/MODERATE + network 84/HIGH everywhere.
- [ ] Evidence IDs stable; audit append-only (no edits/deletes).
- [ ] Local state hash unchanged (re-verify after).
- [ ] No secrets in logs/screenshots/URLs.

## Sign-off
Accepted-by (owner) + date + deployed SHAs + URLs → file in release log → Phase 14-style preservation of the staging release.
