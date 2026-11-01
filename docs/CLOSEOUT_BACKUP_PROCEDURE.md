# CLOSEOUT — BACKUP AND RECOVERY PROCEDURE (plan — NOT executed)

PROGRAMME: CSAI-MASTER-RELEASE-001 CLOSEOUT | DATE: 2026-11-01
STATUS: procedure ready; execution BLOCKED until the owner approves the exact destination + handling method. No backup was created by this closeout. Never overwrite an existing backup.

## 1. Destination (OWNER APPROVAL REQUIRED — no default invented)
- Required from owner: exact path/URL (external drive, encrypted volume, or vault), filesystem/encryption, custodian, retention.
- Secrets: `.env` (live MODEL_API_KEY) goes ONLY to an owner-approved secure secret store (password manager / vault entry / sealed envelope) — NEVER inside the ordinary project archive. Record the secret-store reference (name, NOT value) in the manifest.

## 2. Contents (project archive)
- Full source tree at closeout (HEAD 0eaaaf5 + working tree file list with per-file SHA-256).
- `data/state.json` (verified BA1D4DB4…3790FE, 101417 B at closeout) + Git metadata (`.git/` incl. HEAD, refs, objects for the 3 commits).
- All `docs/` incl. Phase 1–15 reports, closeout decision, demo script/storyboard.
- Test evidence: backend/frontend logs of the final runs; `requirements.txt` + `requirements.lock` + `frontend/package.json` (+ lockfile if present).
- Browser evidence COPIES from %TEMP% (smoke48/smoke11/smoke12 shots + matrix JSONs + live_run.json + decision/WebGL screenshots) — copied INTO the archive with hashes, originals left in place.

## 3. Exclusions (regenerable)
`node_modules/`, `.next/`, `__pycache__/`, `.pytest_cache/`, `*.pyc`, `.venv/`, OS thumbnails. Build/run instructions included so the tree is reproducible from source + manifests.

## 4. Controls
- Archive format: deterministic (sorted entries, fixed mtimes) `.tar.gz` or `.zip`; SHA-256 of the archive recorded + verified after write.
- Access: encrypted at rest if the destination leaves owner custody (age/GPG to owner key — method owner-approved).
- Manifest: file count, per-file hashes, archive hash, Git HEAD, state hash, suite versions, evidence inventory, exclusions list, secret-store reference.

## 5. Restoration procedure (disposable target only for tests)
1. Extract to an EMPTY directory (never over a live tree); verify archive hash first.
2. Recreate env: `python -m venv`, `pip install -r requirements.lock` (hashes), `npm ci` (or per lockfile), `npm run build`.
3. Copy `data/state.json` from archive; verify hash BA1D4DB4…3790FE before first start.
4. Start backend (`uvicorn app.main:app --port 8000`, no DATA_DIR override) + `npm start -- --port 3000`; check /api/v1/health + / = 200.
5. Run suites (pytest + vitest) to confirm the restored tree is green.
6. Live `.env` restored ONLY from the secure secret store by the owner, never from the archive.

## 6. Approval request (exact)
Owner: provide (a) archive destination path/URL, (b) encryption method + key reference, (c) secret-store destination for `.env`, (d) permission to execute steps 1–6 of §5 as a disposable drill after archiving. On approval, Muse executes, verifies hashes, and records the manifest.
