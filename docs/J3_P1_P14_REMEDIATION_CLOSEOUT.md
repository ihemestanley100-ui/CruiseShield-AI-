# J3 — P1–P14 REMEDIATION CLOSEOUT

Each item: original defect (reproduced via defect-triggering test
input) → correction (exact file) → regression test → fresh result.
“Reproduced” = the cited test feeds the original defect trigger and
passes only with the fix present.

| P | Defect → correction | Test (fresh run) | Result |
|---|---------------------|------------------|--------|
| P1 | garbage `PG_CONNECT_TIMEOUT` crashed boot → `_safe_int` + clamp (`app/config.py`) | `test_config_safety.py` (3) | PASS |
| P2 | `Secure` dropped behind TLS proxy → honor `X-Forwarded-Proto` (`app/main.py`) | `test_auth.py` cookie ×3 | PASS |
| P3 | unknown txn leaked `StopIteration` → `UNKNOWN_TXN` 404 (`app/rules.py`) | `test_graph_rules_risk.py` boundary | PASS |
| P4 | follow-up POST hung (no abort) → dedicated abort + 35 s (`ai-panel.tsx`) | `ai-panel.test.tsx` hang test | PASS |
| P5 | FAILED run masked SUCCEEDED → skip non-SUCCEEDED (`app/main.py`) | `test_case_detail_skips_failed_run_for_latest` | PASS |
| P6 | no 403/expiry UX → `csai:unauthorized` + `/me` re-gate (`api.ts`, `login-gate.tsx`) | api + gate tests | PASS |
| P7 | quota message named limit only → used/limit + reset (`app/main.py`) | `test_ai_cost.py` assertions | PASS |
| P8 | AI mapping matrix untested → 6 loop-gated tests (`test_ai_validation.py`) + 1 usage test (closeout) | SKIP here (no loop); run CI | PARTIAL |
| P9 | route coverage gaps → direct twins run here + transport twins (`test_api_flow.py`) | direct green; transport SKIP, run CI | PARTIAL |
| P10 | uplift/DISTDIR/README/openGraph → all fixed + `resolveMetadataBase()` + `NEXT_PUBLIC_SITE_URL` (closeout) | 261/261 incl. 4 new site-url tests | PASS |
| P11 | gate + find_unknown_ids untested → `test_security_gate.py` (4) + `test_find_unknown_ids…` (closeout) | green | PASS |
| P12 | 7 stale-doc FAILs + pointers → dated addenda + closures (J3 + closeout: CONFLICT-001, COMMAND ×5, RENDER_6, README, ZERO_GAP) | doc diff review, no code behavior | PASS |
| P13 | `.gitignore` gaps → D2 + auditor patterns applied, `check-ignore` verified, examples spared | git verification | PASS |
| P14 | demo-scale boundaries unstated → KNOWN_LIMITATIONS (body cap, single-worker, shutdown/timeouts, DI wiring) | doc review | PASS |

**R1–R3** (suite reconciliation): CLOSED — fresh counts recorded
(341/103/1-blocked, 261/261, tsc, build 0).
**R4** (live AI): BLOCKED — key configured locally (count-verified,
value never read) but quota-spend approval + networked env outstanding;
no live call fabricated.
**R5** (staging): BLOCKED — blueprint corrected + parsed; provisioning
and deploy proof need owner approval.
