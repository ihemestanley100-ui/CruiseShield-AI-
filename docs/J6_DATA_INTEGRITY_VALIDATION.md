# J6 — DATA INTEGRITY VALIDATION

Post-restore (or post-migration) acceptance checklist. Every item
must pass before the restored copy is trusted.

1. Byte/hash identity: `sha256` of restored bytes equals the
   manifest `dump_sha256` (JSON: `BA1D4DB4…3790FE` / 101417 B).
2. Row counts equal the manifest (11 txns, 22n/30e, 11 events,
   8 rule results, 39 evidence items, 1 inv/case, 5 audits…).
3. IDs stable: txn_84721, case_84721, inv_84721, audit_0001..0005
   in order, run/agent ids unchanged.
4. Risk pins: txn-only 35/MODERATE, network 84/HIGH, bands + 8/8
   rules reproduced (`test_risk_determinism`, `test_graph_rules`).
5. Evidence provenance: every item resolves to real records
   (`test_evidence`); package hashes match.
6. Graph integrity: 22n/30e, provenance validator clean, BFS
   deterministic.
7. Decisions/audit: append-only order preserved; auth events
   present where expected.
8. App smoke: health/ready PASS; judge-flow direct test green;
   login journey green (armed mode).
9. Secrets absent: secret scan clean on restored tree.

Automated form: backend suite + `tests/test_j6_drill.py` +
`scripts/security_gate.py`. Manual sign-off: owner.
