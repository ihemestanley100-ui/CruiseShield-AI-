# PHASE 15 — REGULATORY ASSESSMENT (Nigeria-first, identification only)

STATUS: This is a REQUIREMENTS IDENTIFICATION document, not legal advice and not a compliance finding. Every item needs qualified Nigerian legal/regulatory review before any pilot. No compliance or certification is claimed.

## Applicable regimes and regulators (Nigeria)
| Area | Law / regulation (identify + verify currency) | Regulator / authority |
|---|---|---|
| Data protection | Nigeria Data Protection Act 2023 (NDPA); NDPC General Application & Implementation Directive | Nigeria Data Protection Commission (NDPC) |
| AML/CFT | Money Laundering (Prevention & Prohibition) Act 2022; CBN AML/CFT/CPF Regulations for banks/OFIs; NFIU reporting rules | CBN, NFIU, EFCC/ICPC (enforcement) |
| Financial intelligence / STRs | NFIU Act 2018; STR/CTR filing obligations | NFIU (via institutions' compliance officers) |
| Banking supervision | Banks and Other Financial Institutions Act 2020; CBN Risk-Based Supervision framework | CBN |
| Cybersecurity | Cybercrimes (Prohibition) Act 2015 as amended 2024; CBN Cybersecurity Framework; NDPC cloud/outsourcing expectations | CBN, ONSA/NG-CERT, NDPC |
| Records retention | CBN AML record-keeping (≥5 years typical for transaction/CDD records — verify current instrument) | CBN / NFIU |
| Cross-border data | NDPA transfer rules + adequacy/contractual safeguards | NDPC |
| Outsourcing/cloud | CBN outsourcing guidelines; institution's vendor-risk policy | CBN + institution board |
| Consumer protection | CBN Consumer Protection Regulations; FCCPA 2018 (competition/consumer) | CBN, FCCPC |

## Product-specific regulatory touchpoints
1. The AI explanation feature processes personal/financial data → NDPA lawful basis, purpose limitation, DPIA likely required.
2. Risk scores + AI outputs inform (never make) STR/escalation judgments → human-authority design HELPS but needs documented procedures + training records.
3. Cross-border model API calls (Meta Model API) = potential cross-border transfer → transfer mechanism + vendor DPA required.
4. Audit immutability claims must match implemented controls (currently append-only JSON — insufficient as a compliance record without hardening).
5. Any automated decisioning (freezes, closures) is OUT OF SCOPE for the product and must remain so contractually.

## Legal/regulatory questions register (for professional review)
- LQ-01: DPIA triggers and NDPC filing expectations for this processing?
- LQ-02: Exact retention schedule + admissible storage for investigation records?
- LQ-03: Cross-border transfer instrument for model-API processing (and fallback if unavailable)?
- LQ-04: CBN outsourcing approval path for a SaaS/self-hosted deployment?
- LQ-05: Evidentiary standards for system-generated investigation records?
- LQ-06: Incident/breach notification clocks (NDPC 72h? CBN cyber-incident windows — verify)?
- LQ-07: Model-risk/explainability expectations under CBN supervision for scoring systems?
- LQ-08: IP/data ownership + return/destruction terms for pilot agreements?
