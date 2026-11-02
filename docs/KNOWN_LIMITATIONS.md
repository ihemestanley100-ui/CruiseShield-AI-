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
- Backend suite 341 passed / 103 skipped / 1 sandbox-blocked
  (2026-11-01 J3 closeout; the blocked node-dependent test is re-proven
  green on an approved unsandboxed rerun); frontend 261/261
  (one transient failure seen in one of two full runs, green on
  immediate rerun — CI watch item); production build exit 0. Skips are
  environmental/optional and never counted as passed.
- Scripted browser sessions verified: 31/31 workflow retest + 69/69 matrix
  (twice re-run, 0 console errors, 0 failed requests). Live UI-driven
  decision submit remains browser-NOT_VERIFIED (API-level verified on
  disposable data).
- JSON file store: single-process; in-process concurrent writes are now
  lock-serialized (PERF-001, 2026-11-01) but multi-worker/multi-process
  writes are still unsafe. Fine for the demo; not a multi-user store.
- Protected-demo login implemented (HMAC sessions, investigator/admin
  roles, CSRF header, login throttle, credentialed CORS) and tested;
  still demo-grade: shared credentials, manual rotation, no tenant
  isolation. API rate limiting (600/min/IP) + login throttle (10/min/IP)
  implemented; cross-process/distributed limits out of scope (single
  worker assumed — demo scale by design, J3-P14).
- False-positive scenario is minimal by design (2 nodes, 1 edge).
- Request body cap (1 MB → 413) is enforced on the declared
  Content-Length only; chunked or length-lying uploads are not
  stream-metered (J3-P14: documented demo-scale boundary, not a
  vulnerability fix — a hostile-body threat model is out of scope).
- P1/P2 backup cryptography, producer, restore, and security gate are
  implemented and scratch-verified (P2.2J, 2026-10-30); production
  enablement (credentials, schedules, 30-day reliability) is intentionally
  absent. V5 enterprise control planes remain deferred (see the hackathon
  blueprint); deferred means absent, not hidden.
- Global text search is OUT OF SCOPE for the hackathon demo (R13,
  2026-10-30): no search box is rendered and none is claimed. Navigation
  uses the sidebar, alert listing, notifications, graph filters, scenario
  picker, and AI follow-up, all of which remain in scope.
- No application-level shutdown/startup handlers (uvicorn default SIGTERM
  handling applies) and no per-route timeout middleware; only the AI
  path has enforced timeouts (30 s server, 35 s client abort). Accepted
  demo scope (J3 closeout, backend EV18) — a stateless single-worker
  demo has no connections to drain.
- The DI-09 AI validator (`build_di_context`/`validate_di_response` in
  `app/intel_ai.py`) is a tested pure-function library with no
  production caller. Wiring it into a live DI-AI path is an owner
  design decision, not scheduled (J3 closeout, AI EV5).
