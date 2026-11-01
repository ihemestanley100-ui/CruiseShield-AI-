# PHASE 9 — INTEGRATED SYSTEM ACCEPTANCE REPORT

Date: 2026-11-01. Scope: reconcile Phases 1–8 + hackathon track 3.1–3.5
against the CURRENT tree, verify cross-module integration end to end,
review security, and rule on acceptance. Fresh evidence this phase:
full suites, fresh production build, 69/69 browser matrix re-run
(`%TEMP%\smoke48\`), disposable write acceptance (`%TEMP%\smoke9w\`),
API relationship cross-checks. Historical reports were used as leads
only — every acceptance claim below re-verified on the current tree.

## 1. Starting repository state

HEAD `0eaaaf5`, branch `master`, 89 status entries (17 modified + 72
untracked; +1 vs the control audit = the Phase 4–8 report). No source
changes since the Phase 8 build, so Phase 8 browser evidence stands on
the current tree — and was still re-run fresh for this report.

## 2. Previous programme reconciliation

| Programme | Reported | Phase 9 re-verification |
|---|---|---|
| Product Phases 1–2 | Complete | Routes/shell/demo re-verified live — HOLDS |
| Phase 3.1–3.2 + remediation | 31/31 retest | Matrix + workflow re-run green — HOLDS |
| Phase 3.3 VQA | 44/44 | Spot-checks + extended matrix hold — HOLDS |
| Phase 3.4 live AI | agentrun_0003 | Artifact + code path intact; no new live call needed — HOLDS |
| Phase 3.5 script | Delivered | File present, routes referenced all exist — HOLDS |
| Phases 4–8 | COMPLETE_WITH_LIMITATIONS | 69/69 re-run, suites green — HOLDS |
| Security/provenance audits | Clean / greenfield | Re-scans clean; conclusions hold — HOLDS |
| Control report (2 errata) | Corrected | A1 (23) + A2 (preserve `.png.png`) verified in place — HOLDS |

Frontend suite now 233/233 (+1 shell test since the 4–8 report);
backend 289/68/0; build exit 0. No reconciling conflicts found.

## 3. Cross-module acceptance matrix

API-level ID-graph verification (all live, :8000):

| Link | Check | Result |
|---|---|---|
| Case → investigation | `case_84721.investigation_id == inv_84721` | PASS |
| Investigation → transaction | `transaction_id == txn_84721` | PASS |
| Evidence package | 39/39 ids belong to the inv_84721 family | PASS |
| Graph | 22 nodes / 30 edges, 0 provenance errors | PASS |
| Audit → case | 1/1 events target `case_84721` | PASS |
| Replay ↔ graph/txn | scn_primary replays 11 txns incl. txn_84721, 30 edges | PASS |
| Scenarios | 3 listed, active `scn_primary` | PASS |
| Risk coherence | txn 35/MODERATE + net 84/HIGH identical across investigation, case strip, replay baseline, network | PASS |

Browser cross-navigation (nav, breadcrumbs, section jumps, audit
route, flat/orbital views) re-verified in the 69/69 run. Modules
exchange consistent data; no invented or dangling relationships.

## 4. End-to-end workflow results

DETECT → CONNECT → INVESTIGATE → EXPLAIN → VERIFY → SIMULATE →
HUMAN DECISION → AUDIT: all eight stages PASS (matrix + workflow
scripts). Human-decision → audit relationship verified on
disposable data: decision `Escalate` recorded (`decision_0001`),
case NEW → TRIAGED, `audit_0006 case.decision NEW->TRIAGED` with
the submitting actor id. Simulation: baseline 84/HIGH preserved,
simulated 84/HIGH for a 1-edge ignore (deterministic; the 5-edge
72/HIGH case stands from Phase 8). Meta AI remains an advisory,
evidence-grounded service: no score fields, no invented ids (3.4
proof stands), `requires_human_approval` enforced, scores
byte-identical after all writes.

## 5. API integration results

Contracts unchanged and consistent: case, investigation,
evidence-package, graph, audit, replay, scenarios, decisions,
simulations, health — all exercised live with expected shapes.
Error envelope (`code`/`message`/`trace_id`) observed; invalid
decision label and illegal transition both 400 (re-verified
pattern; Phase 8 ran the exact probes). No 4xx/5xx in any
browser run. No authentication on app endpoints (see §6).

## 6. Security results

| Item | Finding |
|---|---|
| API authN/authZ | NOT IMPLEMENTED — actor ids self-asserted; demo-local design. Blocks ANY production claim. Documented, not a demo defect. |
| Secrets | Re-scans clean (history + tree); key server-side only; `.env` ignored. PASS. |
| Prompt-injection boundaries | Delimiter quoting + output validators + enforcement filter, mocked tests pass. Live hostile test NOT run. PASS_WITH_LIMITATIONS. |
| Evidence provenance | End-to-end ID verification (§3). PASS. |
| Audit immutability | Append-only; no PUT/PATCH/DELETE routes; no mutation paths. PASS. |
| Input validation | Client + server 400s verified. PASS. |
| Dependency vulnerabilities | pip-audit unavailable offline; NOT VERIFIED (same standing as the in-file note). No installs performed. |
| Error handling | Enveloped errors + trace ids; no stack/secret leakage observed. PASS. |
| Rate limiting | Inbound: NONE (demo). Outbound (Meta API): bounded retries + backoff. Documented. |
| Sensitive-data exposure | None found; synthetic-only. PASS. |
| Permission boundaries | Single demo profile; transitions validated; actors recorded-not-verified. Documented. |

## 7. Data integrity results

`data/state.json` `BA1D4DB4…3790FE` (101417 B) identical before,
during, and after Phase 9. All writes to disposable copies only
(`smoke9w`, destroyed after). Risk engine, rules, evidence,
provenance, AI runs, audit history untouched.

## 8. Browser and responsive results

69/69 matrix re-run on the final build: 0 console errors, 0 failed
requests (31 client-cancelled aborts classified benign with URLs).
Covers 7 routes × 1366/390 + key routes × 1920/1024/768/360/320
(0 px overflow), real-click graph/replay/evidence/decision/dialog/
drawer interactions, DOM a11y audits clean, contrast ≥ 4.5 light
and dark, text-spacing resilient. Evidence: `%TEMP%\smoke48\`.

## 9. Outstanding limitations (explicit review)

| # | Item | Status | Rationale |
|---|---|---|---|
| L1 | Screen-reader verification | NOT_VERIFIED | No AT in environment. Manual proxies (landmarks, names, focus, live regions) all pass. REQUIRED before claiming full accessibility compliance; OPTIONAL for demo acceptance. |
| L2 | Browser-level write submits | NOT_VERIFIED | API-level verified on disposable data (decision + simulation + 400s); no second frontend run. OPTIONAL — coverage adequate for acceptance. |
| L3 | Unified timeline | OPTIONAL | Deliberate decomposition (decision history + audit + AI sections, all ordered/timestamped). A merged list would duplicate content. Enhancement only. |
| L4 | Rule definitions not API-exposed | OPTIONAL | id/threshold/explanation/evidence shown; name/description/weight unavailable without backend change (intentionally avoided). |
| L5 | 67-vs-84 discrepancy | NOT_APPLICABLE (closed) | Was REQUIRED; resolved in 3.2A with proof (animation frame, single source) and re-confirmed (§3 risk coherence). Nothing outstanding. |
| L6 | Live WebGL-failure trigger | NOT_VERIFIED | Untriggerable headless; fallback code + wiring verified. OPTIONAL. |
| L7 | Live hostile-injection test | NOT_VERIFIED | 3.4 approval covered one analysis call; mocked defenses pass. OPTIONAL for acceptance; REQUIRED before claiming live-proven resistance. |
| L8 | Hackathon eligibility questions | BLOCKED | External organizer answers required (Q-*, R-13, LGPL). REQUIRED for submission; outside product acceptance. |

Nothing was silently marked resolved: L5 closed by cited proof; the
rest keep their standing with reasons.

## 10. Required remediation

None for product acceptance. Before ANY production framing, L1
(AT pass), authN/authZ + rate limiting, dependency audit, and L7
would all be REQUIRED — this report makes no production claim
(tests + demos do not establish production readiness).

## 11. Evidence references

- `%TEMP%\smoke48\matrix.ps1`, `matrix-checks.json` (69/69),
  `shots\` (this-phase re-run)
- `%TEMP%\smoke32f\` (31/31 workflow), `%TEMP%\smoke9w\` (write
  acceptance), `%TEMP%\vitest-p9.log` (233), backend log (289/68)
- `docs/PRODUCT_UIUX_PHASE_4_TO_8_COMPLETION_REPORT.md`,
  hackathon reports (9), control report

## 12. Overall acceptance verdict

**INTEGRATED_SYSTEM_ACCEPTED_WITH_LIMITATIONS**

Justification: every module verified individually and integrated;
the full workflow demonstrated with consistent cross-module data;
security posture honestly documented (demo-grade: no authN/authZ,
no inbound rate limiting — acceptable for local demo, blocking
for production); data integrity cryptographically confirmed;
limitations L1–L8 explicitly dispositioned with none hidden.
No commit, push, publish, deploy, or submit performed.
