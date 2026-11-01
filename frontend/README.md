# CruiseShield AI — Next.js frontend (Batch 1 scaffold)

Thin command shell over the existing FastAPI backend. The backend remains
authoritative for risk, evidence, cases, and audit; this app only renders
backend responses. No secrets in this directory: only the public
`NEXT_PUBLIC_API_BASE_URL` (see `.env.example`).

## Prerequisites

- Node.js >= 18.18 and npm with registry network access.
- The FastAPI backend running locally for the dev check:
  `.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`

## Version note

Dependencies pin known-stable lines (Next 15 / React 19 / TS 5) chosen so
this batch builds deterministically. Report `npm view next version` output
with your results; newer stable majors will be adopted deliberately in a
later batch after verifying compatibility.

## Commands (run in `frontend/`)

1. `npm install` — expect: dependency tree resolved, `package-lock.json`
   created, no ERESOLVE errors.
2. `npm run build` — expect: TypeScript compiled, static page generated,
   no type errors. (This also generates `next-env.d.ts`.)
3. `npm run typecheck` — expect: no output (clean).
4. `npm test` — expect: all theme tests pass (logic + provider).
5. `npm run dev`, then open http://localhost:3000 with the backend up —
   expect: branded Command Center with a backend-status card showing the
   live health response (status, version, scenario, checks). With the
   backend down, expect the honest error card + Retry, not a crash.

## Troubleshooting

- Install/peer errors: paste the full npm output; do not force-resolve.
- Page shows `BACKEND_UNREACHABLE`: start the backend (see above) and Retry.
- Never put `MODEL_API_KEY` or any secret in this directory.

## Batch 2 — Investigation detail route

`/investigations/[id]` renders the live investigation: transaction header,
network risk badge, Why-this-risk rules, filterable evidence list, and a
read-only AI analysis panel. All values come from `GET investigations/{id}`,
`GET evidence-package`, and `POST ai-analysis`. Verify with the backend up:
open `/investigations/inv_84721` and compare amount, score, band, rule
count, and evidence count against the same backend endpoints. Graph,
replay, simulation, and decisions land in later batches.

## Batch 3 — Network explorer route

`/network/[txnId]` renders the exact graph from `GET /api/v1/graph/{txn}`:
deterministic 2D SVG (same BFS-layer rule as the backend UI), node/edge
selection with provenance and evidence detail, entity-type and
relationship filters, zoom/pan/fit controls (arrow-key pan on the focused
graph), and a complete relationship table as the accessible alternative.
Filters only hide; nothing invents relationships or changes risk. Verify
with the backend up: open `/network/txn_84721` — expect 22 nodes /
30 edges, selecting `edge_0002` shows provenance `evt_demo_84721`, the
table lists all 30 edges, unknown IDs show not-found, and a stopped
backend shows the error card + Retry.

## Batch 4 — Replay, simulation, cases

`/replay/[scenarioId]` offers scenario reset (two-step confirm; clears
decisions, simulations, AI runs, and audit history beyond the reset
itself), deterministic step/play/restart playback from `GET replay`, and
a what-if panel (`POST simulations`) that always shows the authoritative
`GET risk` baseline beside the labelled-hypothetical result.
`/cases/[caseId]` shows status, allowed transitions, decision history,
a validated decision form, and the audit trail. Verify with the backend
up: step replay 0→11; run a simulation ignoring `edge_0002`,
`edge_0004`, `edge_0005`, `edge_0011`, `edge_0012` (the pinned backend
case — expect baseline 84 HIGH vs simulated 72); record one decision on
`case_84721` and confirm the new audit entry, then reset the demo to
restore the seeded state.

## Batch B — Orbital explorer

`/network/[txnId]` defaults to the orbital view: deterministic rings
(BFS depth from the focus node), elliptical orbit guides, per-type node
shapes, slow pauseable rotation, pin-as-focus, filters, zoom/pan/fit,
label toggle, speed control, and a legend. Rings, angles, sizes, and
motion carry no risk meaning (stated in-UI). The flat Batch 3 explorer
remains one click away via the Orbital/Flat toggle, and the
relationship table is unchanged. No new dependencies. Verify: pause
button freezes motion; pinning `dev_04` re-centers rings on it; reset
restores the default focus; reduced-motion browsers start paused.
