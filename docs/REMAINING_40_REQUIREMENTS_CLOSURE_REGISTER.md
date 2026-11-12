# REMAINING 40 REQUIREMENTS — CLOSURE REGISTER

Generated 2026-11-08 @ d82627d. Read-only audit; no status
changes made. Primary classes: A=0 B=0 C=0 D=23 E=2 F=15 G=0.

## AGOS-UI — TESTING

- Statement: Assistant shell + copilot wiring
- Owner/priority/source: engineering / P1 / agent-os §3/§16
- Implementation: frontend/components/assistant-shell.tsx frontend/lib/api.ts frontend/app/investigations/[id]/page.tsx
- Tests: frontend/components/assistant-shell.test.tsx
- API/UI/DB: AssistantShell
- Blocker: PKG-01 DEFERRED 2026-11-07
- Dependencies: none
- Classification: D primary / B
- Remaining gap: components + tests written, never executed (node EPERM)
- Root cause: PKG-01 DEFERRED: no hosted runner
- Engineering work: none unless hosted run finds defects
- Configuration: none
- Owner approval: YES
- Credentials/provider: no
- Acceptance: one shell, context props; no chat sprawl
- Evidence required: hosted vitest log green for named files; then CLOSED
- Next (matrix): await PKG-01 re-approval; then push + observe
- Effort/risk: S / low — stdin/module checks already pass

## AUD-01 — IN_PROGRESS

- Statement: Tamper-evident audit hash chain
- Owner/priority/source: engineering / P0 / GAP-002
- Implementation: app/audit_chain.py app/store.py migrations/loader.py
- Tests: tests/test_audit_chain.py tests/test_audit_store.py tests/test_loader_gate.py
- API/UI/DB: none
- Blocker: D-018 key ceremony
- Dependencies: ['D-018']
- Classification: D primary / G
- Remaining gap: chain implemented + tested; production ceremony not authorized
- Root cause: D-018 TEST DRILL ONLY
- Engineering work: none — ceremony procedure prepared, awaits approval
- Configuration: production keyring handles at ceremony
- Owner approval: YES
- Credentials/provider: no
- Acceptance: chain verifies, tamper detected
- Evidence required: ceremony record + chain verify under prod keys; then CLOSED
- Next (matrix): test-key drills only; prod ceremony needs approval
- Effort/risk: S / key-custody failure without procedure (procedure ready)

## BAK-01 — IN_PROGRESS

- Statement: Encrypted backup + verified restore drill
- Owner/priority/source: engineering / P1 / GAP-003
- Implementation: backups/local_target.py
- Tests: tests/test_local_target.py scripts/backup_drill.py
- API/UI/DB: none
- Blocker: D-018 key ceremony
- Dependencies: ['D-018']
- Classification: D primary / G
- Remaining gap: scratch drill green; production backup/restore unproven
- Root cause: D-018 TEST DRILL ONLY
- Engineering work: none unless drill gaps found
- Configuration: BACKUP_* vars at ceremony
- Owner approval: YES
- Credentials/provider: no
- Acceptance: restore verified from encrypted backup
- Evidence required: encrypted backup + verified restore log; then CLOSED
- Next (matrix): test-key drills only
- Effort/risk: S / untested restore = no recovery (stated honestly)

## CICD-01 — AWAITING_OWNER_APPROVAL

- Statement: Coverage measurement + thresholds enforced
- Owner/priority/source: engineering / P1 / GAP-005/D-020
- Implementation: docs/COVERAGE_LOCK_PREP.md
- Tests: none
- API/UI/DB: none
- Blocker: D-020 dependency approval
- Dependencies: ['D-020']
- Classification: D primary / A-after-approval
- Remaining gap: coverage pins prepared (COVERAGE_LOCK_PREP), gates unwired
- Root cause: D-020 approve-in-principle needs separate exec auth + PKG-01
- Engineering work: wire backend+frontend coverage gates after approvals
- Configuration: CI threshold values
- Owner approval: YES
- Credentials/provider: no
- Acceptance: backend+frontend coverage gated in CI
- Evidence required: gated CI run green with thresholds enforced; then CLOSED
- Next (matrix): approve pins, wire CI gates
- Effort/risk: S / threshold churn on first run

## DATA-01 — AWAITING_OWNER_APPROVAL

- Statement: Retention/archival/purge execution
- Owner/priority/source: owner / P2 / L13 P14/L14 audit
- Implementation: none
- Tests: none
- API/UI/DB: none
- Blocker: owner retention authorization
- Dependencies: none
- Classification: D primary / A-after-approval
- Remaining gap: tracker-only; no purge code exists
- Root cause: D-056 DEFERRED (retention authorization)
- Engineering work: implement schedule + purge + proof after approval
- Configuration: retention schedule values
- Owner approval: YES
- Credentials/provider: no
- Acceptance: schedule executed + proven
- Evidence required: executed schedule + tombstone proof; then CLOSED
- Next (matrix): await D-056 re-approval; then implement
- Effort/risk: M / irreversible deletion — approval + backup first

