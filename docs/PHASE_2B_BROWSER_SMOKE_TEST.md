# PHASE 2B — BROWSER SMOKE TEST

**Date:** 2026-10-31 · **Method:** REAL headless Chrome
(`C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`) driven via the
DevTools protocol (remote-debugging-port, one persistent browser, 8 sequential
routes) against live servers — backend uvicorn on 127.0.0.1:8123, frontend
`next dev` on :3110 (`NEXT_PUBLIC_API_BASE_URL` override; `FRONTEND_ORIGINS`
matched). Servers started as background jobs in ONE shell. No login anywhere.

## Execution: PASS · Analysis: COMPLETE

- Backend health `healthy`; frontend `/` and `/demo` HTTP 200 before capture.
  Per route: `Page.captureScreenshot` + `Runtime.evaluate(outerHTML)` + console
  events (`Runtime.consoleAPICalled`, `Runtime.exceptionThrown`, `Log.entryAdded`).
  Run wall time 103 s; servers stopped and jobs cleaned up afterwards.
- Artifacts: `%TEMP%\smoke2j\shot_*.png` (8), `dom_*.html` (8, 28–54 kB),
  `console_*.log` (8), `asserts.txt`, `console_triage.txt`, `status.txt`, `jobs.log`.

## DOM assertions: 18/18 PASS

- landing: hero, ILLUSTRATIVE NETWORK VIEW, Enter Demo, "not live monitoring".
- demo: Executive overview, Evidence records, inv_84721, Synthetic demo data.
- investigations: 35/100 MODERATE, R-001, evidence_rr_R-001_84721.
- network: "22 nodes, 30 edges", Orbital explorer.
- cases: requires_review, AI Investigation Assessment panel, VALIDATED.
- replay: 84/100 HIGH baseline, Deterministic replay.
- Settled DOM shows Transactions monitored = 11 (aria-label + value).

## Console triage: PASS (1 cosmetic hit)

- 7/8 routes: zero errors, zero uncaught exceptions.
- landing: 1 network error — `GET /favicon.ico → 404`. Missing favicon asset
  only; no `Uncaught`, no failed API/data loads, no `ERR_` entries.

## Screenshots: 8/8 inspected (desktop 1440×900 + mobile 390×844)

- `/`: brand + logo, hero, DETECT→PROTECT journey, 9 DEMO-badged capabilities,
  regions panel with honesty note, 3D Earth + brain lattice + orbitals, 5 module
  cards, CTA, motion/audio controls. **WebGL works.**
- `/demo`: nav, quick actions, System Status (healthy), executive overview
  (1 / 11 / 1 / 39 / agentrun_0002 SUCCEEDED / 0), network preview 22/30,
  Muse Spark advisory brief.
- `/investigations/inv_84721`: txn #84721 ₦480,000, 35/100 MODERATE line,
  rules R-001…R-005 with evidence IDs, case link.
- `/network/txn_84721`: 22 nodes / 30 edges, provenance errors 0, orbital
  canvas graph rendered with filters and zoom controls.
- `/cases/case_84721`: NEW status, TRIAGED/FALSE_POSITIVE transitions, full AI
  assessment (requires_review, VALIDATED×2, findings + confidences).
- `/replay/scn_primary`: reset, deterministic replay controls, what-if panel
  with 84/100 HIGH immutable baseline.
- Mobile pair: both render; demo stacks correctly. Mobile landing clips the
  hero heading at the right viewport edge — recorded as R-11 (single-shot
  evidence, needs confirmation; NOT claimed as a defect yet).

## Visual notes carried forward

- R-04 (region label sprites oversized) and R-05 (audio toggle "Sound: Off"
  clipped as "und: Off") are both CONFIRMED at 1440×900. No scene/CSS tuning
  performed — polish needs approval.
- An earlier one-shot screenshot caught a loading state (Transactions 0);
  the settled CDP DOM reads 11. One-shot CLI screenshots race first-compile;
  the CDP set is authoritative.

## Diagnosis: why pre-recovery DOM/console files were all 0 bytes

- Measured: foreground `chrome --headless=new --dump-dom <url>` exits in
  ~16 ms with empty stdout (exit code unset). The launcher process returns
  immediately while rendering continues in a persistent child: file outputs
  (`--screenshot`) survive, but the stdout pipe (`--dump-dom`) is lost, so
  `--dump-dom` can never yield bytes in this environment. All 8 pre-recovery
  runs (smoke2b…2h) hit this; none produced a DOM byte.
- Fix applied: persistent browser + CDP `Runtime.evaluate` (result returned
  over the protocol, written to file by the driver) and protocol console
  events. First attempt after the fix captured all 8 routes cleanly.
- No user browser processes were touched: 62 running chrome/msedge processes
  carried no smoke-test markers and were left alone; only job-owned
  uvicorn/`next dev` processes from this task were stopped.

## Coverage honesty

- Claimed: real-browser render + DOM assertions + console triage on all 8
  viewports, favicon 404 disclosed, WebGL proof, loading-state caveat.
- NOT claimed: interaction testing (clicks/inputs need a driver, unavailable),
  mobile horizontal-overflow proof (one static observation only, R-11),
  FPS/load measurements.
