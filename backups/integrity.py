"""Backup integrity gates (Phase 5.4F/P1).

Composes manifest, signature, hash, chain, and cross-copy checks into one
verdict per generation. Pure logic over bytes and dicts; no I/O, no
network, no secrets.
"""
from __future__ import annotations

import hmac
from typing import Any

from backups import manifest as manifest_mod
from backups import signing as signing_mod


class IntegrityError(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code


def verify_dump_sha256(data: bytes, expected_hex: str) -> None:
    """Raise unless sha256(data) == expected_hex (constant-time)."""
    actual = manifest_mod.sha256_hex(data)
    if not hmac.compare_digest(actual, expected_hex.lower()):
        raise IntegrityError("SHA_MISMATCH",
                             f"expected={expected_hex} actual={actual}")


def verify_cross_copy(first: bytes, second: bytes) -> None:
    """Raise unless two copies are byte-identical (constant-time)."""
    if len(first) != len(second) or not hmac.compare_digest(first, second):
        raise IntegrityError("CROSS_COPY_MISMATCH",
                             f"len={len(first)}/{len(second)}")


def verify_manifest_chain(previous: dict[str, Any],
                          current: dict[str, Any]) -> None:
    """Raise unless current links exactly to previous (no gaps)."""
    if not manifest_mod.chain_ok(previous, current):
        raise IntegrityError("CHAIN_BREAK",
                             f"{previous.get('backup_id')} -> "
                             f"{current.get('backup_id')}")


def verify_manifest_signature(manifest_raw: str, signature_doc: str,
                              verify_key: bytes,
                              expected_backup_id: str) -> None:
    """Raise unless the signature is valid AND bound to this backup_id."""
    try:
        trusted = signing_mod.verify_message(
            manifest_raw.encode("utf-8"), signature_doc, verify_key)
    except signing_mod.SignatureError as exc:
        raise IntegrityError("BAD_SIGNATURE", exc.code) from None
    if trusted != expected_backup_id:
        raise IntegrityError("SIGNATURE_BINDING_MISMATCH",
                             f"trusted={trusted!r}")


def verify_generation(*, manifest: dict[str, Any],
                      dump_primary: bytes,
                      dump_secondary: bytes | None = None) -> dict[str, bool]:
    """Run every applicable gate; returns {check: passed}.

    Raises on the first failure so producers fail closed. Provide both
    copies when available for the cross-copy gate.
    """
    checks: dict[str, bool] = {}
    errors = manifest_mod.validate_manifest(manifest)
    checks["manifest_valid"] = not errors
    if errors:
        raise IntegrityError("BAD_MANIFEST", errors[0])
    verify_dump_sha256(dump_primary, manifest["dump_sha256"])
    checks["dump_sha256_ok"] = True
    if dump_secondary is not None:
        verify_cross_copy(dump_primary, dump_secondary)
        checks["cross_copy_ok"] = True
    return checks
