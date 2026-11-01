# HACKATHON CRITICAL GAP REGISTER — CruiseShield AI™

**Date:** 2026-10-31 · **Mode:** READ-ONLY audit deliverable.
Priorities: P0 = judging-blocker · P1 = high judging value · P2 = harden · P3 = polish.
Closed by Phase 6 (verified this turn): H2 XSS, H3 cross-subject mixing, H4 flag bypass,
H5 evidence provenance UI, H6/H7 unhashed deploy installs.

## P0 — Must resolve before judging

### G-01 · No live rehearsal, recording, screenshots, or video (DEMO-04)
- **Category:** Demo · **Status:** MISSING
- **Evidence:** filesystem + docs check; DEMO-03/IMP-01/02 IMPLEMENTED_UNVERIFIED.
- **Impact:** judges cannot be shown the product works live; highest demo risk.
- **Recommendation:** user-operated 9-step rehearsal → screenshots → recorded run-through →
  edited video per VIDEO_STORYBOARD. **Owner:** user (browser + recording).
- **Dependencies:** G-02 (build) for a clean build-based run; backend + frontend start commands.

### G-02 · Production build + hosted smoke outstanding (DEMO-05)
- **Category:** Demo · **Status:** NOT_VERIFIED / MISSING
- **Evidence:** `npm run build` blocked by `.next/trace` EPERM (running dev server lock);
  image unbuilt; no public URL.
- **Recommendation:** stop dev server → `npm run build` → `npm start` smoke of `/` and `/demo`;
  deployment needs separate approval. **Owner:** user (process control).
- **Dependencies:** none (code ready; tsc + 201 tests green).

### G-03 · Pilot/product bar explicitly failed — must stay fenced (IMP-09, TECH-05)
- **Category:** Impact + Technical · **Status:** FAIL (by design, out of scope)
- **Evidence:** verified absent — no auth, tenants, rate limits, JSON locking (`app/` search).
- **Recommendation:** keep the demo-only boundary in pitch, runbook, and README; never imply
  shared-deployment readiness. Docs-only, no code. **Owner:** docs.

## P1 — High judging value

### G-04 · Live AiPanel omits missing_information/alternative_explanations (META-06, DEMO-03)
- **Category:** Meta AI + Demo · **Status:** PARTIAL
- **Evidence:** `ai-panel.tsx` RunResult vs DEMO_SCRIPT step 5 read-aloud.
- **Recommendation:** render the two fields in the live panel + test; or reword step 5 to the
  case page. Small additive UI change.

### G-05 · Prompt-injection resistance untested (META-09)
- **Category:** Meta AI · **Status:** PARTIAL
- **Evidence:** `build_followup_messages` raw concatenation; no injection tests.
- **Recommendation:** delimit/quote the user question; add override-attempt test. Backend-small.

### G-06 · /demo partial-section errors lack Retry (DEMO-02)
- **Category:** Demo · **Status:** PARTIAL
- **Evidence:** `demo/page.tsx` SectionError vs docs recovery claim.
- **Recommendation:** add per-section Retry button + test, or correct the docs claim.

### G-07 · Performance unmeasured (TECH-11)
- **Category:** Technical · **Status:** NOT_VERIFIED (numbers)
- **Recommendation:** record load time, WebGL init, FPS, mobile behavior during G-01 rehearsal.

### G-08 · Impact measurement framework missing (IMP-05)
- **Category:** Impact · **Status:** PARTIAL
- **Recommendation:** 3 scripted scenarios with step counts + demo timings; no production claims.

### G-09 · Docs count drift (TECH-08/D3)
- **Category:** Technical · **Status:** PARTIAL (conflict)
- **Evidence:** storyboard "57" vs script "49+8" vs actual 280 backend / 201 frontend.
- **Recommendation:** refresh TEST_EVIDENCE headline + script/storyboard counts. Docs-only.

### G-10 · Organizer problem-statement citation absent (IMP-01)
- **Category:** Impact · **Status:** PASS_WITH_LIMITATIONS
- **Recommendation:** cite the published statement in IMPACT_CASE. Docs-only, needs the source.

## P2 — Harden (judging polish + engineering)

- G-11 · Main AI validator lacks intel_ai guards (META-04): port banned-score/enforcement/
  human-review checks + tests.
- G-12 · Repeatability unpinned (META-13): pin sampling params or document non-determinism;
  one live follow-up call pending (needs key + network).
- G-13 · No caller rate limiting (META-11/TECH-05): needs the auth-architecture decision first.
- G-14 · JSON concurrency unlocked + len()+1 IDs (TECH-06): single-process label; file lock if reused.
- G-15 · DI edge-contract conflict (TECH-08/D2): reconcile `proposed_edges` types with DI-07
  allowlist or remove dead surface; same for compare/extract/to_ai_context/audit_descriptor.
- G-16 · Old-vs-new comparison visual (IMP-04); FP narration (IMP-08).
- G-17 · CI never executed (TECH-09): needs push approval; then confirm green.
- G-18 · Browser/AT verification pending (TECH-10): keyboard sweep, contrast, screen reader.
- G-19 · pip-audit unpinned in gate; npm-audit moderate+high without committed follow-up.

## P3 — Polish

- G-20 · Dead UI primitives (`tabs/modal/toast/timeline`) — remove or wire.
- G-21 · No lint script; `formatKobo` direct unit test; stale labels (batch note, hardcoded KPI).
- G-22 · `test_pg_migration` LIVE_HASH anchor brittleness; evidence-POST alias semantics;
  gitignored stale `test-output*.txt` leftovers (unshipped).

## Explicitly out of scope (do not implement for the hackathon)
AuthN/Z, multi-tenancy, production backup schedules, 30-day reliability, GPS collection,
paid providers, global search UI (R13 Option C), production migration/cutover.