## DB-01 — AWAITING_OWNER_APPROVAL

- Statement: PostgreSQL operational cutover
- Owner/priority/source: engineering / P0 / GAP-001
- Implementation: app/db.py
- Tests: tests/test_pg_migration.py tests/test_pg_parity.py tests/test_pg_atomic_decision.py tests/test_pg_hardening.py
- API/UI/DB: migrations/loader.py
- Blocker: GAP-001 cutover approval
- Dependencies: ['GAP-001']
- Classification: D primary / A-after-approval
- Remaining gap: PG path scratch-only; JSON active; cutover unapproved
- Root cause: GAP-001 HOLD (needs hosted PG + parity + rollback proof)
- Engineering work: migration + parity + RLS review after approval
- Configuration: DATABASE_URL, STORE_BACKEND at cutover
- Owner approval: YES
- Credentials/provider: no
- Acceptance: PG live with parity + rollback proven
- Evidence required: live PG + parity + rollback evidence; then CLOSED
- Next (matrix): approve cutover after hosted PG available
- Effort/risk: L / data loss on cutover without rollback drill

## DET-03 — IN_PROGRESS

- Statement: Signal events persist with history and outcomes
- Owner/priority/source: engineering / P0 / directive §9/§14 AC-03
- Implementation: app/store.py
- Tests: tests/test_detection.py
- API/UI/DB: /api/v1/signals/ / GAP-001 PG signal_events
- Blocker: GAP-001 PG cutover
- Dependencies: ['GAP-001']
- Classification: D primary / A-after-approval
- Remaining gap: signal_events derived at runtime, not persisted with history
- Root cause: GAP-001 HOLD: no production PG to persist to
- Engineering work: persist signal_events + history/outcomes on approved cutover only
- Configuration: DATABASE_URL + STORE_BACKEND=pg at cutover (not now)
- Owner approval: YES
- Credentials/provider: no
- Acceptance: events persisted, not derived
- Evidence required: PG rows quoted + parity + rollback proof; then CLOSED
- Next (matrix): persist signal_events on PG cutover
- Effort/risk: M / schema/tenant-isolation regression at cutover

## DET-12 — BLOCKED_EXTERNAL_DEPENDENCY

- Statement: Frontend detection tests green
- Owner/priority/source: engineering / P0 / directive §12/§14 AC-12
- Implementation: none
- Tests: frontend/components/detection-panels.test.tsx
- API/UI/DB: frontend/components/detection-panels.tsx
- Blocker: PKG-01 DEFERRED; GAP-010
- Dependencies: ['GAP-010']
- Classification: D primary / B
- Remaining gap: detection-panels vitest written, never executed (node EPERM)
- Root cause: PKG-01 DEFERRED: no hosted runner; GAP-010 observation gap
- Engineering work: none — fix failures only if hosted run finds defects
- Configuration: none
- Owner approval: YES
- Credentials/provider: no
- Acceptance: vitest suite passes
- Evidence required: hosted vitest log green; then CLOSED
- Next (matrix): await PKG-01 re-approval; then push + observe
- Effort/risk: S / low — component already stdin-checked

## DET-13 — AWAITING_OWNER_APPROVAL

- Statement: Hosted CI green
- Owner/priority/source: engineering / P0 / directive §14 AC-13
- Implementation: .github/workflows/security-gate.yml
- Tests: none
- API/UI/DB: none
- Blocker: PKG-01 DEFERRED 2026-11-07
- Dependencies: ['D-017']
- Classification: D primary / -
- Remaining gap: security-gate.yml never ran on hosted Linux
- Root cause: PKG-01 DEFERRED: push unauthorized
- Engineering work: none unless gate finds defects
- Configuration: none
- Owner approval: YES
- Credentials/provider: no
- Acceptance: Linux CI run green
- Evidence required: hosted gate green (install/hash/audit/pytest/gitleaks/fe); then CLOSED
- Next (matrix): await PKG-01 re-approval
- Effort/risk: S / lockfile drift on fresh install (mitigated: --require-hashes)

## DET-14 — AWAITING_OWNER_APPROVAL

