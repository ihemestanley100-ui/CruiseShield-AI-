# CSG-RELEASE-001 — Repository Reconciliation Register

Source tree: `e099b7a` + 15 uncommitted non-scratch files (5 modified,
3 deleted, 7 new). Nothing staged. No generated files pending.

## A. Required product changes (8) — COMMIT

| Path | Status | Purpose / origin |
|---|---|---|
| `frontend/components/landing/scene/earth.ts` | M | GAT-008: all-hub render, oceans marker, corridor arcs |
| `frontend/components/landing/scene/categories.ts` | new | GAT-008: 8-category registry + route data |
| `frontend/components/landing/scene/corridors.ts` | new | GAT-008: corridor arc builder |
| `frontend/components/landing/GlobeControls.tsx` | M | GAT-008: accessible 8-category list |
| `frontend/components/landing/IntelligenceFrameworkPanel.tsx` | new | Card swap: replacement panel |
| `frontend/components/landing/GlobalLandingPage.tsx` | M | Card swap: render replacement |
| `frontend/styles/framework-panel.css` | new | Card swap: replacement styling |
| `frontend/app/layout.tsx` | M | Card swap: stylesheet import |

## B. Required tests (4) — COMMIT

| Path | Status | Purpose / origin |
|---|---|---|
| `frontend/components/landing/scene/atlas-categories.test.tsx` | new | GAT-008: 12 category tests |
| `frontend/components/landing/LandingContent.test.tsx` | M | GAT-008: uniqueness→pair assertions (accessible equivalent) |
| `frontend/components/landing/IntelligenceFrameworkPanel.test.tsx` | new | Card swap: copy + no-hackathon tests |
| `frontend/components/landing/GlobalHeroScene.strictmode.test.tsx` | new | L-01: StrictMode double-mount lifecycle |

## C. Required documentation — COMMIT (audit trail)

Release evidence under `docs/release/CSG-RELEASE-001/` (this file
included). New files only; no existing doc modified.

## D. Generated artifacts — NONE PENDING

`node_modules/` and `.next/` are gitignored and rebuilt; no generated
file is staged or proposed for commit.

## E. Temporary files — OWNER CLEANUP (8, ACL-locked)

`pip-build-tracker-*` (3), `pip-download-*` (1),
`pip-ephem-wheel-cache-*` (2), `pip-install-*` (2) in repo root.
Side effect of authorized Playwright install. Removal, force-delete
and ownership change all return access-denied. Zero functional impact.
Owner: delete the 8 `pip-*` folders from the repo root with an
administrator shell (`Remove-Item pip-* -Recurse -Force`).

## F. Original protected scratch entries (9) — PRESERVE

`.edge-d-probe/`, `a11y-audit.mjs`, `tmp4moi76l0/`, `tmp4wcoj3ci`,
`tmpbll76ret/`, `tmpqt2d6ldg/`, `tmpu9qsfyky`, `tmpw_ta9ikh/`,
`webgl-fail-r10.html`. Untouched; excluded from every commit.

## Deletions (3, part of card swap) — COMMIT

`HackathonRecognitionPanel.tsx` + test, `hackathon-panel.css`.
Authorized content removal; zero remaining code references (verified
by repo-wide grep; only the new test's negative-assertion regex
mentions hackathon terms).

## Commit plan

- Commit C (atlas): 4 A-files + `atlas-categories.test.tsx` + `LandingContent.test.tsx` hunk.
- Commit D (card): 4 A-files + new card test + 3 deletions.
- Commit E (L-01 evidence): StrictMode test.
- Commit F (release evidence): `docs/release/CSG-RELEASE-001/`.
- Push `feat/phasezero-foundations`; hosted CI verifies the final tree.
