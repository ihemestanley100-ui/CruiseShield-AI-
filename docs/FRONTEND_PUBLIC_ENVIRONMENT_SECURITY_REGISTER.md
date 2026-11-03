# FRONTEND PUBLIC ENVIRONMENT SECURITY REGISTER

Date: 2026-11-03 · Rule: every `NEXT_PUBLIC_*` var is
baked into browser JS at build time and is PUBLIC by
construction. Nothing secret may use the prefix.

| Variable | Baked public? | Sensitivity | Verdict |
|---|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | YES | URL only, no secret | SAFE — backend URL is public anyway |
| `NEXT_PUBLIC_SITE_URL` | YES | Self URL | SAFE |
| `NEXT_PUBLIC_DEMO_WRITE_TOKEN` | YES (proven) | Shared write credential | FAIL as-is — see Demo Token Audit; safe only AFTER F-PRIV-1 + F-AUDIT-1 fixes, or leave EMPTY (login-required writes) |

## Backend counterparts (never public)

| Variable | Exposure | Note |
|---|---|---|
| `DEMO_WRITE_TOKEN` | Server env only | Must be set (else gates open); must EQUAL frontend value for the demo flow |
| `SESSION_SECRET` | Server env only | 32+ enforced, fail-closed (R09-F2) |
| `DEMO_USERS` | Server env only | Password hashes; never readable via API |
| `MODEL_API_KEY` | Server env only | Never leaves backend; AI calls server-side |

## Build-time semantics (verified)

- Values are frozen at `next build`; changing a var
  REQUIRES frontend rebuild (Render: set env → Manual
  Deploy). Verified mechanism: proof build 11-03.
- Unset locally → header omitted, local behavior
  unchanged (`api.ts:228`).
- 0 sourcemaps shipped; token absent from HTML.

## Standing rule

Any NEW `NEXT_PUBLIC_*` addition requires a security
review entry in this register BEFORE commit. Secrets
without the prefix are still unreachable from client
components — keep it that way.
