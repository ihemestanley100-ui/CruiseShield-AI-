# CSG-RELEASE-001 — Hosting Reconciliation

Verified read-only 2026-11-10. No setting was viewed beyond API
metadata; no value was exposed; nothing was changed.

## Netlify (frontend)

- Project `cruiseshieldai`, branch `feat/phasezero-foundations`.
- Deploy `6af2c85accbf912dbc76f14c` ↔ commit `e099b7a`
  (via commit check-runs). Build conclusion not reported via API.
- Build: `npm ci && npm run build`, base `frontend`, publish
  `.next` + OpenNext adapter (from `netlify.toml`).
- Preview URL returns HTTP 401 to unauthenticated callers
  (access gate intact; not disabled for testing).
- Env var names/values: not retrievable from this session.

## Render (backend)

- Service reference from `render.yaml` (free web service +
  Postgres template; starter/disk $0 conflict previously noted).
- Frontend calls `${NEXT_PUBLIC_API_BASE_URL}` (default localhost).
- Live backend URL, env values, and API health: not observable
  from this session (env-driven, no credentials).

## Observation classification

| Observation | Verdict | Basis |
|---|---|---|
| Manifest HTTP 401 | Expected platform restriction | Route exists (`app/manifest.ts`); preview gate 401s subresources |
| Auth endpoint 503 | Expected by design | Honest `AUTH_DISABLED` when secret unset (`app/main.py`, `render.yaml`) |
| Notifications 503 | Unresolved (backend-side) | Unavailable backend; specifics need backend logs |
| CORS errors | Expected restriction unless configured | Env-driven allowlist; template excludes Netlify origin |
| three.js Clock warning | Non-blocking warning | Upstream deprecation, pre-existing, zero failures |
| Drawer container warning | External tooling | M-02 Netlify Drawer isolation stands |

## Cost

No paid service introduced or consumed; no billing touched; no
overage vector added. $0 posture unchanged.
