# FREE-TIER & FINANCIAL AUDIT — Release Cert v3.0

- Date: 2026-11-04. Policy: hard $0.00/month ceiling. No billing changes made.

## Evidenced position (owner dashboard read-outs, prior sessions)

| Item | Evidence |
|---|---|
| Workspace | Hobby, displayed $0 |
| Current / projected charges | $0.00 / $0.00 (November) |
| Payment method | Present (Visa ••8142 — presence only) |
| Free instance hours | 1.82 / 750 |
| Bandwidth | 0 MB / 5 GB |
| Pipeline minutes | 0 / 500 |
| Frontend service | None provisioned |
| October invoice | $0.00 paid |

## Exposure analysis

- Observed + projected cost: $0.00. Guaranteed $0.00: **NOT established**.
- Uncapped residual risk: Render bills usage beyond included limits; no
  bandwidth-overage cap was found in official research. A payment method is on
  file, so overage *can* charge. Pipeline spend caps do not cover bandwidth.
- Free-instance exhaustion suspends services (availability risk, not cost).
- Meta API: paid-only (~$0.02/call at Standard rates); no free allowance
  established → excluded from $0 posture until separately approved.

## Pending owner read-outs (R1/R2/R11/R12)

Env-var presence (3 names), full 40-char deployed SHA, services-page plan/price
list, pipeline spend-cap value. No account access on my side.

## Verdict: PILLAR 06 — PARTIAL (current $0 evidenced; future $0 not guaranteed)

## Release closure FRC-001 addendum (2026-11-04)

Computed worst-case ceilings at code defaults (no key exists, so live spend
is currently impossible — this bounds the future armed state):

- One Meta call: ~6k input × $1.25/M + 4096 output cap × $4.25/M ≈ **$0.025**.
- Daily ceiling at `AI_DAILY_CALL_LIMIT=100`: ≈ **$2.50/day**.
- Recommendation (no code change made): when the owner arms Meta, set
  `AI_DAILY_CALL_LIMIT` to 1–5 in Render until usage patterns are known.
  In-app controls already present: daily cap, 30 s timeout, output-token cap,
  bounded retries (transient-only), synthetic demo data.

Per-service disable-ability: backend/frontend Free services can sleep or be
suspended without data loss (JSON re-seeds deterministically; decisions/audits
persist only with the paid disk — accepted Free-tier limitation, no paid disk
provisioned). No domains/add-ons/databases evidenced. Meta API: disabled by
absence of key (fail-closed `MODEL_NOT_CONFIGURED`).

No provider migration proposed: Render Free meets the demo's technical needs
within allowances; the sole uncapped exposure remains bandwidth overage with a
card on file (unchanged). No billing changes, no provisioning. Pillar 06
stays **PARTIAL**.

## Closure round addendum (2026-11-04, CS-FRC-ZG-001)

Official pricing page re-fetched (200): Hobby = 5 GB bandwidth included
(matches owner 0/5 GB read-out); overage now QUANTIFIED at **$0.30/GB**;
no spend-limit or suspension feature found on the pricing surface. Exposure
is therefore bounded in rate but uncapped in total — R06 acceptance (verified
no unapproved billable exposure) still unprovable. Migration assessed and
rejected as a fix: every comparable host bills overages the same way, and any
move needs approval. Evidence: H-F1. Pillar 06 stays **PARTIAL**.

## Owner-gated round addendum (2026-11-04)

No dashboard access arrived. Control 5 (never accept uncapped exposure)
enforced: exposure stays documented, never accepted. One owner-executable
mitigation identified for evaluation (NOT performed): removing the card on
file may convert overage into suspension-at-limit — owner must confirm
Render's actual no-card behavior in billing docs first; I performed no
billing action and recommend none blindly. Pillar 06 stays **PARTIAL**.
