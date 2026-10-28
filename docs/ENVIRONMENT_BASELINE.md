# Environment Baseline — 2026-10-28

Observed facts from read-only inspection. No values of secrets were read or printed.

## Runtime

| Tool | Result |
|---|---|
| OS | Microsoft Windows NT 10.0.22000.0 |
| node | v20.19.6 binary runs (`--version`, `-e` OK) |
| npm / npx | BROKEN — `EPERM: operation not permitted, lstat 'C:\Users\HP'` on every script invocation |
| vercel CLI | BROKEN — same Node EPERM (Node-based CLI) |
| python | 3.13.7, works |
| pip | 25.2, works (local operations) |
| fastapi / uvicorn / pydantic | 0.128.0 / 0.40.0 / 2.12.5 preinstalled |
| httpx / jinja2 / pytest | 0.28.1 / 3.1.6 / 9.0.2 preinstalled |
| git | 2.53.0, identity configured (repo-local use only for this project) |
| docker | 29.4.2 present (daemon access not attempted) |
| Sandbox network | BLOCKED — outbound HTTPS from shell/Python failed (PyPI unreachable) |
| Secrets in env | `MODEL_API_KEY`, `META_API_KEY`, `OPENAI_API_KEY` all absent |
| Deploy CLIs | vercel (broken, see above), aws present; fly/railway/netlify/heroku/az/gcloud absent |

## Repository

- Not a Git repository at baseline. `.hg`, `.sl`, `.eden`, `.agents`, `.muse` all exist with 0 children each (empty stubs, no VCS content to preserve).
- Only content: the two canonical specification `.txt` files. No source, manifests, tests, or deployment config.

## Consequences

1. Node-based stacks (Next.js, npm install, Vercel CLI deploy) are unusable in this environment. Stack decision recorded in `docs/ADR/ADR-001-stack.md`.
2. No package installs possible (network blocked); the build uses only preinstalled Python packages, verified by import.
3. `MODEL_API_KEY` absent: the live Meta Model API call cannot succeed until the user supplies a key. Adapter, validation, provenance UI, and degraded states are built; the live call stays BLOCKED with an exact report.
4. Deployment from this sandbox is not possible (broken Vercel CLI, no network). Handoff target: runnable locally via uvicorn; deployment is a user-side step documented in README.
