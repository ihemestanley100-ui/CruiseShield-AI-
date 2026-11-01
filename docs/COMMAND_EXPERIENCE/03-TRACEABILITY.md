# Phase B — Requirement Traceability vs Existing Code

Status: VERIFIED (in code + tested) / PARTIAL / MISSING / CONFLICT /
PENDING_REVIEW. "Frontend" below means the planned Next.js app (missing).

## Command Center (§4)

- 4A shell/nav/search/profile/notifications/theme → MISSING (frontend).
  Global search needs a new read-only endpoint (proposed:
  `GET /api/v1/search?q=&types=`), additive.
- 4B metrics overview → MISSING endpoint (proposed:
  `GET /api/v1/metrics/overview` computed from store); underlying data
  VERIFIED in store/seed.
- 4C ledger list/search/sort/paginate → MISSING endpoint (proposed:
  `GET /api/v1/events?channel=&risk=&q=&page=`); event data VERIFIED.
- 4D transaction details → VERIFIED backend (`GET transactions/{id}` +
  risk/graph/evidence) — frontend re-presentation only.
- 4E network graph → VERIFIED engine (`GET graph/{txn}` full 22/30 graph
  + provenance); zoom/pan/filter/fallback are frontend work.
- 4F risk indicators → PARTIAL: transaction + network scopes VERIFIED
  (rules R-001..R-008, bands, provenance). Entity/behavioral/channel/
  device/geographic indicators are MISSING — must not be presented.
- 4G timeline/replay → VERIFIED (`GET replay/{scenario}`, deterministic).

## 3D, AI, workflow (§5–§8)

- §5 Three.js scenes/motion → MISSING (no toolchain; see 02-BASELINE).
- §6 AI investigator single-shot → VERIFIED live (agentrun_0002).
  Follow-up questions with context → MISSING endpoint (proposed:
  `POST /api/v1/investigations/{id}/ai-followup` with history + same
  validators). No duplicate AI integration: backend stays the only caller.
- §7 investigations/cases/decisions/audit → VERIFIED (transitions,
  mandatory reasons, persistence, live decision_0001). Assignment and
  notes → MISSING (do not present).
- §8 simulation/replay UX → VERIFIED engine (bounded, baseline-safe,
  audited); comparison UI is frontend work.

## Navigation, quality, demo (§9–§13)

- §9 thirteen nav areas → only Command/Investigation/Health exist;
  the rest are MISSING: implement against real endpoints or mark planned.
- §10 a11y/responsive → PARTIAL in current pages (labels, focus,
  table fallback, reduced-motion); new frontend must re-implement.
- §11 synthetic data + txn_84721 → VERIFIED; status vocabulary to adopt.
- §12 frontend build/tests/perf → MISSING (blocked by toolchain).
- §13 demo chain → VERIFIED except AI follow-up (MISSING endpoint).

## Conflicts / review items

- CONFLICT-001 (deploy): `0eaaaf5` removed `startCommand` from render.yaml;
  Dockerfile CMD hardcodes port 8000 while Render injects `$PORT`
  (default 10000). Risk: deploy health-check failure. Smallest fix
  (needs approval, barred by §14 during initial work): shell-form CMD
  honoring `${PORT:-8000}`, or a `dockerCommand` override. PENDING_REVIEW.
