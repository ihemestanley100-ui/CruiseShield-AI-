# J3 — 165-ITEM AUDIT RECONCILIATION MATRIX

**Source recovered:** all 5 worker + critic + synthesis submissions
extracted verbatim from this session's subagent logs
(`.../subagent/<id>/session.jsonl`, `submit_result` payloads:
backend-api 32 + frontend-ux 45 + engine-data 41 + ai-governance 24 +
docs-provenance-git 23 = 165, all `complete:true`).
**Closeout rule:** no item is PASS on auditor authority — every PASS
below names fresh closeout evidence (code read + test run this turn).

**Closeout totals:** 151 PASS · 7 PARTIAL (4 CI-gated, 1 env-gated,
2 owner-gated) · 2 BLOCKED (R5 staging) · 1 NOT_VERIFIED (R4/R5
quotas) · 4 NOT_APPLICABLE (documented non-defects) · 0 FAIL.

IDs: BE/AI/EN/FE/DC + worker EV number. Orig = auditor verdict.

## Backend-api (32): 29 PASS · 2 BLOCKED · 1 NOT_APPLICABLE

| ID | Finding | Orig | P-map | Fresh closeout evidence | Result |
|----|---------|------|-------|-------------------------|--------|
| BE-00 | health/ready contract | NOT_VERIFIED | P9 | direct twins: `test_pages_render…`(health) + new `test_ready_envelope_direct`; transport twins CI-gated | PASS |
| BE-01 | auth login/logout/me/mode | PASS | — | `test_auth.py` green in fresh full run (341/103) | PASS |
| BE-02 | demo list/reset/start, reset errors | PARTIAL | P9+closeout | new `test_demo_reset_unknown_scenario_404_direct` (reset+start 404); role gates pre-existing | PASS |
| BE-03 | core reads + UNKNOWN_* | NOT_VERIFIED | P9 | `test_full_judge_flow_direct` + `test_unknown_ids_404_direct` green | PASS |
| BE-04 | device/IP/geo reads | NOT_VERIFIED | — | di03–di09 suites: 104 passed fresh (worker hadn't read them) | PASS |
| BE-05 | intel overlay | NOT_VERIFIED | — | `test_di07_graph.py` green fresh | PASS |
| BE-06 | evidence/AI routes | NOT_VERIFIED | P9 | direct twins + `test_ai_validation` 24 passed fresh | PASS |
| BE-07 | replay/sim/events | PARTIAL | P9 | direct twins green; events suite green | PASS |
| BE-08 | error envelope extent | PARTIAL | P9 | 404/400 matrix direct + 429/413 pre-existing | PASS |
| BE-09 | session_guard open/gated | PASS | — | fresh green | PASS |
| BE-10 | admin-only demo routes | PASS | — | fresh green | PASS |
| BE-11 | CSRF header gate | PASS | — | fresh green | PASS |
| BE-12 | PBKDF2/HMAC sessions | PASS | — | fresh green | PASS |
| BE-13 | login throttle | PASS | — | fresh green | PASS |
| BE-14 | write-token session-bypass untested | PARTIAL | closeout | new `test_valid_session_satisfies_gate_without_token` green | PASS |
| BE-15 | per-IP rate limit | PASS | — | fresh green | PASS |
| BE-16 | body cap 413 | PASS | — | fresh green | PASS |
| BE-17 | AI cap/timeout | NOT_VERIFIED | P8 | `test_ai_cost.py` green fresh; mapping matrix = AI-09/P8 CI-gated | PASS |
| BE-18 | no per-route timeouts/shutdown | NOT_VERIFIED | — | verified absent in code; accepted demo scope, documented KNOWN_LIMITATIONS (stateless worker, uvicorn SIGTERM) | NOT_APPLICABLE |
| BE-19 | CORS allowlist/credentials | PASS | — | `test_cors.py` fresh green | PASS |
| BE-20 | secure headers | PASS | — | fresh green | PASS |
| BE-21 | reseed warning unasserted | PARTIAL | — | warns-before-reseed test exists (`test_seed_reset.py`), green fresh | PASS |
| BE-22 | persistence selection | NOT_VERIFIED | — | `open_store` json/pg/require-url tests (`test_pg_migration.py`), green fresh | PASS |
| BE-23 | container bind | NOT_VERIFIED | R5 | static only (Dockerfile verified); runtime bind needs staging | BLOCKED |
| BE-24 | render.yaml deploy | NOT_VERIFIED | R5 | blueprint corrected + YAML-parsed; provisioning needs approval | BLOCKED |
| BE-25 | FE-auth endpoint coverage | PARTIAL | P9 | covered by BE-00/BE-03 twins | PASS |
| BE-26 | scoped route tests missing | FAIL | P9 | direct twins green here; transport twins CI-gated | PASS |
| BE-27 | demo-token frontend exposure | PARTIAL | — | accepted risk, documented (`frontend/.env.example`, render.yaml, RENDER_6); gate tested | PASS |
| BE-28 | SESSION_SECRET/DEMO_USERS handling | PASS | — | fresh green | PASS |
| BE-29 | Secure cookie behind proxy | FAIL | P2 | 3 cookie tests green fresh | PASS |
| BE-30 | PG timeout int() crash | FAIL | P1 | `test_config_safety.py` (3) green fresh | PASS |
| BE-31 | secret redaction | PARTIAL | — | `test_dead_database_fails_closed_without_leaking_url` + `test_secret_safety.py` green fresh (worker hadn't read them) | PASS |

## AI-governance (24): 20 PASS · 4 PARTIAL

| ID | Finding | Orig | P-map | Fresh closeout evidence | Result |
|----|---------|------|-------|-------------------------|--------|
| AI-00 | key server-side only | PASS | — | fresh green | PASS |
| AI-01 | followup validation pre-provider | PASS | — | fresh green | PASS |
| AI-02 | output schema gates | PASS | — | fresh green | PASS |
| AI-03 | evidence-ID allowlist | PASS | — | fresh green | PASS |
| AI-04 | banned score fields | PASS | — | fresh green | PASS |
| AI-05 | DI validator unwired | PARTIAL | — | confirmed test-only; pure-function library as designed — production wiring is an owner design decision, documented | PARTIAL |
| AI-06 | envelope parsing | PASS | — | fresh green | PASS |
| AI-07 | daily cap enforced | PASS | — | fresh green | PASS |
| AI-08 | persistent attempt counting | PASS | — | fresh green | PASS |
| AI-09 | TimeoutException mapping untested | PARTIAL | P8 | passthrough+abort local-green; mapping test loop-gated, runs CI | PARTIAL |
| AI-10 | bounded retries | PASS | — | fresh green | PASS |
| AI-11 | AIError codes end-to-end | PARTIAL | P8 | 4 codes local-green; 5 more loop-gated, run CI; provider-429→503 is intended (client-quota 429 vs provider-failure 503) | PARTIAL |
| AI-12 | panel error display | PASS | — | 261/261 frontend green | PASS |
| AI-13 | FAILED masks SUCCEEDED | PARTIAL | P5 | skip-non-SUCCEEDED test green fresh | PASS |
| AI-14 | followup quoting | PASS | — | fresh green | PASS |
| AI-15 | injection fails closed | PASS | — | fresh green | PASS |
| AI-16 | prior_context breakout untested | PARTIAL | closeout | new `test_hostile_prior_context_cannot_forge_structure` green | PASS |
| AI-17 | usage persistence untested | PARTIAL | closeout | new missing-usage test green; run-persistence test loop-gated, runs CI | PARTIAL |
| AI-18 | quota visibility absent | FAIL | P7 | used/limit+reset message tests green fresh | PASS |
| AI-19 | model cannot set scores/guilt | PASS | — | fresh green | PASS |
| AI-20 | near-miss guilt language | PARTIAL | P14 | six-phrase block works as specified + tested; widening is design, documented | PASS |
| AI-21 | ai-runs GET untested | NOT_VERIFIED | P9+closeout | 404 twins pre-existing; new `test_ai_run_read_roundtrip_direct` green | PASS |
| AI-22 | analysis unknown-inv untested | NOT_VERIFIED | P9 | direct twin green | PASS |
| AI-23 | followup POST no timeout | FAIL | P4 | dedicated abort + hang test green | PASS |

## Engine-data (41): 38 PASS · 3 NOT_APPLICABLE

| ID | Finding | Orig | P-map | Fresh closeout evidence | Result |
|----|---------|------|-------|-------------------------|--------|
| EN-00 | 8 rules deterministic, 200× | PASS | — | fresh green | PASS |
| EN-01 | txn/network scopes + formula | PASS | — | fresh green | PASS |
| EN-02 | unknown-txn StopIteration leak | PARTIAL | P3 | UNKNOWN_TXN guard + boundary test green | PASS |
| EN-03 | scores pinned 35/84 | PASS | — | fresh green | PASS |
| EN-04 | candidate engine isolated | PASS | — | fresh green | PASS |
| EN-05 | 22n/30e graph + provenance | PASS | — | fresh green | PASS |
| EN-06 | provenance validator + BFS order | PASS | — | fresh green | PASS |
| EN-07 | transaction features | PASS | — | fresh green | PASS |
| EN-08 | DI-07 overlay derived-only | PASS | — | fresh green (104 intel tests) | PASS |
| EN-09 | device intel | PASS | — | fresh green | PASS |
| EN-10 | IP intel | PASS | — | fresh green | PASS |
| EN-11 | geo intel | PASS | — | fresh green | PASS |
| EN-12 | intel linkage | PASS | — | fresh green | PASS |
| EN-13 | 39-item evidence package | PASS | — | fresh green | PASS |
| EN-14 | find_unknown_ids untested | NOT_VERIFIED | P11-b | new `test_find_unknown_ids_flags_model_cited_forgeries` green | PASS |
| EN-15 | DI-09 evidence translation | PASS | — | fresh green | PASS |
| EN-16 | reset seeds alert+case+audits | PASS | — | fresh green | PASS |
| EN-17 | case machine | PASS | — | fresh green | PASS |
| EN-18 | append-only audit | PASS | — | fresh green | PASS |
| EN-19 | DETECT→AUDIT chain | PASS | — | judge-flow direct green | PASS |
| EN-20 | replay cursor 11/11/30 | PASS | — | fresh green | PASS |
| EN-21 | store multiprocess collision | PARTIAL | P14 | single-worker demo scope, documented; in-process race-tested | NOT_APPLICABLE |
| EN-22 | reseed warns | PASS | — | fresh green | PASS |
| EN-23 | ingest idempotent | PASS | — | fresh green | PASS |
| EN-24 | event validation | PASS | — | fresh green | PASS |
| EN-25 | PG schema 5.1.0 | PASS | — | migration tests green (scratch/local parts) | PASS |
| EN-26 | loader refuse-live/hash/idempotent | PASS | — | fresh green | PASS |
| EN-27 | PgStore parity | PASS | — | parity tests green/skipped-honest (live parts need SCRATCH_DATABASE_URL) | PASS |
| EN-28 | pg gaps (pooling/cutover) | PARTIAL | — | explicitly future work, documented in migration readiness | NOT_APPLICABLE |
| EN-29 | backup manifest | PASS | — | fresh green | PASS |
| EN-30 | CSBK1 envelope | PASS | — | fresh green | PASS |
| EN-31 | minisign signing | PASS | — | fresh green | PASS |
| EN-32 | SLIP-39 ceremony-only | PASS | — | fresh green | PASS |
| EN-33 | targets no-delete | PASS | — | fresh green | PASS |
| EN-34 | integrity gates | PASS | — | fresh green | PASS |
| EN-35 | log redaction | PASS | — | fresh green | PASS |
| EN-36 | produce pipeline | PASS | — | fresh green | PASS |
| EN-37 | restore read-only | PASS | — | fresh green | PASS |
| EN-38 | backup non-goals absent | PASS | — | fresh green | PASS |
| EN-39 | security gate untested | NOT_VERIFIED | P11 | `test_security_gate.py` (4) green | PASS |
| EN-40 | data/.gitkeep placeholder | NOT_VERIFIED | — | one-line placeholder, no behavior by design | NOT_APPLICABLE |

## Frontend-ux (45): 44 PASS · 1 PARTIAL

All PASS rows re-verified by fresh full vitest (52 files / 261 tests
green), `tsc --noEmit` clean, `next build` exit 0 (BUILD_ID
JZCaaZ1gryKKPCfNZLJJI).

| ID | Finding | Orig | P-map | Fresh closeout evidence | Result |
|----|---------|------|-------|-------------------------|--------|
| FE-00 | landing nav integrity | PASS | — | suite green | PASS |
| FE-01 | hero motion + reduced-motion | PASS | — | suite green | PASS |
| FE-02 | WebGL fallback | PASS | — | suite green | PASS |
| FE-03 | audio off by default | PASS | — | suite green | PASS |
| FE-04 | landing never gated | PASS | — | suite green | PASS |
| FE-05 | demo strips/cards routes | PASS | — | suite green | PASS |
| FE-06 | demo skeletons/retry | PASS | — | suite green | PASS |
| FE-07 | demo API wiring | PASS | — | suite green | PASS |
| FE-08 | 84/35 score distinction | PASS | — | suite green | PASS |
| FE-09 | uplift label untested | PARTIAL | P10 | uplift assertion green | PASS |
| FE-10 | investigations states | PASS | — | suite green | PASS |
| FE-11 | breadcrumbs + anchors | PASS | — | suite green | PASS |
| FE-12 | DI wiring | PASS | — | suite green | PASS |
| FE-13 | badge = API score | PASS | — | suite green | PASS |
| FE-14 | AI panel run/retry/timeout | PASS | — | suite green | PASS |
| FE-15 | network orbital/flat | PASS | — | suite green | PASS |
| FE-16 | network states/provenance | PASS | — | suite green | PASS |
| FE-17 | overlay merge | PASS | — | suite green | PASS |
| FE-18 | explorer interactions | PASS | — | suite green | PASS |
| FE-19 | relationship table | PASS | — | suite green | PASS |
| FE-20 | cases states/anchors | PASS | — | suite green | PASS |
| FE-21 | risk strip | PASS | — | suite green | PASS |
| FE-22 | decision + audit append | PASS | — | suite green | PASS |
| FE-23 | advisory assessment | PASS | — | suite green | PASS |
| FE-24 | case audit page | PASS | — | suite green | PASS |
| FE-25 | replay wiring/states | PASS | — | suite green | PASS |
| FE-26 | replay reset flow | PASS | — | suite green | PASS |
| FE-27 | replay controls | PASS | — | suite green | PASS |
| FE-28 | simulation baseline vs SIM | PASS | — | suite green | PASS |
| FE-29 | RiskBadge semantics | PASS | — | suite green | PASS |
| FE-30 | login gate | PASS | — | suite green | PASS |
| FE-31 | no 403 UX | FAIL | P6 | unauthorized-event + re-gate tests green | PASS |
| FE-32 | mid-session expiry | PARTIAL | P6 | expired-flips-to-sign-in test green | PASS |
| FE-33 | a11y labels/focus | PASS | — | a11y suite green | PASS |
| FE-34 | notifications | PASS | — | suite green | PASS |
| FE-35 | contrast token-only | PARTIAL | — | tokens re-read; real ratios/AT need browser+devices | PARTIAL |
| FE-36 | logo shell+landing | PASS | — | suite green + 9 asset hashes recorded | PASS |
| FE-37 | favicons listing-only | PASS | closeout | new `app/icons.test.ts` (existence + layout wiring) green | PASS |
| FE-38 | openGraph relative | PARTIAL | P10 | `resolveMetadataBase()` + 4 tests + `NEXT_PUBLIC_SITE_URL`; domain value is staging input | PASS |
| FE-39 | next.config headers/DISTDIR | PARTIAL | P10+closeout | DISTDIR removed (J3); new `next.config.test.ts` green; build exit 0 | PASS |
| FE-40 | toolchain config | PASS | — | fresh tsc+vitest+build execution (was read-only) | PASS |
| FE-41 | zero dead controls | PASS | — | a11y + interaction suites green | PASS |
| FE-42 | indirect coverage, no :line | PASS | closeout | :line proofs recorded: theme-selector→theme-provider.test.tsx:5,61; why-risk→page.tsx:161+test:175-179,208; format→format.ts:5 via test:164,248,287; LandingChrome→LandingContent.test.tsx:40,155-157 | PASS |
| FE-43 | Modal/Tabs/Timeline/Toast | PASS | P10 | 4 real suites verified: modal/tabs/timeline/toast.test.tsx, all green | PASS |
| FE-44 | README title stale | PARTIAL | P10 | title fixed | PASS |

## Docs-provenance-git (23): 20 PASS · 2 PARTIAL · 1 NOT_VERIFIED

| ID | Finding | Orig | P-map | Fresh closeout evidence | Result |
|----|---------|------|-------|-------------------------|--------|
| DC-00 | J1 312 manifest accurate | PASS | — | J1 committed + pushed as manifested (d4e2bec, J1/J2 reports) | PASS |
| DC-01 | 293/294 ordering | PASS | — | historical, resolved in J1 | PASS |
| DC-02 | R-13 acceptance proof | PARTIAL | — | owner proof still not filed; eligibility stays AT_RISK | PARTIAL |
| DC-03 | eligibility wording | PASS | — | no new verdicts; consistency holds | PASS |
| DC-04 | backup-state wording | PASS | — | still honestly NOT_EXECUTED everywhere | PASS |
| DC-05 | suite-count drift | PARTIAL | P12+closeout | fresh counts recorded (341/103, 261/261); KNOWN_LIMITATIONS refreshed | PASS |
| DC-06 | L2 browser-write stale | FAIL | P12 | dated addendum (MASTER_CLOSEOUT authoritative) | PASS |
| DC-07 | risk semantics | PASS | — | bands + 35/84 re-verified by green tests | PASS |
| DC-08 | README stale ×4 | FAIL | P12+closeout | arch (J3) + scenarios + counts + auth (closeout) all fixed | PASS |
| DC-09 | TEST_EVIDENCE stale | FAIL | P12 | dated addendum | PASS |
| DC-10 | KNOWN_LIMITATIONS stale | FAIL | P12+closeout | refreshed + closeout scope notes | PASS |
| DC-11 | .png.png refs stale | FAIL | P12 | 4 dated addenda | PASS |
| DC-12 | CONFLICT-001 open | FAIL | P12-closeout | closure addendum (Dockerfile:18 verified live) | PASS |
| DC-13 | COMMAND snapshots unpointed | PARTIAL | P12-closeout | 5 pointer addenda | PASS |
| DC-14 | RENDER_6 omits secrets | FAIL | P12-closeout | SESSION_SECRET/DEMO_USERS/AI_*/CSBK_* rows added | PASS |
| DC-15 | .env.example AGE_* | PARTIAL | P12 | CSBK_* replacement (J3) | PASS |
| DC-16 | .gitignore working | PASS | — | re-verified via check-ignore | PASS |
| DC-17 | .gitignore gaps | PARTIAL | P13 | D2 + auditor patterns applied + verified safe | PASS |
| DC-18 | workflows names-only | PASS | — | re-counted: 30 `secrets.*` refs, 0 literals | PASS |
| DC-19 | logo wired | PASS | — | tests green + live listing + hashes | PASS |
| DC-20 | logo rights UNVERIFIED | PASS | — | consistency holds; Q-IP-1 owner action outstanding | PASS |
| DC-21 | %TEMP% proof volatility | PARTIAL | — | backup still unexecuted (owner-gated D-008) | PARTIAL |
| DC-22 | quotas/web/AI-run | NOT_VERIFIED | R4/R5 | needs network + quota + staging | NOT_VERIFIED |

## Contradictions C1–C9 (all resolved in audit; closeout re-verified)

C1 (complete flags) stands · C2 (R-13) stands, proof still pending ·
C3 (counts) stands, J1 authoritative + fresh runs recorded · C4 (L2)
closed by P12 · C5 (.png.png) closed by P12 · C6 (risk basis) closed
by engine tests · C7 (4-component PASS) closed by P10 suite proof ·
C8 (non-contradictions) re-confirmed, no drift · C9 (stale docs)
closed by P12 + closeout (CONFLICT-001, RENDER_6, README, COMMAND
pointers, ZERO_GAP addendum). No new contradictions introduced.

## Duplicates / conflicts / regressions detected

- Duplicates: none — each finding maps to exactly one disposition;
  P-items each map to ≥1 finding (traceability in J3_P1_P14 doc).
- Latent misses caught by closeout (not regressions): P11-b
  (find_unknown_ids), P12 sub-items (CONFLICT-001, COMMAND pointers,
  RENDER_6 rows, README ×3, ZERO_GAP rows), unassigned PARTIALs
  (BE-14/EV2/AI-16/AI-17/AI-21) — all closed above except CI-gated
  halves.
- Regressions: none — full suites green; state hash unchanged.
