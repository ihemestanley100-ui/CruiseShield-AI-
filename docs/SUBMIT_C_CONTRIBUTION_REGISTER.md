# C. PRE-EXISTING vs HACKATHON CONTRIBUTION REGISTER (final)

DATE: 2026-11-01 | T1 = git commits · T2 = in-repo records · T3 = filesystem mtimes (mutable, marked).
No timestamps invented; no old work attributed to the event.

## A. Created BEFORE Oct 26, 2026 (pre-existing — DISCLOSE, do not claim)
| Item | Evidence | Standing |
|---|---|---|
| V5.0 master blueprint text (105301 B) | T3 mtime 10-08; T2 "only content" record | Pre-existing SPECIFICATION (input, not code) |
| Any code/routes/features/tests/data/landing/logo | None found; T1+T2 say greenfield | NOT pre-existing per evidence |
| External IP named in V5.0 (Frontier/CruiseTech) | Not present in repo | Referenced only; claim no ownership |

## B. Hackathon period Oct 26–Nov 4 (claimable with evidence)
- C-01…C-02 (10-28, T1 `f75c3fb`): P0 backend slice, risk engine, AI endpoint + prompt v2.
- C-03…C-12 (10-28→10-31, T3): follow-up + injection hardening, Next.js app (138 files), DI-03…09 intel, PG scratch adapter, backup subsystem, security gate + lock, hardening tests, demo/audit docs, 6 live AI runs, deploy config.
- C-13…C-14 (11-01, T3): rehearsal remediation (audit route, section nav, fixes) + VQA 44/44 + agentrun_0003 + 3-min script.
- C-15 (11-01, T3): Product UI/UX Phases 4–8 (see completion report).
- C-16 (11-01, T3): Phases 9–12 (SEC-001/002/005, PERF-001, perf/security/acceptance evidence).
- C-17 (11-01, T3): closeout — WebGL fallback live proof + L2 browser-write proof + Firefox renders + D-013 CSS fix + guard test (`frontend/styles/landing.css`, `GlobalHeroScene.test.tsx`), gate PASS, licence scan.
- Full per-file detail: `HACKATHON_NEW_WORK_CONTRIBUTION_REGISTER.md` (C-01…C-14) + `PHASE_13_NEW_WORK_CONTRIBUTION_REGISTER.md` (C-15…C-16) + closeout decision (C-17).
- Tests/demos: backend 294/68/0 · frontend 234/234 · build exit 0 · matrix 69/69 ×3 · 7 live AI runs SUCCEEDED.

## C. Meta AI / Muse Model API integration (in-window)
Adapter + prompts + validators (C-02/C-03, code) and 7 live executions 10-29→11-01 (C-11/C-14). Detail: deliverable D.

## D. Built using Muse Code (AI-assisted coding — explicitly welcomed, S1)
Per S1 the event invites building with the Muse Code coding agent; AI assistance is provenance-neutral. Human developer owns all decisions, reviews, approvals, and submissions.

## E. Third-party tools/libraries/services
Next.js/React/Three.js/MIT-Apache frontend; FastAPI/Pydantic/etc. backend (licence scan: only psycopg LGPL-3.0-only flag, declared dep, scratch-path, image never built); Meta Model API (service, key server-side); Edge/Firefox/Chromium test browsers. No third-party CODE copied into the repo.

## Eligibility uncertainties (organiser clarification)
Q-REUSE-1 (spec-as-prior-work?) · Q-NEW-1 (uncommitted-but-timestamped OK? commit-hardening is owner-d decided, unmade). No other provenance conflicts found.
