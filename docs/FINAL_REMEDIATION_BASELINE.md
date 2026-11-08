# FINAL REMEDIATION BASELINE — CS-FRC-2026-001

- Date: 2026-11-04. Branch: `production-launch`.
- HEAD = origin/production-launch = `ff7052bdf0ac48a68f69c3937d9b8708ca265354`.
- Tree: **62 modified + 85 untracked = 147 entries**, all preserved. No stash,
  reset, clean, checkout, or commit performed or planned without owner approval.

## Modification groups (detail: PUBLIC_REPOSITORY_RELEASE_MANIFEST.md)

- Backend source (4): `app/ai_adapter.py`, `app/config.py` (AI_MAX_OUTPUT_TOKENS,
  this stage), `app/main.py`, `app/store.py` (prior sessions).
- Backend tests (3): `test_ai_validation.py`, `test_config_safety.py` (this
  stage), `test_notifications.py` untracked (prior).
- Frontend source+tests (~35 modified, 7 untracked): landing/Atlas, i18n
  locales, notifications, api, audio, styles (prior sessions; verified green).
- i18n kit (12): regenerated TSVs + inventory (this stage).
- `render.yaml`, `frontend/.env.example` (B1 wording, prior).
- Docs: 5 modified (gate register, manifests, matrix, 2 audit addenda) + ~60
  untracked reports/evidence (prior sessions + this stage's 7).
- Excluded-by-policy scratch: `qa/`, `qa-scratch/`, `.edge-d-probe/`,
  `tmpw_ta9ikh/`, `a11y-audit.mjs`, `webgl-fail-r10.html`,
  `browser-evidence/cert-v3/`, `docs/UGLS_REVIEW_KIT` regenerated content stays.

## Files owned by this execution

Only: the 3 new docs (§01 baseline=this file, §08 manifest, §13 remediation
report), dated addenda to the 7 authoritative audit docs, evidence-register
rows, matrix row J11-33, and ONE config edit (`render.yaml`: declare
`AI_MAX_OUTPUT_TOKENS`, value = code default, behavior-neutral).

## Explicitly excluded from modification

`data/state.json` (byte-pristine), any secret/credential, `.venv/`,
`node_modules/`, production Render config, Git history/branches, user-owned
running processes (:8000/:3000), all prior-session source work.

## Known defects carried in

S-01 unarmed live backend; S-02 live R1–R4 unverified; S-03 postcss residual;
S-04 render.yaml var gap (to be closed for AI_MAX_OUTPUT_TOKENS); Windows
file-lock test flakes (~1/run, all pass on re-run); P05 Meta BLOCKED (paid-only).

## Backup and recovery

Every change is an uncommitted working-tree edit — `git diff` is the complete
reversible patch. Live verifications run against temp `DATA_DIR` copies or
read-only GETs. Any regression: revert only this execution's files, never a
tree-wide reset.
