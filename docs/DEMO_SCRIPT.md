# CruiseShield AI™ — Hackathon Demo Script (synthetic, reproducible)

All data is synthetic demo fixture. Amounts, entities, and AI outputs below
are the seeded scenario values, not real customer activity.

## Setup (local)

1. Backend: `.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
2. Frontend: `cd frontend && npm run dev` → http://localhost:3000
3. Health: Command Center status card must show all checks PASS.

## 9-step run (~6 minutes)

1. **DETECT** — Open `/investigations/inv_84721`. State: txn_84721,
   ₦480,000, acct_A → acct_B. Transaction-only 35 MODERATE, network
   84 HIGH (`risk-score-v1`), rules R-001–R-008 triggered.
2. **CONNECT** — Open `/network/txn_84721`. 22 nodes / 30 edges,
   0 provenance errors. Point at dev_04 shared by acct_B/C/D.
3. **INVESTIGATE** — Evidence list: 39 items, each with event/edge/
   rule provenance. Open one `evidence_edge_*` row.
4. **EXPLAIN** — Run AI analysis. Expect SUCCEEDED, muse-spark-1.3,
   ~13–17 s, schema VALIDATED, refs VALIDATED. Read one finding +
   its evidence IDs + caveat. Ask one follow-up
   ("Why is dev_04 shared across accounts?").
5. **Uncertainty** — Read `missing_information` + disclaimer aloud:
   indicators, not proof of wrongdoing.
6. **SIMULATE** — `/replay/scn_primary`: ignore edge_0002, edge_0004,
   edge_0005, edge_0011, edge_0012 → baseline 84 HIGH vs simulated
   72 HIGH, labelled SIMULATED with limitations.
7. **HUMAN DECISION** — `/cases/case_84721`: submit a compatible
   decision with a real reason (single submit). Show the new audit row.
8. **AUDIT** — Audit trail: decision + prior events in append-only
   order with actor/state-change/reason.
9. **Close** — Restate: deterministic engine authoritative, AI
   advisory-only, human approves, everything audited.

## Measured reference numbers (local runs 2026-10-28/29)

- Backend suite: 49 passed, 8 skipped (transport-gated). Frontend:
  73/73 + typecheck + build green (user runs).
- AI latency observed: 15065 / 16029 / 12941 / 16733 ms.
- Replay: 11 events / 11 txns / 30 edges at cursor 11.

## Recovery plan

- AI timeout/outage: the panel shows the honest error + Retry; continue
  with deterministic evidence (never claim the analysis ran). The one
  observed outage ("connection could not be opened", 4 attempts) was
  provider-side; integration was intact.
- Backend down: every route shows an error card + Retry; restart
  Uvicorn, no data loss (JSON store reloads).
- Wrong case state: do NOT reset mid-demo without announcing it —
  reset wipes decisions/sims/AI runs/audits (two-step confirm).
- Port clash: free :3000 (dev) / :8000 (backend); CORS only allows
  the :3000 origins.

## Smoke checklist (clean browser)

Health PASS → investigation renders → graph 22/30 → evidence 39 →
AI SUCCEEDED+VALIDATED → follow-up answered → simulation 84→72 →
decision recorded once + audit row → reset (only after demo) restores.
