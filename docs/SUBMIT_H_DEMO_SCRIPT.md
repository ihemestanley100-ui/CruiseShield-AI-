# H. COMPLETE THREE-MINUTE DEMONSTRATION SCRIPT (final)

SOURCE: reconciled from `docs/HACKATHON_FINAL_DEMO_SCRIPT.md` (routes re-verified 200; L2 proves the decision submit; agentrun_0003 retained). ~410 words ≈ 3:00 at ~135 wpm. All data synthetic. NO video recorded yet.

## Pre-record (recovery + integrity)
1. Pre-video backup to TEMP (never inside `data/`): `Copy-Item data\state.json $env:TEMP\prevideo-state.json`; record hash (expect BA1D4DB4…3790FE, 101417 B).
2. Start backend :8000 + PROD frontend :3000 (never dev concurrently — evicts `.next`); confirm `/api/v1/health` + `/` = 200.
3. Fresh browser profile, 1440×900, light/system theme. Silent dry-run of the route sequence (warm caches).
4. Record one take, slow mouse. NEVER show `.env`, keys, or secret-bearing terminals.
5. Post-record: restore `Copy-Item $env:TEMP\prevideo-state.json data\state.json -Force`; re-verify hash + bytes. Any deviation → investigate before submitting.
6. Failure recovery: backend hung → restart (state reloads from disk); AI fails → backup sequence below; port busy → verify ownership, never kill blindly.

## Spoken script + screens
### 00:00–00:20 PROBLEM [landing hero]
"Financial investigators drown in disconnected data. One suspicious transfer means nothing until you connect the accounts, devices, phones, and merchants behind it — work that takes analysts hours of manual tracing across fragmented tools." [Click Explore → Command Center.]

### 00:20–00:40 SOLUTION [/demo]
"CruiseShield AI is an evidence-centred investigation platform. A deterministic risk engine scores what it observes, Meta AI explains the evidence in plain language, and a human investigator makes every decision — with each step audited. Everything you see is synthetic demo data."

### 00:40–01:15 DETECT + CONNECT [/investigations/inv_84721 → /network/txn_84721]
"Detection: transfer 84721 — 480,000 naira by mobile app. The engine scores it 35 out of 100 alone — but 84, HIGH, once its network is connected, with eight triggered rules R-001 to R-008. [Section nav.] Connection: twenty-two nodes, thirty edges, zero provenance errors — one device shared across three accounts."

### 01:15–01:55 INVESTIGATE + EXPLAIN [investigation: Evidence → AI analysis]
"Thirty-nine evidence records, each with event, edge, and rule provenance. Now the explanation: [Run AI analysis] Muse Spark reads only this package and returns a validated report — findings tied to evidence IDs, alternative explanations, and what is still missing. Advisory only: it never changes the score."

### 01:55–02:25 VERIFY + SIMULATE [/replay/scn_primary → /cases/case_84721]
"What-if simulation ignores suspect links and re-scores: 84 down to 72 — still HIGH — clearly labelled simulated, never overwriting the baseline. The human decides here, with a recorded reason; the form submits a real, audited decision." [Submit live; decision + audit appear.]

### 02:25–02:45 HUMAN DECISION + AUDIT [/cases/case_84721/audit]
"Every action lands in an append-only audit trail — actor, state change, reason. For a bank, hours of tracing compressed into minutes, with evidence a regulator can replay."

### 02:45–03:00 CLOSING [audit → landing]
"Deterministic scoring, evidence-grounded AI, human authority, full provenance. CruiseShield AI: the financial crime immune system. Built during this hackathon on Meta's models — greenfield code, live integration, human decisions."

## Backup sequence (no live API at record time)
Skip the live click; open the case page and read stored run agentrun_0002 (SUCCEEDED, VALIDATED): "A recorded analysis from the same integration." Say EXPLICITLY it is recorded, not live. Everything else unchanged.

## Required outputs (verify each while recording)
35/MODERATE + 84/HIGH shown · R-001…R-008 · 39 records · 22n/30e · AI report with citations + missing info · sim 72/HIGH labelled simulated · decision_ recorded + audit event · hash restored after.
No invented customers, savings, deployments, or production claims — anywhere.
