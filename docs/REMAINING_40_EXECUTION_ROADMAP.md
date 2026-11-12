# REMAINING 40 — EXECUTION ROADMAP

Order of operations with gates. Nothing below PKG-01 executes
without its named approval. Status stays NOT PRODUCTION READY
until the final gate.

## Phase 0 — DONE (this audit)

- 40-row register, approval register, config audit, dependency
  register, roadmap, acceptance plan. Zero code changes, zero
  external actions.

## Phase 1 — Owner inputs (parallel, no dependencies)

1. Attach reference image → unblocks VIS-01 execution.
2. PKG-01 approval → unblocks 12 hosted-CI rows.
3. PKG-02/03A/05 readings → unblock billing/deploy claims.
4. Commission translators → unblocks I18N-02.

## Phase 2 — Hosted CI (needs Phase 1.2)

- Push reviewed branch → PR to production-launch → gate green.
- Closes: DET-13, DET-12, FE-01, 8 TESTING (+QA-02 with D-057).
- Fix-forward only for defects the hosted run proves.

## Phase 3 — Ceremony & data decisions (needs Phase 2 evidence)

- D-018 ceremony → AUD-01, BAK-01.
- D-020 exec → CICD-01 gate wiring (follow-up CI run).
- D-055 policy → LEAFLET bind (follow-up CI run).
- D-056 schedule → DATA-01 implement (needs backup proof first).

## Phase 4 — Staging deploy (needs Phase 2 + readings + free-variant choice)

- Free-tier services → smoke capture → INF-01.
- D-019b alias removal → REL-02 (follow-up run).

## Phase 5 — Production deploy + cutover (needs Phase 4)

- Production approval → DET-14 → public URL verification.
- GAP-001 evidence (hosted PG + parity + rollback) → DB-01, DET-03.

## Phase 6 — Reopens (each needs its own NEW decision)

- PKG-09 → AUTH-01..09 batch. PKG-06 → REL-01 LICENSE.
- D-053 per-provider → TEL-08/LIVE-GEO/UFI-LIVE handshakes.
- PKG-04/D-054 → AI-01/AI-03/UFI-AIMODEL. D-058 → scheme windows.

## Phase 7 — Final acceptance

- 192/192 reconciled, evidence manifest extended, legal signoff,
  operational signoff → PRODUCTION VERIFIED (only then).

## Critical path

image + PKG-01 → CI green → D-018/GAP-001 evidence → deploy →
reopens → legal/ops signoff. Current position: Phase 0 complete.
