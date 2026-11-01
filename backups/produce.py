"""Backup production: snapshot -> encrypt -> sign -> upload -> verify (P2).

One backup generation per call. Reads the PostgreSQL database (source
``neon`` or ``scratch``) inside a single REPEATABLE READ transaction,
seals the canonical dump with the P1 CSBK1 envelope, signs the manifest
with the P1 minisign layout, uploads to the C2/C3 targets idempotently,
and promotes only after re-downloading and re-verifying every artifact.

Binding contracts (from P1, unchanged here):
- ``manifest.dump_sha256`` covers the ENCRYPTED envelope bytes, i.e. the
  exact bytes stored at ``<backup_id>/dump.csbk1``. Integrity gates on
  download compare against these bytes.
- ``manifest.age_recipient_fp`` carries the CSBK1 recipient fingerprint
  (``crypto.fingerprint`` of the first recipient). The P1 field name is
  retained; there is no age-format claim.
- The manifest signature's trusted comment is exactly ``backup_id``, so
  ``integrity.verify_manifest_signature`` binds signature to generation.
- Targets expose put/get/exists only; the producer never overwrites
  divergent bytes (fail closed) and never deletes.

What this module never does: import the SLIP-39 ceremony module
(``backups.shamir``), touch ``data/state.json`` or the JSON backend,
open provider connections itself (callers inject constructed targets),
or retry integrity failures (only transport errors are retried).
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Protocol

from backups import crypto as crypto_mod
from backups import integrity as integrity_mod
from backups import logutil as log_mod
from backups import manifest as manifest_mod
from backups import signing as signing_mod
from backups import targets as targets_mod

RETRY_ATTEMPTS = 3
RETRY_BASE_DELAY_S = 1.0


class ProduceError(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code


@dataclass(frozen=True)
class Snapshot:
    """One consistent database capture plus its manifest metadata."""

    dump: bytes
    schema_version: str
    table_counts: dict[str, int] = field(default_factory=dict)
    risk: dict[str, dict[str, int]] = field(default_factory=dict)
    audit: dict[str, Any] = field(default_factory=dict)
    package_hashes: dict[str, str] = field(default_factory=dict)


class SnapshotProvider(Protocol):
    def capture(self) -> Snapshot:
        """Capture one consistent snapshot (raise on any failure)."""


def canonical_json_bytes(document: Any) -> bytes:
    """Canonical JSON bytes (sorted keys, stable separators, UTF-8)."""
    return json.dumps(document, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("utf-8")


def new_backup_id(now: datetime | None = None) -> tuple[str, str]:
    """Fresh (backup_id, created_at) pair for one generation (UTC)."""
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%d-%H%M%SZ")
    return f"csbk-{stamp}", stamp


def dump_path(backup_id: str) -> str:
    return f"{backup_id}/dump.csbk1"


def manifest_path(backup_id: str) -> str:
    return f"{backup_id}/manifest.json"


def signature_path(backup_id: str) -> str:
    return f"{backup_id}/manifest.sig"


def capture_postgres_snapshot(conn: Any) -> Snapshot:
    """Read every domain table inside one REPEATABLE READ transaction.

    The connection must be freshly opened (no transaction in flight) so
    ``SET TRANSACTION`` is the first statement. Read-only by
    construction: the transaction ends with rollback, never commit.
    """
    from app import db as db_mod
    from app.models_pg import LOAD_ORDER

    with conn.cursor() as cur:
        cur.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        cur.execute("SELECT value FROM schema_meta WHERE key = "
                    "'schema_version'")
        version_row = cur.fetchone()
        schema_version = str(version_row[0]) if version_row else ""
        tables: dict[str, list[Any]] = {}
        for table in LOAD_ORDER:
            cur.execute(f'SELECT document FROM "{table}" '
                        "ORDER BY document::text")
            tables[table] = [row[0] for row in cur.fetchall()]
        counts = db_mod.table_counts(conn)
        cur.execute("SELECT target_id, target_type, score "
                    "FROM risk_assessments ORDER BY target_id, target_type")
        risk: dict[str, dict[str, int]] = {}
        for target_id, target_type, score in cur.fetchall():
            if target_type in ("transaction", "network"):
                risk.setdefault(str(target_id), {})[str(target_type)] = int(
                    score)
        cur.execute("SELECT COUNT(*), MAX(seq) FROM audit_events")
        audit_row = cur.fetchone()
        audit_count = int(audit_row[0]) if audit_row else 0
        cur.execute("SELECT audit_event_id FROM audit_events "
                    "ORDER BY seq DESC LIMIT 1")
        head_row = cur.fetchone()
        cur.execute("SELECT package_id, package_hash FROM evidence_packages "
                    "ORDER BY package_id")
        package_hashes = {str(pid): str(phash)
                          for pid, phash in cur.fetchall()}
    conn.rollback()
    dump = canonical_json_bytes({"schema_version": schema_version,
                                 "tables": tables})
    return Snapshot(
        dump=dump, schema_version=schema_version, table_counts=counts,
        risk=risk, audit={"count": audit_count,
                          "head_id": str(head_row[0]) if head_row else ""},
        package_hashes=package_hashes)


class PostgresSnapshotter:
    """SnapshotProvider over a caller-supplied connect callable."""

    def __init__(self, connect: Callable[[], Any] | None = None) -> None:
        if connect is None:
            from app import db as db_mod
            connect = db_mod.connect
        self._connect = connect

    def capture(self) -> Snapshot:
        conn = self._connect()
        try:
            return capture_postgres_snapshot(conn)
        finally:
            conn.close()


def put_idempotent(target: targets_mod.BackupTarget, path: str, data: bytes,
                   *, target_name: str = "target",
                   logger: Any = None,
                   redactor: log_mod.SecretRedactor | None = None) -> str:
    """Store bytes unless identical bytes are already present.

    Returns the provider receipt, or ``present:<sha256>`` when the exact
    bytes were already stored. Raises ``UPLOAD_DIVERGENT`` (never
    overwrites) when different bytes occupy the path.
    """
    digest = manifest_mod.sha256_hex(data)
    if target.exists(path):
        try:
            stored = target.get(path)
        except targets_mod.NotFoundError:
            stored = None  # exists/get race: fall through to put
        if stored is not None:
            if manifest_mod.sha256_hex(stored) == digest:
                if logger is not None:
                    log_mod.log_event(logger, 20, "upload_skip",
                                      redactor, target=target_name,
                                      path=path, sha256=digest)
                return f"present:{digest}"
            raise ProduceError("UPLOAD_DIVERGENT",
                               f"{target_name}:{path}")
    return target.put(path, data)


def put_with_retry(target: targets_mod.BackupTarget, path: str, data: bytes,
                   *, target_name: str = "target",
                   attempts: int = RETRY_ATTEMPTS,
                   sleep: Callable[[float], None] = time.sleep,
                   base_delay_s: float = RETRY_BASE_DELAY_S,
                   logger: Any = None,
                   redactor: log_mod.SecretRedactor | None = None) -> str:
    """Idempotent put with bounded retries on transport errors only.

    Integrity failures (divergent bytes) fail fast without retry.
    """
    last: targets_mod.TargetError | None = None
    for attempt in range(1, attempts + 1):
        try:
            return put_idempotent(target, path, data,
                                  target_name=target_name, logger=logger,
                                  redactor=redactor)
        except ProduceError:
            raise
        except targets_mod.TargetError as exc:
            last = exc
            if logger is not None:
                log_mod.log_event(logger, 30, "upload_retry", redactor,
                                  target=target_name, path=path,
                                  attempt=attempt, error=exc.code)
            if attempt < attempts:
                sleep(base_delay_s * attempt)
    raise ProduceError("UPLOAD_FAILED",
                       f"{target_name}:{path} attempts={attempts} "
                       f"last={last.code if last else 'unknown'}") from None


def produce_backup(*, snapshot: Snapshot,
                   recipient_pubkeys: list[bytes],
                   signing_seed: bytes, signing_verify_key: bytes,
                   targets: Mapping[str, targets_mod.BackupTarget],
                   backup_id: str, created_at: str, source: str,
                   producer: str = "gha-backup",
                   previous_manifest: dict[str, Any] | None = None,
                   attempts: int = RETRY_ATTEMPTS,
                   sleep: Callable[[float], None] = time.sleep,
                   logger: Any = None,
                   redactor: log_mod.SecretRedactor | None = None
                   ) -> dict[str, Any]:
    """Produce, upload, verify, and promote one backup generation.

    Returns a promotion report. Raises (CryptoError, ProduceError,
    IntegrityError, ValueError codes as ProduceError) without promoting
    on any failure. ``previous_manifest`` links the generation chain;
    ``None`` starts a new chain.

    Every call seals with a fresh ephemeral DEK, so re-production under
    an already-stored ``backup_id`` always fails closed with
    ``UPLOAD_DIVERGENT`` instead of silently replacing a backup. Crashed
    runs resume with a fresh ``backup_id``; same-bytes retries inside one
    run are idempotent via :func:`put_idempotent`.
    """
    active_logger = logger or log_mod.get_logger(
        "cruiseshield.backup.produce")
    active_redactor = redactor or log_mod.SecretRedactor()
    active_redactor.add(signing_seed.hex())
    try:
        return _produce(snapshot=snapshot,
                        recipient_pubkeys=recipient_pubkeys,
                        signing_seed=signing_seed,
                        signing_verify_key=signing_verify_key,
                        targets=targets, backup_id=backup_id,
                        created_at=created_at, source=source,
                        producer=producer,
                        previous_manifest=previous_manifest,
                        attempts=attempts, sleep=sleep,
                        logger=active_logger, redactor=active_redactor)
    except Exception as exc:
        log_mod.log_event(active_logger, 40, "produce_failed",
                          active_redactor, backup_id=backup_id,
                          error=type(exc).__name__,
                          code=getattr(exc, "code", "UNKNOWN"))
        log_mod.heartbeat(active_logger, backup_id=backup_id, target="all",
                          ok=False, detail=type(exc).__name__,
                          redactor=active_redactor)
        raise


def _produce(*, snapshot: Snapshot, recipient_pubkeys: list[bytes],
             signing_seed: bytes, signing_verify_key: bytes,
             targets: Mapping[str, targets_mod.BackupTarget],
             backup_id: str, created_at: str, source: str, producer: str,
             previous_manifest: dict[str, Any] | None, attempts: int,
             sleep: Callable[[float], None], logger: Any,
             redactor: log_mod.SecretRedactor) -> dict[str, Any]:
    if not targets:
        raise ProduceError("NO_TARGETS", "at least one target required")
    log_mod.log_event(logger, 20, "produce_start", redactor,
                      backup_id=backup_id, source=source,
                      producer=producer,
                      targets=",".join(sorted(targets)))
    envelope = crypto_mod.encrypt_bytes(snapshot.dump, recipient_pubkeys)
    envelope_sha = manifest_mod.sha256_hex(envelope)
    try:
        manifest = manifest_mod.build_manifest(
            backup_id=backup_id, source=source,
            schema_version=snapshot.schema_version,
            dump_sha256=envelope_sha, dump_bytes=len(envelope),
            table_counts=snapshot.table_counts, risk=snapshot.risk,
            audit=snapshot.audit, package_hashes=snapshot.package_hashes,
            prev_backup_id=(previous_manifest["backup_id"]
                            if previous_manifest else None),
            age_recipient_fp=crypto_mod.fingerprint(recipient_pubkeys[0]),
            producer=producer, created_at=created_at)
    except ValueError as exc:
        raise ProduceError("MANIFEST_INVALID", str(exc)) from None
    manifest_raw = manifest_mod.serialize_manifest(manifest)
    signature_doc = signing_mod.sign_message(
        manifest_raw.encode("utf-8"), signing_seed,
        trusted_comment=backup_id)
    artifacts = {
        dump_path(backup_id): envelope,
        manifest_path(backup_id): manifest_raw.encode("utf-8"),
        signature_path(backup_id): signature_doc.encode("utf-8"),
    }
    receipts: dict[str, str] = {}
    for name in sorted(targets):
        start = time.monotonic()
        for path, data in artifacts.items():
            receipts[f"{name}:{path}"] = put_with_retry(
                targets[name], path, data, target_name=name,
                attempts=attempts, sleep=sleep, logger=logger,
                redactor=redactor)
        latency_ms = int((time.monotonic() - start) * 1000)
        log_mod.heartbeat(logger, backup_id=backup_id, target=name, ok=True,
                          latency_ms=latency_ms, redactor=redactor)
    checks = _verify_before_promotion(
        targets=targets, backup_id=backup_id, manifest=manifest,
        manifest_raw=manifest_raw, signature_doc=signature_doc,
        signing_verify_key=signing_verify_key,
        previous_manifest=previous_manifest, logger=logger,
        redactor=redactor)
    log_mod.log_event(logger, 20, "produce_promoted", redactor,
                      backup_id=backup_id, sha256=envelope_sha)
    return {"backup_id": backup_id, "envelope_sha256": envelope_sha,
            "envelope_bytes": len(envelope), "manifest": manifest,
            "receipts": receipts, "checks": checks, "promoted": True}


def _verify_before_promotion(*, targets: Mapping[str,
                                                 targets_mod.BackupTarget],
                             backup_id: str, manifest: dict[str, Any],
                             manifest_raw: str, signature_doc: str,
                             signing_verify_key: bytes,
                             previous_manifest: dict[str, Any] | None,
                             logger: Any,
                             redactor: log_mod.SecretRedactor
                             ) -> dict[str, bool]:
    """Re-download every artifact and re-verify before promotion."""
    checks: dict[str, bool] = {}
    envelopes: dict[str, bytes] = {}
    for name in sorted(targets):
        target = targets[name]
        try:
            fetched_dump = target.get(dump_path(backup_id))
            fetched_manifest = target.get(manifest_path(backup_id))
            fetched_sig = target.get(signature_path(backup_id))
        except targets_mod.TargetError as exc:
            raise ProduceError("PROMOTION_READBACK_FAILED",
                               f"{name}:{exc.code}") from None
        integrity_mod.verify_dump_sha256(fetched_dump,
                                         manifest["dump_sha256"])
        fetched_raw = fetched_manifest.decode("utf-8")
        if fetched_raw != manifest_raw:
            raise integrity_mod.IntegrityError(
                "MANIFEST_READBACK_MISMATCH", name)
        integrity_mod.verify_manifest_signature(
            fetched_raw, fetched_sig.decode("utf-8"), signing_verify_key,
            backup_id)
        envelopes[name] = fetched_dump
        checks[f"target_verified:{name}"] = True
        log_mod.log_event(logger, 20, "promotion_verified", redactor,
                          backup_id=backup_id, target=name)
    names = sorted(envelopes)
    for other in names[1:]:
        integrity_mod.verify_cross_copy(envelopes[names[0]],
                                        envelopes[other])
    if len(names) > 1:
        checks["cross_copy_ok"] = True
    if previous_manifest is not None:
        integrity_mod.verify_manifest_chain(previous_manifest, manifest)
        checks["chain_ok"] = True
    return checks
