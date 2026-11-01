# CruiseShield AI — Backup Recovery Runbook (P2)

## 1. Scope

This runbook covers the P2 backup producer: consistent PostgreSQL
snapshots sealed with the CSBK1 envelope, signed manifests, C2 (Backblaze
B2 over S3) and C3 (private GitHub repository) copies, monitoring
verification, and read-only restore drills.

Out of scope: loading a verified plaintext into any database (no such
step exists yet and none is authorized here), production restores,
scheduled jobs (all workflows are disabled by default).

## 2. Mandatory acceptance gates (record)

No production-source backup may execute until BOTH gates pass. Both
passed as recorded below; production also needs section 10 closed.

1. **Minisign CLI interoperability: VERIFIED (P2.2C, 2026-10-30).**
   Five tests against minisign CLI 0.12 (win64, synthetic fixtures):
   Python sign -> CLI `-V` exits 0; CLI `-S -l` -> Python accepts
   with the CLI `.pub` keynum; tampered bytes, wrong keys, and
   corrupted signatures rejected by both sides. Scope: legacy `Ed`
   format only. Global line carries the bare 64-byte signature over
   message-signature + trusted comment. Our keynums are deterministic
   (sha256(vk)[:8]); CLI keynums are random and must come from the
   trusted `.pub` — never from the manifest. `ED`-prehashed CLI
   signatures remain out of scope.
2. **Dependency advisory verification: VERIFIED, point-in-time.**
   `pip-audit` clean across the 37-pin hash-locked closure (P2.2A,
   2026-10-30; re-verified by every `security-gate` run since,
   including the weekly schedule). Cleanliness expires with new
   disclosures: never treat an old audit as current.

## 3. Artifacts and layout

Each generation stores three objects per target under one prefix:

- `<backup_id>/dump.csbk1` — CSBK1 envelope: X25519 multi-recipient
  seal (libsodium, fresh ephemeral keypair per recipient), full
  ciphertext per recipient. No age compatibility is claimed.
- `<backup_id>/manifest.json` — canonical manifest; `dump_sha256`
  covers the envelope bytes exactly as stored.
- `<backup_id>/manifest.sig` — minisign-layout signature whose trusted
  comment is exactly `<backup_id>`: signature packet
  (tag + keynum + 64-byte Ed25519 signature) plus a global line
  carrying the bare 64-byte global signature. Verification always
  runs against an explicitly trusted verify key (and, for
  CLI-issued signatures, the keynum from the trusted `.pub`):
  nothing security-relevant is taken from the manifest itself.

`backup_id` form: `csbk-YYYYMMDD-HHMMSSZ`. Generations chain via
`prev_backup_id`. Targets expose put/get/exists only: there is no
delete, and divergent bytes under an existing path fail closed instead
of overwriting.

## 4. Roles

- **Operator**: dispatches workflows, reads heartbeats, escalates.
- **Key custodian**: transcribes the restore private key from the
  sealed ceremony shares at drill time; the key never lives in the
  repository, logs, or chat.
- **Approver**: owns the `backup-production-gate` environment's
  required reviewers; every enabled run needs human approval.

Key ceremony (Shamir): recovery shares are SLIP-39 mnemonics created
in a witnessed ceremony; shares live on paper only, are never
digitized, and the ceremony threshold and share count are recorded
with the ceremony minutes. No rotation procedure is implemented:
rotating keys requires a new ceremony plus re-encryption of the
newest verified generation, which needs its own authorization.

## 5. Producing a backup (manual, gated)

1. Confirm both acceptance gates in section 2.
2. Open Actions → `backup-produce` → Run workflow.
3. Set `enabled=true` (default false) and `source` (`scratch` for
   drills; `neon` only with separate production authorization).
4. Approve the `backup-production-gate` environment request.
5. Watch the run: `produce_start`, per-target `heartbeat ok=true`,
   `promotion_verified` per target, `produce_promoted`.
6. Record the `backup_id` from the step summary.

On failure the run fails closed: `produce_failed` plus a
`heartbeat ok=false` name the error code. Crashed runs resume with a
fresh `backup_id`; re-production under a stored id always raises
`UPLOAD_DIVERGENT` and changes nothing.

## 6. Verifying a generation (monitoring)

1. Open Actions → `backup-verify` → Run workflow with `enabled=true`
   and the `backup_id`.
