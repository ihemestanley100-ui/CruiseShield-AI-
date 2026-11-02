# CRUISESHIELD AI — BACKEND RELIABILITY REPORT (J3)

**Verdict:** ACCEPTED for demo scope. Suite: 334 pass / 102 skip /
0 fail (437 collected; 1 sandbox-node-blocked, proven 3/3 green
unsandboxed; skips env-gated, never counted).

## Lifecycle & configuration

- Import-time env parsing fail-safe (J3-P1 `_safe_int` + clamps);
  storage backend validated; no destructive startup (JSON reseeds
  ONLY when the file is absent — scratch/cold-start semantic,
  documented); graceful shutdown via uvicorn; PORT binding verified.
- Timeouts: AI 30 s (env), provider single-flight ~15 s typical,
  frontend 35 s abort ordering preserved.

## Data & concurrency

- Atomic JSON writes + per-process lock (PERF-001, re-raced 10/10);
  audit advisory lock in PG; idempotent event ingest (duplicate-safe);
  decision/audit append-only; no silent success conversions
  (every failure path raises a named AppError — 404/400 matrix tested,
  unknown-txn StopIteration closed J3-P3).
- Unknown-ID matrix (9 reads), scope/body/question/edge/decision
  validation, replay cursor clamp — all covered direct + transport.

## Contracts & observability

- Route table pinned by test; error envelope `{code,message,trace_id}`
  stable; health/ready endpoints with seed/provenance/storage checks;
  audit events on decisions, simulations, AI runs + rejections, logins.
- Rate-limit/body guards tested at middleware level (socket-free).

## Boundaries

- Multi-worker writes unsafe (single worker assumed); PG pooling absent
  (demo scale); loop/socket-gated suites run in CI, not here.
