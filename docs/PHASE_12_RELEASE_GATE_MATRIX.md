# PHASE 12 — RELEASE GATE MATRIX

PROGRAMME: CSAI-MASTER-RELEASE-001 | PHASE: 12 | DATE: 2026-11-01 | HEAD: 0eaaaf5
GATE SCALE: OPEN (demo may proceed) / OPEN_WITH_CONDITIONS / CLOSED. Production use is out of scope for every gate.

| Gate | Status | Evidence | Conditions / carried defects |
|---|---|---|---|
| Functional acceptance | OPEN | 8-stage workflow verified; 69/69 matrix (2 re-runs); suites 294+233 green; build exit 0 | L2 browser-write (API-verified); L3/L4 optional |
| Security acceptance (demo) | OPEN_WITH_CONDITIONS | SEC-001/002/005 closed w/ live proof; secrets clean; CORS+errors verified | D-001, D-002: loopback-only demo; no network exposure |
| Performance acceptance | OPEN | p50 3 ms API / 7–38 ms routes / ~1 s pages; 410-req stability clean; PERF-001 fixed | Demo-scale only; no soak/multi-user claim |
| Data integrity | OPEN | Persistent BA1D4DB4…3790FE unchanged across Phases 9–11; scores coherent everywhere | None |
| AI governance | OPEN_WITH_CONDITIONS | Advisory-only boundaries enforced; no score/evidence fabrication; human authority; live agentrun_0003 proof | D-005 live red-team outstanding; each new live call needs key+network |
| Accessibility | OPEN_WITH_CONDITIONS | Keyboard/contrast/landmarks/focus verified; contrast ≥4.5 both themes | D-003 screen reader NOT_VERIFIED — no full-compliance claim |
| Browser compatibility | OPEN_WITH_CONDITIONS | Chromium 69/69, 320px–1920px, 0 overflow | D-011 non-Chromium/devices untested; D-004 WebGL trigger unproven |
| Operational recovery | OPEN | Restart hash-identical; isolated restore drill; atomic locked writes | D-008 backup unexecuted (approval gate); prod DR unverified |
| Documentation | OPEN | Phases 9–11 reports + registers; KNOWN_LIMITATIONS reconciled; demo script present | None (video + submission docs in Phase 13) |
| Backup and restoration | OPEN_WITH_CONDITIONS | Plan + isolated drill verified | D-008: execution needs owner-approved destination |
| Deployment readiness | CLOSED | No public deployment (stated in limitations); image never built; no hosted smoke | Intentionally closed — demo is localhost-only; NOT a defect |

Overall: demo release gates OPEN (4 with conditions, 1 intentionally closed). Production readiness: NOT established (by design at this stage).
