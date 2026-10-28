# ADR-001: Python stack for the hackathon vertical slice

Status: accepted
Date: 2026-10-28

## Context

Greenfield workspace. The hackathon blueprint prefers reusing an existing stack
and names Next.js + TypeScript only when a new app is needed. Baseline probing
(`docs/ENVIRONMENT_BASELINE.md`) proved the Node toolchain unusable here: every
`npm`/`npx`/Node-script invocation fails with
`EPERM: operation not permitted, lstat 'C:\Users\HP'`.
Python 3.13 with FastAPI, Uvicorn, Pydantic, httpx, Jinja2, and pytest is
preinstalled and verified working. Sandbox network is blocked, so no new
packages can be installed.

## Decision

- Backend: FastAPI + Pydantic (server-side rendering + JSON API in one process).
- Frontend: Jinja2 templates + vanilla JS, SVG graph rendered from backend data,
  no CDN or build step, keyboard-accessible table fallback.
- Storage: JSON file store with atomic writes under `data/` (simplest durable
  option; deterministic reset = re-seed from the versioned manifest).
- Tests: pytest + FastAPI TestClient (httpx), committed under `tests/`.
- Environment: project-local `.venv` created offline with
  `--system-site-packages` (no installs possible); `requirements.txt` pins the
  verified versions for user machines with network access.

## Consequences

- The app runs with zero installs on this machine: `.venv/Scripts/python -m
  uvicorn app.main:app`.
- No framework migration later without a new ADR; this choice follows the
  blueprint's "smallest compatible option" rule given the broken Node toolchain.
- Deployment target stays open (Dockerfile + README for user-side deploy).
