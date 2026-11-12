"""Tamper-evident audit chaining (Level 14 §E, GAP-002 implementation).

Hash-chained, HMAC-signed audit events over canonical JSON. stdlib
only. Keys are caller-supplied bytes and NEVER persisted here:
production signing keys live in the key ceremony (D-018), tests use
ephemeral keys. Rotation: each record carries a key id; verification
accepts any key id present in the supplied keyring.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

GENESIS_HASH = "0" * 64


def _canon(event: dict[str, Any]) -> bytes:
    return json.dumps(event, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("utf-8")


def seal(event: dict[str, Any], prev_hash: str, key_id: str,
         key: bytes, seq: int) -> dict[str, Any]:
    """Append chain fields + signature to a copy of event."""
    if not key:
        raise ValueError("AUDIT_KEY_REQUIRED")
    body = dict(event)
    body["audit_seq"] = seq
    body["audit_prev"] = prev_hash
    digest = hashlib.sha256(_canon(body)).hexdigest()
    sig = hmac.new(key, digest.encode("ascii"),
                   hashlib.sha256).hexdigest()
    body["audit_digest"] = digest
    body["audit_key_id"] = key_id
    body["audit_sig"] = sig
    return body


def verify_chain(records: list[dict[str, Any]],
                 keyring: dict[str, bytes],
                 genesis: str = GENESIS_HASH) -> dict[str, Any]:
    """Verify ordering, linkage, and signatures. Raises on failure.

    Returns {"events": n, "head": digest} when valid.
    """
    prev = genesis
    for index, record in enumerate(records):
        seq = record.get("audit_seq")
        if seq != index:
            raise ValueError(f"AUDIT_SEQ_BREAK: want {index}, got {seq}")
        if record.get("audit_prev") != prev:
            raise ValueError(f"AUDIT_LINK_BREAK at seq {index}")
        key_id = record.get("audit_key_id")
        key = keyring.get(key_id) if isinstance(key_id, str) else None
        if not key:
            raise ValueError(f"AUDIT_KEY_UNKNOWN: {key_id!r} at {index}")
        check = {k: v for k, v in record.items()
                 if k not in ("audit_digest", "audit_key_id", "audit_sig")}
        digest = hashlib.sha256(_canon(check)).hexdigest()
        if not hmac.compare_digest(digest, str(record.get("audit_digest", ""))):
            raise ValueError(f"AUDIT_TAMPER at seq {index}")
        expect = hmac.new(key, digest.encode("ascii"),
                          hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expect, str(record.get("audit_sig", ""))):
            raise ValueError(f"AUDIT_SIG_INVALID at seq {index}")
        prev = digest
    return {"events": len(records), "head": prev}


def export_chain(records: list[dict[str, Any]]) -> bytes:
    """Canonical export bytes for portability + report hashing."""
    return _canon({"audit_chain": records, "version": 1})


def verification_report(records: list[dict[str, Any]],
                        keyring: dict[str, bytes],
                        legacy_skipped: int = 0) -> dict[str, Any]:
    """Structured verification outcome; never raises, never leaks keys.

    Returns {"ok", "sealed", "legacy_skipped", "head", "key_ids",
    "error"}. On failure "error" is {"code", "detail"} naming the
    check and position only. ``legacy_skipped`` counts unsealed
    entries the caller set aside (pre-ceremony records).
    """
    key_ids = sorted({str(r.get("audit_key_id"))
                      for r in records
                      if isinstance(r.get("audit_key_id"), str)})
    try:
        result = verify_chain(records, keyring)
    except ValueError as exc:
        return {"ok": False, "sealed": len(records),
                "legacy_skipped": legacy_skipped, "head": None,
                "key_ids": key_ids,
                "error": {"code": "AUDIT_CHAIN_INVALID",
                          "detail": str(exc)}}
    return {"ok": True, "sealed": result["events"],
            "legacy_skipped": legacy_skipped, "head": result["head"],
            "key_ids": key_ids, "error": None}
