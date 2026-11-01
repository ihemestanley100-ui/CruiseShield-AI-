# Impact Case — who benefits and why it matters

## Problem

Transaction-monitoring teams triage isolated alerts: one row, one amount,
no context. Networked abuse (shared devices, phones, mules, merchants)
hides across those rows, so analysts either miss connected fraud or burn
hours stitching it together in spreadsheets. False positives cause
customer friction; missed networks cause real loss.

## Who benefits

- **Fraud/AML analysts** — one investigation surface: alert → network →
  evidence → explanation → what-if → decision → audit, instead of five tools.
- **Investigation leads** — every decision carries reason, evidence, and an
  append-only audit trail a regulator can replay.
- **Small PSPs/fintechs** — deterministic, explainable rules over their own
  data, without a data-science team or a black-box vendor score.

## Why this approach matters

1. **Network over row.** txn_84721 looks like one ₦480,000 transfer
   (35 MODERATE alone); the network scores 84 HIGH via shared device,
   phone, beneficiary, and merchant links. That gap is the product.
2. **Explainable by construction.** Every point of score traces to a
   versioned rule and a cited evidence ID — no black box to defend.
3. **AI advises, never authorizes.** The model explains supplied evidence
   under schema + reference validation; scores, cases, and actions stay
   deterministic and human-approved. Wrong-model-output cannot move money.
4. **Honest about uncertainty.** Ambiguous (38 MODERATE) and false-positive
   scenarios ship alongside the suspicious one; limitations print on-screen.

## Measured signals (synthetic, local — not customer results)

- Rule engine: 0.109 ms/eval, 200/200 byte-identical (determinism test).
- AI: 4/4 live SUCCEEDED runs, schema + refs VALIDATED, 12.9–16.7 s.
- Demo path: 9 steps, ~6 minutes, fully reproducible via seeded reset.

## Pilot path (proposed, not started)

1. Read-only shadow mode on historical alerts: compare rule hits + AI
   explanations against analyst dispositions for 2–4 weeks.
2. Measure: triage time per alert, network-find rate, overturn rate.
3. Graduate to assisted triage with human approval retained; audit stays.

## Limitations (stated, not hidden)

Synthetic data only; no production PII handling proven; no auth beyond
demo trust boundary; hosted persistence/backup unproven until deploy.
