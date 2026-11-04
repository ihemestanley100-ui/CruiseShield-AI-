# PROVIDER ELIGIBILITY MATRIX

| Provider | Role | Eligible | Key limits | Veto/notes |
|----------|------|----------|------------|------------|
| Cloudflare Pages Free | Frontend | YES | 500 builds/mo, 20k files, 25 MiB/asset, unlimited static BW | Needs next-on-pages adapter (not yet configured) |
| Vercel Hobby | Frontend (rejected) | NO | 100 GB, 1M req | ToS: personal/non-commercial only — branded judged entry cannot clear |
| Render Free | Backend | YES | 512 MB/0.1 CPU, sleep 15 min, 750 hrs/mo, no disk/shell | Cold start 30–60 s; verify bandwidth-overage line before deploy |
| Neon Free | Database | YES | 100 CU-h/mo, 0.5 GB (1 GB claimed by 2 sources), 5 GB egress, sleep 5 min | 101 KB state fits either figure |
| GitHub Free | Source | YES | public repo free | Repo already public |
| Meta Model API | AI | METERED | $1.25/M in, $4.25/M out (1 source) | Quota/billing NOT_VERIFIED; $0 = hosting only |

Rollback: canonical docs/RENDER_8_ROLLBACK_RECOVERY.md
(no duplicate runbook created — this matrix + that file are
the deployment package; Pages-adapter rollback TBD with its
config).
