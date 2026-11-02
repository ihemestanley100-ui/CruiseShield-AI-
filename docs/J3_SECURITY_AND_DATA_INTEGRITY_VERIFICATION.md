# J3 — SECURITY AND DATA-INTEGRITY VERIFICATION

## Supply chain (project `.venv`, fresh)

- lock_covers_requirements: PASS (16 direct pins locked exactly).
- installed_matches_lock: PASS (37 pins installed exactly).
- lockfile_hashes: PASS (37 pins / 463 sha256).
- pip_check: PASS (no broken requirements).
- secret_scan: PASS (no real-credential shapes; `.env` + state
  excluded by verified `.gitignore`).
- Workflows: 30 `secrets.*` refs, 0 literals (re-counted).
- pip_audit (OSV vuln DB): NOT_VERIFIED — OSV unreachable from this
  sandbox (gate timeout + hung retry, stopped). Static pinning/
  hashing above is the compensating control; run `pip_audit` in CI.

## Auth / session / transport (fresh green suites)

Login/logout/me/mode, HMAC 12 h sessions, PBKDF2 210k, roles,
admin fence, CSRF header, login throttle, credentialed CORS,
Secure incl. proxy (P2), rate limits, 1 MB body cap, secure
headers both tiers, session-expiry re-gate (P6). No CSP (Three.js,
documented); shared demo credentials (documented); single-worker
limits (documented).

## AI governance (fresh green + CI-gated halves)

Server-only key (absence asserted in runs/state/HTML), validated
I/O, evidence-ID allowlist, injection shield (+ hostile
prior_context, closeout), 30 s timeout, daily cap with used/limit
message, bounded retries, failure fallback, no-score/no-guilt/
human-approval gates, byte-identical authoritative state after
hostile runs. Live provider behavior: BLOCKED (R4).

## Data integrity

- `data/state.json` `BA1D4DB4…3790FE` / 101417 B — identical before,
  during, after (3+ independent hash reads, incl. independent pass).
- Determinism: 200× identical, bands + 35/84 pinned, 22n/30e,
  39-item package, audit append-only — all green.
- Every mutating test uses `tmp_store`; no reseed/reset/migration;
  unknown-ID matrix fails closed (9 reads); PG redaction tested
  (`test_dead_database_fails_closed_without_leaking_url`).
- Logos: canonical + 8 icons hashed; no asset modified.
