# Deployment — Render Blueprint (Docker)

Chosen path: deploy the existing `Dockerfile` on Render via `render.yaml`
(Blueprint). Rationale: no new infrastructure code, no CLI needed, declarative
review, managed secret store, and a persistent disk for `DATA_DIR`. Any Docker
host with a volume works the same way (mount the volume at the `DATA_DIR`
path, set `MODEL_API_KEY`, route to the app port).

## What Render does from `render.yaml`

- Builds the image server-side (`dockerfilePath: ./Dockerfile`).
- Starts one web instance:
  `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  (`$PORT` is injected by Render; the Dockerfile's port 8000 default is only
  for local `docker run`.)
- Health-checks `GET /api/v1/health`.
- Attaches a 1 GB persistent disk at `/srv/data` (= `DATA_DIR`), so
  `data/state.json` (decisions, runs, cases, audits) survives restarts.
- Prompts for `MODEL_API_KEY` once (`sync: false`) and keeps it in the
  Render secret store. It never appears in the repo, image, or logs.

## Cost / tier note (needs your approval)

Persistent disks require a paid instance type; the blueprint sets the
smallest such type (`starter`) plus a 1 GB disk. Nothing here provisions or
pays for anything — approving the deploy in the dashboard does.
Free-tier alternative: delete the `disk:` block before deploying. The app
still runs (an empty `DATA_DIR` re-seeds deterministically on boot), but
decisions, AI runs, and audits evaporate on restart — acceptable for a
single-session judge demo, not for a persistent showcase.

## Required environment variables

| Name | Value | Notes |
|---|---|---|
| `MODEL_API_KEY` | your Meta key | Render secret (prompted, `sync: false`). No default. |
| `META_MODEL_ID` | `muse-spark-1.3` | Default in image; override only per current Meta docs. |
| `META_BASE_URL` | `https://api.meta.ai/v1` | Default in image. |
| `DATA_DIR` | `/srv/data` | Must equal the disk `mountPath`. |
| `PORT` | injected by Render | Used by `startCommand`; do not set manually. |

## Manual steps (exact)

1. Push the repo to GitHub (see the release checklist in chat for commands;
   needs your approval — nothing is committed or pushed by the agent).
2. Render dashboard → New → Blueprint → select the repo.
3. Service name `cruiseshield-ai`; confirm plan `starter` (or free without
   the disk — see note above); enter `MODEL_API_KEY` when prompted.
4. Confirm disk `cruiseshield-data`, 1 GB, mount path `/srv/data`. Deploy.
5. Smoke test against the public URL (replace `$APP`):
   `curl $APP/api/v1/health` → `status: healthy`;
   open `$APP/` → Start Signature Investigation → open the investigation →
   Reveal Network → Run AI analysis (expect SUCCEEDED) → record a reasoned
   decision → confirm the audit entry.
6. Rollback: Render dashboard → service → Rollbacks → pick the previous
   deploy. Redeploy: push to the connected branch (auto-deploy default).

## Security notes

- Never commit `.env` or keys; `git check-ignore -q .env` must pass (covered
  by `tests/test_secret_safety.py`).
- The public demo has no login by design (P0 scope). It only mutates seeded
  demo records and discloses demo mode in the UI. Do not present it as a
  production service and do not load real financial data into it.
