# FRONTEND–BACKEND FEATURE MAPPING — CruiseShield AI™

Date: 2026-11-03 · Every wired frontend feature traced to its
data source. CONN legend: LIVE (fetches real API) · STATIC
(honest design state, no fetch needed) · N/A (infra).

| Frontend | Backend API / source | CONN |
|---|---|---|
| Landing hero/panels/strip/metrics | STATIC (copy + route links; motion prefs local) | STATIC |
| Demo dashboard (9 command comps) | `/api/v1/health|alerts|graph|investigations/{id}|cases/{id}|replay/{id}` | LIVE |
| Investigation studio | `/api/v1/investigations/{id}`, evidence, AI analyze/followup, risk-intel, device/ip/geo | LIVE |
| Network explorer | `/api/v1/graph?txn_id=` (+ table/orbital views of same payload) | LIVE |
| Case workspace + audit | `/api/v1/cases/{id}`, decisions POST, case-audit (server-ordered) | LIVE |
| Replay + simulation | `/api/v1/replay/{id}`, `/api/v1/simulations` POST | LIVE |
| AI brief panel | `/api/v1/ai/*` (analyze/followup/runs) + FAILED-run honest states | LIVE |
| LoginCard/session | `/api/v1/auth/*` (login/logout/logout-all/me/mode) + CSRF + cookies | LIVE |
| SystemStatus | `/api/v1/health` checks (+ humanized labels) | LIVE |
| Notifications | Session + audit-derived client state | LIVE |
| i18n/RTL/theme/a11y/shell | Local (dictionaries, prefs, CSS) | STATIC |
| Loading/error/404 | Local UX states | STATIC |
| Legacy templates (`/`, investigation, health pages) | Same JSON APIs via `static/*.js` fetch | LIVE |
| Timeline/Modal/Tabs/Toast | NONE (unwired; tree-shaken) | N/A |

No wired component lacks a backend or honest STATIC source. No
fetch targets a non-existent route (client paths cross-checked
against the 40-route inventory + openapi).
