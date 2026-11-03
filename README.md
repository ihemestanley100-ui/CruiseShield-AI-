# CruiseShield AI™ — Hackathon Vertical Slice

The Financial Crime Immune System™: network-level, evidence-linked financial-crime
investigation. *"The transaction is only the beginning. The network is the signal."*

> All data is deterministic synthetic demo fixtures, labelled in the UI. No real
> financial data is used anywhere.

## Hackathon provenance (Meta Global AI Developer Hackathon, Oct 26 – Nov 4, 2026)

Everything in `app/`, `frontend/`, `tests/`, `migrations/`,
`.github/` and the deployment config was built during the
hackathon window (commits `7b39f60`…`753a6c5`, all dated Oct 28 –
Nov 2, 2026). Pre-existing and NOT presented as new: the v5.0
specification text (`CRUISESHIELD_AI_*_V5.0.txt`, authored Oct 8),
third-party open-source libraries, and the owner-supplied logo
asset (integrated, not created). Evidence:
`docs/NEW_WORK_CONTRIBUTION_MATRIX.md`.

## Problem

Transaction-by-transaction monitoring misses suspicious relationships spread across
accounts, devices, phones, merchants, and time. Investigators need a traceable way
to understand why an event was flagged and what the surrounding network shows.

## What this build does

One complete, reproducible investigation path:

`Synthetic Event → Validate → Entity Resolution → Graph → Rules/Risk → Evidence →
Investigation → Replay/Simulation → Human Decision → Case → Audit`

- Signature case: Transaction #84721, ₦480,000, Account A → Account B.
- Reveal Network expands the real seeded graph: 12 accounts, 4 devices, 3 phones,
  2 merchants, 1 beneficiary (22 nodes, 30 edges, every edge provenance-backed).
- Transaction-only risk 35/100 MODERATE → network risk 84/100 HIGH, computed by
  versioned deterministic rules (`risk-score-v1`), never by the model.
- Meta Muse Spark (`muse-spark-1.3`) explains the supplied evidence package
  server-side; output is schema- and evidence-ID-validated.
- Deterministic replay, one bounded what-if simulation, reasoned human decision
  gate, case lifecycle, append-only audit trail.

Live demo URL: none yet — runs locally (see below). Screenshots/video: not captured
in this headless sandbox; capture from the local run before submission.

## Architecture

Single FastAPI process: JSON API + server-rendered pages (Jinja2 + vanilla JS,
dependency-free SVG graph, no CDN/build step). JSON file store with atomic writes.
Primary UI is the Next.js 15 frontend (`frontend/`, 254 vitest suite,
production build verified); the Jinja pages (`/`, `/investigations/*`,
`/system-health`) remain as a legacy surface.
Details: `docs/ARCHITECTURE.md`. Stack decision: `docs/ADR/ADR-001-stack.md`.

Meta integration: OpenAI-compatible `POST {META_BASE_URL}/chat/completions`,
model `META_MODEL_ID` (default `muse-spark-1.3`), server-only `MODEL_API_KEY`.
Verified against public Meta docs 2026-10-28 (see `docs/TEST_EVIDENCE.md`).

## Local setup

Prerequisites: Python 3.13 (a project `.venv` already exists in this checkout).

```powershell
# On a networked machine (first time only):
.venv/Scripts/python -m pip install -r requirements.txt

# Optional: enable live AI analysis (never commit real values):
Copy-Item .env.example .env
# then set MODEL_API_KEY in .env

# Run:
.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in a browser, then press
**Start Signature Investigation**.

## Synthetic scenario

Three versioned scenarios (`app/seed.py`, manifest `seed_hash` pinned in tests):

- `scn_primary` — txn_84721 network (11 txns, 11 events, 30 edges).
- `scn_false_positive` — txn_84730: large but unconnected transfer (LOW/LOW).
- `scn_ambiguous` — borderline device-sharing pair, txn 20 LOW /
  network 38 MODERATE (one device shared by exactly two accounts).

Reset reproducibly: `POST /api/v1/demo/reset {"scenario_id": "scn_primary"}`,
or use the scenario form on the Command Center.

## Tests

```powershell
.venv/Scripts/python -m pytest tests/ -q
```

Result in this sandbox (2026-11-01 J3 closeout): backend **341 passed,
103 skipped** (skips are socket/loop-gated, verified socket-free by
direct-handler twins; 1 node-dependent test is sandbox-blocked here and
re-proven green on an approved unsandboxed rerun); frontend **261/261
vitest + typecheck + production build green** (approved unsandboxed
runs). Skips are never counted as passed.
Evidence: `docs/J3_FULL_REGRESSION_EVIDENCE.md`.

## Demo steps (3 minutes)

1. Command Center → Start Signature Investigation (clean reset).
2. Open txn #84721; press Reveal Network; select an edge; read its provenance.
3. Read Why-this-risk; run AI analysis; check provider/model/validation panel.
4. Step replay; run a what-if ignoring device-sharing edges; compare 84 → 72.
5. Record a reasoned decision; inspect the audit event and case state.

## Limitations and deferred work

See `docs/KNOWN_LIMITATIONS.md` and `docs/IMPLEMENTATION_INVENTORY.md`.
P1/P2 and the full V5 enterprise layers are explicitly deferred, not claimed.

## Security

- `MODEL_API_KEY` lives only in server env/`.env` (gitignored); never in code,
  logs, responses, or screenshots. `tests/test_secret_safety.py` guards this.
- Demo mutations are restricted to seeded records; the UI discloses demo mode.
- Protected-demo login is implemented (HMAC sessions, investigator/admin
  roles, CSRF header, login throttle) but remains demo-grade: shared
  credentials, manual rotation, no tenant isolation. Do not expose it as
  a production service.
