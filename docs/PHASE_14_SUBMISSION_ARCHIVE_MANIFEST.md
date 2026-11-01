# PHASE 14 — SUBMISSION ARCHIVE MANIFEST (template — fill at activation)

STATUS: BLOCKED (no submission yet). All fields below are EMPTY until the owner confirms actual submission.

| Field | Value at activation |
|---|---|
| Submission timestamp (with timezone) | — |
| Submission ID / receipt | — |
| Submitted repository URL | — |
| Submitted branch / commit | — |
| Tree hash at submit (`git status` + worktree inventory) | — |
| Persistent state hash (`data/state.json` SHA-256 + bytes) | — |
| Submitted video URL | — |
| Submitted track / theme / problem statement | — |
| Submitted project description (exact text) | — |
| Backend suite result at submit | — |
| Frontend suite + build result at submit | — |
| Dependency lockfiles included (names + hashes) | — |
| Evidence artifacts included (names + hashes) | — |
| Archive location (owner-approved) | — |
| Archive hash (post-write verification) | — |
| Secrets handling confirmation (no live secrets in archive) | — |

## Capture procedure (at activation)
1. Freeze: record every field above from live commands (no copy-paste from older reports).
2. Snapshot: exact submitted source + required docs + evidence + video REFERENCE (never re-upload the video file unless the portal requires it) + lockfiles + receipt.
3. Exclude: `.env`, any file with live credentials, `node_modules/`, `.next/`, `__pycache__/`, TEMP-only files (note their absence explicitly).
4. Verify: recompute archive hash after writing; store manifest alongside.
5. Seal: manifest + archive become immutable-by-process; subsequent changes logged as post-submission deltas.