- Statement: Production deployment verified
- Owner/priority/source: engineering / P0 / directive §14 AC-14
- Implementation: render.yaml netlify.toml
- Tests: none
- API/UI/DB: none
- Blocker: GAP-009; PKG-01 DEFERRED
- Dependencies: ['GAP-009']
- Classification: D primary / C-after-approval
- Remaining gap: deploy configs written, never executed or verified live
- Root cause: GAP-009 + PKG-01: CI-first ordering, no deploy approval
- Engineering work: none unless smoke finds defects
- Configuration: render/netlify env values at deploy time (owner-entered secrets)
- Owner approval: YES
- Credentials/provider: no
- Acceptance: live backend+frontend verified
- Evidence required: deploy logs + public-URL smoke quotes; then CLOSED
- Next (matrix): deploy after CI green + approval
- Effort/risk: M / starter-plan $0 conflict; cold starts; ephemeral JSON

## FE-01 — AWAITING_OWNER_APPROVAL

- Statement: Frontend executed-test evidence on current tree
- Owner/priority/source: engineering / P1 / L13 P15/L14 audit
- Implementation: none
- Tests: none
- API/UI/DB: frontend
- Blocker: PKG-01 DEFERRED 2026-11-07
- Dependencies: ['D-017']
- Classification: D primary / B
- Remaining gap: frontend suites exist; zero executed runs on current tree
- Root cause: PKG-01 DEFERRED + node EPERM
- Engineering work: none unless hosted run finds defects
- Configuration: none
- Owner approval: YES
- Credentials/provider: no
- Acceptance: vitest+tsc+build green quoted
- Evidence required: hosted typecheck+vitest+build quoted green; then CLOSED
- Next (matrix): await PKG-01 re-approval
- Effort/risk: S / hidden frontend defects (unknown until run)

## INF-01 — AWAITING_OWNER_APPROVAL

- Statement: Deploy verification (logs + smoke)
- Owner/priority/source: engineering / P0 / GAP-009
- Implementation: none
- Tests: none
- API/UI/DB: none
- Blocker: GAP-009/D-017
- Dependencies: ['D-017']
- Classification: D primary / C-after-approval
- Remaining gap: no deploy logs, no smoke evidence
- Root cause: GAP-009/D-017: no deploy approval
- Engineering work: smoke-fix only if failures
- Configuration: deploy-time env values
- Owner approval: YES
- Credentials/provider: no
- Acceptance: health/ready/root/auth/smoke quoted
- Evidence required: health/ready/root/auth/smoke quotes; then CLOSED
- Next (matrix): approve deploy; capture logs
- Effort/risk: M / same as DET-14

## LEAFLET — NOT_STARTED

- Statement: OSM/Leaflet tile renderer binding
- Owner/priority/source: engineering / P2 / geointel §9
- Implementation: none
- Tests: none
- API/UI/DB: none
- Blocker: none
- Dependencies: none
- Classification: D primary / A-after-approval
- Remaining gap: schematic ships; tile binding not done
- Root cause: D-055 POLICY FIRST (review done, decision pending)
- Engineering work: bind renderer after MAP_PROVIDER decision
- Configuration: MAP_PROVIDER value
- Owner approval: YES
- Credentials/provider: no
- Acceptance: tile-policy review + owner MAP_PROVIDER decision
- Evidence required: policy approval + tiles render + attribution; then CLOSED
- Next (matrix): owner approves policy; then bind
- Effort/risk: S / OSM tile-use violation without policy

## MAP-02 — TESTING

- Statement: Geointel UI: map + verify + admin panels
- Owner/priority/source: engineering / P1 / geointel §14
- Implementation: frontend/components/geointel-map.tsx frontend/components/intel-verify-sections.tsx frontend/components/intel-admin-panels.tsx
- Tests: frontend/components/geointel-map.test.tsx frontend/components/intel-verify-sections.test.tsx
- API/UI/DB: GeointelMap
- Blocker: PKG-01 DEFERRED 2026-11-07
- Dependencies: none
- Classification: D primary / B
- Remaining gap: components + tests written, never executed (node EPERM)
- Root cause: PKG-01 DEFERRED: no hosted runner
- Engineering work: none unless hosted run finds defects
- Configuration: none
- Owner approval: YES
- Credentials/provider: no
- Acceptance: evidence renders; masked honored; no verdicts
- Evidence required: hosted vitest log green for named files; then CLOSED
- Next (matrix): await PKG-01 re-approval; then push + observe
- Effort/risk: S / low — stdin/module checks already pass

## QA-02 — AWAITING_OWNER_APPROVAL

- Statement: Scratch-PG pass line (migration/parity/J6)
- Owner/priority/source: engineering / P1 / GAP-015
- Implementation: none
- Tests: none
- API/UI/DB: none
- Blocker: PKG-01 DEFERRED 2026-11-07
- Dependencies: ['D-017']
- Classification: D primary / B
- Remaining gap: PG suites skip without SCRATCH_DATABASE_URL
- Root cause: PKG-01 + D-057 DEFERRED
- Engineering work: none unless hosted run finds defects
- Configuration: CI PG service already in workflow
- Owner approval: YES
- Credentials/provider: no
- Acceptance: unskipped green run quoted
- Evidence required: unskipped green run quoted; then CLOSED
- Next (matrix): await PKG-01/D-057 re-approval
- Effort/risk: S / parity gaps surfacing under real PG

