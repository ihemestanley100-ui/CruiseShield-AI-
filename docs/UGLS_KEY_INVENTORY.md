# UGLS-02 Task 1 — Translation-Key Inventory & Missing-Key Report

Date: 2026-11-02. Source of truth: `frontend/lib/i18n/locales/en.ts`
(575 keys) via `englishKeyPaths()` / `coverageFor()` — the same functions
the parity gate test executes. Raw dump:
[UGLS_KEY_INVENTORY_GENERATED.txt](UGLS_KEY_INVENTORY_GENERATED.txt)
(EN_KEYS + full key list + per-locale missing lists, 5128 lines).

## Extraction scope (Task 1)

Every application route and converted component was inspected: demo,
investigation, network, replay, evidence, audit, notifications,
authentication, decision workflows, forms, errors, modals, tables, empty
states, tooltips, loading states, accessibility labels. All genuinely
user-facing chrome now resolves through namespaced `t()` / `tp()` calls.

Deliberately NOT extracted (data, never chrome): authoritative financial
evidence values, transaction/account/evidence/audit IDs, immutable audit
record content, deterministic risk scores and bands, server rule
explanations, model IDs, timestamps, counts. These render verbatim in
every locale — verified by the RTL DOM dumps (`verbatim-id=True`, zero
`[key]` markers on all 8 pages).

## Namespace inventory (22 namespaces, 575 keys)

| Namespace | Keys | UI area |
| --------- | ---- | ------- |
| landing | 111 | Landing hero, journey, capabilities, regions, footer |
| command | 78 | Command Center KPIs, briefs, previews, features |
| graph | 54 | Graph + orbital explorers, legends, relation table |
| intel | 41 | Device / IP / geo intelligence panels |
| case | 37 | Case workspace, AI assessment, decisions, audit page |
| replay | 31 | Replay controls, scenario reset, simulation target |
| nav | 25 | Sidebar, brand, session, quick actions |
| investigation | 21 | Investigation header, risk strip, tabs |
| demo | 20 | Demo dashboard sections, hero copy, backend states |
| sim | 18 | What-if simulation panel |
| network | 16 | Network page header, overlay states |
| ai | 16 | AI analysis panel, follow-up Q&A |
| common | 13 | Shared loading / retry / empty / unknown states |
| evidence | 13 | Evidence package search, filters, provenance |
| system | 12 | System status rows |
| audit | 12 | Audit list headers, captions, plural events |
| decision | 12 | Human decision form |
| selector | 10 | Language selector chrome + status tags |
| workflow | 9 | Workflow strip stages |
| notify | 9 | Notification bell + panel |
| auth | 9 | Login gate card |
| theme | 4 | Theme selector |

Total: 575. No key is referenced by components without existing in
`en.ts` (missing-in-English renders `[key]` and is ledger-tracked as a
product bug; the full browser matrix recorded zero markers).

## Missing-key report

- All eleven dictionaried locales (fr, ar + nine drafts): 0 missing
  (exact parity, enforced by `coverage.test.ts` → "holds every
  dictionaried locale at exact key parity"; corrected 2026-11-02 —
  drafts completed during UGLS-02 final, earlier 505-missing figures
  superseded).
- Fallback/ledger machinery stays covered via undictionaried locales:
  misses fall back to English AND are recorded in the missing-key
  ledger (`getMissingKeys()`), surfaced in tests, never hidden.
- Remaining 207 registry languages: no dictionary; whole-UI English
  fallback with selector "English fallback" badge (a known registry
  status, not per-key gaps — by design, ledger stays quiet).

Plural-form keys resolve whole-map with English fallback (`lookupForms`)
and degrade missing categories to `other`, never to nothing. All 8
plural maps (audit.events, command.activityEvents, graph.relationships,
graph.droppedEdges, intel.findingsCount/obsCount/accountCount/
candidateFindings) are complete in all 12 dictionaries (kit-verified).

## Late key changes (UGLS-02 RTL hardening)

Six timestamp templates were split so ISO values render inside `<bdi>`
(RTL isolation; English textContent byte-identical, proven by unchanged
text pins): `updatedPost→updatedPre`, `decidedBy→decidedByPre`,
`overviewLine→overviewLinePre`, `observedLine→observedPre/observedPost`,
`checkedLine→checkedPre`, `detailValid→detailValidPre/Arrow/Post`.
fr/ar carry the identical splits (parity gate green). Net key delta: +3
(571 total).
