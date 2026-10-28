# Known Limitations

Honest list of what this slice does not do. Nothing below is presented as
working in the UI.

- Live Meta Model API call not yet executed: `MODEL_API_KEY` was absent in
  this sandbox (and sandbox network is blocked). Adapter, validation, and
  provenance UI are implemented and unit-tested; the live call is BLOCKED.
- No public deployment from this sandbox (no network; Node-based Vercel CLI
  broken here). `Dockerfile` provided for user-side deploy; image not built.
- No screenshots or demo video captured (headless sandbox). Capture from a
  local run before submission.
- HTTP-transport tests (TestClient) skip here (socket creation forbidden);
  identical flow verified socket-free. They run in CI/user environments.
- Interactive-JS behavior (graph clicks, forms) verified by code + API tests,
  not yet by a real browser session.
- JSON file store: single-process, no concurrent-writer locking beyond atomic
  replace. Fine for the demo; not a multi-user store.
- No authentication/authorization, no tenant isolation, no rate limiting.
- False-positive scenario is minimal by design (2 nodes, 1 edge).
- All P1/P2 items and V5 enterprise control planes are deferred (see the
  hackathon blueprint); deferred means absent, not hidden.
