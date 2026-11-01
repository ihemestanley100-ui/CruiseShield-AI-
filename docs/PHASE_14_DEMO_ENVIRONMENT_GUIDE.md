# PHASE 14 — DEMO ENVIRONMENT GUIDE (judge/owner operation)

PROGRAMME: CSAI-MASTER-RELEASE-001 | Verified localhost procedure (Windows). No deployment needed.

## Requirements
- Python 3.13 + project `.venv` (deps installed per `requirements.txt`); Node 20 + `frontend/node_modules`; Edge/Chrome (Chromium).
- Ports free: 8000 (backend), 3000 (frontend). Loopback only — do not expose to a network (no authN/authZ, no rate limiting by design).

## Startup (measured 2026-11-01)
1. Backend: from repo root, `.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` → ready ~2.5 s; check `GET http://127.0.0.1:8000/api/v1/health` = 200.
2. Frontend (production): from `frontend/`, `npm start -- --port 3000` (build first with `npm run build`, ~50 s) → check `http://127.0.0.1:3000/` = 200.
3. Frontend calls the backend at `http://127.0.0.1:8000` by default (`NEXT_PUBLIC_API_BASE_URL` override available).

## Environment variables (names only — never print values)
- Backend: `MODEL_API_KEY` (live AI only), `META_MODEL_ID`, `META_BASE_URL`, `FRONTEND_ORIGINS`, `DATA_DIR` (override for disposable demo copies), `STORE_BACKEND` (leave `json`), `DATABASE_URL` (unused in demo).
- Without `MODEL_API_KEY`+network the app runs fully EXCEPT fresh AI analyses, which show honest error states; the retained `agentrun_0003` record demonstrates a live run.

## Demonstration dataset (synthetic — say so on the record)
- inv_84721 / case_84721 / txn_84721; ₦480,000 MOBILE_APP 2026-10-27T10:00:00Z; txn risk 35/MODERATE, network risk 84/HIGH; rules R-001…R-008; 39 evidence records; graph 22 nodes/30 edges; scenario scn_primary.
- Integrity check: `Get-FileHash data\state.json` = BA1D4DB4…3790FE, 101417 B, case NEW. If it differs, the demo DB was written to — restore from an owner-approved backup, never by hand-editing.

## Judge walkthrough (route order)
`/` → `/demo` → `/investigations/inv_84721` → `/cases/case_84721` → `/network/txn_84721` → `/replay/scn_primary` → `/cases/case_84721/audit`. All verified 200 with medians 7–38 ms server-side, ~1 s in-browser.

## Known limitations (speak them, don't hide them)
Single-user localhost demo; no login; no throttling; screen-reader pass outstanding; video/backup pending owner actions. Full list: `docs/KNOWN_LIMITATIONS.md`.

## Recovery
- Backend hung: stop its process tree, restart (state reloads from disk; restart verified hash-identical).
- Port busy: another instance is running — verify ownership before stopping anything.
- AI fails: show the retained run + error state; do NOT improvise a fake analysis.