## REC-UI — TESTING

- Statement: Recovery section + dashboard wiring
- Owner/priority/source: engineering / P1 / recovery §14
- Implementation: frontend/components/recovery-section.tsx frontend/lib/api.ts frontend/app/investigations/[id]/page.tsx
- Tests: frontend/components/recovery-section.test.tsx
- API/UI/DB: RecoverySection
- Blocker: PKG-01 DEFERRED 2026-11-07
- Dependencies: none
- Classification: D primary / B
- Remaining gap: components + tests written, never executed (node EPERM)
- Root cause: PKG-01 DEFERRED: no hosted runner
- Engineering work: none unless hosted run finds defects
- Configuration: none
- Owner approval: YES
- Credentials/provider: no
- Acceptance: metrics from stored tenant rows
- Evidence required: hosted vitest log green for named files; then CLOSED
- Next (matrix): await PKG-01 re-approval; then push + observe
- Effort/risk: S / low — stdin/module checks already pass

## REL-01 — AWAITING_OWNER_APPROVAL

- Statement: Public repository license selected
- Owner/priority/source: owner / P1 / D-015
- Implementation: none
- Tests: none
- API/UI/DB: none
- Blocker: D-015
- Dependencies: ['D-015']
- Classification: D primary / -
- Remaining gap: no LICENSE file; selection deferred
- Root cause: D-015/PKG-06 DEFERRED (reaffirmed UPDATE-002)
- Engineering work: add chosen LICENSE text after owner selection
- Configuration: none
- Owner approval: YES
- Credentials/provider: no
- Acceptance: LICENSE committed
- Evidence required: LICENSE committed per selection; then CLOSED
- Next (matrix): await PKG-06 re-approval
- Effort/risk: S / distribution without licence (currently private)

## REL-02 — AWAITING_OWNER_APPROVAL

