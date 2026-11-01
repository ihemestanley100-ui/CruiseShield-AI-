# HACKATHON ASSET AND CODE PROVENANCE

READ-ONLY audit evidence. Origin of every material asset in the submission.

## Code origin map

| Group | Files | Origin evidence | Standing |
|---|---|---|---|
| Backend P0 (14 modules) | `app/*.py` at HEAD | Written 10-28 07:10–09:47, committed `f75c3fb` 11:06 | Hackathon-new (T1) |
| Backend additions | `app/db.py`, `models_pg.py`, 8 intel modules | Mtimes 10-30→10-31, uncommitted | Hackathon-new (T3) |
| Backend deltas | main (+298), ai_adapter (+153), seed/store/config/app.js | Diff vs T1 HEAD + mtimes 10-29→10-31 | Hackathon-improved (T1+T3) |
| Server pages | `templates/`, `static/` | 10-28 07:12–09:03, committed | Hackathon-new (T1) |
| Frontend (138 files) | `frontend/` excl. `node_modules/`, `.next/` | Oldest 10-28 14:07, bulk 10-29→11-01, uncommitted | Hackathon-new (T3) |
| Tests (33 files) | `tests/test_*.py` | 10-28 (4) → 10-29 (4) → 10-30 (12) → 10-31 (9+) | Hackathon-new (T1/T3) |
| Backups (9 modules) | `backups/*.py` | 10-30, uncommitted | Hackathon-new (T3) |
| CI + gate | `.github/workflows/*` (4), `scripts/`, `migrations/` | 10-30→10-31, uncommitted | Hackathon-new (T3) |
| Config/deploy | `.env.example`, `requirements*`, `Dockerfile`, `render.yaml` | Committed 10-28 + later deltas | Hackathon-new/improved |

## Third-party and external references (NOT claimed as own work)

- Runtime deps (FastAPI, uvicorn, pydantic, httpx, jinja2, pytest, Next.js,
  React, three@0.187.0, etc.): standard OSS packages, declared in
  `requirements.txt` / `frontend/package.json`, pinned in
  `requirements.lock`. No vendored/copied external source found in repo.
- LICENSE FLAG (11-01): `psycopg==3.3.2` is LGPL-3.0-only. It is an
  installed dependency (scratch migration verification only; JSON
  remains the active backend), not copied code — but any distribution
  or competition-packaging rule touching copyleft needs organizer
  confirmation (see rules compliance R-11).
- The V5.0 blueprint REFERENCES external IP (Frontier Enterprise AI
  Platform™, CruiseTech UI/UX sections 01–116, "CruiseLink telecom
  architecture" as a prohibited pattern). None of that IP exists in this
  repository — no corresponding code, and the baseline record confirms a
  greenfield start. The references are specification lineage, not reuse.
- No other repos, submodules, or copied codebases detected (single remote,
  no vendored dirs).

## Specification documents

- V5.0 master blueprint (105301 B): mtime 10-08 — the sole pre-event
  artifact (see baseline report for caveats incl. v3.0/v5.0 header
  mismatch and missing authorship record). Disclose as pre-existing input.
- V1.0 hackathon build blueprint (40648 B): internally dated 27 Oct 2026,
  mtime 10-28 — an in-window derived work product.

## Data

- `data/state.json` (101417 B, git-ignored): seeded 10-30 06:23 from
  deterministic `app/seed.py`; contains the 2 persisted live AI runs.
  Fully synthetic (kobo minor units, `SYNTHETIC` labelling in UI + docs).
  Reproducible via `POST /api/v1/demo/reset`. No real user/financial data
  anywhere (asserted in README + secret-safety tests).

## Brand / media assets — ATTENTION ITEM

- `frontend/public/assets/cruiseshield-logo-original.png` (now
  1273370 B, 1219 px wide live; was 11121 B at the 10-31 audit —
  replaced with a high-res file during the brand phases).
  **Its source is UNVERIFIED**: the developer asserts it is their
  "original" logo (user instruction 10-31), but no record states
  whether it is developer-created brand art or third-party. Do not
  represent its origin beyond the developer's assertion until
  confirmed — see eligibility report Q-IP-1.
- `frontend/public/assets/cruiseshield-logo-original.png.png`
  (1273370 B, byte-identical): apparent accidental double-extension
  duplicate. PRESERVED as the documented original
  (see `PHASE_2B_REMAINING_GAPS.md`: "original `.png.png` file
  untouched"; control audit 11-01: identical SHA-256) — do not delete,
  rename, overwrite, or replace it.
- Favicon set derived from the logo (11-01): `frontend/app/favicon.ico`,
  `frontend/app/icon.png`, `frontend/public/icons/` (16/32/48 px,
  apple-touch-icon, 192/512 px) — all served 200, verified live.
- No other image/audio/font asset files exist in `frontend/public/` or
  `static/` (only `app.css`, `app.js`, `graph.js` + the above). The
  "synth audio" mentioned in readiness docs is code-generated sound, not
  a media file — no audio provenance issue.

## Secrets hygiene (verified 10-31, re-verified 11-01)

- `.env` + `data/*` ignored by root `.gitignore`; `frontend/.next/` +
  `node_modules/` ignored by `frontend/.gitignore`; both `.env.example`
  files names-only. `tests/test_secret_safety.py` guards against secret
  leakage (passing 11-01). 11-01 scans: git history (3 commits, full
  diff) clean — only `Bearer [REDACTED]` placeholders, a spec-sketch env
  reference, and `risk-*` false positives; working-tree scan (source,
  tests, docs, lockfiles, test-output logs) clean — zero real hits.
  See HACKATHON_PUBLIC_REPOSITORY_SECURITY_AUDIT.
