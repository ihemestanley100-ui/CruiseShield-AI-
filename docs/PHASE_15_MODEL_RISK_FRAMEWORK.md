# PHASE 15 — MODEL RISK FRAMEWORK

SCOPE: governs BOTH the deterministic risk engine and the Meta AI explanation layer. No real-world effectiveness is claimed (no measurements exist).

## Risk register
| Risk | Control (designed) | Residual |
|---|---|---|
| False positives → investigator overload | Threshold tuning on golden cases; precision/recall tracking (see metrics) | Tuning data doesn't exist yet — pilot must collect it |
| False negatives → missed crime | Second-eyes sampling of cleared alerts; never auto-clear above LOW | Human capacity bounds the control |
| Bias (segment/region/channel skew) | Segmented performance reporting; bias review gate per release | No baseline; first measurement IS the pilot finding |
| AI hallucination (invented evidence) | Evidence-ID validators (implemented + tested); citation grounding checks; temp 0 | Live red-team outstanding (D-005) |
| Human overreliance ("AI said so") | Mandatory independent rationale field; UI keeps scores + AI text visually distinct; training | Cultural — needs audit sampling to verify |
| Data quality / drift | Ingest validation + reject-with-reason; feature-distribution monitoring; versioned engine | Monitors not built |
| Score governance | Engine versions pinned + golden-case regression (35/84 invariants); changes go through release process | Process exists on paper only |
| Independent validation | Pre-pilot validation by party independent of builders; periodic revalidation | Not performed |

## Hard prohibitions (contractual + technical)
AI must never: declare a person guilty; freeze funds or trigger punitive actions; alter authoritative risk scores; fabricate evidence; operate without a named accountable human. Current product enforces the technical side (validators, approval gate, score ownership); the pilot contract must enforce the rest.

## Monitoring (minimum viable)
Per-release: golden-case pass, segmented precision/recall, grounding rate, override rate (human disagrees with AI framing), latency. Alert on drift beyond agreed bands; rollback on breach. No pilot dashboards exist yet — build before go-live.
