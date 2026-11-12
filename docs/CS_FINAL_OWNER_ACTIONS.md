# CS FINAL — OWNER ACTIONS (CS-FINAL-VERIFY-005)

Date: 2026-11-03. Do these in order; paste results back
(values never — names/presence/observations only).

## 1. Full SHA (unblocks B2)

Dashboard → `cruiseshield-ai` → deployments → click the
`ff7052b` SHA → paste the FULL 40-character hash.

## 2. Arm the backend (unblocks R5 + R1–R4)

Environment → confirm or set (fresh backend-only values):
`SESSION_SECRET` (32+) · `DEMO_USERS` · `DEMO_WRITE_TOKEN`
(32+ random). Save (redeploys) → report PRESENT ×3.

## 3. Billing read-out (unblocks B3)

Billing page → report: workspace plan · service plan +
price · card YES/NO · usage vs allowances · spend limits.

## 4. After 1–3 (Muse resumes)

Muse will: match SHA → re-probe health + auth/mode →
run safe R1–R4 probes → reconcile costs → update reports
→ re-evaluate G-PROVISION.

## 5. Still NOT requested

Frontend creation · plan/billing changes · AI quota use ·
commit/push · release. Each needs its own explicit approval.
