# PHASE 13 — ASSET AND CODE PROVENANCE

PROGRAMME: CSAI-MASTER-RELEASE-001 | PHASE: 13 | DATE: 2026-11-01
BASE: `docs/HACKATHON_ASSET_AND_CODE_PROVENANCE.md`. This file reconciles it against the current tree (HEAD 0eaaaf5 + working tree).

## Code: greenfield in-window (HOLDS)
- T1: 3 commits, all 2026-10-28, single identity; T2: greenfield baseline record ("only the two spec files"); T3: all source mtimes Oct 28–Nov 1. No third-party code reuse detected (re-scans 11-01 clean).
- Official event page (S1) explicitly welcomes Muse Code AI-assisted coding — AI assistance is not a provenance risk.

## Specifications (pre-existing input — DISCLOSE)
- V5.0 master blueprint text (105301 B, mtime 10-08): sole pre-event artifact; a specification, not code. References external IP (Frontier Enterprise AI Platform™, CruiseTech sections) NOT present in this repo — claim no ownership, disclose the reference (Q-REUSE-1).

## Logo (UNVERIFIED — heightened by S2 ownership clause)
- `frontend/public/assets/cruiseshield-logo-original.png` (1273370 B, high-res) + byte-identical duplicate `cruiseshield-logo-original.png.png` (1273370 B) — duplicate PRESERVED per erratum A2 (do not delete without owner approval).
- Developer asserts original authorship (recorded, NOT independently verified). No license/assignment document on file.
- S2 reports entrants must own everything submitted + grant organizers a broad licence → Q-IP-1 (confirm ownership + submission/press reuse rights) is now the highest-value IP action.
- Meta/Muse marks appear as integration facts/labels only (Q-IP-2: attribution requirements from full rules text).

## Dependencies (declared, not vendored)
- `requirements.txt` + hash-pinned `requirements.lock` (CI `--require-hashes`); installed == pinned (verified 11-01). No vendored third-party code.
- psycopg 3.3.2 (LGPL-3.0) present in requirements/lock/installed for the scratch PG-verification path; JSON remains the active backend. No psycopg code is copied into the repo; Docker image never built. IF a submission/distribution includes a built image with psycopg, LGPL distribution obligations need a qualified read — recorded as a question, not a violation.
- Frontend: Next.js/React/Three.js OSS via package manifests; no license conflicts identified (standard permissive stack).
- Fonts/icons/audio/textures: per base report (no changes in Phases 9–12; no new assets added).

## Data
- Synthetic demo data only (`data/state.json`, git-ignored); no real PII; no external datasets.

## Verdict
Provenance: SUPPORTED for code/build; logo ownership UNVERIFIED (owner action Q-IP-1); LGPL note narrowed to image-distribution scenario.
