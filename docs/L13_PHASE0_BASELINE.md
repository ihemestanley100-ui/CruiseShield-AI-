# L13 PHASE 0 FORENSIC BASELINE — CruiseShield AI™

Date: 2026-11-06. Read-only inspection; no source, data, or Git
mutations were made to produce this baseline. All counts below were
measured, not carried over from earlier reports.

## 1. Baseline identifiers

- Branch: `feat/phasezero-foundations` (no upstream; already a
  feature branch, so Part 22 rule 7 is satisfied without creating
  another branch).
- HEAD: `d82627d77592160875c53f4a35c956632a994231`.
- Worktree: 143 modified + 2 deleted + 227 untracked = 372 lines
  (`git status --short`; +1 vs the simulations slice = this
  program's new packages doc).
- `data/state.json` SHA-256:
  `BA1D4DB4BB4DBC6FC3ACA346664A539610CCC6460CCD530F523C8043453790FE`
  (unchanged).
- Matrix: `docs/ZERO_GAP_MATRIX.json` 85 rows valid (72
  CLOSED_VERIFIED / 4 IN_PROGRESS / 3 BLOCKED_EXTERNAL_DEPENDENCY /
  6 AWAITING_OWNER_APPROVAL).
- Inventory: `docs/FORENSIC_INVENTORY.json` matches (1111 tracked
  files, 89 API routes, 1068 backend tests, 7 frontend pages).

## 2. Coverage inventory (measured)

| Area | Count | Source |
|---|---|---|
| Backend API routes (APIRoute) | 89 | forensic inventory |
| Frontend pages (`page.tsx`) | 7 | forensic inventory |
| Backend tests collected | 1068 | `pytest --collect-only` |
| `app/*.py` modules | 83 | filesystem |
| Industry registry entries | 45 | matrix validator enforces 45 IND rows |
| Dependency manifests present | 7/7 | inventory (requirements, lockfiles, Dockerfile, render.yaml, netlify.toml) |
| Env names documented | 38 backend + 3 frontend | `.env.example` files (names only) |

Canonical stores: JSON file store ACTIVE (`STORE_BACKEND=json`
default); PostgreSQL adapter exists (`app/db.py`,
`app/models_pg.py`, `migrations/loader.py`) for scratch
verification only — no competing canonical DB; cutover gated on
GAP-001/DB-01 owner approval.

## 3. Demo-identity search report (Part 1.1 evidence)

Method: case-insensitive regex `demo` over production code areas,
then exact banned-phrase scan over shipped user strings. Verdicts use
these dispositions: REMOVE (user-facing product concept),
COMPAT (identifier/contract that must keep its name),
PENDING (approved removal path already exists), INTERNAL
(never user-facing), HISTORICAL (evidence history, preserved).

### 3.1 Production code (`app/`, frontend lib, templates, migrations, scripts)

| Location | Occurrences | Disposition |
|---|---|---|
| `app/auth.py`, `app/config.py`, `app/abac.py`, `app/main.py`: `DEMO_USERS`, `DEMO_WRITE_TOKEN` env names + readers | 12 refs | COMPAT — deployment contracts, R5/R6 owner-approved; renaming breaks Render config without approval |
| `app/auth.py`, `app/cases.py`: `demo_viewer` / `DEMO_VIEWER` role | 5 refs | COMPAT — API/session-internal; verified zero occurrences in locales, `frontend/app`, `frontend/components` (no UX leak) |
| `app/main.py`: 4× `/api/v1/demo/*` deprecated aliases + admin prefix entry | 5 refs | PENDING — REL-02/D-019b removal approved for post-deploy-verified |
| `frontend/lib/api.ts:273` `NEXT_PUBLIC_DEMO_WRITE_TOKEN` read | 1 ref | COMPAT — R6: stays empty, header omitted; owner-approved |
| `app/device_intel.py:30`, `scripts/perf_smoke.py:3` comments ("demonstration", "demo-scale") | 2 refs | INTERNAL — prose comments, zero product surface |
| `app/seed.py` purpose strings ("Demonstrate…") | 1 user-visible word | INTERNAL — proven unrendered: `available_scenarios()` returns id+title only; no template/API/frontend reads `.purpose`; scenario titles clean |
| `scripts/zero_gap_matrix.py` row statements (SEC-R1…R6, REL-02) | 8 refs | HISTORICAL — immutable register history |
| `frontend/app`, `frontend/components` (non-test), `templates/`, `migrations/` | 0 | CLEAN |
| Frontend test files (4× `*.test.*`) | fixture use | INTERNAL — isolated test doubles |

### 3.2 Banned product phrases in shipped user strings

Scanned `frontend/lib/i18n/locales/en.ts`, `frontend/app/**`,
`templates/**` for: live demo, explore demo, demo sign-in, demo
dashboard, demo mode, demo account, demo credentials, synthetic
demo, demo-only, demo trial. Result: ZERO matches. I18N-01 holds
for EN. (Other 11 locales: machine-migrated, human review pending
per I18N-02 BLOCKED — unchanged known limitation.)

Honest synthetic-data disclosure (banner, seed docs, API
`synthetic_data_flag`) is RETAINED by design: removing it would
violate the never-present-fixtures-as-real-records rule.

### 3.3 Active docs and configuration

| Location | Finding | Disposition |
|---|---|---|
| `README.md` | Hackathon-era product positioning was present; rewritten 2026-11-06 (platform title, honest synthetic disclosure kept, current 924/141 test evidence, evaluation walkthrough, accurate security limits) | REMOVED — verified zero `demo` matches + hygiene gate `tests/test_product_identity.py` (2 green) |
| `frontend/README.md`, `docs/ARCHITECTURE.md`, `netlify.toml`, `Dockerfile` | 0 matches | CLEAN |
| `.env.example`, `render.yaml` | Config-contract names + accurate comments | COMPAT |
| `tests/` (19 files + 1 fixture) | `DEMO_*` config, remediation tests, `demo-pass-1` fixture passwords | INTERNAL — isolated fixtures, permitted |
| Historical docs (`docs/`, root `*.md`, logs) | Extensive `demo` residue across phase reports | HISTORICAL — evidence history; never rewritten |

Part 1.1 acceptance status: MET for production code paths,
shipped UI strings, and active product docs (README rewrite +
gate, 2026-11-06); every remaining occurrence carries the
disposition above. Non-EN locale human review still pending per
I18N-02 (unchanged).

## 4. Duplication report (Part 21 gate 1)

Method: exact-SHA grouping over the 1111 tracked files in
`FORENSIC_INVENTORY.json`. Result: 42 identical groups, ZERO in
production source:

- 39 groups: QA evidence JSON/PNG captures (identical pass/empty
  artifacts across viewports — legitimate per-capture records).
  Disposition: RETAIN as evidence; EXCLUDE from release manifest.
- 1 group: `frontend/app/icon.png` =
  `frontend/public/icons/favicon-32x32.png` (legitimate asset reuse;
  Next.js convention). RETAIN.
- 2 groups: root `*.log` pairs with identical content (old run
  logs). RETAIN as history; EXCLUDE from release manifest.

No duplicate files under `app/`, frontend source, `migrations/`,
`scripts/`, `tests/`, or `templates/`. Near-duplicate families are
intentional registries (`app/industries_*.py` 45 profiles,
`tests/test_industry_*.py`), each with distinct tested content.

## 5. Secrets and security baseline

- Offline gate (`python scripts/security_gate.py --skip-audit`):
  secret_scan PASS, lockfile_hashes PASS (37 pins / 463 hashes),
  lock-covers-requirements PASS; installed-matches-lock FAIL and
  pip_check FAIL reproduce the known shared-interpreter signatures
  (drift + moviepy/pillow), unchanged, no new deps. Overall GATE
  FAIL on those two environmental items only.
- Tracking hygiene: `.env`, `.env.arming.local`, `data/state.json`
  all git-ignored (verified via `git check-ignore`). No
  `id_rsa`/`.pem`/key material tracked.
- One tracked state snapshot: `qa-scratch/data/state.json`
  (tracked since `753a6c5`, pre-existing). Scanned: zero secret
  shapes (no pbkdf2/private keys/tokens/passwords), synthetic seed
  only. Disposition: TRACKED-FIXTURE; release-manifest decision
  deferred to PKG-06 (presumption: exclude as scratch).

## 6. Phase 1 register reconciliation (Part 20 schema)

The canonical requirements register REMAINS `docs/ZERO_GAP_MATRIX.json`
(85 rows; Part 22 rule 13 — one register, no reset). Field mapping
to the Part 20 schema:

| Part 20 field | Existing field | Gap |
|---|---|---|
| Requirement ID | `id` | none |
| Domain | derivable from ID prefix (DET/SEC/TEN/AUD/…) | not yet materialized; derive in generator when a consumer needs it |
| Requirement | `statement` | none |
| Priority | `priority` (P0/P1/P2) | naming differs from Critical/high/medium/low; mapping P0=Critical, P1=high, P2=medium is recorded here, not renamed |
| Implementation path | `implementation` | none |
| Test path | `test` | none |
| Dependency | `dependencies` | none |
| Owner | `owner` | none |
| Status | `status` | vocabulary differs; current 8-state set retained (NOT_STARTED/IN_PROGRESS/…/CLOSED_VERIFIED); Part 20 VERIFIED ≡ CLOSED_VERIFIED |
| Evidence | `evidence` | none |
| Acceptance criterion | `acceptance` | none |
| Last verified commit | `commit` | partial: some rows carry WORKTREE (uncommitted) honestly; resolved at release commit |
| Residual risk | — | MISSING: tracked per-risk in `CRUISESHIELD-AI-RAID-LOG.md` (RSK-*) instead of per-row; no per-row backfill without evidence |

No register was reset, renamed, or duplicated. New L13 work items
enter the matrix as new rows only when they name a distinct,
testable requirement with an owner.

## 7. Blocked and owner-gated items (pointer, not duplicate)

All execution blockers live in
`docs/LEVEL14_OWNER_APPROVAL_PACKAGES.md` (PKG-01…PKG-07, all
AWAITING OWNER): push/PR/CI, deploy identity, arming + live R1–R4,
Meta live-call decision, financial readings + overage call, license
+ manifest rule, and the D-014/D-018/GAP-001/D-020/D-019b batch.
This program proceeds only with unblocked work.

## 8. Next implementation batches (dependency order)

1. B-L13-01 (DONE 2026-11-06): README product-identity rewrite +
   `tests/test_product_identity.py` hygiene gate (Part 1.1, Part 21
   gate 5). Docs + one new test file; zero behavior change. Full
   backend 926 passed / 141 skipped, same sandbox-only 1F+2E.
2. B-L13-02 (DONE 2026-11-06): audit export + verification report
   (`verification_report` + `scripts/audit_export.py`; 10 tests;
   AUD-02 closed). Caller-supplied keys only; no production keys.
3. B-L13-03 (DONE 2026-11-06): backup drill re-verified exit 0 +
   parity (csbk-20261106-021504Z); BAK-01 non-ceremony remainder
   holds pending D-018.
4. B-L13-04 (DONE 2026-11-06): unknown-location login-risk
   scoring (app/login_risk.py + store baselines + login
   wire-in; 12 tests; SEC-RISK closed). Baseline learns on
   password success only; low keeps the exact login body;
   digests/hour buckets only, no raw IP/UA, no GeoIP.

5. Owner-gated remainder: D-014 map, PG cutover, ceremony-backed
   audit/backup closure, push/PR/CI, deploy, live AI, license.

Branch note: all work stays on `feat/phasezero-foundations`;
no new branch created (rule 7 intent already satisfied), no
staging/committing/pushing (rule 29 + standing owner gate).
