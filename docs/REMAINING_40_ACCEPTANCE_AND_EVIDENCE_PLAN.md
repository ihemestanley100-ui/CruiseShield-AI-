# REMAINING 40 — ACCEPTANCE & EVIDENCE PLAN

## Status vocabulary (binding)

- CLOSED_VERIFIED: acceptance met + tests pass + evidence filed.
- TESTING/IN_PROGRESS: work underway, evidence incomplete.
- NOT_STARTED: deferred or unbegun, honestly stated.
- BLOCKED_EXTERNAL_DEPENDENCY / AWAITING_OWNER_APPROVAL: gated.
- NOT_VERIFIED: claimed without evidence (forbidden as end-state).
- Skipped tests NEVER count as passed. Failed gates fail the release.

## Evidence required per closure group

| Group | Rows | Evidence that closes |
|---|---|---|
| Hosted vitest | 8 TESTING + DET-12 + FE-01 | CI log: typecheck + named vitest files + build green |
| Hosted gate | DET-13 | Full security-gate log (hashes/audit/pytest/gitleaks/fe) |
| Scratch PG | QA-02 | Unskipped PG-service run quoted green |
| Ceremony | AUD-01, BAK-01 | Ceremony record + prod-key verify + restore log |
| Coverage | CICD-01 | Threshold-gated CI run green |
| Policy/bind | LEAFLET | Policy approval + MAP_PROVIDER + render proof |
| Deploy/smoke | DET-14, INF-01 | Deploy logs + public-URL smoke quotes |
| Alias removal | REL-02 | Zero dependents + regression green |
| Retention | DATA-01 | Executed schedule + tombstone proof |
| Cutover | DET-03, DB-01 | Live PG + parity + rollback proof |
| Licence | REL-01 | LICENSE committed per owner selection |
| Auth batch | AUTH-01..09 | Per-method verified login + abuse tests |
| Translators | I18N-02 | Per-locale sign-off + merged dicts + vitest |
| Visual | VIS-01 | Diff register + corrections + real screenshots |
| Reopens | AI/TEL/GEO/UFI rows | Per-provider handshake + quota + audit |

## Matrix update rules

1. Status changes only with filed evidence (log/quote/record).
2. `next` must name the exact unblocking action + owner.
3. Reopened NO-LIVE/DEFER items need a NEW decision entry first.
4. Every phase ends with `zero_gap_matrix.py --check` + manifest regen.
5. Counts must sum to the row total; validator exit 0 required.

## Current evidence ledger (this audit)

- Matrix valid: 192 rows, 152 closed, 40 open (re-verified).
- Manifest: 11 files, integrity ok.
- Skip register: 142 IDs indexed, 0 passed-by-skip.
- Failure logs: 1F+2E verbatim, sandbox-only.
- Tenant strict-deny: 14/14 green (re-verified).
- Demo sweep: clean. Licence inventory: 17 pins, 1 LGPL flag.
- i18n pack: 17 keys x 11 locales, reviewer-ready.
- Publication manifest: 517 entries classified + 7 exclusions.
- Live handshakes: ZERO. Browser runs: ZERO. Deploys: ZERO.
