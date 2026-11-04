# ZERO-COST INFRASTRUCTURE REGISTER — CruiseShield AI™

Global constraint: $0 total infrastructure and operational spending.
No paid plans, no paid trials, no billable resources, no purchased
domain. Terms verified 2026-11-03 via public sources; re-verify at
deploy time — free tiers change without notice.

Legend: EST = estimated monthly cost at expected demo usage.

## Selected for $0 launch

| # | Service / use | Free allowance | Hard limits | Card / billing | EST |
|---|---|---|---|---|---|
| 1 | Render Free — Next.js frontend (Web Service, `*.onrender.com`, auto HTTPS) | 750 hrs/mo shared workspace budget, 512 MB RAM, free TLS + logs | Sleeps after 15 min idle (~30–60 s cold start on first page load — see L2). No static export: dynamic SSR routes REQUIRE the Node service (verified in build output) | No paid resources enabled; verify no card at signup | $0 |
| 2 | Render Free — FastAPI backend, `*.onrender.com`, auto HTTPS | 750 hrs/mo shared workspace budget, 512 MB RAM, free TLS + logs | Sleeps after 15 min idle (~30–60 s cold start). EPHEMERAL filesystem, NO persistent disk: runtime writes vanish on sleep/restart (see limitation L1) | Same as above | $0 |
| 3 | GitHub Free (public repo) + Actions | Unlimited Actions minutes on standard runners for PUBLIC repos; 500 MB storage | Private repo would cap at 2,000 min/mo — repo must stay public for $0 CI | No card | $0 |
| 4 | Meta Muse API — AI inference within existing entitlements | Existing local key (presence verified, value never read) | Quota/validity UNKNOWN until one approved live call; app enforces AI_DAILY_CALL_LIMIT=100 + 30 s timeout + FAILED-run fallback | No new spend without owner approval | $0 |

## Accepted $0 limitations (disclosed, not hidden)

- L1 — Backend records are ephemeral on Render Free. Seeded demo
  data always re-seeds deterministically (hash-verified); decisions,
  AI runs, and audits created during a session are LOST when the
  instance sleeps. No keep-alive hack (respects platform intent);
  mitigation is procedural: warm up via `/api/v1/health` ~1 min
  before a demo, and the frontend already maps unreachable-backend
  to an honest error state.
- L2 — First load after idle takes ~30–60 s per sleeping
  service (cold start on BOTH frontend and backend Web Services).
  Disclosed in the demo script; not a defect. Warm-up order:
  backend `/api/v1/health` first, then the frontend URL.
- L3 — Free-subdomain URLs only (`*.onrender.com`).
  No custom domain.
- L4 — Log retention is whatever the free platforms keep (brief).
  No paid APM. Persistent evidence stays in-repo (git) as today.
- L5 — Supabase/Neon PG is the persistence UPGRADE path, not the
  launch path: the PG adapter is verified for scratch parity only,
  and production cutover needs its own verification sprint (run
  the migration + parity suite against a scratch URL, review
  connection handling, then promote). Claiming PG production-ready
  without that work would violate the correctness rule.

## Evaluated but NOT selected (with reason)

| Service / use | Terms found | Verdict |
|---|---|---|
| Vercel Hobby | $0 with ~100 GB bandwidth, BUT ToS restricts Hobby to personal/non-commercial use — a branded ™ fintech product in a judged competition cannot be cleared (J8 analysis 10-31, re-confirmed by 11-03 sources) | NOT SELECTED (ToS). Do not use for this launch |
| Cloudflare Pages Free | Commercial use allowed, unlimited static bandwidth, 500 builds/mo — but dynamic-routed Next.js needs the next-on-pages adapter (NOT implemented) | Approved ALTERNATIVE only: requires adapter implementation + verification sprint (future work, owner decision) |
| Supabase Free — managed PG (500 MB, 50k MAU, 5 GB egress, no card, 2 projects) | Projects PAUSE after 7 days inactivity (manual restore); plenty of room for a 100 KB state | Reserve for the persistence upgrade (see L5). Alternative: Neon free (1 GB, auto-resume after 5-min suspend) if Supabase pausing proves annoying — same verification sprint required either way |
| Render Free PostgreSQL (1 GB) | EXPIRES 30 days after creation (+14-day grace) | Rejected: time-bombed, unsuitable for production |
| Render persistent disk | Paid add-on (~$0.25/GB-mo) | Rejected under $0 (this is why L1 exists) |
| Fireworks AI | NO ongoing free tier; one-time ~$1 signup grant (some sources: uncertain/prepaid-only), then pay-per-token with payment method on file | Rejected as the production provider. At most a bounded trial (~tens of demo calls on small models) with explicit approval — never the launch integration |
| Modal Starter ($30/mo recurring compute, per-second billing, scales to zero) | Genuinely free allowance, no card reported | Not needed: the app has no batch/GPU workload (AI is external API calls). Revisit only if a batch feature is specified |
| Custom domain | ~$10–15/yr registrar | Rejected under $0 (see L3) |

## Cost summary

- Hosting at expected demo usage: $0/mo target (Render Free × 2 +
  GitHub $0). Per J8 honesty rule, $0 TOTAL cannot be claimed —
  only the $0 hosting target: the Meta-quota vector is unverified
  until the entitlement is confirmed, and one J8-cited source
  reports a possible Render bandwidth overage past 5 GB/mo
  ($0.15/GB) — re-verify on render.com/pricing at deploy, stay
  orders of magnitude below demo scale, set usage alerts.
- AI usage stays $0 only while inside existing Meta entitlements;
  the app-side daily cap (100) and fallback bound the exposure, but
  the owner must confirm the entitlement covers demo traffic.

## Approvals still required (no exceptions)

1. One quota-spending Meta live verification call (proves key
   validity; ~10k tokens based on the 11-01 run).
2. Commit approval for the working tree onto `production-launch`.
3. Owner-created account: Render (+ Supabase later, only
   for the L5 upgrade). Account creation is an owner action.
4. Credential provisioning into hosting prompts (never chat/files).
5. Final deployment approval. No external resource is created
   before it.
