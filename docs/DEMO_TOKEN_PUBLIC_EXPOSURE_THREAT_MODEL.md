# DEMO TOKEN — PUBLIC EXPOSURE THREAT MODEL

Date: 2026-11-03 · Assumes token extracted (PROVEN trivial).

## Attacker profile

Anyone with a browser: judges, attendees, scrapers, no
account, no login. Cost to obtain token: ~10 seconds in
DevTools. Assume full replay with curl from any IP.

## Attack scenarios (all verified reachable in code)

| # | Scenario | Impact | Bounds |
|---|---|---|---|
| T1 | Reset shared demo mid-judging (`demo/reset`) | Availability: wipes interactive state, disrupts live demo | Recoverable in 1 click (reseed); seed data intact |
| T2 | Burn 100/day AI budget (`ai-analysis` loop) | Feature-DoS: judges see 429s; quota spend (free tier) | Daily cap + 600/min/IP throttle; resets 00:00 UTC |
| T3 | Forge decisions as "judge" (`actor_id` body field) | Integrity: poisoned case/audit narrative on shared screen | Synthetic only; reset wipes; decisions are transitions-validated |
| T4 | Inject junk events | Store pollution, noise in demo | Schema-validated, deduped, first-wins, capped fields |
| T5 | Read all demo data | Confidentiality of SYNTHETIC data only | No PII, no secrets, no hashes reachable |
| T6 | Backend token unset at deploy | All writes world-open, no creds needed | Deploy control (must-set), not code |

## Explicit NON-threats (verified absent)

- No session minting / login bypass (login needs
  `DEMO_USERS` creds; token path cannot create cookies).
- No privilege escalation to admin session.
- No secret/env disclosure via any endpoint.
- No real-customer-data access (store is synthetic-only
  by construction + seed policy).
- No persistent damage (ephemeral disk + reseed).
- CSRF-exemption for token is safe: `Authorization`
  headers are never auto-attached by browsers.

## Residual risk (post-R1–R4, 11-03)

T1/T2/T3 CLOSED (admin-gated reset, login-gated AI,
bound actor). T4 stands but bounded (validated,
deduped, rate-limited, reseedable). T5 stands by
design (synthetic reads). T6 stands by design
(must-set deploy control R5). Rating: LOW residual
for a synthetic public demo; R6-empty reduces it to
read-only-public if desired.

## Risk rating (original, pre-fix)

HIGH likelihood (extraction trivial) × LOW-MEDIUM
impact (synthetic demo, recoverable, capped) =
MEDIUM overall, concentrated on DEMO-DAY disruption
(T1/T2) and audit-theater integrity (T3). Unacceptable
as-is for a judged public release; acceptable AFTER
R1+R2 with T2 monitored (see Remediation Plan).
