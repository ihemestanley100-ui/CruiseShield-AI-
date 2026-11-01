# E. INTELLECTUAL PROPERTY AND LICENCE REPORT

DATE: 2026-11-01 | SCALE: PASS / PARTIAL / NOT_VERIFIED.

## Code ownership — PASS (evidence-backed)
Greenfield in-window authorship (T1 3 commits 10-28 + T2 baseline record + T3 mtimes); no third-party code copied in (re-scans clean 11-01). AI-assisted coding explicitly welcomed by the event (S1).

## Logo / brand — NOT_VERIFIED (highest-value IP action)
- `frontend/public/assets/cruiseshield-logo-original.png`: 1273370 B, SHA-256 1A0CC66B…C32A623 (re-verified 11-01).
- Duplicate `.png.png`: identical hash + size, ZERO code references (proven 11-01) — safe to delete, KEPT pending owner approval.
- Developer asserts original authorship (recorded, no document). No licence/assignment on file.
- S2 reports entrants must own everything + grant organisers a broad licence → Q-IP-1: owner must file a rights memo (creator, ownership, submission/press-reuse position) BEFORE submitting.
- "Meta"/"Muse Spark"/model IDs used as integration facts + provider labels, not endorsement (Q-IP-2: check mark-attribution rules in full Rules text).

## Dependencies / licences — PASS_WITH_LIMITATIONS
- Backend scan 11-01 (60 installed pkgs): MIT/Apache-2.0/BSD/PSF/MPL-2.0 (certifi) throughout; metadata-gap "?" on a few (Jinja2 etc. — well-known permissive, noted not hidden).
- Sole copyleft flag: `psycopg==3.3.2` LGPL-3.0-only — declared dependency, NOT vendored, scratch PG-verification path only (JSON is the active backend), Docker image never built. Obligation arises only if a distributed image includes it → recorded question for qualified read, not a violation.
- Frontend: next/react/react-dom/three MIT, typescript Apache-2.0, vitest MIT (package metadata 11-01).
- Fonts/icons/audio/textures: per base provenance report; no new assets added in Phases 9–12 or closeout.

## Data — PASS
Synthetic fixtures only; no real PII; `data/state.json` git-ignored + scanned clean.
