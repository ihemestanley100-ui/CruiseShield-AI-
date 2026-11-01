# PHASE 3.2 — FINDINGS REMEDIATION AND REHEARSAL RETEST

Date: 2026-11-01. Scope: remediate rehearsal findings F-01..F-05, then rerun
the real-click walkthrough. The historical `docs/PHASE_3_2_REHEARSAL_REPORT.md`
is preserved unchanged; this document records only the new work.

Method: production servers (uvicorn :8000 + `next start` :3000 on a fresh
verified build) + headless Edge driven over CDP with real mouse input.
Retest script + evidence: `%TEMP%\smoke32f\retest.ps1`,
`%TEMP%\smoke32f\shots\shot_*.png`, `%TEMP%\smoke32f\checks.json`.
READ-ONLY against persistent data: no AI runs, simulations, decisions, or
resets were submitted.

## F-01 — Risk-score reconciliation (P1) — RESOLVED, no data defect

Reported: network page 67 vs API 84 vs replay baseline 84.

Root cause (traced end to end): there is exactly ONE network score.
`GET /api/v1/investigations/inv_84721` returns `risk_network.score = 84`;
the investigation page binds the badge to that field
(`frontend/app/investigations/[id]/page.tsx` → `RiskBadge score={...}`),
and the replay baseline reads the same authoritative assessment
(`GET /api/v1/risk?scope=network` → 84). The badge animates 0 → score over
~1s (`useCountUp`, easeOutCubic, rAF); its `aria-label` always announces
the exact authoritative value. The observed "67" was a mid-animation frame
captured before the count-up settled — not a second metric and not a
mapping defect. Transaction-only 35/100 MODERATE is a separate,
correctly labelled scope shown beside it.

Action taken (no score changed anywhere):
- Added a mapping test that renders the page with a non-84 fixture score
  (72) and asserts badge text, absence of 84, and exact aria-label —
  proving the display is mapped, not hardcoded.
- Demo-script guidance (for 3.5): capture/judge the badge after it
  settles (~1–2 s); the aria-label is authoritative at all times.