2. The job re-downloads every artifact on every target and checks the
   signature binding, the envelope hash, and the cross-copy equality.
   No private key is involved.
3. Expected summary: `verified=true cross_copy_ok=true`.

## 7. Restore drill (read-only)

1. Open Actions → `backup-restore-drill` → Run workflow with
   `enabled=true`, the `backup_id`, and the copy (`c2` or `c3`).
2. The custodian supplies the restore private key through the secret
   (transcribed at drill time, never stored elsewhere).
3. The job fetches, runs every validation gate in order —
   manifest schema, signature binding to `backup_id`, envelope hash,
   chain link to the previous generation (when one exists),
   cross-target equality where compared, then decryption — and
   attests `drill_ok=true ... writes=none`. The first failed gate
   stops the drill; a drill that stops is a finding, not a pass.
4. Confirm the summary line `writes=none`: the drill must never write
   to any database.

## 8. Failure playbook

- `UPLOAD_DIVERGENT`: different bytes already occupy the path. Stop:
  investigate before any retry with a fresh id.
- `UPLOAD_FAILED` after retries: transport outage. Heartbeats show the
  failing target; nothing was promoted.
- `SHA_MISMATCH` / `CROSS_COPY_MISMATCH`: a stored copy is corrupt or
  tampered. Quarantine the generation, verify the other copy, escalate.
- `CHAIN_GAP`: the previous generation is missing. Do not declare the
  chain healthy; recover the missing generation first.
- `SIGNATURE_BINDING_MISMATCH` / `VERIFY_FAILED`: signature or manifest
  tampering, or wrong key. Stop and escalate.
- Single-target outage (`UPLOAD_FAILED` naming one target): nothing is
  promoted and the healthy target is left untouched. Fix the outage,
  then resume with a fresh `backup_id`.
- Partial artifacts (missing object) or `PROMOTION_READBACK_FAILED`:
  the generation does not exist as far as recovery is concerned.
  Never hand-edit a target to "complete" it; re-produce instead.
- Termination mid-upload: the run dies without a promotion report and
  its orphan bytes are never adopted (same-id retry raises
  `UPLOAD_DIVERGENT`). Resume with a fresh `backup_id`.

## 9. Recovery objectives

Approved maximum RPO is 24 hours. No schedule is enabled, so no RPO is
currently met: the first enabled production cadence must be sized (and
restore-drilled) to hold the 24-hour objective before anyone claims it.

## 10. Remaining acceptance gaps (explicit)

Open items block production readiness; closed items record where the
evidence lives. Sandbox evidence below proves the code in isolation —
it is not production execution.

1. GitHub Actions first execution: NOT VERIFIED. The
   `security-gate` workflow has never run (pushes forbidden so far);
   CI-only steps are written but unexecuted.
2. PostgreSQL tests: EXECUTED in sandbox (P2.2H, 2026-10-30).
   PG-specific files: 86 passed, 0 failed, against an isolated
   disposable PostgreSQL 17.11 container (synthetic data only,
   localhost-only, RAM-only storage, removed after). Full backend
   with scratch PG: 250 passed, 0 skipped, 0 failed. Not yet
   reproduced in CI; rerun there on first live execution.
3. Sandboxed skips (167 passed / 83 skipped without a database) are
   not passed tests. The 15 socket/event-loop skips additionally
   pass unsandboxed (33/33 with their files). Counts above are
   sandbox evidence only.
4. Same-ID concurrent producers share a check-then-act window in
   `put_idempotent`. Serialized workflows plus fresh IDs per run
   mitigate it; no concurrent producers exist.
5. Production workflows, credentials, and schedules remain disabled
   by design; no secrets are installed anywhere.
6. 30-day backup reliability acceptance has not begun: no cadence
   has run, so no RPO/RTO is demonstrated.
7. Frontend/typecheck/build (closed sandbox evidence, P2.2H):
   165/165 vitest green, `tsc --noEmit` exit 0, `next build`
   exit 0. Rerun in CI on first live execution.

## 11. Never list

- Never enable a workflow without the section-2 gates for
  production-source data.
- Never store the signing seed, restore key, or recovery shares in the
  repository, workflow files, logs, or chat.
- Never add a schedule trigger without a separate authorization.
- Never `put` divergent bytes over an existing backup path.
- Never load a drill plaintext into a production database.
