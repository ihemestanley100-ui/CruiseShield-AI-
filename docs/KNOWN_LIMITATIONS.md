# Known Limitations

Honest list of what this slice does not do. Nothing below is presented as
working in the UI.

- Live Meta Model API calls executed and verified (2026-10-29):
  `agentrun_0001`–`agentrun_0004` SUCCEEDED via muse-spark-1.3, schema
  and evidence refs VALIDATED. Each new live call still needs
  `MODEL_API_KEY` + network at demo time; without them the UI shows
  honest error states, never a fake analysis.
- No public deployment yet. Render Docker Blueprint config corrected
  (`0eaaaf5`); image not built, no public URL, no hosted smoke.
- Screenshots captured (CDP matrix runs under %TEMP%\smoke48, %TEMP%\smoke11;
  volatile TEMP). No demo video recorded yet — capture from a local run
  before submission (owner approval required).
- Backend suite 294 passed / 68 skipped / 0 failed (2026-11-01); frontend
  233/233; production build exit 0. Skips are environmental/optional and
  never counted as passed.
- Scripted browser sessions verified: 31/31 workflow retest + 69/69 matrix
  (twice re-run, 0 console errors, 0 failed requests). Live UI-driven
  decision submit remains browser-NOT_VERIFIED (API-level verified on
  disposable data).
- JSON file store: single-process; in-process concurrent writes are now
  lock-serialized (PERF-001, 2026-11-01) but multi-worker/multi-process
  writes are still unsafe. Fine for the demo; not a multi-user store.
- No authentication/authorization, no tenant isolation, no rate limiting.
- False-positive scenario is minimal by design (2 nodes, 1 edge).
- P1/P2 backup cryptography, producer, restore, and security gate are
  implemented and scratch-verified (P2.2J, 2026-10-30); production
  enablement (credentials, schedules, 30-day reliability) is intentionally
  absent. V5 enterprise control planes remain deferred (see the hackathon
  blueprint); deferred means absent, not hidden.
- Global text search is OUT OF SCOPE for the hackathon demo (R13,
  2026-10-30): no search box is rendered and none is claimed. Navigation
  uses the sidebar, alert listing, notifications, graph filters, scenario
  picker, and AI follow-up, all of which remain in scope.
