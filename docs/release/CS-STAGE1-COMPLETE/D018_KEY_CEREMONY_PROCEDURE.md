# D-018 — Audit-Chain Key Ceremony Procedure (CS-OPS-001)

Status: PROCEDURE PREPARED (not executed). No keys generated,
installed, rotated, or accessed under this programme. Owner +
witness execution required before any production sealing.

## 1. Authority and roles

- Key owner: project owner (authorizes generation, rotation,
  revocation; sole approver for ceremony scope changes).
- Witness: independent party (observes, co-signs the ceremony
  record; never handles key material unsupervised).
- Operator: engineer executing commands under owner direction
  (no independent authority over key lifecycle).

## 2. Approved generation method

On an owner-controlled offline-capable machine, never in chat,
docs, CI logs, or the repo:

1. `python -c "import secrets;print(secrets.token_hex(32))"`
   (32 bytes, 64 hex chars — meets MIN_AUDIT_CHAIN_KEY_BYTES).
2. Assign key id `k1` (rotation epochs increment: `k2`, …;
   ids match `[A-Za-z0-9_-]{1,32}`).
3. Witness confirms generation output seen once, recorded only
   into the secret store in step 3.

Accepted encodings (code order): even-length hex, strict
base64, raw UTF-8 ≥ 32 bytes. Hex is the standard.

## 3. Secure storage

- Production: Render secret store as `AUDIT_CHAIN_KEY`
  (+ `AUDIT_CHAIN_KEY_ID`). Dashboard entry only; values never
  in `render.yaml`, `.env.example`, docs, Git, logs, or chat.
- Recovery copy: sealed envelope / owner vault (see §7).
- Local/dev: unset (legacy mode) unless a sealed drill is
  explicitly authorized with test-only material.

## 4. Arming and verification

1. Set vars → redeploy → boot must succeed (misconfigured
   values fail closed with AUDIT_CHAIN_MISCONFIGURED).
2. `GET /api/v1/health`: `audit_chain_verified` reads
   `PASS sealed=N …`; status must not be `degraded` on that key.
3. Append a canary audit action; re-check sealed count +1.
4. Record sealed count, key id, and timestamp in the ceremony log.

## 5. Rotation runbook

1. Generate new key + id (`k{n+1}`) per §2 (owner + witness).
2. Set `AUDIT_CHAIN_KEY_ID`=`k{n+1}`, `AUDIT_CHAIN_KEY`=new,
   `AUDIT_CHAIN_KEY_PREVIOUS`=old, `AUDIT_CHAIN_KEY_ID_PREVIOUS`=`k{n}`.
3. Redeploy; verify health PASS and old-epoch verification
   (keyring holds both — covered by rotation tests).
4. After one full verification window (owner-defined, minimum
   7 days), clear `*_PREVIOUS`; redeploy; re-verify.
5. Log every step with timestamps + witness initials.

## 6. Compromise and revocation

1. On suspected exposure: owner declares compromise, freezes
   deploys relying on the key, and runs §5 immediately with a
   fresh id (skip the waiting window; keep previous only long
   enough to verify history, then clear).
2. Mark the epoch `REVOKED:<id>:<date>` in the key register.
3. Verify chain: history sealed under the revoked key still
   verifies (integrity preserved); new seals use the new id.
4. File an incident record per CS-OPS-003 (audit-chain
   compromise path).

## 7. Recovery-copy custody

- One recovery copy per active key, sealed, stored offline in
  the owner vault; access logged (who/when/why).
- Recovery drill annually or after any rotation: restore the
  copy into a scratch verifier (never production), verify a
  copied sealed export, destroy scratch material, log result.

## 8. Key identifier register

| Key ID | Epoch | State | Ceremony date | Witness |
|---|---|---|---|---|
| (none yet) | — | NOT_CREATED | — | — |

## 9. Pre-production checklist

- [ ] Ceremony executed by owner + witness; log signed.
- [ ] `AUDIT_CHAIN_KEY`/`_ID` in Render secret store only.
- [ ] Health `audit_chain_verified` PASS on the live service.
- [ ] Recovery copy sealed + custody logged.
- [ ] Rotation + compromise runbooks acknowledged by owner.
