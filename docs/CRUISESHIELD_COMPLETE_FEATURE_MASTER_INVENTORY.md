# COMPLETE FEATURE MASTER INVENTORY — CruiseShield AI™

Date: 2026-11-03 · Read-only audit · 84 features inventoried.
Statuses: IMPLEMENTED 80 · PARTIAL 4 · DESIGN_ONLY 0 ·
NOT_IMPLEMENTED 0 · NOT_VERIFIED 0 (implementation; live
behavior separately NOT_VERIFIED pending deploy).

Conventions: ORIG = original Command Center location (backend
`templates/*.html` + `static/*.js`); GIC = Global Intelligence
Core location (`frontend/**`); FE = frontend source; BE =
backend/API source; CONN = connected to live data; TEST = test
evidence (all local; live acceptance pending).

## Pages (13) — all IMPLEMENTED

| ID | Name | ORIG | GIC | FE | BE/CONN | TEST |
|---|---|---|---|---|---|---|
| F-P01 | Landing (Global Intelligence Core) | — (new) | `/` | `app/page.tsx` → `landing/GlobalLandingPage.tsx` | Static + links; no fetch needed | LandingContent/GlobalHeroScene/scene tests |
| F-P02 | Demo command dashboard | `command.html` | `/demo` | `app/demo/page.tsx` + 9 command comps | health/alerts/graph/inv/case/replay; live fetch | page test + smoke2j + t55 |
| F-P03 | Investigation studio | `investigation.html` | `/investigations/[id]` | page + EvidenceList/AiPanel/WhyRisk/IntelSection | inv/evidence/AI/risk-intel APIs | page test + captures |
| F-P04 | Network explorer | `graph.js` canvas | `/network/[txnId]` | page + GraphExplorer/OrbitalExplorer/GraphTable | graph API (22n/30e) | page test + RTL capture |
| F-P05 | Case workspace | — (J-phase new) | `/cases/[caseId]` | page + DecisionForm/AuditList/RiskBadge | cases/decisions/audit APIs | page test |
| F-P06 | Case audit trail | — (J-phase new) | `/cases/[caseId]/audit` | page + AuditList/Breadcrumbs | case-audit API (server order) | page test |
| F-P07 | Replay & simulation | — (J-phase new) | `/replay/[scenarioId]` | page + ReplayControls/SimulationPanel | replay/simulations APIs | page test |
| F-P08 | Loading state | n/a | `app/loading.tsx` | Static skeleton, aria-busy | n/a (design state, honest) | loading test |
| F-P09 | Error boundary | n/a | `app/error.tsx` | Retry + digest ref, no stacks | n/a | error test (2) |
| F-P10 | Branded 404 | n/a | `app/not-found.tsx` | Directions + links | n/a | not-found test |
| F-L01 | Legacy Command Center | `GET /` → `command.html` | preserved (backend) | `templates/command.html` + `static/app.js` | Same JSON APIs (fetch) | Live 200 11-03 |
| F-L02 | Legacy investigation page | `GET /investigations/{id}` | preserved (backend) | `templates/investigation.html` | Same JSON APIs | Route in openapi |
| F-L03 | Legacy system-health page | `GET /system-health` | preserved (backend) | `templates/system_health.html` | health API | Route in openapi |

## Components (43) — 39 IMPLEMENTED, 4 PARTIAL (unwired)

Wired + tested + live-data-connected (39): ai-panel,
ambient-background, app-shell, audit-list, breadcrumbs,
command-activity, command-ai-brief, command-kpis,
command-network-preview, command-rule-summary, decision-form
(permission-gated, backend-enforced), evidence-list, exec-kpis,
feature-cards, graph-explorer, graph-table, intel-panels
(IntelSection), language-selector, login-gate (LoginCard),
notifications, orbital-explorer, replay-controls, risk-badge,
section-nav, simulation-panel, skip-link, stat, system-status,
theme-provider, theme-selector, why-risk-panel,
workflow-strip + 7 landing/* (GlobalLandingPage, LandingChrome,
LandingPanels, LandingStrips, LandingControls, GlobalHeroScene
+ scene/{earth,orbital,network,brain,stars,webgl,shared},
WebGLFallback). Each: FE file + colocated test + page importer
verified by import graph (audit notes 11-03).

PARTIAL (implemented + tested, NO production importer —
tree-shaken out; wire-or-remove post-hackathon, DO NOT touch now):

| ID | Component | Evidence | Action |
|---|---|---|---|
| F-C40 | Timeline | `timeline.tsx` + test; importers: test only | Wire to investigation/activity view or remove (post-event) |
| F-C41 | Modal | `modal.tsx` + test; importers: test only | Wire to confirm-dialog flows or remove (post-event) |
| F-C42 | Tabs | `tabs.tsx` + test; importers: test only | Wire to multi-view panels or remove (post-event) |
| F-C43 | ToastRegion | `toast.tsx` + test; importers: test only | Wire to mutation feedback or remove (post-event) |

## Backend API groups (16) — all IMPLEMENTED

Health/ready · auth (login/logout/logout-all/me/mode) ·
demo scenarios/reset · alerts · investigations · evidence
packages/items · graph · risk assessments + rule results ·
device/ip/geo/risk-intel · cases/decisions/case-audit ·
replay · simulations · AI (analyze/followup/runs) · events
ingest · seed reset (guarded) · static legacy pages.
40 routes inventoried 11-03; every group has pytest cover +
at least one live 200 (local or prod-probe).

## Cross-cutting (12) — all IMPLEMENTED

i18n 12-locale + RTL (registry/context/coverage/review-kit) ·
theme system (dark/light/system + persistence) · a11y (skip
links, landmarks, aria, keyboard, focus, reduced-motion) ·
responsive 390/768/1440 + RTL (R-11 closed) · session mgmt
(HMAC cookies, revocation, epochs) · RBAC 4-role · audit trail
(append-only, hash-chained packages) · AI fail-closed
validation · rate limiting + body/field caps · CORS/headers/
HSTS/CSP · honest UX states (loading/error/404/fallbacks) ·
synthetic-data labelling (no fake liveness anywhere).

## Negative findings (verified absent)

- No TODO/FIXME/lorem/coming-soon in `frontend/` (grep 11-03).
- No dead buttons: all `disabled` states are permission- or
  submission-driven with backend enforcement (decision-form:
  `useCan("write")`; ai-panel: running guards).
- No dead links: every landing href resolves to a real route;
  `#ai-h` anchor target exists (investigations §127).
- No missing-link 404s in cited evidence (smoke2j 18/18).
- No live-data misclaims: illustrative/coverage language is
  explicitly labelled; satellite claims deliberately absent.
