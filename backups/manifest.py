"""Backup manifests: build, validate, serialize, chain-check (stdlib only).

A manifest describes one backup generation: what was captured, its
checksums, and its link to the previous generation. Manifests never carry
secrets (no URLs, keys, or tokens) and are safe to store in plaintext
alongside the encrypted dump.

Schema (all keys required unless noted):
    backup_id: "csbk-YYYYMMDD-HHMMSSZ"
    source: "neon" | "scratch"
    schema_version: e.g. "5.1.0"
    dump_sha256: 64 lowercase hex chars
    dump_bytes: non-negative int
    table_counts: {table: non-negative int}
    risk: {txn_id: {"transaction": int, "network": int}}
    audit: {"count": non-negative int, "head_id": str}
    package_hashes: {package_id: 64 lowercase hex}
    prev_backup_id: str | None (None only for the first generation)
    age_recipient_fp: str (public-key fingerprint, non-secret)
    producer: "gha-backup" | "manual"
    created_at: UTC "YYYYMMDD-HHMMSSZ"
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

BACKUP_ID_RE = re.compile(r"^csbk-\d{8}-\d{6}Z$")
TIMESTAMP_RE = re.compile(r"^\d{8}-\d{6}Z$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

REQUIRED_KEYS = (
    "backup_id", "source", "schema_version", "dump_sha256", "dump_bytes",
    "table_counts", "risk", "audit", "package_hashes", "prev_backup_id",
    "age_recipient_fp", "producer", "created_at",
)

SOURCES = ("neon", "scratch")
PRODUCERS = ("gha-backup", "manual")


def sha256_hex(data: bytes) -> str:
    """SHA-256 hex digest (dump checksums, fingerprint comparisons)."""
    return hashlib.sha256(data).hexdigest()


def build_manifest(*, backup_id: str, source: str, schema_version: str,
                   dump_sha256: str, dump_bytes: int,
                   table_counts: dict[str, int],
                   risk: dict[str, dict[str, int]],
                   audit: dict[str, Any],
                   package_hashes: dict[str, str],
                   prev_backup_id: str | None, age_recipient_fp: str,
                   producer: str, created_at: str) -> dict[str, Any]:
    """Build a manifest dict. Raises ValueError listing defects, if any."""
    manifest = {
        "backup_id": backup_id, "source": source,
        "schema_version": schema_version, "dump_sha256": dump_sha256,
        "dump_bytes": dump_bytes, "table_counts": dict(table_counts),
        "risk": {k: dict(v) for k, v in risk.items()},
        "audit": dict(audit),
        "package_hashes": dict(package_hashes),
        "prev_backup_id": prev_backup_id,
        "age_recipient_fp": age_recipient_fp, "producer": producer,
        "created_at": created_at,
    }
    errors = validate_manifest(manifest)
    if errors:
        raise ValueError("MANIFEST_INVALID: " + "; ".join(errors))
    return manifest


def validate_manifest(manifest: Any) -> list[str]:
    """Return a list of schema defects (empty == valid). Never raises."""
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["manifest must be an object"]
    for key in REQUIRED_KEYS:
        if key not in manifest:
            errors.append(f"missing key: {key}")
    if errors:
        return errors
    if not BACKUP_ID_RE.match(str(manifest["backup_id"])):
        errors.append("backup_id must match csbk-YYYYMMDD-HHMMSSZ")
    if manifest["source"] not in SOURCES:
        errors.append(f"source must be one of {list(SOURCES)}")
    if not str(manifest["schema_version"]).strip():
        errors.append("schema_version must be non-empty")
    if not SHA256_RE.match(str(manifest["dump_sha256"])):
        errors.append("dump_sha256 must be 64 lowercase hex chars")
    if (not isinstance(manifest["dump_bytes"], int)
            or manifest["dump_bytes"] < 0):
        errors.append("dump_bytes must be a non-negative int")
    counts = manifest["table_counts"]
    if not isinstance(counts, dict) or not counts:
        errors.append("table_counts must be a non-empty object")
    else:
        for table, count in counts.items():
            if not isinstance(count, int) or count < 0:
                errors.append(f"table_counts[{table!r}] must be "
                              "a non-negative int")
    risk = manifest["risk"]
    if not isinstance(risk, dict) or not risk:
        errors.append("risk must be a non-empty object")
    else:
        for txn_id, scopes in risk.items():
            if not isinstance(scopes, dict):
                errors.append(f"risk[{txn_id!r}] must be an object")
                continue
            for scope in ("transaction", "network"):
                score = scopes.get(scope)
                if not isinstance(score, int) or not 0 <= score <= 100:
                    errors.append(f"risk[{txn_id!r}][{scope!r}] must be "
                                  "an int 0..100")
    audit = manifest["audit"]
    if not isinstance(audit, dict):
        errors.append("audit must be an object")
    else:
        if (not isinstance(audit.get("count"), int)
                or audit["count"] < 0):
            errors.append("audit.count must be a non-negative int")
        if not str(audit.get("head_id", "")).strip():
            errors.append("audit.head_id must be non-empty")
    hashes = manifest["package_hashes"]
    if not isinstance(hashes, dict) or not hashes:
        errors.append("package_hashes must be a non-empty object")
    else:
        for package_id, digest in hashes.items():
            if not SHA256_RE.match(str(digest)):
                errors.append(f"package_hashes[{package_id!r}] must be "
                              "64 lowercase hex chars")
    prev = manifest["prev_backup_id"]
    if prev is not None and not BACKUP_ID_RE.match(str(prev)):
        errors.append("prev_backup_id must be null or match "
                      "csbk-YYYYMMDD-HHMMSSZ")
    if not str(manifest["age_recipient_fp"]).strip():
        errors.append("age_recipient_fp must be non-empty")
    if manifest["producer"] not in PRODUCERS:
        errors.append(f"producer must be one of {list(PRODUCERS)}")
    if not TIMESTAMP_RE.match(str(manifest["created_at"])):
        errors.append("created_at must match YYYYMMDD-HHMMSSZ")
    return errors


def serialize_manifest(manifest: dict[str, Any]) -> str:
    """Canonical JSON (sorted keys, stable separators)."""
    errors = validate_manifest(manifest)
    if errors:
        raise ValueError("MANIFEST_INVALID: " + "; ".join(errors))
    return json.dumps(manifest, sort_keys=True, separators=(",", ":"))


def parse_manifest(raw: str) -> dict[str, Any]:
    """Parse + validate a manifest document. Raises ValueError if bad."""
    try:
        manifest = json.loads(raw)
    except ValueError as exc:
        raise ValueError(f"MANIFEST_NOT_JSON: {exc}") from None
    errors = validate_manifest(manifest)
    if errors:
        raise ValueError("MANIFEST_INVALID: " + "; ".join(errors))
    return manifest


def chain_ok(previous: dict[str, Any], current: dict[str, Any]) -> bool:
    """True when current.prev_backup_id links exactly to previous.

    Both manifests must be valid; any defect (or a gap) returns False
    instead of raising, so monitors can alert rather than crash.
    """
    if validate_manifest(previous) or validate_manifest(current):
        return False
    expected = previous["backup_id"]
    return current["prev_backup_id"] == expected
