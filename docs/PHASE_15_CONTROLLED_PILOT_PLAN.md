# PHASE 15 — CONTROLLED PILOT PLAN

STATUS: PLAN ONLY. Do NOT start without: owner approval + institutional sponsorship + signed agreements + legal/security review + closed pilot gates.

## Entry gates (all must be GREEN)
1. G-P1 AuthN/authZ + roles implemented + tested (closes D-002).
2. G-P2 Rate limiting + body limits at edge (closes D-001).
3. G-P3 Encrypted backup executed + restore tested (closes D-008).
4. G-P4 DPIA complete; data-sharing/processing agreements signed (LQ-01…LQ-04, LQ-08).
5. G-P5 Independent validation of risk engine + AI grounding on pilot-like data.
6. G-P6 Screen-reader pass (D-003) OR documented scope exclusion for pilot users.
7. G-P7 Live AI red-team run reviewed (D-005) OR AI features disabled for pilot.
8. G-P8 Incident runbook + on-call + monitoring dashboards live.

## Pilot design
- Scope: ONE institution, ONE team (5–10 investigators), read-assist + workbench use; synthetic or lawfully-authorised test data ONLY in month 1; production-data use only after month-1 review.
- Duration: 90 days with 30/60/90 reviews and written exit criteria (below).
- Human oversight: every AI explanation reviewed; escalations second-eyed; weekly audit sampling.
- Risk controls: transaction caps on pilot actions (none financial); kill-switch (disable AI features without losing case work); rollback to prior engine version < 1 h.

## Success metrics (targets set with the institution at kickoff — NO fabricated baselines)
Detection precision / recall, false-positive rate, median investigation time, evidence completeness, explanation grounding rate, override rate, decision traceability (100% rationale coverage), availability, API reliability, investigator satisfaction (survey).

## Exit criteria
- GRADUATE: gates held for 90 days + metrics meet agreed targets + independent review accepts → proceed to production gate (see matrix).
- EXTEND: partial — named gaps with dated remediation, max one 60-day extension.
- EXIT: metric miss, control failure, incident, or agreement lapse → wind down: export institution data, verify deletion, post-mortem, archive lessons.

## Incident procedure (pilot)
Detect → contain (kill-switch if model-related) → notify (institution DPO/compliance + owner, within LQ-06 clocks) → preserve forensics → remediate → post-incident review → defect-register entry. No silent fixes.
