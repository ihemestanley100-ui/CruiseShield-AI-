# PHASE 0 — DEPLOYMENT PROVENANCE & SECURITY REPORT

2026-11-08. Read-only investigation + this report file. No service
contacted (no probes sent), nothing changed on any service.

## 1. Provenance

- Repo HEAD: `feat/phasezero-foundations @ d82627d` (frozen,
  push-list sha `ac2bb947…`, now +1 file: this report — regen
  the list before any B1 execution).
- Deployed: `production-launch`, observed commit `ff7052b`
  (branch tip `b4732cb`; delta is frontend-only + cookie fix +
  netlify pin — backend effectively identical).
- Committed gap deployed→HEAD: 51 files +5846/−553; app/ 11 files
  +1132/−50, including NEW `app/tenancy.py`, CSEnv guard in
  `store.py`, +331 in `main.py`. Plus the uncommitted worktree.
- Live evidence (repo docs, Nov 4): backend healthy, UNARMED
  (`auth_enabled:false`), JSON active, pg/model NOT_CONFIGURED,
  no disks/databases, frontend never provisioned. No evidence of
  traffic, users, or durable records either way.

## 2. Deployed write surface (ff7052b)

- 3 demo POSTs (reset/start/judge-start) + 6 non-demo POSTs
  (evidence/ai/sim/decisions/events) — ALL behind
  `_require_write_token`, which is **fail-open when the token is
  unset** (verified code). Dashboard token UNKNOWN → openness
  conditional. GET scenarios + all intel reads open by design.
- Auth endpoints open (auth disabled live). No CSEnv guard, no
  tenant module, demo aliases ACTIVE (deprecation came later).
- Render blueprint: no CSEnv/DATABASE_URL/USER_TENANTS keys;
  secrets all `sync:false`; DATA_DIR=/srv/data (ephemeral on
  Free); STORE_BACKEND=json. Blueprint unchanged since deploy.

## 3. Current-tree write surface (d82627d + worktree)

- 40+ mutating routes (auth, admin, billing, passkeys, MFA,
  agents, governance, recovery…). Protection model: session/RBAC/
  ABAC + tenant strict-deny + approval gates (matrix-verified
  where CLOSED; 40 rows still open). Full route-by-route matrix
  is Phase 4 work, not repeated here.

## 4. Records determination

- Repo: ZERO genuine customer records. `data/state.json` is a
  fresh synthetic seed (scn_primary, 5 audits, no users/customers
  keys); `qa-scratch` is the HEAD QA snapshot; all fixtures
  synthetic-patterned; secret/PII scans corroborate.
- Live service: content unobservable from here; construction
  (ephemeral FS + observed reseeds) makes durable records
  impossible. Transient writes by visitors cannot be confirmed
  or denied. No production-records claim is made either way.

## 5. Security posture & required decisions (unchanged)

- Exposure review stands: conditionally-open demo writes, no
  sensitive data served, blast radius = the demo itself.
- Pending: live-demo disposition (leave/harden/undeploy), PKG-03A
  dashboard readout, B10 incorporation (ID 58335), S1/S2/B7/B1.
- A–Z matrix: NO such file exists in repo (searched, 0 matches) —
  the 192-row matrix remains canonical; Phase 1 will map A–Z
  sections onto it without duplicating requirements.

## 6. Integrity note

This file is new since the frozen push list; the B1 package's
mandated pre-execution regen covers it. No other tree changes.
