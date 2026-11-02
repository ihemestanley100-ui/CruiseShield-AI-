# UGLS Responsive Layout Audit (Section D)

Date: 2026-11-02 (resume run). Question: what caused the 390px
app-shell clipping (UGLS-02 item X.2), and is any overflow left?

## Root cause

The app-shell topbar (`.topbar` in `frontend/app/globals.css`,
rendered by `frontend/components/app-shell.tsx`) was a non-wrapping
flex row: hamburger + brand + theme switcher + language selector +
notifications + synthetic badge + profile block. At tablet widths the
row exceeded the viewport and the profile block was pushed past the
right edge (observed: `scrollW=805` at viewport 768, offenders
`div.profile`, `.profile-text`, `strong`, `span.muted` —
`responsive-evidence/d-768-en`, `p-768-en`, `q-768-en`).

Attribution: the **existing application shell**, not the language
selector or navigation. The selector is one flex item among eight;
removing it would not have fixed the row. No 390px offender was ever
reproduced by the overflow probe (all 390 captures, pre- and
post-fix, report `offenders: []`); the historical 390 clip
(`d-390-en-before.png`, content text cut at the right edge) dates
from the same pre-fix builds and no longer reproduces.

## Fix (in tree, prior session; verified this session)

`frontend/app/globals.css`, `.topbar`: `flex-wrap: wrap` (comment
tag `UGLS-D`). No other responsive rule changed; `.profile-text`
still hides only at ≤640px, desktop rows still fit on one line.

## Verification (this session, armed + authed)

Fresh sweep, production build, authenticated sessions (the authed
topbar is WIDER than the open-demo one: username, role, two sign-out
buttons), `?locale=` pinned per run:

| width | en offenders/console | ar offenders/console |
| - | - | - |
| 320 | 0 / 0 | 0 / 0 |
| 360 | 0 / 0 | 0 / 0 |
| 390 | 0 / 0 | 0 / 0 |
| 430 | 0 / 0 | 0 / 0 |
| 768 | 0 / 0 | 0 / 0 |
| 800 | 0 / 0 | 0 / 0 |
| 1024 | 0 / 0 | 0 / 0 |
| 1440 | 0 / 0 | 0 / 0 |

Evidence: `responsive-evidence/w-*` (16 captures × 7 files).
`scrollW` equals viewport in all 16; remaining `net.json` entries
are `ERR_ABORTED` only (no 4xx/5xx). Viewed screenshots:
`w-390-ar.png` (RTL mobile: wrapped topbar, Arabic text clean, data
loaded), `w-768-en.png` (tablet: topbar wraps to two rows, profile +
sign-out fully visible), `w-1440-en.png` (desktop unchanged:
topbar fits on ONE row with all eight items).

Probe limits (honest): the overflow probe compares element boxes to
the viewport; it cannot see text painted past a box edge. The three
viewed screenshots above close that gap for 390/768/1440.

## Verdict

**D PASS.** Root cause identified (shell topbar, not selector),
fixed with a one-rule CSS change that leaves desktop untouched, and
verified at 320/360/390/430/768/800/1024/1440 in en + ar under
authenticated sessions. UGLS-02 item X.2 is closed.
