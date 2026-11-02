# UGLS Browser Verification (Section C)

Date: 2026-11-02 (resume run). Same armed QA stack as the session
audit. All testing below is genuine headless-Edge testing over CDP:
screenshots, DOM, console errors, and failed-request capture per page
(`cdp-capture.mjs`), plus a trusted-mouse/keyboard interaction driver
(`cdp-interact.mjs`). Evidence: `browser-evidence/`
(34 files), `auth-evidence/`, `responsive-evidence/w-*`.

## Results

| # | Requirement | Status | Evidence |
| - | ----------- | ------ | -------- |
| C1 | Genuine browser-based testing | PASS | 30+ Edge captures this session (armed), CDP console+network listeners on every capture |
| C2 | Console errors captured | PASS | `.console.json` per capture; logged-out 401 lines, authed runs 0 errors (see matrix) |
| C3 | Network failures captured | PASS | `.net.json` per capture; authed failures are `ERR_ABORTED` only (RSC/React aborts), plus one documented 403 (below) |
| C4 | English, French, Arabic verified | PASS | en (14+ captures), ar (14+ captures, RTL), fr (`fr-demo`, `fr-inv` authed, `b1-gate-fr` gate): 0 console errors, correct `lang`/`dir` |
| C5 | Mobile, tablet, desktop verified | PASS | Armed sweep 320/360/390/430/768/800/1024/1440 × en+ar: 0 offenders, 0 console errors (see responsive audit) |
| C6 | Dropdown interaction verified | PASS | `i1-selector` VERDICT=PASS: trusted click opens (221 options, dialog+combobox roles, search focused), "ara" filters to 17, arrow+Enter selects `an` (lang+stored agree), panel closes, focus returns to button; outside click closes. `i1-selector-open.png` shows the open panel (native scripts + fallback badges) |
| C7 | Keyboard behaviour verified | PASS | ArrowDown moves `aria-activedescendant`, Enter selects, Escape closes with focus return — all via real `Input.dispatchKeyEvent`, recorded in `i1-selector.interact.json`. Screen-reader RUNTIME check remains human-only (see limitation L2) |
| C8 | RTL on critical routes | PASS | ar RTL verified authed on demo, investigations, network (`rtl-ar-network` 0/0), replay, cases-audit (`b3-b-audit` 0/0); `dir=rtl`, `lang=ar` in every doc record |
| C9 | Reproducible screenshots + logs | PASS | Every capture = png + dom.html + doc/overflow/console/net/phases JSON; backend logs `be-qa-resume*.log`; repro commands in this repo (`cdp-*.mjs` usages) |

## Observations (not language defects)

- O1: `/api/v1/demo/scenarios` returns 403 `ADMIN_REQUIRED` for the
  auditor on the replay page (`rtl-ar-replay`: 1 console line, 1 net
  entry). The page renders an honest permission error card; other
  sections load. Identical in every locale — pre-existing role-gating
  UX, out of UGLS scope, no action taken.
- O2: `net.json` entries on healthy authed pages are exclusively
  `net::ERR_ABORTED` (Next.js `?_rsc=` prefetch aborts and React
  refetch aborts on unmount/locale switch). Client-side aborts, not
  server failures; data renders in every case (DOM lengths 22–40 KB).

## Limitations

- L1: Screen-reader runtime behaviour (NVDA/VoiceOver) cannot be
  automated here. Static ARIA evidence is strong (dialog, combobox
  with `aria-activedescendant`, listbox `aria-selected`, labelled
  button, `role=status` live regions, focus return on close — all
  recorded live in `i1-selector.interact.json`), and keyboard
  operation is fully verified; a human SR pass stays owner-side.
- L2: Interaction coverage is the language selector (the UGLS
  surface). Other controls were exercised only by navigation +
  render, not by synthetic events.

## Verdict

**C1–C9 PASS** (C7 runtime-SR human check disclosed). EN/FR/AR,
mobile/tablet/desktop, dropdown + keyboard interaction, and RTL on
all critical routes are browser-verified with reproducible evidence.
