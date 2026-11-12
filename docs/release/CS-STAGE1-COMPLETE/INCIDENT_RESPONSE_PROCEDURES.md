# Incident Response Procedures (CS-OPS-003)

Status: PREPARED, untested against live incidents. Severity:
S1 (active compromise/exposure) → S4 (minor anomaly). All paths:
contain → preserve evidence → recover → post-mortem within 5 days.

## IR-01 audit-chain compromise

Signs: `audit_chain_verified` FAIL (tamper), unexpected key-id
epochs, ceremony-log gaps. Actions: freeze writes (maintenance
mode if available); snapshot `state.json` + logs read-only;
run D-018 §6 rotation; verify history under old epoch; new seals
under new id; post-mortem + register update. Owner + witness.

## IR-02 credential compromise (session/token/secret)

Revoke: `logout-all` + epoch bump for users; rotate the
exposed secret; audit `auth.login.failed` + grant deltas
(access-review endpoint). If SESSION_SECRET: rotate with
PREVIOUS overlap, then clear. Never reuse the exposed value.

## IR-03 tenant data exposure

Confirm scope via tenant-scoped reads + audit trail; revoke
offending access; notify affected tenant owner(s); rotate
credentials of involved accounts; fix + regression test the
boundary; record in risk register.

## IR-04 unauthorized access / privilege escalation

Lock the account (disable user record); kill sessions; review
audit for lateral actions; restore correct RBAC; verify with
access-review deltas before/after.

## IR-05 database corruption (JSON)

Stop writes; snapshot the corrupt file; restore last verified
backup into EMPTY `DATA_DIR` (PKG-07 §4); health fingerprint;
if no backup: reseed is DATA LOSS — owner decision only, with
explicit written acceptance.

## IR-06 service outage

Health `/api/v1/health` + `/api/v1/ready`; distinguish hosting
(free-tier cold start/ephemeral wipe — reseed path) from app
fault (logs, recent deploy → Render one-click rollback to prior
release). Communicate status; no silent restarts.

## IR-07 AI-provider compromise / quota abuse

Revoke/rotate MODEL_API_KEY; set daily caps to 0 (disable lane);
audit AI runs for exfiltration-shaped prompts; review outputs
persisted during the window; re-arm only after owner review.

## IR-08 data-integrity failure (seed/provenance)

Quarantine affected flows; recompute `seed_integrity` +
`graph_provenance`; restore from backup if persistent; root-cause
the writer; add the missing invariant test before closing.

## IR-09 suspected financial fraud (platform abuse)

Freeze the implicated case entities (case hold, not deletion);
preserve evidence + audit trail; assign investigator; no
automated fund movement exists — human decision only; escalate
to owner/counsel per typology severity.

## IR-10 escalation matrix

S1/S2: owner + witness immediately, hourly updates. S3: owner
within 24 h. S4: weekly review batch. Every incident gets an
IR ID, timeline, evidence links, and a signed closure note.
