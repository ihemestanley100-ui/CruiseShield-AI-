# CONFLICT-001 — Render port contract (PENDING_REVIEW, not applied)

## Observed state (evidence)

- `render.yaml` (commit `0eaaaf5`): no `startCommand` / `dockerCommand`; only
  `dockerfilePath`, `healthCheckPath: /api/v1/health`, disk, envVars.
- `Dockerfile` CMD (exec form): uvicorn on `--host 0.0.0.0 --port 8000`.
- Render injects `$PORT` (default 10000) and routes public traffic + health
  checks to the port the service listens on.

## Impact

If Render requires the container to listen on `$PORT`, the hardcoded `:8000`
fails deploy health checks. If Render instead honors `EXPOSE`/CMD, the
current files work unchanged. The blueprint author removed `startCommand`
because that key is for native runtimes (Docker uses `dockerCommand`),
which fixed the schema but left the port question open. Local `docker run`
is unaffected either way (no `$PORT` set → 8000).

## Smallest safe fix (PROPOSED — do not apply without approval)

One-line Dockerfile change (shell form honors both worlds):

```dockerfile
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

- Local/no `$PORT`: behaves exactly as today (`:8000`).
- Render: binds `$PORT` automatically; no render.yaml change needed.
- Alternative: `dockerCommand:` override in render.yaml with `$PORT`.
  Rejected as first choice: two places then own the port contract, and
  `$PORT` substitution inside `dockerCommand` is less documented.

## Gate

Per transformation-brief §14, Dockerfile/render.yaml stay untouched during
initial frontend work. Apply only after explicit approval, then re-verify
with a deploy (or a local `docker run -e PORT=9000` bind check).
