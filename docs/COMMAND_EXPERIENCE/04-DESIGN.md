# Phase B — Frontend Design (PROPOSED, unverified)

Nothing below is built. It is the implementation target for Phase C,
pending a working Node toolchain (see 02-BASELINE).

## Page architecture (App Router)

- `/command` — shell + overview + ledger + transaction panel (default `/`).
- `/investigations/[id]` — studio: graph, why-risk, AI, replay, sim,
  decision, audit (mirrors existing studio sections 1:1).
- `/network` — full explorer (filter, paths, 2D fallback).
- `/cases`, `/cases/[id]`, `/replay`, `/copilot`, `/health`.
- Areas without backend support stay out of nav until their endpoint
  exists (per 03-TRACEABILITY); nothing renders as a dead placeholder.

## Design tokens (interpreted from the brief text; image MISSING)

- Surfaces: navy `#0A1628`, deep `#060D1A`, panel `#0E1E38`.
- Accents: cyan `#22D3EE` (primary), blue `#3B82F6`; violet restrained
  `#8B5CF6` (AI-only); risk: teal/amber/red + text labels (never
  color-alone). Light theme: same hues on `#F3F6FB`.
- Type: system stack, tabular numerals for amounts/IDs; min 12 px data.
- Glass: 1 px illuminated borders, 10–12 px radii, subtle depth; 2D graph
  fallback + `prefers-reduced-motion` honored everywhere.

## API integration layer (proposed `frontend/lib/api.ts`)

Typed client over the 21 real JSON endpoints (see 01-AUDIT); envelope
`{error:{code,message,trace_id}}` mapped to UI states; 30 s AI timeout
with abort; no secrets in browser (backend remains the only Meta caller).
Four additive endpoints proposed in 03-TRACEABILITY must land with
backend tests before the UI calls them.

## 3D + motion (selective, per brief §5)

Shield emblem hero, orbital motif backdrop, network-focus mode; R3F only
if versions align at install time, else plain Three.js; strict pointer
limits, interruptible transitions, WebGL cleanup, idle-animation off,
keyboard/touch equivalents for every pointer interaction.

## Validation plan (Phase E, when toolchain exists)

`npm ci` → typecheck → lint → unit/a11y tests → `next build` → critical
flows vs local backend → secret scan → backend `pytest` regression. No
metric is claimed until its command output exists.
