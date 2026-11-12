# PHASE 1 APPROVAL & EXECUTION SEQUENCE

Safest approval order with unlocks, gates, and 40-row impact.
2026-11-08 @ d82627d.

## Batch 0 — Zero-risk inputs (any order, no approval needed)

- Attach image (E2) → VIS-01 comparison unblocks.
- Supply B10 readings → billing/deploy facts unblock B9.
- Nominate translators (E1) → I18N-02 review unblocks.

## Batch 1 — Observe-only (reversible, $0)

1. B1 PKG-01 → 11 rows executable (8 TESTING + DET-12/13 + FE-01).
2. B7 D-057 → QA-02 joins Batch 1 (12th row).
3. Gate: hosted logs quoted per row → CLOSED_VERIFIED or defect
   fix-forward. Impact: 40 → 28 open (if all green).

## Batch 2 — Bounded execution (needs Batch 1 green)

4. B4 D-020 exec → CICD-01 (follow-up CI run proves gates).
5. B8 D-055 → LEAFLET bind (follow-up run proves render).
6. B2 D-018 ceremony → AUD-01 + BAK-01 (ceremony records).
7. Gate: evidence per acceptance plan. Impact: 28 → 23 open.

## Batch 3 — Data authorization (needs B2 backup proof)

8. B6 D-056 → DATA-01 implement + execute (tombstone proof).
9. Impact: 23 → 22 open.

## Batch 4 — Deploy (needs B10 readings + free-variant choice)

10. B9 staging → INF-01 smoke evidence.
11. B5 D-019b → REL-02 removal + regression.
12. B9 production → DET-14 live verification.
13. Impact: 22 → 19 open.

## Batch 5 — Conditional cutover (needs Phase 4 + PG evidence)

14. B3 GAP-001 evidence → DB-01 + DET-03.
15. Impact: 19 → 17 open.

## Remaining 17 (NOT in approval scope now)

- F-held (15): AUTH-01..09 (PKG-09), AI-01/AI-03 (NO-LIVE),
  TEL-08/LIVE-GEO/UFI-LIVE (NO-LIVE), UFI-AIMODEL (D-054).
- Decided-deferred (1): REL-01 (D-015).
- Owner-action (1 net): I18N-02 and/or VIS-01 if inputs pending
  (each closes on delivery + verification).

## Test/evidence gates between batches

- Every batch ends: matrix --check exit 0, manifest regen + ok,
  regression green, per-row evidence filed before status change.
- Any red gate stops the sequence; no batch skips its gate.

## Safest order summary

readings/image/translators → B1+B7 → B4+B8+B2 → B6 → B9-staging
→ B5 → B9-production → B3. Stops cleanly at any point with 40-row
accounting intact.
