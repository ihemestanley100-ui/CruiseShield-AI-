# HACKATHON_FINAL_DEMO_SCRIPT — 3-minute recorded demonstration

Target duration 3:00 at a natural speaking pace (~135 wpm; ~410 spoken
words below). All data synthetic. Route sequence, key messages,
architecture/Meta AI/new-work explanations, disclaimer, recording
checklist, and backup sequence included. No video has been recorded yet.

## Spoken script with screen directions

### 00:00–00:20 — THE PROBLEM [screen: landing hero]

"Financial investigators drown in disconnected data. One suspicious
transfer means nothing until you connect the accounts, devices, phones,
and merchants behind it — work that takes analysts hours of manual
tracing across fragmented tools."

[Click Explore / Enter Demo → Command Center.]

### 00:20–00:40 — THE SOLUTION [screen: /demo]

"CruiseShield AI is an evidence-centred investigation platform. A
deterministic risk engine scores what it observes, Meta AI explains the
evidence in plain language, and a human investigator makes every
decision — with each step audited. Everything you see is synthetic demo
data."

### 00:40–01:15 — DETECT AND CONNECT [screens: /investigations/inv_84721 → /network/txn_84721]

"Detection: transfer 84721 — 480,000 naira by mobile app. The engine
scores it 35 out of 100 alone — but 84, HIGH, once its network is
connected, with eight triggered rules from R-001 to R-008.
[Jump to section nav: Why this risk?]
Connection: twenty-two nodes, thirty edges, zero provenance errors —
one device shared across three accounts."

### 01:15–01:55 — INVESTIGATE AND EXPLAIN [screen: investigation, Evidence → AI analysis]

"Thirty-nine evidence records, each with event, edge, and rule
provenance. Now the explanation: [click Run AI analysis] Muse Spark
reads only this package and returns a validated report — findings tied
to evidence IDs, alternative explanations, and what is still missing.
Advisory only: it never changes the score."

### 01:55–02:25 — VERIFY, SIMULATE, HUMAN DECISION [screens: /replay/scn_primary → /cases/case_84721]

"What-if simulation ignores suspect links and re-scores: 84 down to 72
 — still HIGH — clearly labelled simulated, never overwriting the
baseline. The human decides here, with a recorded reason; the form you
see submits a real, audited decision."

### 02:25–02:45 — AUDIT AND IMPACT [screen: /cases/case_84721/audit]

"Every action lands in an append-only audit trail — actor, state change,
reason. For a bank, this means hours of tracing compressed into minutes,
with evidence a regulator can replay."

### 02:45–03:00 — CLOSING [screen: audit → landing]

"Deterministic scoring, evidence-grounded AI, human authority, full
provenance. CruiseShield AI: the financial crime immune system."

## Key messages for judges

1. Deterministic engine is authoritative; AI explains, never scores.
2. Every AI claim is validated against supplied evidence IDs.
3. Humans decide; the audit trail proves it.
4. Synthetic data, honestly labelled, reproducible in one command.

## Architecture (if asked)

Next.js frontend → FastAPI backend → JSON demo store; Muse Spark via a
server-side adapter (key never leaves the server); risk engine, evidence
assembler, and AI are separate modules with tested boundaries.

## Meta AI contribution (if asked)

Muse Spark performs evidence-grounded analysis: summary, findings with
citations, alternatives, missing information, next steps. Output is
schema- and reference-validated; invented IDs, scores, and enforcement
language are rejected. Verified live: agentrun_0003, SUCCEEDED,
VALIDATED/VALIDATED. See HACKATHON_META_AI_CONTRIBUTION_REPORT.

## New-work explanation (if asked)

Describe only what HACKATHON_NEW_WORK_CONTRIBUTION_REGISTER verifies.
Do not present pre-existing capabilities as hackathon work.

## Synthetic-data disclaimer (show or speak once)

"All transactions, people, devices, and AI outputs in this demo are
synthetic fixtures. No real customer data is used."

## Recording checklist

1. Back up state: `Copy-Item data\state.json data\state.json.prevideo`.
2. Start backend :8000 + production frontend :3000; confirm health.
3. Fresh browser profile; 1440×900; system theme (light records best).
4. Run the route sequence once silently (warm caches, settle badge).
5. Record in one take if possible; keep mouse movement slow.
6. Restore state: `Move-Item data\state.json.prevideo data\state.json -Force`;
   verify hash `BA1D4DB4…3790FE` + 101417 bytes.
7. Never show `.env`, keys, or terminal output containing secrets.

## Backup sequence (no live API connectivity)

Skip the live click at 01:15–01:55. Instead open the case page and read
stored run agentrun_0002 (SUCCEEDED, VALIDATED): "A recorded analysis
from the same integration — findings, evidence IDs, and missing
information." Say explicitly it is a recorded run, not a live call.
Everything else is unchanged; simulation and decision need no AI.
