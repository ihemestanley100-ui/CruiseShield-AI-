# SECURITY & GOVERNANCE AUDIT — Release Cert v3.0

- Date: 2026-11-04. Commit: `ff7052bdf0ac48a68f69c3937d9b8708ca265354`.
- No penetration test performed. No auth controls disabled for testing.

## Findings register

| ID | Severity | Finding | Evidence | Status |
|---|---|---|---|---|
| S-01 | HIGH (residual) | Live backend UNARMED: `auth_enabled:false`, all 10 POST writes open, `DEMO_WRITE_TOKEN` missing server-side | Prior Task-4 probe: 400 INVALID_DECISION not 401; fresh health 200 with same posture | OPEN — owner R3 arming required |
| S-02 | MEDIUM | R1–R4 live verification impossible while unarmed (local: 17/17 green) | Test suite; live probes correctly withheld | OPEN — blocked on S-01 |
| S-03 | LOW | postcss ≤8.5.22 advisories (GHSA-qx2v…, 6g55…, fxqj…, r28c…) via Next; fix = breaking Next 16 upgrade | `npm audit`: 2 vulns (1 mod, 1 high), build-time-only, needs attacker CSS | ACCEPTED — owner decision for breaking upgrade |
| S-04 | INFO | `AI_MAX_OUTPUT_TOKENS` (+3 vars) read by backend but absent from `render.yaml` env list | config/render.yaml diff | OPEN — harmless (defaults apply); add on next config touch |

## Verified controls (fresh evidence)

- Secret scan: 0 key-pattern matches across 1151 files; no `.env`/`.pem`/`.key` tracked.
- Built-bundle scan: `MODEL_API_KEY`/`SESSION_SECRET`/`DEMO_WRITE_TOKEN` absent;
  `NEXT_PUBLIC_DEMO_WRITE_TOKEN` present only as a code reference with `""` fallback.
- `pip-audit`: no known vulnerabilities. Auth/authz/remediation suites green.
- CORS: exact-origin allowlist, never `*`. Synthetic-data isolation intact; audit clean.
- AI credentials server-side only; live AI routes fail closed at unconfigured key (no spend possible).

## Verdict: PILLAR 04 — PARTIAL (code posture green; live arming owner-gated)

## Release closure FRC-001 addendum (2026-11-04)

Source-level audit (fresh reads, no behavior changes except noted):

- AuthN: stateless HMAC-SHA256 cookies, 12 h expiry, signature+expiry+
  revocation+epoch validation; PBKDF2-HMAC-SHA256, 210k iterations;
  cookie flags `httponly`, scheme-aware `secure` (https/X-Forwarded-Proto),
  `samesite=lax`; 32-char minimum fails closed (503), unset = honest open demo.
- AuthZ: R1–R4 gates + RBAC (investigator/admin/auditor/demo_viewer) covered by
  green suites (`test_auth*`, `test_demo_token_remediation`, `test_write_token`).
- AppSec: exact-origin CORS (never `*`); R09-F1 bounded rate-limit buckets;
  body-size guards; error taxonomy without secret disclosure; audit logging
  without credential capture.
- Supply chain (fresh): repo-wide secret-pattern scan 0 matches / 1114 files;
  rebuilt-bundle grep: no backend secrets, public token ref with `""` fallback;
  `pip-audit` 0 vulns (prior, unchanged deps); `npm audit fix --dry-run` →
  **no non-breaking fix exists** (only `--force` to Next 16 / vitest 4).
- Governance: synthetic-data isolation, hashed evidence provenance, human
  decision authority, persisted audit trail — all suite-verified.

Safe repair executed (S-04, partial close): declared `AI_MAX_OUTPUT_TOKENS:
4096` (= code default, behavior-neutral) in `render.yaml` AI cost-controls
block; YAML re-validated; `test_config_safety` 6/6 green. Remaining
code-defaulted vars (`TRUSTED_PROXIES`, `STORE_BACKEND`, `PG_CONNECT_TIMEOUT`,
`DATABASE_URL`) accepted as documented-code-default posture — no secret values
in Blueprint, unchanged.

Risk treatment S-03 (postcss): accepted residual. Build-time-only advisories
requiring attacker-controlled CSS; no non-breaking remediation; breaking
upgrade stays an owner decision. No concealment: `npm audit` still reports 2.

Arming procedure (owner-gated, unchanged): set the 3 backend secrets in the
Render dashboard → redeploy → I verify `auth_enabled:true` + run safe R1–R4
probes. No live secrets touched, invented, or printed.

Pillar 04 stays **PARTIAL** (live PASS needs armed-backend probes).

## Owner-gated round addendum (2026-11-04)

Fresh secret scan 0/1181. No code changes; R08 closure stands. Live probes
still correctly withheld (backend unarmed). Evidence: J-S1. Pillar 04 stays
**PARTIAL**.

## Closure round addendum (2026-11-04, CS-FRC-ZG-001, R08 CLOSED)

PostCSS root-cause hunt (fresh): installed next=15.5.28 pins
`"postcss": "8.4.31"` EXACT (no range); latest 15.5.x (15.5.29) pins the same
vulnerable 8.4.31. Therefore NO patch/minor Next 15 update can remediate.
Remaining paths: npm `overrides` against the framework pin (compatibility
risk, untested-by-upstream CSS-output changes) or breaking Next 16 upgrade
(prohibited without approval). Attack-surface grep: zero postcss imports and
zero dynamic-CSS handling in app source — advisories are build-time-only
against first-party authored CSS. Disposition: formally documented accepted
risk with severity (1 high + 1 moderate), exposure (build tooling, no runtime
reach), and remediation plan (owner-approved Next 16 + full re-verification).
R08 acceptance satisfied via documented disposition. Fresh secret scan
0/1181. Evidence: H-S1, H-S3. Pillar 04 stays **PARTIAL** (live R1–R4 gated).
