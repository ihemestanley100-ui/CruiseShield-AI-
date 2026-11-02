# J8 — ZERO-COST HOSTING AND DEPLOYMENT ACCEPTANCE

Checked 2026-10-31 via web (secondary sources quoting vendor
docs/ToS; vendor pages not fetched directly — re-verify at deploy).

## Provider eligibility

Vercel Hobby: NOT SELECTED. ToS (quoted, updated 2026-06-01):
"only use the Services under a Hobby plan for your personal or
non-commercial use"; fair-use: "Hobby teams are restricted to
non-commercial personal use only". A branded ™ fintech product
entered in a judged competition cannot be independently cleared
as personal/non-commercial. Caps noted: 100 GB transfer, 1M
requests/invocations, no purchasable overage (hard stop, safe).

SELECTED (frontend): Cloudflare Pages Free — commercial use
allowed, unlimited static bandwidth/requests, 500 builds/mo,
20k files/site, 25 MiB/asset, 100 domains. Caveat: our Next.js
app is dynamic-routed; Pages needs the next-on-pages adapter
(or static export redesign) — config NOT yet implemented.

Render Free (backend): eligible with trade-offs — 512 MB /
0.1 CPU, sleep after 15 min idle, ~30–60 s cold start, 750
instance-hrs/workspace/mo (one always-on svc max), no disk,
no shell, ephemeral FS. WARNING: one source reports 5 GB/mo
bandwidth then $0.15/GB overage — a paid-overage vector;
verify on render.com/pricing before deploy, set usage alerts.

Neon Free (database): eligible — 100 CU-hrs/project/mo,
storage 0.5 GB/project (two Oct-2026 sources claim 1 GB;
conflict recorded, our 101 KB fits either), 5 GB egress,
scale-to-zero after 5 min, compute suspends / writes block
past quota. Fits demo with large headroom.

Meta AI API: cost/quota NOT_VERIFIED (no account access).
Controls implemented (limit/timeout/fallback/429 audit),
but $0 TOTAL cost cannot be claimed — only $0 hosting target.

## Cost register: $0/mo hosting within quotas; overage vectors
(Render bandwidth?, Meta quota) disclosed, not resolved.

## Deployment status

NOT DEPLOYED. No services provisioned, no DNS, no live URL —
all owner-gated. Prepared: render.yaml (corrected), env
register, CORS/origin design, health checks, auth, migration
code (rehearsed on scratch PG only). Local config tests are
NOT deployment evidence. Full-stack login/demo on a live URL
remains the DEPLOYMENT PASS criterion.
