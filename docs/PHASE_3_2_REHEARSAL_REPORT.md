# PHASE 3.2 — END-TO-END LIVE DEMONSTRATION REHEARSAL

**Date:** 2026-10-31 · **Mode:** read-only (GETs + real navigation clicks only;
no form submissions, no POSTs, no state changes).
**Method:** production servers + real headless Chrome (CDP); screenshots per
stage in `%TEMP%\smoke3b\shot_*.png`; API cross-checks; hash before/after.

## Stage results

- S1 DETECT — PASS. `/demo`: KPIs 1/11/1/39/agentrun_0002/0, journey pills,
  System Status healthy, synthetic badge. 0 console errors.
- S2 CONNECT — PASS. Real click landed `/network/txn_84721`; orbital canvas
  renders 22/30; filters + zoom controls. 0 errors.
- S3 INVESTIGATE — PASS. Real click landed `/investigations/inv_84721`;
  R-001… rules with evidence IDs render. 0 errors. Note F-01 below.
- S4 EXPLAIN — PASS. `/cases/case_84721`: AI panel, requires_review,
  VALIDATED×2, confidence-labelled findings. 0 errors.
- S5 VERIFY — PASS. Evidence package: 39 items, package hash present,
  `synthetic_flag: true`; all 8 risk evidence IDs matched in package.
- S6 SIMULATE — PASS. `/replay/scn_primary`: reset/replay/what-if render
  with 84/100 baseline. Simulation POST intentionally not executed.
- S7 HUMAN DECISION — PASS. Decision form renders (decision select,
  TRIAGED move-to, required Reason, Analyst ID, Record button).
  NOT submitted (read-only bound); POST covered by component/API tests.
- S8 AUDIT — PASS. API returns 1 well-formed event (`audit_0002`,
  case.opened, actor, reason, trace). UI table renders actor/action/
  state-change/reason. No dedicated audit route: nav links land on the
  case page (see F-04).

## Transitions — PASS (5/5 real clicks)

demo → network → investigations → cases → replay → cases(audit).
Brand-link suite (7 routes) still green from prior turn; code unchanged.

## Preservation — PASS

`data/state.json` hash identical before/after (`BA1D4DB4…3790FE`);
0 orphan processes/ports after shutdown. Nothing committed/deployed.

## Prioritised findings for UI/UX Phases 4–8

- F-01 (P1) Risk-figure inconsistency: investigation badge shows "67/100
  HIGH network risk" while `/api/v1/risk` reports network 84 HIGH and
  replay cites 84/100 as the immutable baseline. Reconcile or label scopes
  — a judge will spot the contradiction.
- F-02 (P1) Breadcrumb separator mojibake ("â€º" for ›) on all subpages.
  Encoding fix in the shared breadcrumb component.
- F-03 (P2) System Status storage line renders truncated/overlapped
  ("storage_b…Degraded: PASS…"). Layout fix on demo status panel.
- F-04 (P2) No dedicated audit-trail route: "Audit Trail" nav lands on the
  case page top; the trail sits far below. Consider anchor navigation
  (`#audit-trail`) or a dedicated section link.
- F-05 (P3) Case page is long (AI panel → decision form → audit); add
  in-page section navigation to keep the judge flow tight.
- F-06 (P3) Live-AI demo beat still needs `MODEL_API_KEY` + network
  (standing R-10); fallback beat verified.
- F-07 (note) Simulation POST + decision POST untested live by read-only
  design; covered in test env. Execute once in a disposable pre-demo
  rehearsal with reset afterwards (requires approval).