Retest evidence: `3.inv.badge-settles-84` PASS (live DOM settles to
"84/100 HIGH"), `3.inv.badge-aria` PASS ("Risk 84 of 100, HIGH"),
`6.sim.baseline-84` PASS ("Authoritative baseline (network): 84/100
HIGH"). Verdict: PASS.

## F-02 — Breadcrumb separator mojibake — FIXED

Root cause: `frontend/app/globals.css` line 1068 contained the literal
bytes `â€º` (U+203A mis-decoded as Windows-1252 and re-saved), plus two
more `â€”` sites in comments (lines 2, 620). No other mojibake found in
`frontend/app`, `components`, `lib`, `public`.

Fix: separator is now the encoding-proof CSS escape `content: "\203A"`;
comments use ASCII `--`. No other file contained the separator (it is
pure CSS; the `Breadcrumbs` component is unchanged).

Retest evidence: `3.inv.breadcrumb-sep` PASS (computed `::before` content
char code U+203A); screenshot `shot_08_audit.png` shows clean `›`
separators. Verdict: PASS.

## F-03 — System Status storage display — FIXED (defect + layout)

Root cause (two layers):
1. Contract mismatch: the backend emits detail-carrying verdicts
   (`storage_backend: "PASS active=json selected=json"`, `app/main.py`),
   while the frontend `describe()` required exact `"PASS"`, so healthy
   storage rendered as "Degraded: PASS active=json selected=json".
2. Long value strings could overflow the third grid column on narrow
   screens.

Fix (`frontend/components/system-status.tsx`, `globals.css` only; no
backend change): verdict word and detail are split; `PASS` + detail →
Operational with the detail shown (`Operational: active=json selected=
json`); `FAIL` + detail keeps the detail visible; status grid uses
`minmax(0, auto)` + `overflow-wrap: anywhere`. Two regression tests added.

Retest evidence: `1.detect.storage-operational` PASS (live text
"storage_backend Operational: active=json selected=json"),
`1.detect.pg-not-configured` PASS, `9.mobile.no-h-overflow` PASS
(0 px at 390 px); screenshots `shot_01_demo.png`, `shot_09_demo_390px.png`.
Verdict: PASS.

## F-04 — Audit navigation — FIXED (new dedicated route)

 finding: no dedicated audit route; audit links landed on the case page top.

Implementation (smallest consistent route; existing architecture reused):
- New `frontend/app/cases/[caseId]/audit/page.tsx`: fetches the existing
  `GET /api/v1/cases/{id}/audit`, reuses `AuditList` (server order kept,
  zero invented entries), same loading/error/not-found/Retry states and
  breadcrumb pattern as the parent case route, plus "Back to case".
- Case page gained an "Open full audit trail" link above the audit list.
- Every audit-labelled destination now targets the route: sidebar "Audit
  Trail", "View Audit Trail" quick action, Command Center "Open case
  audit trail", feature card, workflow-strip "Audit" stage.
- 5 new route tests; 4 existing href expectations updated to the new
  route (the intended behaviour change). Landing "Evidence and Audit"
  cards still target the case page (combined destination; unchanged).

Retest evidence: `8.audit.nav` PASS (real click lands on
`/cases/case_84721/audit`), `8.audit.rows` PASS (1 recorded event,
`audit_0002`, real data), `8.audit.crumb` PASS; `shot_08_audit.png`.
Verdict: PASS.

## F-05 — Investigation section navigation — FIXED

Implementation: new shared `SectionNav` component
(`frontend/components/section-nav.tsx`): plain anchor links (work without
JS), IntersectionObserver active indication (`aria-current` + `.active`),
graceful no-observer fallback. Wired into the investigation page
(Overview / Why this risk? / Evidence / Intelligence / AI analysis) and
the case page (Overview / AI assessment / Decision history / Human
decision / Audit trail); anchor ids added to previously unanchored
headings; sticky-header clearance via `scroll-margin-top`; global
`:focus-visible` covers keyboard focus. 3 component tests + 2 page-level
anchor-resolution tests added.

Retest evidence: `3.inv.section-nav` + `3.inv.section-jump` PASS (5 links,
`#evidence-h` jump verified), `7.case.section-nav` PASS.
Verdict: PASS.

## Retest result — 31/31 checks PASS

Stages 1–8 all PASS: Detect, Connect (22 nodes, 30 edges, 0 provenance
errors), Investigate, Explain (panel + Run button render), Verify (39
evidence records, API↔DOM id echo), Simulate (baseline 84, form renders),
Human Decision (form + section nav + audit link), Audit (dedicated route).
Console errors: 0. Failed requests: 0 (`net::ERR_ABORTED` fetches are
client-cancelled in-flight requests on navigation — app AbortController
cleanup + Next.js RSC prefetch cancels — classified benign with URL
correlation; every aborted URL succeeds on completion).

Write operations (Run AI analysis, Run simulation, Submit decision,
Reset demo): forms verified rendered; submissions NOT executed against
persistent data — NOT VERIFIED at browser level (per directive; backend
POST paths are covered by the backend suite).

## Data integrity

`data/state.json` SHA-256 `BA1D4DB4BB4DBC6FC3ACA346664A539610CCC6460CCD53
0F523C8043453790FE`, 101417 bytes — identical before and after the
retest. No scores, records, evidence, or assets altered.

## Gates

- `tsc --noEmit`: PASS (exit 0).
- Frontend suite: 48 files / 225 tests PASS (exit 0). (One earlier full
  run exited 1 with all tests passing — transient worker teardown flake;
  the repeated full run is clean with no FAIL/Unhandled lines.)
- `npm run build`: PASS (exit 0; new `/cases/[caseId]/audit` route in
  the route table). The `metadataBase` stderr warning is pre-existing.

## Files changed (3.2 remediation)

- `frontend/app/globals.css` (separator escape, status wrapping,
  section-nav styles, scroll margin, comment mojibake)
- `frontend/components/system-status.tsx` + test (verdict/detail split)
- `frontend/components/section-nav.tsx` + test (new)
- `frontend/app/investigations/[id]/page.tsx` + test (section nav, ids,
  score-mapping test)
- `frontend/app/cases/[caseId]/page.tsx` + test (section nav, ids, audit
  link)
- `frontend/app/cases/[caseId]/audit/page.tsx` + test (new route)
- `frontend/components/app-shell.tsx` + test (audit hrefs)
- `frontend/components/command-activity.tsx` + test (audit href)
- `frontend/components/feature-cards.tsx` + test (audit href)
- `frontend/components/workflow-strip.tsx` + test (audit href)
- `frontend/components/audit-list.tsx`, `decision-form.tsx` (anchor ids)
- `frontend/app/demo/page.test.tsx` (href expectations for new route)

## Observations for Phase 3.3 (not 3.2 defects)

- Audit table timestamp wraps mid-string at 1440 px (readable; consider
  `nowrap` on the time column).
- `shot_03_investigation.png` captured post-jump (evidence section);
  badge/breadcrumb were DOM-asserted, but 3.3 should capture the page top.
- Headless Edge renders the light theme (system preference); 3.3 should
  cover dark mode explicitly.
