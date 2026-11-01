# G. BACKUP READINESS REPORT

DATE: 2026-11-01 | STATUS: plan complete, NOT executed (D-008). Procedure: `docs/CLOSEOUT_BACKUP_PROCEDURE.md`.

## Proposed destination — OWNER APPROVAL REQUIRED (nothing invented)
Owner must supply: (a) exact archive path/URL, (b) encryption method + key reference, (c) secure secret-store destination for `.env`, (d) execution + disposable-drill approval. No backup exists yet; never overwrite an existing one.

## Required contents (frozen values 11-01)
- Source tree: HEAD 0eaaaf5 + 123-entry working-tree file list with per-file SHA-256.
- `data/state.json`: SHA-256 BA1D4DB4…3790FE, 101417 B, case NEW.
- Git metadata: `.git/` (3 commits, HEAD, refs).
- Docs: all `docs/` (Phases 1–15, closeout, SUBMIT A–J, demo script/storyboard).
- Manifests: `requirements.txt`, `requirements.lock`, `frontend/package.json`.
- Evidence copies (volatile %TEMP% → archive with hashes): smoke48/smoke11/smoke12 shots + matrix JSONs, `live_run.json` (agentrun_0003), `l2_decision.png`, `webgl_fallback*.png`, `fx2_*.png`, final suite logs.
- Logos: original `cruiseshield-logo-original.png` 1273370 B SHA-256 1A0CC66B…C32A623 (+ duplicate `.png.png`, identical, disposition pending).

## Exclusions
`node_modules/`, `.next/`, `__pycache__/`, `.pytest_cache/`, `*.pyc`, `.venv/`, OS thumbnails. Rebuild/run instructions included.

## `.env` handling (mandatory)
Live `.env`/MODEL_API_KEY goes ONLY to the owner-approved secret store — NEVER in the project archive. Manifest records the store REFERENCE (name, never value).

## Restoration (disposable target for tests)
Verify archive hash → extract to EMPTY dir → venv + hash-pinned installs + build → restore state.json + verify hash → start :8000/:3000 → health 200s → suites green. Live `.env` restored by owner from secret store only.
