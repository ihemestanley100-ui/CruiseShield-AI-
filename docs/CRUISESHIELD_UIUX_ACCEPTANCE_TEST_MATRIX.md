# UI/UX ACCEPTANCE TEST MATRIX — CruiseShield AI™

Date: 2026-11-03 · Per-feature acceptance: local evidence
cited; LIVE column stays NOT_VERIFIED until Phase 8.

| Feature | Local evidence | Live | Required live test |
|---|---|---|---|
| Landing hero/panels/strip/metrics | Component tests + build prerender | NOT_VERIFIED | `/` 200, core label, 10 cards link correctly |
| Demo dashboard + KPIs | page test + smoke2j + t55 | NOT_VERIFIED | Data renders from prod API; KPIs match |
| Investigations + evidence + AI | page tests + captures | NOT_VERIFIED | Package resolve; brief VALIDATED or honest error |
| Network explorer + table + orbital | page test + RTL shot | NOT_VERIFIED | 22n/30e render; filters work |
| Cases + decisions + audit | page tests + e2e | NOT_VERIFIED | TRIAGED flow; audit order + hashes |
| Replay + simulation | page tests | NOT_VERIFIED | Baseline immutable; what-if diffs |
| Auth/login/logout/RBAC | 35 tests + e2e journey | NOT_VERIFIED | 401→200→me→logout→401 on prod |
| i18n 12-locale + RTL | coverage/format/review-kit tests | NOT_VERIFIED | Locale switch incl. ar RTL live |
| Themes/a11y/responsive | a11y audit + R-11 shots | NOT_VERIFIED | Keyboard, 390/768/1440 live |
| Loading/error/404 | 4 new tests | NOT_VERIFIED | Bad route → branded 404 live |
| Legacy `/` + studio + health pages | Live 200 (legacy root verified) | PARTIAL | Legacy root 200 already observed; others on prod |
| Timeline/Modal/Tabs/Toast | Unit tests only | NOT_APPLICABLE | Unwired — no live behavior to test |

Rule: no row flips to PASS without captured live evidence.
