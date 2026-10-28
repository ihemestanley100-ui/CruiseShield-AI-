# Implementation Inventory

Greenfield build — no pre-existing code. Status vocabulary: MISSING,
IN_PROGRESS, WORKING_UNVERIFIED, VERIFIED, BLOCKED, DEFERRED.

## P0 vertical slice

| # | Capability | Status | Source files | Evidence |
|---|---|---|---|---|
| 1 | Baseline + repo + stack ADR | VERIFIED | docs/, .gitignore, requirements.txt | commit 7b39f60 |
| 2 | Deterministic scenario + reset | VERIFIED | app/seed.py, app/store.py | tests/test_seed_reset.py: 4 pass |
| 3 | Event validation/normalization/idempotency | VERIFIED | app/events.py | tests/test_events.py: 5 pass |
| 4 | Entity resolution (seeded demo) | VERIFIED | app/seed.py, app/graph.py | tests/test_graph_rules_risk.py |
| 5 | Graph + provenance | VERIFIED | app/graph.py | tests/test_graph_rules_risk.py + flow |
| 6 | Versioned rules + deterministic risk | VERIFIED | app/rules.py | tests/test_graph_rules_risk.py: 6 pass |
| 7 | Investigation view + Why-risk | VERIFIED | app/main.py, templates/ | tests/test_flow_direct.py renders |
| 8 | Evidence package | VERIFIED | app/evidence.py | tests/test_evidence.py: 1 pass |
| 9 | Server-side Muse Spark call | BLOCKED | app/ai_adapter.py | prompt v2 + structured output shipped; live call unverified |
| 10 | Schema + evidence-ID validation | VERIFIED | app/ai_adapter.py | tests/test_ai_validation.py |
| 11 | AI provenance panel | WORKING_UNVERIFIED | templates/investigation.html | renders; live data pending B-001 |
| 12 | Replay | VERIFIED | app/replay.py | tests/test_flow_direct.py |
| 13 | Bounded what-if simulation | VERIFIED | app/simulate.py | tests/test_flow_direct.py (84→72) |
| 14 | Human decision gate | VERIFIED | app/cases.py | tests + live decision_0001/audit_0006 |
| 15 | Case transition + audit | VERIFIED | app/cases.py, app/store.py | tests + live NEW→TRIAGED chain 0001–0006 |
| 16 | UI states | WORKING_UNVERIFIED | templates/, static/ | pages render; no real browser run yet |
| 17 | Automated tests | VERIFIED | tests/ | 41 pass, 7 env-gated skips |
| 18 | Deployment verification | BLOCKED | render.yaml + Dockerfile + docs/DEPLOYMENT.md | config done; image unbuilt (engine denied); not deployed |
| 19 | README + docs + demo | WORKING_UNVERIFIED | docs/, README.md | docs done; screenshots/video pending |

## Blockers

- B-001: `MODEL_API_KEY` absent → live model call BLOCKED. Adapter, validation,
  provenance UI, and degraded states implemented; awaiting user credential.
- B-002: Sandbox has no network and the Node toolchain is broken → deployment
  from here impossible. Local uvicorn run is the verified target; user-side
  deploy documented in README.
