# PROBLEM / SOLUTION MATRIX

| # | Problem (observed in fraud ops) | CruiseShield answer | Evidence | Status |
|---|----------------------------------|---------------------|----------|--------|
| P1 | Isolated txn scoring misses network crime | Dual scores: txn-only + network risk, labelled by scope | 35 vs 84 demo; risk engine tests | PASS |
| P2 | Investigators drown in context-free alerts | 39-record evidence package per case with provenance | evidence tests; /cases/case_84721 | PASS |
| P3 | Hidden mule/layering relationships | 22-node/30-edge graph with explainable edges | graph tests; /network/txn_84721 | PASS |
| P4 | Black-box AI verdicts | Deterministic engine authoritative; AI explains only | AI boundary tests | PASS |
| P5 | AI hallucinations in case files | Evidence-grounded prompts; ID validation; uncertainty sections | AI validation tests | PASS |
| P6 | No accountability for decisions | Human-decision form + append-only audit trail | audit tests; decision flow | PASS |
| P7 | Fear of acting on first sight | Scenario replay/simulation before deciding | replay tests; /replay/scn_primary | PASS |
| P8 | Real-customer risk during evaluation | Synthetic-data-only demo; disclosures throughout | state.json; labels | PASS |
| P9 | Production deployment | NOT SOLVED — prototype; see adoption path | Phase 15 gap register | BLOCKED |
| P10 | Measured operational uplift | NOT MEASURED — no pilot run | — | NOT_VERIFIED |
