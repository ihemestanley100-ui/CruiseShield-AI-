# FINAL GLOBAL I18N AUDIT (R13)

Date: 2026-11-02. This workstream is closed by the UGLS-02 programme;
this audit reconciles (no re-implementation).

## Verdicts

| Check | Status | Evidence |
| ----- | ------ | -------- |
| Selectable registry (ISO 639 / BCP 47, native scripts, variants) | PASS | 221 entries, unique `Intl.Locale`-valid tags; searchable selector with keyboard + screen-reader support |
| Translation catalogues, all namespaces | PASS | 571 keys / 22 namespaces; en source + fr/ar complete + 9 core drafts; parity gate enforced by suite |
| Missing-key detection + English fallback | PASS | Ledger + `[key]` markers; mixing test; zero markers in 8-page browser matrix |
| RTL rendering | PASS | Edge matrix (ar ×3 breakpoints, ha-Arab script subtag); `<bdi>` timestamp isolation; before/after screenshots |
| Unicode / complex scripts | PASS | Arabic/Ajami/CJK/Devanagari verified visually; UTF-8 DOM capture |
| Locale dates/numbers/currency | PARTIAL | `format.ts` locale-aware formatting retained; data timestamps verbatim ISO by design; no currency conversion |
| Persistent preferences | PASS | localStorage + browser-detect + `?locale=` override; real-browser proof (override + cross-navigation persistence) |
| Coverage reporting | PASS | `UGLS_COMPLETE_TRANSLATION_COVERAGE.md` + generated 221-row matrix + key inventory (5128 lines) |
| No broken workflows | PASS | 321/321 frontend + 463/463 backend; en byte-identical; state hash unchanged (321 = UGLS-02's 320 + the R07 CSP header test, added same day post-acceptance) |

## Standing items

Human translation review (register provided; reviewers/date pending),
armed-session locale check (needs staging). Verdict: R13 PASS (see
`docs/UGLS_RELEASE_ACCEPTANCE.md`: accepted with documented
limitations).
