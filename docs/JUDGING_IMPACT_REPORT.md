# JUDGING IMPACT REPORT (Category A — 30%)

## Problem (A1, A3)

Financial crime moves through networks of accounts, devices, IPs
and intermediaries, but transaction monitoring typically scores
each transaction in isolation. A ₦480,000 transfer can look
routine alone (demo: 35/100 MODERATE transaction-only) while
its network context is high-risk (demo: 84/100 HIGH). Isolated
scoring misses mule rings, layering chains and shared-device
fraud — or floods investigators with context-free alerts.

## Product (A4–A7)

CruiseShield AI is an evidence-centred investigation workbench:

- DETECT: deterministic rules (R-001…R-008) score every
  transaction reproducibly — no model randomness in the verdict.
- CONNECT: a 22-node / 30-edge relationship graph (demo
  figures) links accounts, devices, IPs and counterparties.
- INVESTIGATE → EXPLAIN: 39-record evidence packages with
  provenance; Meta AI explains the supplied evidence only.
- VERIFY → SIMULATE → HUMAN DECISION → AUDIT: the investigator
  verifies, rehearses, decides and leaves a traceable trail.

The deterministic engine is authoritative; AI assists; the
human is accountable. See docs/ARCHITECTURE.md.

## Users and beneficiaries (A2, A8)

Primary: fraud investigators and compliance analysts at banks,
fintechs, PSPs and microfinance institutions. Secondary:
financial-intelligence teams, auditors, regulators receiving
traced case files. End beneficiaries: customers protected from
scams and mule recruitment; institutions with lower fraud loss.

## Outcomes: demonstrated vs projected (A9, A10)

DEMONSTRATED (this repo, synthetic data): complete 8-stage
workflow runs end-to-end; scores reproduce exactly; evidence
IDs trace; audit records append. PROJECTED (not measured):
faster triage, fewer false positives, shorter investigation
cycles — plausible consequences of connected evidence, but no
pilot has run and no customer metrics exist. Nothing here
claims measured savings or deployments.

## Adoption path and constraints (A11, A12)

See docs/INSTITUTIONAL_ADOPTION_PATH.md. Hard constraints:
synthetic-data prototype; no core-banking/KYC connectors
built; auth demo-grade; single-tenant; Neon/RBAC/retention
work needed before any pilot (Phase 15 docs). Integration
requirements (APIs, mapping, reconciliation) are DESIGNED
(docs/PHASE_15_INTEGRATION_ARCHITECTURE.md), not built.

## Landing-page evidence

Problem, product definition, workflow, beneficiaries and CTA
are now on `/` (LandingChrome.tsx) with honest copy pinned by
LandingContent.test.tsx (8/8 green). No customer, performance
or coverage claims are made; illustrative visuals are labelled.
