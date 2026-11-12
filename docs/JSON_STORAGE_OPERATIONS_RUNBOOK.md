# JSON Storage Operations Runbook (C-1)

Authoritative backend: JSON file store (`app/store.py`). Status:
production path for Stage 1. Review state: OWNER REVIEW (this
unit); O-05 approval NOT claimed. Re-validate this runbook on
any `app/store.py` change (see §10).

## 1. Layout and selection

- Active file: `DATA_DIR/state.json` (`DATA_DIR` env, default
  `ROOT/data`). Current seed ≈ 101 KB.
- `STORE_BACKEND` unset/`json` = JSON store. `pg` selects the
  PostgreSQL adapter for scratch migration verification
  ONLY (owner HOLD — never production without a cutover
  decision). No code path auto-selects pg.

## 2. Atomic-write guarantees (`Store._save`)

- Each save serializes under a `threading.Lock`, writes the
  full document to `state.tmp`, then atomically replaces
  `state.json` (`Path.replace`). Readers never see a
  half-written document from this process.
- Limits (honest): NO `fsync` — an OS crash in the write
  window can lose the latest save or (on some filesystems)
  the tmp file; the previous `state.json` survives replace
  semantics. There is no write-ahead log and no
  point-in-time recovery inside the store.

## 3. Concurrency limitations

- Safe: multi-threaded single process (shipped
  configuration: one uvicorn process, default single
  worker — see `Dockerfile` CMD).
- UNSAFE: `--workers N>1`, two processes, or any second
  writer against the same `DATA_DIR` (one fixed tmp path,
  no cross-process lock — concurrent writers collide and
  last-writer-wins silently). Do NOT scale workers without
  a real database (§9).

## 4. Restart and recovery behaviour

- Missing file: the store seeds a FRESH deterministic
  state and emits a `RuntimeWarning` naming the path
  (fail-loud, never silent). On free-tier ephemeral
  disks a restart wipes data by platform design — see §8.
- Corrupt file: `json.loads` raises at construction and
  the process fails to boot (fail-closed). Recovery =
  restore a backup (§6) or delete to reseed (data loss,
  operator decision only).
- Fingerprint after any restart: `GET /api/v1/health`
  (`seed_integrity`, `graph_provenance`,
  `audit_chain_verified`) must read PASS before serving
  traffic.

## 5. Integrity checks (all executable today)

- `seed_integrity`: live graph counts vs manifest
  expectations (health, blocking).
- `graph_provenance`: every edge carries source event
  ids (health, blocking).
- `audit_chain_verified`: HMAC chain verification +
  legacy count (health; degraded on FAIL since A-1).
- Canonical fixture: `tests/fixtures/canonical-state.json`
  (byte-anchored, git `binary`) backs parity, loader-gate,
  and drill tests.

## 6. Backup, export, restore

- Full backup drill (scratch): `python
  scripts/backup_drill.py --dir <empty-dir>` — produce →
  verify → restore → parity over the canonical fixture
  with fresh ephemeral keys; exits nonzero on any failed
  gate. Uses `backups/{crypto,signing,produce,restore,
  local_target}` (Sealed-box + signed manifest).
- Evidence export (live, read-only):
  `GET /api/v1/investigations/{id}/evidence-package/export`
  serves canonical bytes with an `X-Export-SHA256`
  fingerprint — two exports of one package are
  byte-identical.
- Audit export: `scripts/audit_export.py` (attributed
  event stream for review tooling).
- Restore rule: restore into an EMPTY `DATA_DIR`, then
  run the §4 health fingerprint. Never merge two live
  state files (no merge primitive exists).
- Owner ceremony gap: production backup keys + schedule
  still owe D-018 / PKG-07 (external, unchanged).

## 7. Storage exhaustion handling

- The store enforces NO quota: a full disk surfaces as
  a failed save (exception → HTTP 500), never silent
  loss. Mitigations without paid infra: host disk-usage
  alerts (Render dashboard meters, free), keep the seed
  small (current ≈ 101 KB; growth is operator-visible in
  git and health counts), and rotate/copy `state.json`
  out before risky operations.
- Free-tier caveat: ephemeral disks lose `state.json` on
  restart/redeploy (platform behaviour, not a bug). The
  reseed path (§4) keeps the service honest, not stateful.

## 8. Free-tier deployment notes ($0 preserved)

- This runbook adds no service, volume, or dependency.
  Render Free + ephemeral JSON remains the $0 launch
  shape; Supabase Free PG stays the reserved (unverified)
  persistence upgrade, NOT claimed ready here.

## 9. PostgreSQL migration criteria

Migrate (via `migrations/loader.py`: copy-only,
hash-verified, transactional, reconciled) when ANY holds:

1. Durability: restarts must preserve writes (leaving
   ephemeral disks), or backups must be continuous.
2. Concurrency: more than one writer process/worker, or
   sustained concurrent-write contention.
3. Scale: `state.json` approaches operational review
   size (rule of thumb: > 50 MB or save latency above
   the perf-smoke budget) — measure, never guess.
4. Integrity load: audit-chain verification cost
   (O(sealed) per health call) exceeds budget.

Until then JSON stays authoritative. The loader + parity
tooling (`test_pg_*`, loader gate) already exist and are
exercised against scratch URLs only.

## 10. Re-validation triggers

Re-run on any store change: `tests/test_store_durability_m3.py`,
`tests/test_seed_reset.py`, `tests/test_audit_arming.py`,
`tests/test_health_qualified.py`, plus
`scripts/backup_drill.py --dir <tmp>` and the health
fingerprint. Update this runbook when behaviour changes.
