# GOVERNANCE IDENTIFIER RECONCILIATION — CruiseShield AI™

Date: 2026-11-08 · Package: PKG-M3A (M3A-02) · Branch:
`feat/phasezero-foundations` @ `e8058e5` · Status: PROPOSAL —
no identifier has been renamed, no record has been rewritten, and no
proposal below takes effect without explicit owner approval.

## 1. Purpose

The repository and its session history use many overlapping identifier
namespaces (milestones, gates, levels, decisions, evidence). This
document inventories them, records the conflicts verbatim, preserves
every historical identifier, and proposes one future naming convention.
It does not modify the canonical matrix, the decision log, or any
existing record.

## 2. Canonical repository namespaces (do not rename)

| Namespace | Authority | Examples | Notes |
|---|---|---|---|
| Matrix IDs (`DET-01` …) | `docs/ZERO_GAP_MATRIX.json` (192 rows) | 40 prefixes incl. `DET-`, `UFI-`×26, `SEC-`×16, `IND-`×45, `AUTH-`×12 | Sole requirement authority; statuses change only with evidence |
| `D-001`…`D-053`, `D-058` | `CRUISESHIELD-AI-DECISION-LOG.md` | `D-014` tenancy, `D-018` backup drill, `D-020` pins | `D-054`…`D-057` are cited in session history but absent from the log |
| `PKG-01`, `PKG-04`, `PKG-09` | Decision log + `docs/LEVEL14_OWNER_APPROVAL_PACKAGES.md` | `PKG-01` publication (EXECUTED, PR #2) | `PKG-02/03/05/06/07/08` and `PKG-M3A` are session-level until recorded |
| `GAP-001`, `GAP-015` | Decision log | `GAP-001` PostgreSQL HOLD | — |
| `B1`, `B10` | Decision log, batch docs | `B1` push/PR batch, `B10` billing readings | `B1` is a string prefix of `B10`: always match with a word boundary |
| `QA-02`, `B7`, `S1`, `S2`, `Q1` | Batch/risk docs (`docs/BATCH1_*`, `docs/POST_Q1_*`) | `B7` scratch-PG approval, `S1` profile quarantine | Cited in docs but absent from the decision log |
| `L10`…`L14` layers | `docs/ARCHITECTURE.md:62-70` | L10 AI, L11 Industry, L12 Governance, L13 Operations, L14 Evolution | Architecture layers — not maturity levels, not milestones |
| `G-COMMIT`…`G-RELEASE` | `docs/FINAL_DEPLOYMENT_GATE_REGISTER.md` | `G-PUSH` EXECUTED 2026-11-03 | Bound to the 11-03 `production-launch` release; do not reopen |
| `E-Mx`/`F-Mx`/`I-Mx`/`W-Vx` | `docs/CRUISESHIELD_MASTER_EVIDENCE_REGISTER.md` | `E-M1` Meta docs, `F-M2` 49 offline tests | Evidence IDs; the `-M` suffix collides visually with milestones |
| `REL-M1`…`REL-M5` | `docs/CANONICAL_FILE_MANIFEST.md:251-260` | `REL-M3` matrix reconciliation | Manifest work items, not milestones |
| `J1`…`J10`, `J11-xx` | `docs/J*_*.md`, `docs/FINAL_ZERO_GAP_MATRIX.md` | `J11-25` hackathon directive | Job-series audit trail |
| `R-01`…`R-10`, `R5/R6`, `R09-F1…F8` | Execution state, gate register | `R-09` security fixes | Workstream/inspection series |
| `G-P4/G-P5` | `docs/RENDER_10_RELEASE_GATES.md:16` (Phase 15 prod gates) | Institutional gates | Phase-15 production gate series |
| `A`…`J` staging gates | `docs/STAGING_GATE_A_TO_J.md` | Staging acceptance | Distinct from all `G-` series |
| `RENDER_1`…`RENDER_10` | `docs/RENDER_1_*.md`…`docs/RENDER_10_*.md` | `RENDER_10_RELEASE_GATES.md` | Numbered doc series, not gate IDs |

## 3. Session-level namespaces (not yet canonical records)

These exist in session/directive history. Where a directive cites them
as authority, that authority is session-level only until recorded.

| Namespace | Meaning in session history | Repository footprint |
|---|---|---|
| `M1`…`M7` milestones | M1 B10 text acceptance … M7 end-to-end acceptance | `M1` recorded in the decision-log M1 entry; `M2`…`M7` unrecorded (incl. `M2B`…`M2K`, `M3A-01/02`) |
| `PRA-001`, `PRA-002` | Production-readiness audits | `PRA-002` cited in the M1 log entry; neither has a repository report file |
| Architecture `Levels 0`…`6` | M3–M7 execution levels | Absent from the repository; distinct from `L10`–`L14` layers |
| Release gates `G01`…`G12` | Product-grade readiness gates | Absent as a defined series (see §4 conflicts) |
| `G13` subscription assurance | Proposed 13th gate | Absent as defined; `G13` already means two other things (§4) |

## 4. Conflicts (verbatim, unresolved)

1. **`G13` has three meanings.** (a) `docs/MASTER_REMAINING_GAP_REGISTER.md:17`:
   `G13` = "Logo rights memo (Q-IP-1)". (b) `docs/RELEASE_GAP_AUDIT.md:40`:
   `G13` = "AI observability" (PARTIAL). (c) Session history: `G13` =
   subscription assurance gate. (a) and (b) are both repository records
   and directly contradict; (c) is session-only.
2. **`G01`–`G12` has four meanings.** (a) `docs/FINAL_ZERO_GAP_MATRIX.md:123`
   (`J11-25`): hackathon execution directive `C01-C06, G01-G12`. (b)
   `docs/GEOINTELLIGENCE_OS.md:163-167`: geointel work groups
   `G01`…`G08` (e.g. `G08` maps). (c) `docs/DEMO_PRODUCTION_AUDIT.md`:
   demo dispositions `G1`–`G10` (unpadded). (d) Session history:
   `G01`–`G12` product-grade release gates. No repository document
   defines (d).
3. **Ambiguous cross-references.** `docs/RELEASE_GAP_AUDIT.md:10`
   ("`G10/G12/G13` closed by the mandate") and
   `docs/FINAL_ZERO_GAP_MATRIX.md:144` ("`G05/G08` PASS") do not name
   which `G-` series they cite; each has ≥2 plausible readings.
4. **`M-` prefix has four families.** Chat milestones `M1`–`M7` (+
   `M2B`…`M2K`, `M3A`), manifest items `REL-M1`…`REL-M5`, evidence IDs
   `E-Mx`/`F-Mx`/`I-Mx`, and matrix-adjacent `M` mentions. Bare `Mn`
   is ambiguous without its family prefix.
5. **`L-` prefix has two families.** Architecture layers `L10`–`L14`
   (`docs/ARCHITECTURE.md`) vs session execution Levels `0`–`6`.
   "L14"/"Level 14" additionally denotes the continuous-evolution
   milestone family (`docs/LEVEL14_OWNER_APPROVAL_PACKAGES.md`).
6. **Decision-log gaps.** `D-054`…`D-057`, `PKG-02/03/05/06/07/08`,
   `B7`, `B9`, `S1`, `S2`, and the `M2B`…`M2K` acknowledgments are
   acted upon in session history but have no decision-log entry.

## 5. Proposed convention (PROPOSAL — requires owner approval)

1. The 192-row matrix keeps its IDs forever; new requirements take the
   next number in their existing family prefix, never a recycled ID.
2. The decision log remains the only place that mints `D-` and `PKG-`
   identifiers; session-level `PKG-`/`B-`/`S-` items are proposals
   until logged.
3. Historical `G-` references stay verbatim but new citations must
   qualify the series: `HACKATHON-G01`, `GEOINTEL-G08`, `DEMO-G1`,
   `DEPLOY-G-PUSH`, `RELEASE-G01` (only after the release-gate series
   is defined in a repository document).
4. `G13` must never appear bare; qualify as `GAPREG-G13` (logo memo),
   `RELAUD-G13` (AI observability), or `RELEASE-G13` (proposal).
5. Milestones use family prefixes: `MS-M1`… for execution milestones,
   keeping `REL-Mx` (manifest) and `E-/F-/I-Mx` (evidence) untouched.
6. Architecture layers stay `L10`–`L14`; execution levels, if adopted,
   are written `LVL-0`…`LVL-6` and defined in one repository document.
7. `B1`/`B10`, `D-019`/`D-019b`, `R5`/`R-05`-style near-collisions
   must be matched and cited with exact full IDs and word boundaries.

## 6. Cross-reference map (current)

- `MS-M1` (recorded) → decision-log "B10 TEXT-BASED EVIDENCE
  ACCEPTANCE" entry; `PRA-002` (cited there) → session history only.
- `PKG-01` (recorded, EXECUTED) → PR #2, commits `d0afd7a`,
  `152df0e`, `e8058e5`; `M2B`…`M2K` + `M3` reviews → session history.
- `MS-M3A` (this package, unrecorded) → `M3A-01` lint gates
  (`pyproject.toml`, `ruff check .`, CI step), `M3A-02` this document.
- `GEOINTEL-G08` → matrix `MAP-02` (TESTING); `HACKATHON-G01…G12` →
  `J11-25` (PARTIAL); `DEMO-G1/G10` → `D-019` retain dispositions.
- `GAPREG-G13` → `Q-IP-1` memo; `RELAUD-G13` → AI observability
  (PARTIAL); `RELEASE-G13` → unapproved proposal.

## 7. Recommended next governance actions

1. Owner approves or amends §5 (one decision, no code).
2. If approved, log the missing decisions (`D-054`…`D-057`,
   `PKG-02/03/05/06/07/08`, `B7`, `S1`, `S2`) or confirm they stay
   session-level.
3. If the release-gate series is wanted, define `RELEASE-G01`…`G13`
   in one repository document before any gate verdict cites them.
