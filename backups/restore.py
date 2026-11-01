"""Isolated restore: fetch, verify, decrypt, report (Phase 5.4F/P2).

Restoring is READ-ONLY with respect to every database: this module
downloads one generation from a target, re-verifies the manifest
signature binding, the envelope hash, and the chain link, decrypts with
a caller-supplied private key, and returns the plaintext snapshot plus
a check report. It contains no database code, no ``put``/``delete``
calls, and no duty to load anything anywhere: promoting a verified
plaintext into a scratch database is a separately authorized step that
does not exist yet.

The private key arrives as an argument (in production: transcribed
from the sealed ceremony shares by a human operator at drill time)
and is never logged; tests assert its absence from every record.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from backups import crypto as crypto_mod
from backups import integrity as integrity_mod
from backups import logutil as log_mod
from backups import manifest as manifest_mod
from backups import produce as produce_mod
from backups import targets as targets_mod


class RestoreError(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code


@dataclass(frozen=True)
class RestorePlan:
    """Verified plaintext snapshot, ready for an authorized load step."""

    backup_id: str
    target_name: str
    manifest: dict[str, Any]
    plaintext: bytes
    checks: dict[str, bool] = field(default_factory=dict)


def fetch_generation(target: targets_mod.BackupTarget,
                     backup_id: str) -> tuple[str, str, bytes]:
    """Download (manifest_raw, signature_doc, envelope) for one backup.

    ``NotFoundError`` propagates typed when any artifact is absent; other
    transport failures surface as ``RestoreError``.
    """
    try:
        manifest_raw = target.get(
            produce_mod.manifest_path(backup_id)).decode("utf-8")
        signature_doc = target.get(
            produce_mod.signature_path(backup_id)).decode("utf-8")
        envelope = target.get(produce_mod.dump_path(backup_id))
    except targets_mod.NotFoundError:
        raise
    except targets_mod.TargetError as exc:
        raise RestoreError("RESTORE_READ_FAILED", exc.code) from None
    except UnicodeDecodeError as exc:
        raise RestoreError("RESTORE_BAD_ENCODING",
                           type(exc).__name__) from None
    return manifest_raw, signature_doc, envelope


def plan_restore(*, target: targets_mod.BackupTarget, target_name: str,
                 backup_id: str, verify_key: bytes, private_key: bytes,
                 logger: Any = None,
                 redactor: log_mod.SecretRedactor | None = None
                 ) -> RestorePlan:
    """Verify and decrypt one generation; return the isolated plan.

    Fails closed on any missing artifact, bad signature, hash mismatch,
    chain gap, or decryption failure. Never writes anywhere.
    """
    active_logger = logger or log_mod.get_logger(
        "cruiseshield.backup.restore")
    active_redactor = redactor or log_mod.SecretRedactor()
    active_redactor.add(private_key.hex())
    log_mod.log_event(active_logger, 20, "restore_start", active_redactor,
                      backup_id=backup_id, target=target_name)
    manifest_raw, signature_doc, envelope = fetch_generation(target,
                                                             backup_id)
    try:
        manifest = manifest_mod.parse_manifest(manifest_raw)
    except ValueError as exc:
        raise RestoreError("MANIFEST_INVALID", str(exc)) from None
    if manifest["backup_id"] != backup_id:
        raise RestoreError("MANIFEST_ID_MISMATCH",
                           manifest["backup_id"])
    integrity_mod.verify_manifest_signature(manifest_raw, signature_doc,
                                            verify_key, backup_id)
    integrity_mod.verify_dump_sha256(envelope, manifest["dump_sha256"])
    plaintext = crypto_mod.decrypt_bytes(envelope, private_key)
    checks = {"signature_ok": True, "dump_sha256_ok": True,
              "decrypt_ok": True}
    prev_backup_id = manifest["prev_backup_id"]
    if prev_backup_id is not None:
        try:
            prev_raw, prev_sig, _ = fetch_generation(target, prev_backup_id)
            prev_manifest = manifest_mod.parse_manifest(prev_raw)
        except targets_mod.NotFoundError:
            raise RestoreError("CHAIN_GAP", prev_backup_id) from None
        except ValueError as exc:
            raise RestoreError("MANIFEST_INVALID",
                               f"prev: {exc}") from None
        integrity_mod.verify_manifest_signature(prev_raw, prev_sig,
                                                verify_key, prev_backup_id)
        integrity_mod.verify_manifest_chain(prev_manifest, manifest)
        checks["chain_ok"] = True
    log_mod.log_event(active_logger, 20, "restore_planned",
                      active_redactor, backup_id=backup_id,
                      target=target_name,
                      plaintext_bytes=len(plaintext))
    return RestorePlan(backup_id=backup_id, target_name=target_name,
                       manifest=manifest, plaintext=plaintext,
                       checks=checks)


def verify_backup_set(*, targets: Mapping[str, targets_mod.BackupTarget],
                      backup_id: str, verify_key: bytes,
                      logger: Any = None,
                      redactor: log_mod.SecretRedactor | None = None
                      ) -> dict[str, Any]:
    """Verify one generation identically on every target (monitor use).

    No private key required: signature, hash, and cross-copy gates only.
    Returns a verification report; raises on the first failed gate.
    """
    active_logger = logger or log_mod.get_logger(
        "cruiseshield.backup.verify")
    active_redactor = redactor or log_mod.SecretRedactor()
    if not targets:
        raise RestoreError("NO_TARGETS", "at least one target required")
    per_target: dict[str, dict[str, bool]] = {}
    envelopes: dict[str, bytes] = {}
    for name in sorted(targets):
        manifest_raw, signature_doc, envelope = fetch_generation(
            targets[name], backup_id)
        try:
            manifest = manifest_mod.parse_manifest(manifest_raw)
        except ValueError as exc:
            raise RestoreError("MANIFEST_INVALID",
                               f"{name}: {exc}") from None
        if manifest["backup_id"] != backup_id:
            raise RestoreError("MANIFEST_ID_MISMATCH",
                               f"{name}:{manifest['backup_id']}")
        integrity_mod.verify_manifest_signature(manifest_raw, signature_doc,
                                                verify_key, backup_id)
        integrity_mod.verify_dump_sha256(envelope, manifest["dump_sha256"])
        envelopes[name] = envelope
        per_target[name] = {"signature_ok": True, "dump_sha256_ok": True}
        log_mod.log_event(active_logger, 20, "backup_verified",
                          active_redactor, backup_id=backup_id, target=name)
    names = sorted(envelopes)
    for other in names[1:]:
        integrity_mod.verify_cross_copy(envelopes[names[0]],
                                        envelopes[other])
    report: dict[str, Any] = {"backup_id": backup_id,
                              "targets": per_target, "verified": True}
    if len(names) > 1:
        report["cross_copy_ok"] = True
    return report
