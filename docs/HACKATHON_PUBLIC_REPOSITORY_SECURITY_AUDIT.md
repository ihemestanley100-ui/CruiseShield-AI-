# HACKATHON PUBLIC REPOSITORY SECURITY AUDIT

Date: 2026-11-01. Scope: current working tree + full git history.
No values of any secret were read or printed at any point.

## 1. Git history (3 commits, full-diff scan) — CLEAN

Pattern set: `Bearer <token>`, `api[-_]key = <20+ chars>`,
`sk-…`, `ghp_…`, `BEGIN … PRIVATE KEY`. Hits, all benign:
- `Bearer [REDACTED]` (docs prose + test assertion placeholder).
- `const apiKey = process.env.MODEL_API_KEY` — inside the V1.0
  blueprint SPEC text (code sketch, name reference only, no value).
- `risk-assessment.json` / `risk-intelligence…` — `sk-` substring
  false positives.
Verdict: no secret material in history.

## 2. Working tree scan — CLEAN

Same patterns over all source, tests, docs, lockfiles, CI workflows,
scripts, migrations, backups, and `frontend/test-output*.txt`
(excluding `node_modules/`, `.next/`, `.venv/`, `__pycache__/`,
`data/`, binaries). Zero real hits. The only matches are the
`risk-intelligence-v2-candidate` engine id (false positive) and the
`Bearer [REDACTED]` doc placeholder.

## 3. Environment files — SAFE

- Root `.env`: present, git-ignored, never read for values (key names
  only: `MODEL_API_KEY`, `META_MODEL_ID`, `META_BASE_URL`).
- Root `.env.example` + `frontend/.env.example`: names/placeholder
  URLs only, safe to publish.
- No `frontend/.env.local`, no other `.env*` files found.

## 4. Ignore coverage — ADEQUATE with one note

- Root `.gitignore`: `.venv/`, `__pycache__/`, `.env`, `data/*`
  (except `.gitkeep`), test-output logs.
- `frontend/.gitignore`: `node_modules/`, `.next/`, `out/`,
  `.env*.local`, `*.tsbuildinfo`.
- NOTE: `data/state.json` (101417 B, synthetic fixtures + 2 persisted
  AI runs, no secrets — scanned) is correctly ignored; `frontend/`
  as a whole is currently untracked, so a future `git add` must be
  selective (add source/docs, never `.next/`, `node_modules/`,
  `test-output*.txt`, or any `.env*` beyond examples).

## 5. Data / PII — NONE FOUND

Synthetic-only fixture data (kobo minor units, seeded ids, `SYNTHETIC`
labelling, `synthetic_data_flag` on runs); no real user, customer, or
financial records; no private logs or database exports in the tree.
`tests/test_secret_safety.py` passes (11-01).

## 6. Dependency risks — NOTED

- `requirements.txt` pins versions; several carry CVE-remediation
  comments (P2.2A). `pip-audit` status for the backup-crypto pins is
  self-declared NOT VERIFIED in-file — run an audit on a networked
  machine before any production use (out of scope for the demo).
- `psycopg==3.3.2` (LGPL-3.0-only): dependency only, no copied code;
  flagged for organizer IP confirmation (see provenance R-11 note).

## Verdict

SAFE TO MAKE PUBLIC from a secrets/data standpoint, provided the push
is selective per §4 and the logo-rights question (Q-IP-1) is resolved
separately. No remediation required before pushing; no secrets were
found to rotate. This audit changed nothing (no commits, no pushes,
no visibility changes).
