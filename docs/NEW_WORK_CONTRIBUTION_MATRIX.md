# NEW WORK CONTRIBUTION MATRIX — CruiseShield AI™

Window: Oct 26 – Nov 4, 2026. Evidence hierarchy: git commits
(authoritative) > session logs > file mtimes (supplementary only).
All 5 commits fall in-window; sole pre-window artifact is noted.

Commits: 7b39f60 (10-28 baseline, 7 files) · f75c3fb (10-28 P0
slice, 44 files) · 0eaaaf5 (10-28 blueprint fix) · d4e2bec
(11-01 worktree, 312 files) · 753a6c5 (11-02 UGLS-03, 789 files)
· uncommitted 110 entries (10-28…11-03 sessions).

| ID | Feature | Original state | Hackathon contribution | Evidence | Commit/diff | Date evidence | Demo? | Status |
|---|---|---|---|---|---|---|---|---|
| NW-01 | FastAPI backend (risk engine, rules, graph, cases, replay, sim, events, store) | None (greenfield) | 16-module backend + 40 routes, all implemented in-window | f75c3fb file list (`app/*.py`) | f75c3fb 10-28 | commit date + tests | YES | VERIFIED |
| NW-02 | Meta Muse Spark integration (`ai_adapter.py`) | None | Server-side chat-completions client, structured output, temp-0, retries, timeout, fail-closed validation | f75c3fb + `test_ai_validation.py`; live_run.json 11-01 | f75c3fb 10-28; run 11-01 | commit + run artifact | YES | VERIFIED |
| NW-03 | Next.js frontend (all routes, components, 3D scenes) | None | 135-file app: landing, demo, investigations, network, cases, replay + explorers | d4e2bec `frontend/` 135 files | d4e2bec 11-01 | commit date | YES | VERIFIED |
| NW-04 | 12-locale i18n (UGLS) + RTL + review kit | None | 12 locales, RTL, coverage/format/review-kit systems + 500+ evidence captures | 753a6c5 + uncommitted `frontend/lib/i18n/**` | 753a6c5 11-02 + worktree | commit + session logs | YES | VERIFIED |
| NW-05 | AuthN/Z + RBAC + sessions | None | HMAC sessions, PBKDF2, 4 roles, revocation/epochs, CSRF, login throttle, 32-char rule (R-09) | d4e2bec `app/auth.py` + R-09 diffs + 35 auth tests + e2e | d4e2bec 11-01; R-09 11-03 | commit + test runs | YES | VERIFIED |
| NW-06 | Security hardening (rate limit, HSTS, CSP, headers, validation, gates) | None | 600/min/IP bounded throttle, HSTS, CSP, body/field caps, secret scans, CI gate | d4e2bec + R-09 F1–F4 diffs; gate 6/6 | 11-01…11-03 | commits + gate logs | Support | VERIFIED |
| NW-07 | Test suites (750+ tests) | None | 403 backend + 354 frontend tests, browser smoke, Edge captures, a11y/RTL audits | `tests/`, `frontend/**/*.test.*`, evidence dirs | f75c3fb→753a6c5 + worktree | commits + logs | Support | VERIFIED |
| NW-08 | Deploy config (Docker, Render, CI) | None | Dockerfile (non-root, pinned), render.yaml, 5 CI workflows | f75c3fb + d4e2bec `.github/` | 10-28, 11-01 | commit dates | Support | VERIFIED |
| NW-09 | Demo script/storyboard/video plan | None | Truthful 150 s + 180 s plans, checklists (this programme) | docs/FINAL_*_STORYBOARD/PLAN | uncommitted 11-03 | session log | YES | VERIFIED |
| PW-01 | v5.0 blueprint spec TEXT | Authored 10-08 (pre-window) | NONE — prior work, disclosed | file mtime 10-08; `HACKATHON_CONTRIBUTIONS.md` §Pre-existing | committed 10-28 (import, not authorship) | mtime + doc | NO | INELIGIBLE (correctly excluded) |
| TP-01 | Third-party libs (FastAPI, Next.js, React, psycopg…) | External OSS | NONE — declared dependencies | requirements.txt, package-lock.json | n/a | manifests | NO | INELIGIBLE (declared) |
| AS-01 | Owner logo asset | Owner property | Integration 10-31 only (rendering, not creation) | Q1 SELF; file mtime 10-31 | worktree | mtime + Q-IP-1 | Incidental | PARTIAL (show, don't claim) |

Rule: demo shows NW-01…NW-09 only. PW-01/TP-01/AS-01 appear
solely as labelled context (spec inspiration, stack credits,
brand), never as built work.
