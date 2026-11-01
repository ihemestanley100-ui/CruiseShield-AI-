# STAGING DEPLOYMENT APPROVAL PREPARATION

DATE: 2026-11-01 | SCOPE: controlled demo, synthetic only, Render hosting, existing architecture.
STATUS: preparation only. No services created, no plans activated, no backup executed, no DNS/domain changes, no commits/pushes/deploys.

## 1. BACKUP (not executed — D-008 still open)
- Destination: OWNER PENDING (no destination approved; nothing invented). See `docs/CLOSEOUT_BACKUP_PROCEDURE.md` §6 for the exact 4-item approval request.
- Files if approved: source tree (HEAD 0eaaaf5 + 134-entry list), `data/state.json` (BA1D4DB4…3790FE, 101417 B), `.git/`, all docs, manifests, %TEMP% evidence copies (incl. `%TEMP%\redteam\` artifacts), logos (1A0CC66B…).
- Integrity: per-file SHA-256 + archive hash, verified post-write; exclusions: node_modules/.next/__pycache__/.venv/caches; `.env` to owner-approved secret store ONLY.
- Restoration: empty-dir extract → hash verify → venv + hash-pinned installs + build → state restore + hash verify → :8000/:3000 health → suites green.
- Rollback drill results: LOCAL disposable drills green (hash-identical restores ×3, incl. closeout). Render rollback (service redeploy + disk state restore) UNTESTED — first staging deploy must include a rollback drill to convert RTO/RPO targets into measurements.

## 2. RENDER COST (third-party verified Oct 2026 — confirm in dashboard before purchase; ex-tax)
Sources agree (latest check 2026-10-28): web Starter (0.5 CPU/512 MB) $7/mo each; persistent disk $0.25/GB/mo; Postgres Basic-256MB ~$6/mo; free tier $0 (sleeps, no disk, hour caps).
- RECOMMENDED staging (Option A): frontend Starter $7 + backend Starter $7 + 1 GB disk $0.25 = **~$14.25/mo**.
- With Postgres later (Option B workstream): +~$6/mo (plus $0.30/GB storage growth).
- Extras: bandwidth overages if exceeded; custom domain ~$0.25/mo over included (one source — verify); workspace Hobby $0.
- Free-tier alternative: $0 but services sleep (cold starts mid-demo) and NO persistence (judge decisions/audits lost on restart) — NOT recommended for a judged demo window.
- No plan activated; no payment instrument touched.

## 3. DOMAIN
- A. Free Render URLs (RECOMMENDED for staging): `https://<service>.onrender.com` ×2 (HTTPS included, zero config). Confirm exact hostnames post-deploy; they feed FRONTEND_ORIGINS + NEXT_PUBLIC_API_BASE_URL.
- B. Custom domain (public demo later): owner DNS action (CNAME to Render) + Render custom-domain attach (~$0.25/mo over included — verify). No DNS changed, nothing purchased.
- Recommendation: A for staging; revisit B only if a public demo URL is required.

## 4. DEMONSTRATION SECURITY (explicit)
- Authentication: shared demo write token (SEC-012) — SET at staging deploy (owner-generated). Reads open; 8 POST endpoints 401 without it. This is LOW-ASSURANCE (public-by-design in frontend bundle), NOT user auth. Real auth deferred (needs identity decision).
- Demo-user permissions: all demo users share one role (investigator-equivalent); no per-user identities on staging; actor IDs self-asserted as in local demo. Documented limitation.
- Rate limiting: 600 req/min/IP, health-exempt, 429+Retry-After (SEC-011, live-verified). Single-instance scope; XFF-keyed behind Render proxy (documented caveats).
- CSP: NOT IMPLEMENTED (Three.js inline scripts need nonce design). Compensating: nosniff/DENY/referrer/permissions-policy live on both surfaces. No CSP claim made.
- CORS: FRONTEND_ORIGINS locked to the exact staging frontend origin (step 6 of runbook); localhost defaults do NOT ship.
- API secret protection: MODEL_API_KEY in Render secret store (sync:false); never in image/repo/logs; frontend holds only the public demo token + backend URL.
- Synthetic-data safeguards: staging seeds FRESH synthetic state on first boot (no local data copied up); synthetic labelling + disclaimers throughout; no real-data import path exists.
- Decisions/audits on staging: real within staging (writes require token); paid disk persists them; free tier would lose them (another reason for Starter).
- POSITION (per restriction): unrestricted public access is NOT approved. Staging runs with throttle + write-token + headers + CORS-lock + URL-secrecy; judges get the URLs + token out-of-band. Any wider opening needs real auth first.

## 5. STAGING CONFIGURATION (exact — from verified `render.yaml` + runbook)
- Backend `cruiseshield-ai`: Docker, starter, `./Dockerfile`, health `/api/v1/health`, disk 1 GB → /srv/data; env MODEL_API_KEY‡, META_MODEL_ID, META_BASE_URL, DATA_DIR=/srv/data, FRONTEND_ORIGINS=<staging FE URL>, DEMO_WRITE_TOKEN‡.
- Frontend `cruiseshield-ai-frontend`: Node, starter, rootDir frontend, build `npm ci && npm run build`, start `npm start -- --port $PORT`, health `/`; env NODE_VERSION=20.19.6, NEXT_PUBLIC_API_BASE_URL=<staging BE URL> (build-baked), NEXT_PUBLIC_DEMO_WRITE_TOKEN‡ (same value as backend).
- Order: backend → record URL → frontend env+build → backend CORS redeploy → smoke (doc 7 runbook) → staging acceptance checklist (doc 9).
- Rollback: service redeploy prior release; disk NOT rolled back — restore state.json from approved backup + restart + verify (doc 8). Rollback drill untested — schedule on first deploy.

## 6. FINAL STAGING APPROVAL MATRIX
1. Backup destination + secret handling (E a–d) | approve + execute pre-deploy | $0 (owner storage) | enables rollback claims | PENDING.
2. Render spend ~$14.25/mo + domain later | approve Starter×2 + disk | recurring until torn down | warm demo + persistence | PENDING.
3. Demo-grade security acceptance (token + throttle + headers, no real auth/CSP) | accept for judged window | $0 | residual abuse/claim limits documented | PENDING.
4. Free Render URLs for staging | approve option A | $0 | zero DNS work | PENDING.
5. Execute runbook (services → smoke → acceptance) | approve execution window | time (~1–2 h) | staging live + rollback drill owed | PENDING.
6. Custom domain (optional, later) | defer | ~$0.25/mo + DNS work | public URL | DEFERRED.

Nothing created, activated, committed, pushed, migrated, or deployed. Awaiting explicit owner approval per item.
