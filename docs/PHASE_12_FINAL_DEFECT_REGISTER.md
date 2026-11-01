# PHASE 12 — FINAL DEFECT REGISTER

PROGRAMME: CSAI-MASTER-RELEASE-001 | PHASE: 12 | DATE: 2026-11-01 | HEAD: 0eaaaf5 (no commit/push)

## Open defects / limitations
| ID | Description | Severity | Component | Reproduction / evidence | Impact | Remediation | Owner | Acceptance |
|---|---|---|---|---|---|---|---|---|
| D-001 (SEC-003) | No inbound API rate limiting | MEDIUM | app/main.py (absent) | Code grep 2026-11-01: no limiter | Flood/brute-force if network-exposed | Add throttling before any exposure | Owner→pilot | Limiter live-tested |
| D-002 (SEC-004) | No API authN/authZ | MEDIUM | app/* (absent) | Code grep 2026-11-01 | Anonymous local read/write | Auth design before pilot; loopback-only demo | Owner→pilot | Auth live-tested |
| D-003 (L1) | Screen-reader verification not performed | MEDIUM | Frontend | No AT in environment | Full a11y compliance unclaimed | AT pass with real reader | Owner | AT run recorded |
| D-004 (L6) | WebGL-failure fallback never triggered live | LOW | Landing/Three.js | Untriggerable headless; code verified | Fallback unproven end-to-end | Forced-failure run | Owner/Muse | Fallback screenshot |
| D-005 (L7) | Live hostile prompt-injection not run | LOW | AI adapter | NOT_RUN (no adversarial-spend approval); mocked tests pass | Live resistance unproven | Approved live red-team call | Owner | Red-team log |
| D-006 (SEC-007) | Live pip-audit scan not run locally | LOW | Deps | No-install policy; pins lifted + installed==pinned verified; CI gate covers post-push | Unknown CVEs possible | Review CI audit after push | Owner | CI audit green |
| D-007 (NV-01) | tmpw_ta9ikh/ contents unscannable | LOW | Repo hygiene | OS permission denied; unreferenced by code | Unknown contents | Owner inspects/deletes | Owner | Dir resolved |
| D-008 | Backup not executed | MEDIUM | Ops | BACKUP_NOT_EXECUTED_PENDING_APPROVAL (standing gate) | %TEMP% evidence volatile | Owner approves destination+method | Owner | Verified archive |
| D-009 | Demo video not recorded/uploaded | MEDIUM | Submission | No recording yet; script+checklist ready | Submission incomplete without it | Owner-approved record/upload | Owner | Video URL |
| D-010 (L8) | Organizer questions unanswered | HIGH (process) | Eligibility | No written organizer replies | Eligibility/submission at risk | Owner contacts organizers | Owner | Written answers |
| D-011 | Firefox/Safari/real devices untested | LOW | Compat | Chromium-only matrix | Non-Chromium issues unknown | Extended matrix | Owner | Matrix extended |
| D-012 | Multi-worker concurrent writes unsafe | LOW | app/store.py | PERF-001 lock is per-process (single worker verified) | N/A at demo scale | Unique tmp names / external store for scale | Owner→pilot | Race under workers |

## Closed in Phases 9–12 (with proof)
| ID | Description | Closed | Proof |
|---|---|---|---|
| SEC-001 | Unbounded inputs persisted | Phase 10 | Caps + tests + live 400s; persistent hash unchanged |
| SEC-002 | Silent reseed | Phase 10 | RuntimeWarning + test + live stderr proof |
| SEC-005 | Dead CI push trigger | Phase 10 | Branch fixed main→master |
| PERF-001 | Concurrent-write 500s | Phase 11 | Lock + failing-first test + 10/10 live re-race |
| L5 | 67-vs-84 discrepancy | Phase 3.2A/9 | Animation-frame proof, coherence re-verified |
| A1/A2 | Report errata (23 count, .png.png) | Control audit/9 | Verified in place |
