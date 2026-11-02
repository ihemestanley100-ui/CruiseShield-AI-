# J5 - MIGRATION MANIFEST

Generated 2026-11-01 by `scripts/migration_manifest.py` from a
read-only byte copy of `data/state.json` (live file never touched;
loader refuses live sources). Reconciliation target for the PG
rehearsal load.

source bytes: 101417
source sha256: ba1d4db4bb4dbc6fc3aca346664a539610ccc6460ccd530f523c8043453790fe
scenario: scn_primary v1.0.0

## Collection counts

- ai_runs: 2 rows
- alerts: 1 rows
- audit_counter: scalar
- audits: 5 rows
- cases: 1 rows
- created_at: scalar
- decisions: 0 rows
- edges: 30 rows
- events: 11 rows
- evidence_packages: 1 keys
- investigations: 1 rows
- manifest: 11 keys
- nodes: 22 rows
- primary_transaction_id: scalar
- replay: 1 keys
- risk: 1 keys
- rule_results: 1 keys
- run_id: scalar
- scenario_id: scalar
- scenario_version: scalar
- seed_hash: scalar
- seen_event_ids: 11 rows
- simulations: 1 rows
- trace_id: scalar
- transactions: 11 rows

## Identifier inventory

- transactions: 11 (txn_84721, txn_84722, txn_84723)
- nodes: 22; edges: 30
- events: 11
- rule_results: 8
- evidence_packages: 1 (39 items)
- investigations: 1
- cases: 1
- decisions: 0
- audits: 5
- ai_runs: 2
- simulations: 1

## Content hashes (canonical subsets, sha256/16)

- transactions: 56c2e2d4fceea324
- edges: 0da5fcb96e5c60f6
- risk: 8386f92a074e8d9a
- audits: c90cc1df17beed17

## Referential checks

- edges reference known nodes: OK
- evidence items resolve: OK
- decisions reference cases: OK
- audit chain audit_0001..N in order: OK

## Risk pins

- txn-only: 35/MODERATE
- network: 84/HIGH
