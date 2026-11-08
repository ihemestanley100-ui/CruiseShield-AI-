# PKG-05 FREE-TIER & BILLING VERIFICATION

2026-11-08 @ d82627d. Config-derived findings only; account-level
facts need the 7 owner readings. $0 operation is NOT verified.

## Config-derived findings

- GitHub Actions: workflows use github-hosted runners + free OSS
  actions; no paid action detected. Quota unknown (readout 1).
- Render (render.yaml): backend `plan: starter` + 1GB disk;
  frontend `plan: starter`. Starter is PAID — conflicts with $0.
  Free variant exists (remove disk, plan=free) with consequences:
  cold starts, ephemeral JSON store (re-seeds; no durability).
- Netlify (netlify.toml): standard Next build; plan/bandwidth/build
  minutes unknown (readouts 2-4).
- Overage exposure: Render $0.30/GB overage documented in prior
  audit; no hard cap verified (readout 5).
- Databases: none provisioned; JSON file store only. Free PG
  options (Neon/Render/Supabase) unverified on quota/card/expiry/
  commercial terms.
- AI/models: NO-LIVE; $0 spend confirmed by non-use. Any activation
  needs quota + cap proof first.
- Providers/telecom/geo/banking: NO-LIVE; $0 by non-use.

## Persistence limitations (free tier)

- No disk: decisions, runs, audits lost across restarts/instances.
- JSON re-seeds deterministically: safe for demo, NOT adequate for
  durable financial-investigation records. Do not describe free
  ephemeral storage as production-ready.

## Backup / restore / DR findings

- Encrypted local-target backup + scratch drill green (test keys).
- Production backup unproven (D-018 ceremony pending).
- No cross-region DR; RPO/RTO undefined until production store
  exists. Backup workflows cannot self-trigger (safe default).

## 7 readings required from owner

1. Actions plan + minutes used/limit. 2. Netlify plan + bandwidth/
   build usage. 3. Render plan(s) + usage. 4. Card-on-file status
   per provider. 5. Overage behavior + caps. 6. Paid add-ons
   present. 7. Free-tier expiry/trial flags.

## Verdict

$0 feasibility: CI yes (pending quota proof); hosting only via the
free variant with stated durability loss; PG/AI/providers no free
path verified. Strict $0 production with durable investigation
storage is NOT established on current evidence.
