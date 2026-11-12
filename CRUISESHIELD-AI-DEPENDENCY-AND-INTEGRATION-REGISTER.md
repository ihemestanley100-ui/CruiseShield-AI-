# CRUISESHIELD-AI-DEPENDENCY-AND-INTEGRATION-REGISTER.md

Load-bearing integrations, versions, and ordering constraints.
"Load-bearing" = changing it breaks boot, security, or verification.

## 1. Boot order (backend)

`STORE_BACKEND`/`DATA_DIR` env → `Store()` (`app/main.py:182`) → seed
(`app/store.py:74-162`) → health/ready (`app/main.py:413-471`).
`.env` loader (`app/config.py:11-32`) never overrides real env.
`pg` selection affects probes only — there is no production PG boot
path (GAP-001).

## 2. Frontend build chain (load-bearing)

`NEXT_PUBLIC_API_BASE_URL` is baked at build time; `next.config.ts:14-22`
derives CSP `connect-src` from the same variable by construction, so
each environment needs its own build. `render.yaml:5-10` deploy-order
handshake (backend first → frontend with backend URL) is therefore
load-bearing and correctly documented. Standard SSR app: no
`output`/`export`, `next start` required; static hosting incompatible
(GAP-008).

## 3. Auth chain (3-way consistent, verified)

Backend HMAC-SHA256 cookie + 4-role PERMISSIONS matrix + CSRF header +
10/min login limit + logout-all epoch (`app/auth.py`, `app/main.py`)
matches frontend mode/me/login/logout/logout-all clients
(`frontend/lib/api.ts:965-997`) and the login gate (`login-gate.tsx`).
`DEMO_WRITE_TOKEN` is a non-browser fallback that can never satisfy
admin gates or self-assert audit identity (`app/main.py:116-128`).
AI endpoints need write token + (armed) login session + `ai_run` perm
(`app/main.py:225-236,293-302`). CORS allowlist is explicit, never `*`
(`app/config.py:99-132`).

## 4. Graph chain (record-backed end to end)

`store.state` (synthetic_flag seed) → `GET /api/v1/graph/{txn}` with
`validate_provenance` + counts (`app/main.py:767-777`) → `getGraph`
(`api.ts:378-386`) → `/network/[txnId]` page + explorers, which render
exactly supplied nodes/edges. Overlay (`/overlay`) merges render-side,
best-effort. Landing hero 3D (hubs/beams/satellites) is decorative
SIMULATED and honestly labeled — never treat as data.

## 5. AI chain (advisory-only, traceable)

Rules → evidence items → package sha256 (`app/evidence.py:59-69`) →
`evidence_ids_sent` allowlist (`app/ai_adapter.py:396`) → validated
model citations. AI persists run + one audit only; risks/rules/
evidence/cases stay byte-identical (`app/main.py:952-963`). Daily cap,
30s timeout (< 35s frontend abort), and 4096 max-output are enforced
pre-provider. Decisions stay human-only (`app/cases.py:38-77`).
MockTransport tests never touch the network; live path unproven
(GAP-014). No eval harness (GAP-004).

## 6. Audit ↔ backup link

Audits are ordered-not-chained (GAP-002 decision); backup manifests
separately bind audit count + head per generation
(`backups/manifest.py:16`). The tamper story spans GAP-002 + GAP-003.

## 7. Test ↔ CI ↔ deploy spine

Hermetic backend (isolated Store + key-strip + snapshot guard) +
mocked-boundary frontend (72 files, 0 skips) + 6-check gate script +
gitleaks + tsc + vitest + next build (`security-gate.yml:18-90`,
local 6/6 PASS). Hosted proof missing (GAP-010) gates deploy trust
(GAP-009); current-tree green (GAP-006) gates everything else.

## 8. API ↔ UI coverage cluster

GAP-012 (9 server routes unwired) + GAP-013 (5 clients uncalled) close
in one joint pass. `accounts-intel` is the only DI route without any
client; device/IP/geo/txn-intel clients exist but no page calls them.

## 9. Pinned versions (do not drift without a gate run)

- Python 3.13-slim; fastapi 0.133.0, starlette 1.3.1, uvicorn 0.40.0,
  pydantic 2.12.5, httpx 0.28.1, jinja2 3.1.6, pytest 9.0.3,
  psycopg 3.3.2, pynacl 1.6.2, boto3/botocore 1.43.117
  (requirements.txt:6-34; lock: 37 pins / 463 hashes).
- Node frontend: next ^15.0.0 (build log 15.5.28), react 19,
  three 0.187.0 + matching @types/three, vitest 3, typescript 5
  (frontend/package.json). Node >= 18.18; Render pins 20.19.6.
- No `@netlify/plugin-nextjs` in deps — Netlify runtime never runs
  (see Netlify A-E report).

## 10. External integrations

- Meta Model API: `POST {META_BASE_URL}/chat/completions`, Bearer
  server-side, model default `muse-spark-1.3`. Key unset → honest
  503 MODEL_NOT_CONFIGURED. No paid call without approval.
- Render: manual Blueprint (backend docker + disk; frontend node).
  No CI deploy. Dashboard state uninspected (GAP-009).
- GitHub Actions: security-gate (push/PR/weekly) + 3 disabled manual
  backup workflows. Hosted runs unobserved (GAP-010).
- Backup targets (B2/C3-style + CSBK keys): names only in workflows;
  no credentials in repo; ceremony not performed (GAP-003).
