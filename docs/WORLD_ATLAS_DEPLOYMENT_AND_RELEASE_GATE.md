# WORLD ATLAS — DEPLOYMENT & RELEASE GATE REGISTER

Date: 2026-11-03 · All gates CLOSED. No action authorized.

| Gate | Action | Prerequisites | Status | Evidence to open |
|---|---|---|---|---|
| ATLAS-ARCH | Approve architecture (§5 Master) | Owner reads Architecture doc | CLOSED | Explicit "approve Three.js plan" (or R3F/MapLibre override) |
| ATLAS-PROV | Approve candidate providers | Owner reviews current ToS/quotas for Landsat/Sentinel/CelesTrak | CLOSED | Named providers + terms URLs + "approved" |
| ATLAS-B-DIR | Track B direction | Owner picks defer / supply / manual | CLOSED | Explicit option choice |
| ATLAS-GO | Begin Phase 1 implementation | ARCH + preservation ack | CLOSED | Explicit "go" |
| ATLAS-DEP-ADD | Install `world-atlas` + `topojson-client` | GO + license/audit PASS | CLOSED | Audit output in commit notes |
| ATLAS-CSP | Any CSP amendment (phase 2+ only) | Security review | CLOSED | Diff + justification |
| ATLAS-LIVE | Label any layer LIVE | Per-provider checklist (Satellite §6) | CLOSED | Dated verification log |
| ATLAS-RELEASE | Ship `/atlas` to production | Acceptance T01–T26 green + regression + gap reconciled | CLOSED | Matrix + test logs |

## Standing prohibitions (until gates open)

No `npm install`, no code edits, no Git staging, no
Render changes, no accounts, no keys, no API spend,
no imagery download. F-EPH-1 reminder: atlas cache is
ephemeral on Render Free — accepted by design (cache,
not authority).

## Deployment shape (no new infra)

Atlas ships inside the EXISTING frontend service
(`/atlas` route, same build). No new Render service,
no new database, no domain, $0 delta. Backend router
ships inside the existing backend service.
