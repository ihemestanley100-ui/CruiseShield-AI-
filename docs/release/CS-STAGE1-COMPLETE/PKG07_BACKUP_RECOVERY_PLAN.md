# PKG-07 — Backup and Recovery Plan (CS-OPS-002)

Status: PROCEDURE PREPARED. No production backup executed or
verified under this programme. Drill evidence below is scratch-only.

## 1. Ownership and schedule

- Owner: project owner (approves schedule, retention, restores).
- Operator: on-call engineer (executes, records evidence).
- Proposed schedule: daily encrypted generation + weekly
  restore drill (owner to ratify; `backup-*.yml` workflows stay
  disabled-by-default until the `backup-production-gate`
  environment + reviewers exist).

## 2. Scope and encryption

- Scope: canonical state snapshot (schema 5.1.0) via
  `backups/produce.py` (Sealed-box recipients + signed manifest).
- Keys: `CSBK_*` environment secrets (names only here); private
  restore keys never leave the owner vault; values never in Git.
- Retention: 30 daily generations + 12 monthly pins (proposed;
  owner to ratify against free-tier storage limits).

## 3. RTO / RPO (proposed, pending owner acceptance)

- RPO ≤ 24 h (daily generation). RTO ≤ 4 h (restore + health
  fingerprint + smoke). Both unproven against production until
  the first authorized live drill.

## 4. Restore verification (mandatory per restore)

1. Restore into an EMPTY `DATA_DIR` (never merge live files).
2. `GET /api/v1/health`: `seed_integrity`, `graph_provenance`,
   `audit_chain_verified` all PASS.
3. Spot-check audit tail + evidence export fingerprint.
4. Record: backup id, restorer, timestamps, health output.

## 5. Recovery drill (scratch, executable today)

`python scripts/backup_drill.py --dir <empty-dir>` — produce →
verify → restore → parity over the canonical fixture with
fresh ephemeral keys; exit 0 + parity true required. Last run
(C-1 evidence): exit 0, parity true. A documented procedure is
NOT an executed live drill — distinguish always.

## 6. Recovery-copy custody

Same rule as D-018 §7: sealed offline copies, logged access,
annual drill. Backup encryption keys and audit-chain keys are
separate lineages — compromise of one never implies the other.

## 7. Evidence record template

backup_id / source / produced_at / produced_by / verify_ok /
restore_target / restored_at / parity_ok / health_fingerprint /
sign-off. One row per generation; monthly owner review.
