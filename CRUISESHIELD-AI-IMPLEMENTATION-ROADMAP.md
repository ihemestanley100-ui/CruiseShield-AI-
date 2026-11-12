# CRUISESHIELD-AI-IMPLEMENTATION-ROADMAP.md

Dependency-ordered batches from the Phase Zero audit. Rule: FIX →
VERIFY → CAPTURE EVIDENCE → RECONCILE → CERTIFY. Each batch reports
files inspected/changed, reason per change, preserved behavior, new
behavior, tests + results, remaining gaps, risks, and next batch.
No deploy, billable action, secret handling, or push without explicit
owner approval per batch.

## Phase 0 — Baseline truth (no dependencies; do first)

| Batch | Closes | Work |
|---|---|---|
| 0.1 | GAP-006 | Fresh full backend (`pytest tests/`) + frontend (`vitest run`, `tsc`, `next build`) runs on clean HEAD; fresh `--collect-only` settles 46/47 drift; dated pass logs + refreshed checkpoint |
| 0.2 | GAP-011 | One-line RENDER_6_ENV_REGISTER.md:23 correction to LEAVE-EMPTY; refresh TEST_RESULTS/matrix counts to HEAD logs |
| 0.3 | GAP-010 | Observe a green security-gate dispatch on GitHub (push/PR/weekly); link the run |
| 0.4 | GAP-015 | Provision scratch PG (local/CI free), run parity/migration/atomic/hardening suites; green log on HEAD |

Gate to Phase 1: dated green logs for 0.1–0.4 (or recorded BLOCKED
with owner cause for 0.3/0.4).

## Phase 1 — Contract + UX coverage (after Phase 0)

| Batch | Closes | Work |
|---|---|---|
| 1.1 | GAP-012 + GAP-013 | DONE 2026-11-05 — per-route decisions recorded in matrix; 3 routes + 4 clients wired with tests; rest documented API-only/library-only |
| 1.2 | GAP-017 | Thread real session role into record_decision (keep `demo-token` fallback) + audit test |
| 1.3 | GAP-018 | Scale note (single-instance limit; sticky/Redis design sketch) + RISK flag-provider doc |
| 1.4 | GAP-005 | Coverage providers + thresholds + CI artifact, or recorded no-coverage decision |

Gate to Phase 2: full regression green after 1.1–1.2; docs merged.

## Phase 2 — Trust hardening (after Phase 1)

| Batch | Closes | Work |
|---|---|---|
| 2.1 | GAP-002 | Audit decision record; harden (chain/verify + tamper tests + loader gate) only if required |
| 2.2 | GAP-003 | Backup ceremony with owner (keys off-repo), enable workflows + reviewers, schedules, drill, implement load-into-scratch |
| 2.3 | GAP-004 | Golden prompt/response fixtures + offline quality/drift assertions |
| 2.4 | GAP-014 | Keyed staging live AI call (one bounded request, owner approves key + spend $0 check); capture golden for 2.3 — or record no-live decision |
| 2.5 | GAP-007 | Browser WebGL smoke incl. gestures + context-loss restore proof |

Gate to Phase 3: trust decisions recorded; 2.2/2.4 explicitly
approved-and-done or honestly BLOCKED.

## Phase 3 — Ship readiness (after Phase 2)

| Batch | Closes | Work |
|---|---|---|
| 3.1 | GAP-016 | Manifest-assertion tests + locked-install execution + digest-pin decision |
| 3.2 | GAP-008 | Netlify owner call: remove netlify.toml, or add OpenNext adapter + plugin + verified build (see Netlify A-E report for the minimal correction) |
| 3.3 | GAP-001 | Prod-store decision record (JSON-canonical vs PG cutover); cutover implemented only on approval |
| 3.4 | GAP-009 | Owner-approved first Render deploy (backend→frontend order) + dashboard reconciliation + live health/ready proof |

Release gates G01–G18 map 1:1 onto batches 0.1–3.4; a gate stays
NOT_VERIFIED until its batch evidence lands. Final acceptance per
directive §20 (end-to-end workflows, data correctness, reproducible
detection, record-backed graph, traceable evidence, enforced access
control, real evaluated AI, tested reliability, verified recovery,
assessed security/privacy, complete docs, passed gates).
