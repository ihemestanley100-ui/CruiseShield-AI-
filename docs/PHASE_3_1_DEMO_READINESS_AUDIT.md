# PHASE 3.1 — LIVE DEMONSTRATION READINESS AUDIT

**Date:** 2026-10-31 · **Mode:** read-only (no source/data changes; no POSTs issued).
**Method:** live production servers (backend :8000 + `next start` :3111), real
headless Chrome via CDP, direct API GETs, backend suite, code inspection.

## 1. Startup / shutdown — PASS

- Cold boot to healthy + 200 in **5.9 s** (single command per server; procedure
  documented in handoff notes, no special flags beyond ports/env).
- Shutdown: jobs stopped/removed; 0 listening ports, 0 node/python processes
  afterwards; `data/state.json` hash identical before/after
  (`BA1D4DB4…3790FE`).

## 2. Routes — PASS (8/8)

- `/`, `/demo`, `/cases/case_84721`, `/investigations/inv_84721`,
  `/network/txn_84721`, `/replay/scn_primary` → 200.
- `/favicon.ico` → 200. Unknown route → **404** with not-found page.

## 3. Data & records — PASS

- 3 scenarios (`scn_primary` first); graph 22 nodes / 30 edges; network risk
  **84 HIGH** (`risk-score-v1`, R-001…R-008 all triggered with evidence IDs);
  transaction-only 35 MODERATE (DOM-verified earlier); case NEW with zero
  decisions; AI run `agentrun_0002` SUCCEEDED/VALIDATED. All synthetic.

## 4. DETECT→AUDIT workflow — PASS (with stated bound)

- Journey stages map to live routes; case exposes `TRIAGED, FALSE_POSITIVE`
  transitions; audit/decisions endpoints exist and are covered by
  `test_cases_audit.py` + decision-form component tests.
- Bound: the mutating decision POST was intentionally NOT executed live
  (would alter state); covered in test env instead.

## 5. Meta AI live + grounded responses — PARTIAL

- Integration code PASS: server-side call, temp 0, structured output,
  validators, provenance persistence (`app/ai_adapter.py`).
- Grounded responses PASS: persisted run shows evidence-ID-linked findings
  with confidences + missing-information list (verified live via API).
- Live execution BLOCKED: no `MODEL_API_KEY` in environment (verified);
  health `model_configured: PASS` reflects config shape, not reachability.
  Needs key + network at demo time (standing item R-10).

## 6. Prompt-injection protection — PASS

- Untrusted-text delimiters + breakout neutralizer in adapter; 305-line
  validation-test growth; backend suite green (below).

## 7. Desktop navigation — PASS

- Brand home-link proven on 7 routes last turn (code unchanged since);
  `/demo` at 1440 clean this turn (no overflow, 0 console errors).

## 8. Responsive — PASS

- 390/1440 spot this turn: no overflow, 0 errors; full 390/768/1024/1440/
  1920 matrix proven last turn (no layout code changed since).

## 9. Landing + logo — PASS

- Three.js scene live; official logo renders at natural 1219×1290 in both
  checked views; both logo file hashes unchanged (`1A0CC66B…C32A623`).

## 10. Audio / favicon / visual — PASS

- Audio defaults OFF (`aria-pressed=false` live); favicon 200, no 404s;
  zero console errors on all checked views.

## 11. Errors / loading / retry — PASS

- 404 handling verified live; skeleton loaders, error alerts with retry,
  and empty states verified in code + component tests
  (`decision-error-flow`, `command-*-test`, replay/cases/AI panels).

## 12. Security & disclosure — PASS

- No secrets in history/tree (audited 10-31); `.env` ignored/untracked;
  Meta key server-side only; "Synthetic demo data" live on demo page;
  landing carries "Simulated regional signals · not live monitoring".

## 13. Three-minute judge readiness — PARTIAL

- Ready: 6 s boot, all content live, `docs/DEMO_SCRIPT.md` exists,
  storyboard exists, fallbacks verified.
- Missing: no recorded video yet; no live-API key for the live-call beat
  (fallback beat verified instead).

## Backend suite (this audit)

- **272 passed / 85 skipped / 0 failed** (357 collected). One initial
  failure in `test_static_escaping.py` proven environmental (sandbox
  blocks the `node` subprocess with EPERM); passes unsandboxed (3/3).
  Skips are env-gated (PG scratch DB, live-AI, network) with reasons.

## Artifacts & notes

- Live evidence: `%TEMP%\smoke3a\audit.txt`. Audit created one empty
  git-ignored dir (`pytest-of-HP/`, pytest tmp root) that the OS refused
  to delete (access denied); it is invisible to git and safe to remove
  manually. No other workspace changes.
