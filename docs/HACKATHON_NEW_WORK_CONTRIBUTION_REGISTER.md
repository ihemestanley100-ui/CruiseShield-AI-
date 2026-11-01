# HACKATHON NEW-WORK CONTRIBUTION REGISTER (2026-10-26 onward)

READ-ONLY audit evidence. Timestamp basis: T1 git commits where committed,
T3 filesystem mtimes where uncommitted (all post-Oct-28 work is uncommitted;
HEAD == origin/master). No timestamps were invented; mtime-only items are
marked as such. "Eligible" below means "evidence supports creation in the
hackathon window" — NOT an organizer eligibility ruling.

## C-01 · P0 backend vertical slice — 2026-10-28 (T1 committed `f75c3fb`)

- Files: `app/` (config, models, seed, store, events, graph, rules,
  evidence, cases, replay, simulate, ai_adapter, main), `templates/` (4),
  `static/` (3), `tests/` (9 files), root config/docs.
- Before: nothing (T2 greenfield record). New: entire API + pages +
  deterministic risk engine + seed scenario + audit chain.
- Meta AI use: adapter + prompt v2 + validators shipped; live call BLOCKED
  (no key) — integration code new, live use pending.
- Tests: 48 passed / 8 skipped / 0 failed (`docs/TEST_EVIDENCE.md`, 10-28).
- Eligible: YES (T1).

## C-02 · AI analysis endpoint + prompt v2 — 2026-10-28 (T1 committed)

- Files: `app/ai_adapter.py` (310 lines at HEAD), `app/main.py`
  `/ai-analysis` + run retrieval.
- Before: nothing. New: server-side Meta call path, structured-output
  handling, schema + evidence-ID validation, provenance persistence.
- Meta AI use: direct (the integration itself).
- Tests: `tests/test_ai_validation.py` at HEAD.
- Eligible: YES (T1).

## C-03 · Follow-up endpoint + prompt-injection hardening — 10-29→10-30 (T3)

- Files: `app/main.py` (+298 lines vs HEAD), `app/ai_adapter.py`
  (+153 vs HEAD: follow-up builder, untrusted-text quoting, retry bounds).
- Before (HEAD): no `/ai-followup`, no follow-up prompt, no temperature pin.
  New: follow-up endpoint with continuity + injection delimiters
  (`<<<ANALYST_QUESTION … >>>`); `REQUEST_TEMPERATURE = 0` (10-31).
- Meta AI use: direct (hardens the model path).
- Tests: `test_ai_validation.py` (+305 lines: approval gate, enforcement
  phrases, banned fields, temperature pin, injection cases).
- Eligible: YES (T3 mtime + diff vs T1 HEAD).

## C-04 · Next.js frontend application — 10-28 PM→11-01 (T3, 138 files)

- Files: `frontend/` (app routes, components incl. Three.js landing,
  lib incl. API client, styles, tests, public assets). Oldest file
  10-28 14:07; bulk 10-29→11-01. Entirely uncommitted.
- Before: nothing (server-rendered Jinja pages only at HEAD). New: 8-route
  Next.js app (incl. 11-01 dedicated audit route), orbital graph explorer,
  replay/simulation UI, AI panels, demo shell, section navigation,
  responsive layouts, logo + favicon integration.
- Meta AI use: none directly — calls backend `/ai-analysis`,
  `/ai-followup` only; `MODEL_API_KEY` never in frontend (asserted in
  `frontend/lib/api.ts`, `frontend/README.md`; verified by tree scan
  11-01: zero secret hits).
- Tests: 225/225 vitest (48 files) + `tsc --noEmit` exit 0 + `next
  build` exit 0, all observed 11-01; a11y tests included.
- Eligible: YES (T3).

## C-05 · DI workstream DI-03…DI-09 — 2026-10-31 (T3)

- Files: `app/device_intel.py`, `ip_intel.py`, `geo_intel.py`,
  `app/link`/`graph`/`risk`/`evidence` intel modules, `app/intel_ai.py`
  (context builder + validators, pure functions); `tests/test_di*.py` (7).
- Before: nothing (no intel modules at HEAD). New: device/IP/geo/link/
  graph/risk/evidence intelligence + DI AI-response validation.
- Meta AI use: indirect — `intel_ai` builds grounded context and validates
  responses; performs no network calls itself.
- Tests: DI suites green (backend 289 passed / 0 failed, Phase 2B report).
- Eligible: YES (T3).

## C-06 · PostgreSQL backend + migrations — 2026-10-30 (T3)

- Files: `app/db.py`, `app/models_pg.py`, `migrations/`,
  `tests/test_pg_*.py` (4). JSON remains the active backend.
- Before: JSON-only store at HEAD. New: PG adapter + parity/migration/
  hardening/atomic-decision verification (scratch-DB-gated skips
  reported, not passed).
- Meta AI use: none. Eligible: YES (T3).

## C-07 · Backup / recovery subsystem — 10-30→10-31 (T3)

- Files: `backups/` (9 modules: manifest, crypto, shamir, signing,
  integrity, targets, produce, restore, logutil), `tests/test_p1_*.py`,
  `tests/test_p2_*.py`, `.github/workflows/backup-*.yml` (3),
  `docs/BACKUP_RECOVERY_RUNBOOK.md`.