- Statement: Demo API aliases removed after migration
- Owner/priority/source: engineering / P2 / D-019b
- Implementation: app/main.py
- Tests: none
- API/UI/DB: /api/v1/demo/*
- Blocker: D-019b post-deploy approval
- Dependencies: ['D-019b']
- Classification: D primary / A-after-approval
- Remaining gap: 4 deprecated /api/v1/demo/* aliases retained in app/main.py
- Root cause: D-019b HOLD until verified deploy
- Engineering work: removal patch after deploy verification + approval
- Configuration: none
- Owner approval: YES
- Credentials/provider: no
- Acceptance: aliases removed, no dependents
- Evidence required: aliases gone, dependents zero, regression green; then CLOSED
- Next (matrix): remove after deploy verified
- Effort/risk: S / breaking unknown external callers (deprecated + logged)

## SITE-01 — TESTING

- Statement: Help/support/legal/privacy pages
- Owner/priority/source: engineering / P2 / product directive WS-01
- Implementation: frontend/app/help/page.tsx frontend/app/support/page.tsx frontend/app/legal/page.tsx frontend/app/privacy/page.tsx frontend/components/static-page.tsx
- Tests: frontend/app/static-pages.test.tsx
- API/UI/DB: StaticPage
- Blocker: PKG-01 DEFERRED 2026-11-07
- Dependencies: none
- Classification: D primary / B
- Remaining gap: components + tests written, never executed (node EPERM)
- Root cause: PKG-01 DEFERRED: no hosted runner
- Engineering work: none unless hosted run finds defects
- Configuration: none
- Owner approval: YES
- Credentials/provider: no
- Acceptance: pages render; cross-links live; no invented channels
- Evidence required: hosted vitest log green for named files; then CLOSED
- Next (matrix): await PKG-01 re-approval; then push + observe
- Effort/risk: S / low — stdin/module checks already pass

## TEL-05 — TESTING

- Statement: Telecom investigation UI (4 views + admin panel)
- Owner/priority/source: engineering / P1 / telecom spec §6
- Implementation: frontend/components/telecom-section.tsx frontend/app/network/[txnId]/page.tsx frontend/app/investigations/[id]/page.tsx frontend/app/cases/[caseId]/page.tsx frontend/app/platform/page.tsx
- Tests: frontend/components/telecom-section.test.tsx
- API/UI/DB: TelecomSection
- Blocker: PKG-01 DEFERRED 2026-11-07
- Dependencies: none
- Classification: D primary / B
- Remaining gap: components + tests written, never executed (node EPERM)
- Root cause: PKG-01 DEFERRED: no hosted runner
- Engineering work: none unless hosted run finds defects
- Configuration: none
- Owner approval: YES
- Credentials/provider: no
- Acceptance: allocation/history/co-signals render; no verdicts
- Evidence required: hosted vitest log green for named files; then CLOSED
- Next (matrix): await PKG-01 re-approval; then push + observe
- Effort/risk: S / low — stdin/module checks already pass

## THEME-01 — TESTING

- Statement: Dark/light/system themes
- Owner/priority/source: engineering / P2 / L13 L01/P10
- Implementation: frontend/components/theme-provider.tsx frontend/components/theme-selector.tsx frontend/lib/theme.ts
- Tests: frontend/components/theme-provider.test.tsx frontend/lib/theme.test.ts
- API/UI/DB: none
- Blocker: PKG-01 DEFERRED 2026-11-07
- Dependencies: none
- Classification: D primary / B
- Remaining gap: components + tests written, never executed (node EPERM)
- Root cause: PKG-01 DEFERRED: no hosted runner
- Engineering work: none unless hosted run finds defects
- Configuration: none
- Owner approval: YES
- Credentials/provider: no
- Acceptance: mode switch persists + applies; tests green
- Evidence required: hosted vitest log green for named files; then CLOSED
- Next (matrix): await PKG-01 re-approval; then push + observe
- Effort/risk: S / low — stdin/module checks already pass

## UFI-UI — TESTING

- Statement: Tracing UI: trace + parties + typologies
- Owner/priority/source: engineering / P1 / universal §20
- Implementation: frontend/components/tracing-section.tsx frontend/lib/api.ts frontend/app/investigations/[id]/page.tsx
- Tests: frontend/components/tracing-section.test.tsx
- API/UI/DB: TracingSection
- Blocker: PKG-01 DEFERRED 2026-11-07
- Dependencies: none
- Classification: D primary / B
- Remaining gap: components + tests written, never executed (node EPERM)
- Root cause: PKG-01 DEFERRED: no hosted runner
- Engineering work: none unless hosted run finds defects
- Configuration: none
- Owner approval: YES
- Credentials/provider: no
- Acceptance: verbatim states; masked parties; gap flags
- Evidence required: hosted vitest log green for named files; then CLOSED
- Next (matrix): await PKG-01 re-approval; then push + observe
- Effort/risk: S / low — stdin/module checks already pass

## UFI-UI2 — TESTING

- Statement: Monitoring + industry UI sections
- Owner/priority/source: engineering / P1 / universal §20
- Implementation: frontend/components/monitoring-section.tsx frontend/components/industry-section.tsx frontend/lib/api.ts frontend/app/network/[txnId]/page.tsx frontend/app/platform/page.tsx
- Tests: frontend/components/monitoring-section.test.tsx frontend/components/industry-section.test.tsx
- API/UI/DB: MonitoringSection IndustrySection
- Blocker: PKG-01 DEFERRED 2026-11-07
- Dependencies: none
- Classification: D primary / B
- Remaining gap: components + tests written, never executed (node EPERM)
- Root cause: PKG-01 DEFERRED: no hosted runner
- Engineering work: none unless hosted run finds defects
- Configuration: none
- Owner approval: YES
- Credentials/provider: no
- Acceptance: verbatim states; NOT_READY renders as-is
- Evidence required: hosted vitest log green for named files; then CLOSED
- Next (matrix): await PKG-01 re-approval; then push + observe
- Effort/risk: S / low — stdin/module checks already pass

## I18N-02 — BLOCKED_EXTERNAL_DEPENDENCY

- Statement: Native human review of non-EN values
- Owner/priority/source: owner / P1 / D-020 locale gate
- Implementation: docs/UGLS_REVIEW_KIT
- Tests: none
- API/UI/DB: none
- Blocker: human translators
- Dependencies: none
- Classification: E primary / -
- Remaining gap: 17 detection.* keys x11 locales untranslated (en fallback covers); ar +32 extras
- Root cause: no native translators commissioned (owner action)
- Engineering work: merge translations after review; no code now
- Configuration: none
- Owner approval: ACTION
- Credentials/provider: no
- Acceptance: translators sign off
- Evidence required: translator sign-off per locale + merged dictionaries; then CLOSED
- Next (matrix): commission translator review
- Effort/risk: M / mistranslation of risk/security strings

## VIS-01 — BLOCKED_EXTERNAL_DEPENDENCY

- Statement: Visual fidelity to reference image
- Owner/priority/source: engineering / P1 / product directive S2/S10
- Implementation: none
- Tests: none
- API/UI/DB: none
- Blocker: reference image absent
- Dependencies: none
- Classification: E primary / B-after-receipt
- Remaining gap: no comparison performed; nothing implemented against it
- Root cause: reference image absent from Muse session
- Engineering work: compare + correct + screenshot after receipt
- Configuration: none
- Owner approval: ACTION
- Credentials/provider: no
- Acceptance: match verified against supplied reference
- Evidence required: diff register + corrections + real screenshots; then CLOSED
- Next (matrix): owner supplies image; then compare
- Effort/risk: M / visual drift from canonical reference

## AI-01 — BLOCKED_EXTERNAL_DEPENDENCY

- Statement: Live Meta provider integration verified
- Owner/priority/source: engineering / P1 / GAP-014/D-016
- Implementation: app/ai_adapter.py
- Tests: tests/test_ai_eval.py tests/test_ai_validation.py tests/test_ai_cost.py tests/test_ai_gateway.py
- API/UI/DB: /api/v1/investigations/{id}/ai-analysis
- Blocker: D-016 NO-LIVE recorded
- Dependencies: ['D-016']
- Classification: F primary / -
- Remaining gap: mock-transport only; no live provider call
- Root cause: PKG-04/D-016 NO-LIVE (settled direction)
- Engineering work: forbidden unless reopened: none
- Configuration: none
- Owner approval: REOPEN-ONLY
- Credentials/provider: YES
- Acceptance: real provider call succeeds
- Evidence required: reopen needs new approval + key + handshake; stays as-is
- Next (matrix): NO-LIVE settled; reopen needs new approval + key
- Effort/risk: S / billable usage if ever activated without caps

## AI-03 — BLOCKED_EXTERNAL_DEPENDENCY

- Statement: Model-driven agent planning
- Owner/priority/source: engineering / P2 / L14 §11
- Implementation: none
- Tests: none
- API/UI/DB: none
- Blocker: D-016 live model
- Dependencies: ['D-016']
- Classification: F primary / -
- Remaining gap: no model-driven planning (caller-specified per D-026)
- Root cause: D-016 NO-LIVE live model
- Engineering work: forbidden unless PKG-04 Option A approved
- Configuration: none
- Owner approval: REOPEN-ONLY
- Credentials/provider: YES
- Acceptance: planned run recorded + approved
- Evidence required: reopen path only; stays as-is
- Next (matrix): owner approves PKG-04 Option A
- Effort/risk: M / autonomy without approvals if ever activated

## AUTH-01 — NOT_STARTED

- Statement: Google OIDC federation
- Owner/priority/source: engineering / P1 / federation directive/owner plan
- Implementation: none
- Tests: none
- API/UI/DB: none
- Blocker: PKG-09 owner approval
- Dependencies: ['PKG-09']
- Classification: F primary / -
- Remaining gap: planned only; no code, no OAuth apps, no credentials
- Root cause: PKG-09 DEFERRED (UPDATE-002); existing auth preserved
- Engineering work: forbidden unless PKG-09 re-approved
- Configuration: none
- Owner approval: YES
- Credentials/provider: YES
- Acceptance: verified Google login via approved app
- Evidence required: reopen path only; stays NOT_STARTED
- Next (matrix): owner approves PKG-09; then implement
- Effort/risk: M / account-takeover via unsafe linking if ever rushed

## AUTH-02 — NOT_STARTED

- Statement: Apple OIDC federation
- Owner/priority/source: engineering / P1 / federation directive/owner plan
- Implementation: none
- Tests: none
- API/UI/DB: none
- Blocker: PKG-09 owner approval
- Dependencies: ['PKG-09']
- Classification: F primary / -
- Remaining gap: planned only; no code, no OAuth apps, no credentials
- Root cause: PKG-09 DEFERRED (UPDATE-002); existing auth preserved
- Engineering work: forbidden unless PKG-09 re-approved
- Configuration: none
- Owner approval: YES
- Credentials/provider: YES
- Acceptance: verified Apple login via approved app
- Evidence required: reopen path only; stays NOT_STARTED
- Next (matrix): owner approves PKG-09; then implement
- Effort/risk: M / account-takeover via unsafe linking if ever rushed

## AUTH-03 — NOT_STARTED

- Statement: Microsoft OIDC federation
- Owner/priority/source: engineering / P1 / federation directive/owner plan
- Implementation: none
- Tests: none
- API/UI/DB: none
- Blocker: PKG-09 owner approval
- Dependencies: ['PKG-09']
- Classification: F primary / -
- Remaining gap: planned only; no code, no OAuth apps, no credentials
- Root cause: PKG-09 DEFERRED (UPDATE-002); existing auth preserved
- Engineering work: forbidden unless PKG-09 re-approved
- Configuration: none
- Owner approval: YES
- Credentials/provider: YES
- Acceptance: verified Microsoft login via approved app
- Evidence required: reopen path only; stays NOT_STARTED
- Next (matrix): owner approves PKG-09; then implement
- Effort/risk: M / account-takeover via unsafe linking if ever rushed

## AUTH-04 — NOT_STARTED

- Statement: Yahoo OIDC federation
- Owner/priority/source: engineering / P2 / federation directive/owner plan
- Implementation: none
- Tests: none
- API/UI/DB: none
- Blocker: PKG-09 owner approval
- Dependencies: ['PKG-09']
- Classification: F primary / -
- Remaining gap: planned only; no code, no OAuth apps, no credentials
- Root cause: PKG-09 DEFERRED (UPDATE-002); existing auth preserved
- Engineering work: forbidden unless PKG-09 re-approved
- Configuration: none
- Owner approval: YES
- Credentials/provider: YES
- Acceptance: verified Yahoo login via approved app
- Evidence required: reopen path only; stays NOT_STARTED
- Next (matrix): owner approves PKG-09; then implement
- Effort/risk: M / account-takeover via unsafe linking if ever rushed

## AUTH-05 — NOT_STARTED

- Statement: Email OTP login
- Owner/priority/source: engineering / P1 / federation directive/owner plan
- Implementation: none
- Tests: none
- API/UI/DB: none
- Blocker: PKG-09 owner approval
- Dependencies: ['PKG-09']
- Classification: F primary / -
- Remaining gap: planned only; no code, no OAuth apps, no credentials
- Root cause: PKG-09 DEFERRED (UPDATE-002); existing auth preserved
- Engineering work: forbidden unless PKG-09 re-approved
- Configuration: none
- Owner approval: YES
- Credentials/provider: YES
- Acceptance: OTP issue/verify rate-limited + tested
- Evidence required: reopen path only; stays NOT_STARTED
- Next (matrix): implement in auth batch after go
- Effort/risk: M / account-takeover via unsafe linking if ever rushed

## AUTH-06 — NOT_STARTED

- Statement: Passwordless magic links
- Owner/priority/source: engineering / P2 / federation directive/owner plan
- Implementation: none
- Tests: none
- API/UI/DB: none
- Blocker: PKG-09 owner approval
- Dependencies: ['PKG-09']
- Classification: F primary / -
- Remaining gap: planned only; no code, no OAuth apps, no credentials
- Root cause: PKG-09 DEFERRED (UPDATE-002); existing auth preserved
- Engineering work: forbidden unless PKG-09 re-approved
- Configuration: none
- Owner approval: YES
- Credentials/provider: YES
- Acceptance: link issue/consume single-use + tested
- Evidence required: reopen path only; stays NOT_STARTED
- Next (matrix): implement in auth batch after go
- Effort/risk: M / account-takeover via unsafe linking if ever rushed

## AUTH-07 — NOT_STARTED

- Statement: Enterprise SSO (OIDC + SAML 2.0)
- Owner/priority/source: engineering / P1 / federation directive/owner plan
- Implementation: none
- Tests: none
- API/UI/DB: none
- Blocker: PKG-09 owner approval
- Dependencies: ['PKG-09']
- Classification: F primary / -
- Remaining gap: planned only; no code, no OAuth apps, no credentials
- Root cause: PKG-09 DEFERRED (UPDATE-002); existing auth preserved
- Engineering work: forbidden unless PKG-09 re-approved
- Configuration: none
- Owner approval: YES
- Credentials/provider: YES
- Acceptance: SSO login via approved IdP metadata
- Evidence required: reopen path only; stays NOT_STARTED
- Next (matrix): owner approves PKG-09; then implement
- Effort/risk: M / account-takeover via unsafe linking if ever rushed

## AUTH-08 — NOT_STARTED

- Statement: Safe federated account linking
- Owner/priority/source: engineering / P1 / federation directive/owner plan
- Implementation: none
- Tests: none
- API/UI/DB: none
- Blocker: PKG-09 owner approval
- Dependencies: ['PKG-09']
- Classification: F primary / -
- Remaining gap: planned only; no code, no OAuth apps, no credentials
- Root cause: PKG-09 DEFERRED (UPDATE-002); existing auth preserved
- Engineering work: forbidden unless PKG-09 re-approved
- Configuration: none
- Owner approval: YES
- Credentials/provider: YES
- Acceptance: unverified-link rejected; no privilege from claims
- Evidence required: reopen path only; stays NOT_STARTED
- Next (matrix): implement in auth batch after go
- Effort/risk: M / account-takeover via unsafe linking if ever rushed

## AUTH-09 — NOT_STARTED

- Statement: Password recovery (forgot/reset)
- Owner/priority/source: engineering / P1 / product directive WS-02
- Implementation: none
- Tests: none
- API/UI/DB: none
- Blocker: PKG-09 owner approval
- Dependencies: ['PKG-09']
- Classification: F primary / -
- Remaining gap: planned only; no code, no OAuth apps, no credentials
- Root cause: PKG-09 DEFERRED (UPDATE-002); existing auth preserved
- Engineering work: forbidden unless PKG-09 re-approved
- Configuration: none
- Owner approval: YES
- Credentials/provider: YES
- Acceptance: reset tokens single-use + tested
- Evidence required: reopen path only; stays NOT_STARTED
- Next (matrix): implement in auth batch after go
- Effort/risk: M / account-takeover via unsafe linking if ever rushed

## LIVE-GEO — BLOCKED_EXTERNAL_DEPENDENCY

- Statement: Live intel providers (identity/address/geo/map)
- Owner/priority/source: owner / P0 / geointel §10
- Implementation: none
- Tests: none
- API/UI/DB: none
- Blocker: D-053 NO-LIVE recorded
- Dependencies: ['D-016']
- Classification: F primary / -
- Remaining gap: adapters exist; no creds, no handshakes
- Root cause: D-053 NO-LIVE
- Engineering work: forbidden unless reopened per provider
- Configuration: none
- Owner approval: REOPEN-ONLY
- Credentials/provider: YES
- Acceptance: creds + connectivity + green requests + evidence
- Evidence required: reopen needs creds + handshake + approval; stays as-is
- Next (matrix): NO-LIVE settled; reopen needs creds + approval
- Effort/risk: M / location-privacy breach if mis-scoped

## TEL-08 — BLOCKED_EXTERNAL_DEPENDENCY

- Statement: Live telecom provider integrations
- Owner/priority/source: owner / P0 / telecom spec §3
- Implementation: none
- Tests: none
- API/UI/DB: none
- Blocker: D-053 NO-LIVE recorded
- Dependencies: ['D-016']
- Classification: F primary / -
- Remaining gap: adapters exist; no creds, no handshakes
- Root cause: D-053 NO-LIVE
- Engineering work: forbidden unless reopened per provider
- Configuration: none
- Owner approval: REOPEN-ONLY
- Credentials/provider: YES
- Acceptance: creds + connectivity + green requests + evidence
- Evidence required: reopen needs creds + handshake + approval; stays as-is
- Next (matrix): NO-LIVE settled; reopen needs creds + approval
- Effort/risk: M / subscriber-data exposure if mis-scoped

## UFI-AIMODEL — NOT_STARTED

- Statement: Model-backed AI generation (PII lane)
- Owner/priority/source: owner / P2 / universal §24
- Implementation: none
- Tests: none
- API/UI/DB: none
- Blocker: none
- Dependencies: none
- Classification: F primary / -
- Remaining gap: deterministic only; PII lane absent
- Root cause: D-054 DEFERRED (needs named model + data-flow + redaction)
- Engineering work: forbidden unless D-054 approved
- Configuration: none
- Owner approval: REOPEN-ONLY
- Credentials/provider: YES
- Acceptance: needs owner PII-processing approval
- Evidence required: reopen path only; stays NOT_STARTED
- Next (matrix): owner PII-processing approval
- Effort/risk: M / PII exfiltration to model provider

## UFI-LIVE — BLOCKED_EXTERNAL_DEPENDENCY

- Statement: Live financial providers (banks/rails/crypto)
- Owner/priority/source: owner / P0 / universal §22
- Implementation: none
- Tests: none
- API/UI/DB: none
- Blocker: D-053 NO-LIVE recorded
- Dependencies: ['D-016']
- Classification: F primary / -
- Remaining gap: adapters exist; no creds, no handshakes
- Root cause: D-053 NO-LIVE
- Engineering work: forbidden unless reopened per provider
- Configuration: none
- Owner approval: REOPEN-ONLY
- Credentials/provider: YES
- Acceptance: creds + connectivity + green requests + evidence
- Evidence required: reopen needs creds + handshake + approval; stays as-is
- Next (matrix): NO-LIVE settled; reopen needs creds + approval
- Effort/risk: L / financial-data scope + provider agreements

## Shared dependencies (no merges; requirements stay canonical)

- PKG-01/D-017 gates 13 rows: 8 TESTING + DET-12/13 + FE-01 + QA-02 (+DET-14/INF-01 ordering).
- D-018 gates AUD-01 + BAK-01.
- GAP-001 gates DET-03 + DB-01.
- D-053 NO-LIVE covers TEL-08 + LIVE-GEO + UFI-LIVE.
- D-016 NO-LIVE covers AI-01 + AI-03.
- PKG-09 DEFER covers AUTH-01..09.
- GAP-009/D-017 deploy approval gates DET-14 + INF-01 (+REL-02 after).
