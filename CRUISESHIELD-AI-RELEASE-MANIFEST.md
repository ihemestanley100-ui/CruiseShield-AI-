# CRUISESHIELD-AI-RELEASE-MANIFEST.md

Release manifest for the working tree (2026-11-05, branch
`feat/phasezero-foundations` @ `b4732cb`). 190 status entries:
71 modified, 119 untracked paths (dirs count once).

BASELINE NOTE: an earlier count read 162; only 5 of the +28 are
this slice's new files. No per-entry baseline was captured at
162, so the remainder is unattributed — capture `git status`
before/after every slice from here on. Nothing was staged,
committed, or deleted by this slice (scratch scripts removed).

## Dispositions

| Group | Entries | Disposition | Rationale |
|---|---|---|---|
| app/ modified (16) + new industries.py | 17 | INCLUDE (C1) | Product source; suite green |
| tests/ modified (18) + new (8 + fixtures/) | 27 | INCLUDE (C1) | Tests + canonical fixture |
| frontend/ modified (10) + page.test new | 11 | INCLUDE (C1) | Batch 1.1 + tests |
| templates/, static/ | 2 | INCLUDE (C1) | Served legacy UI |
| render.yaml, .env.example, security-gate.yml, .gitattributes | 4 | INCLUDE (C1) | Deploy/test config; review render.yaml diff |
| docs/ modified (20: matrices, registers, TSVs) | 20 | INCLUDE (C3) | Live registers + i18n review kit |
| Root CRUISESHIELD-AI-*.md + HACKATHON_CONTRIBUTIONS (15) | 15 | INCLUDE (C2) | Audit/evidence chain |
| docs/ new reports (~100) | ~100 | INCLUDE (C3) | Evidence/cert batches; secret-clean |
| qa-scratch/data/state.json (tracked, modified) | 1 | REVIEW | Scratch data is tracked; needs owner call (ignore+untrack vs keep) |
| tmpbll76ret/, tmpw_ta9ikh/, .edge-d-probe/ | 3 | EXCLUDE | Scratch/probe dirs, never ship |
| browser-evidence/cert-*/ (4), qa/, webgl-fail-r10.html | 6 | EXCLUDE | Bulk QA artifacts; keep local |
| a11y-audit.mjs (root script) | 1 | REVIEW | Keep (move to scripts/?) or exclude |

Proposed commits: C1 product+tests+config; C2 root audit docs;
C3 docs batches. No commit without owner approval.

## Secret check

- `secret_scan`: PASS on this tree (2026-11-05 gate rerun).
- `.env`, `.env.arming.local`: present on disk, absent from
  status → ignored, never staged. No credentials in C1–C3 sets.

## Full status listing (2026-11-05)

```
M .env.example
M .github/workflows/security-gate.yml
M README.md
M app/ai_adapter.py
M app/auth.py
M app/cases.py
M app/config.py
M app/db.py
M app/device_intel.py
M app/events.py
M app/evidence.py
M app/main.py
M app/models.py
M app/models_pg.py
M app/ratelimit.py
M app/risk_intel.py
M app/rules.py
M app/seed.py
M app/store.py
M docs/DEMO_TOKEN_ENDPOINT_AUTHORIZATION_MATRIX.md
M docs/DEMO_TOKEN_SECURITY_REMEDIATION_PLAN.md
M docs/FINAL_DEPLOYMENT_GATE_REGISTER.md
M docs/FINAL_DEPLOYMENT_VERIFICATION.md
M docs/FINAL_GIT_RELEASE_MANIFEST.md
M docs/FINAL_ZERO_GAP_MATRIX.md
M docs/META_AI_INTEGRATION_AUDIT.md
M docs/RENDER_6_ENV_REGISTER.md
M docs/UGLS_KEY_INVENTORY_GENERATED.txt
M docs/UGLS_REVIEW_KIT/ar.tsv (+es,fr,ha,hi,ig,ja,pt,sw,yo,zh)
M frontend/app/cases/[caseId]/page.test.tsx + page.tsx
M frontend/app/investigations/[id]/page.test.tsx + page.tsx
M frontend/app/network/[txnId]/page.test.tsx + page.tsx
M frontend/components/intel-panels.test.tsx + intel-panels.tsx
M frontend/lib/api.test.ts + api.ts
M qa-scratch/data/state.json
M render.yaml
M static/app.js
M templates/base.html
M tests/conftest.py + test_ai_validation + test_api_flow
M tests/test_auth + test_auth_e2e + test_cases_audit
M tests/test_config_safety + test_cors + test_demo_token_remediation
M tests/test_di03_device + test_flow_direct + test_j5_rehearsal
M tests/test_j6_drill + test_pg_atomic_decision + test_pg_hardening
M tests/test_pg_migration + test_pg_parity + test_seed_reset
?? .edge-d-probe/ + .gitattributes + a11y-audit.mjs
?? CRUISESHIELD-AI-*.md (14 root docs) + HACKATHON_CONTRIBUTIONS.md
?? app/industries.py
?? browser-evidence/cert-{frc,v3,zg,zgep}/
?? docs/B1_*,B2_*,B3_* (6) + CRUISESHIELD_* (17) + CRUISE_ORBIT_* (12)
?? docs/CS_FINAL_* (13) + WORLD_ATLAS_* (12) + audit/cert misc (~40)
?? docs/OPERATIONS_RUNBOOK.md
?? frontend/app/page.test.tsx
?? qa/ + tests/_integrity.py + tests/fixtures/
?? tests/test_ai_eval + test_canonical_fixture + test_deploy_manifests
?? tests/test_homepage_routing + test_industries + test_notifications
?? tmpbll76ret/ + tmpw_ta9ikh/ + webgl-fail-r10.html
```

(Compressed from the verbatim `git status --short`; full output
retained in session record.)