- Before: nothing. New: manifest-signed encrypted backups with restore
  drills and CI workflows.
- Meta AI use: none. Eligible: YES (T3).

## C-08 · Security gate + dependency lock — 10-30→10-31 (T3)

- Files: `scripts/security_gate.py`, `requirements.lock`,
  `.github/workflows/security-gate.yml`, `docs/SECURITY_GATE_POLICY.md`.
- Before: `requirements.txt` only. New: 6/6 gate (pins, hashes, pip check,
  pip-audit, secret scan) + locked dependencies.
- Meta AI use: none. Eligible: YES (T3).

## C-09 · Hardening + integration tests — 10-29→10-31 (T3)

- Files: `tests/test_cors.py` (10-29), `tests/test_static_escaping.py`
  (10-31), updates to seed/reset, flow, cases/audit, graph/rules suites;
  `app/seed.py`, `app/store.py`, `app/config.py`, `static/app.js` deltas.
- Before: HEAD versions. Materially improved: CORS contract, escaping,
  determinism benchmarks, ambiguous-scenario + restart coverage.
- Meta AI use: none (except C-03 validator tests). Eligible: YES (T3).

## C-10 · Demo, narrative, and verification docs — 10-29→10-31 (T3)

- Files: `docs/DEMO_SCRIPT.md`, `VIDEO_STORYBOARD.md`, `IMPACT_CASE.md`,
  hackathon audit set (readiness, rubric, gaps ×3), Phase 2B set (4),
  security/release/backups docs, `frontend/README.md`.
- Before: 10-28 baseline docs only. New: full demo + audit trail.
- Note: storyboard/script are PLANS; no demo video exists (see
  eligibility report). Screenshots in `%TEMP%\smoke2*` are real renders
  but outside the repo and ephemeral.
- Eligible: YES (T3).

## C-11 · Live Meta AI runs (data evidence) — 10-29→11-01 (T2+T3)

- 10-29: 4 SUCCEEDED runs, latencies 12.9–16.7 s (project record,
  `docs/TEST_EVIDENCE.md` — attributed, raw responses not retained).
- 10-30: 2 SUCCEEDED runs persisted in `data/state.json`
  (`agentrun_0001` initial, `agentrun_0002` follow-up; 23.6 s / 25.3 s,
  token usage + provider request IDs recorded, VALIDATED/VALIDATED).
- 11-01: 1 SUCCEEDED run against a disposable backend copy
  (`agentrun_0003`, 18.8 s, 10,305 tokens, provider request ID,
  VALIDATED/VALIDATED, 46/46 citations grounded; full artifact
  `%TEMP%\smoke34\live_run.json`, deliberately NOT persisted —
  persistent state hash unchanged). See `docs/PHASE_3_4_LIVE_AI.md`.
- Before: no runs (B-001 BLOCKED at HEAD). New: live executions.
- Meta AI use: direct — this IS live model execution.
- Eligible: YES as in-window execution evidence (T2/T3, see Meta AI report
  for bounds).

## C-12 · Deploy config — 10-28 (T1) + 10-31 tweak (T3)

- Files: `render.yaml` + `Dockerfile` (committed, incl. `0eaaaf5` fix);
  later Dockerfile/CORS-origin adjustments uncommitted.
- Image never built by the agent (engine denied); user-reported local
  build PASS 10-30 (attributed); agent-observed `next build` exit 0
  on 10-31 (R-06) and repeatedly 11-01. Never deployed.
- Eligible: YES (T1/T3). Deployment itself: NOT DONE.

## C-13 · Rehearsal remediation: audit route, section nav, display fixes — 11-01 (T3)

- Files: new `frontend/app/cases/[caseId]/audit/` route + tests; new
  `frontend/components/section-nav.tsx` + tests; `system-status.tsx`
  (verdict/detail split for `PASS ...` strings); `globals.css`
  (breadcrumb `\203A` escape, status wrapping, section-nav styles,
  table nowrap); audit-link rewiring in app-shell, command-activity,
  feature-cards, workflow-strip, case page (+ test expectation updates
  for the intended new route); anchor ids in audit-list/decision-form.
- Before: F-01…F-05 rehearsal findings (mojibake separator, mislabelled
  storage row, no audit route, no section nav, unsettled-badge capture).
  New: all five resolved; F-01 proven a count-up frame, not a data
  defect (mapping test pins the semantics).
- Meta AI use: none. Tests: 225/225 vitest + tsc + build (11-01);
  31/31 live CDP retest checks (`docs/PHASE_3_2_REMEDIATION_AND_RETEST.md`).
- Eligible: YES (T3).

## C-14 · Visual QA + live-AI verification + presentation package — 11-01 (T3)

- Files: `docs/PHASE_3_3_VISUAL_QA.md` (44/44 checks, 14 screenshots),
  `docs/PHASE_3_4_LIVE_AI.md` (agentrun_0003), `docs/HACKATHON_FINAL_DEMO_SCRIPT.md`
  (3-minute script + checklist + backup sequence); audit-cell nowrap fix.
- Before: no systematic VQA record; live execution last shown 10-30;
  no 3-minute script (only the 6-minute runbook + storyboard plan).
  New: full VQA evidence, fresh live proof, recording-ready script.
  No video recorded yet (user step).
- Meta AI use: direct for the C-14 live run only.
- Eligible: YES (T3).
