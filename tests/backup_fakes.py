"""Shared P2 test doubles. In-memory targets, stub PG, synthetic data.

No network, no real credentials, no database. Imported by the P2 unit and
integration tests so the fakes exist exactly once.
"""
from __future__ import annotations

import logging

from backups import crypto as crypto_mod
from backups import produce as produce_mod
from backups import signing as signing_mod
from backups import targets as targets_mod


class FakeTarget(targets_mod.BackupTarget):
    """In-memory BackupTarget with call recording + failure injection."""

    def __init__(self) -> None:
        self.store: dict[str, bytes] = {}
        self.puts: list[str] = []
        self.gets: list[str] = []
        self.fail_puts = 0
        self.tamper_gets = False

    def put(self, path: str, data: bytes) -> str:
        self.puts.append(path)
        if self.fail_puts > 0:
            self.fail_puts -= 1
            raise targets_mod.TargetError("FAKE_FLAKY", path)
        self.store[path] = bytes(data)
        return f"fake-etag-{len(self.store)}"

    def get(self, path: str) -> bytes:
        self.gets.append(path)
        if path not in self.store:
            raise targets_mod.NotFoundError(path)
        data = self.store[path]
        if self.tamper_gets:
            data = bytes([data[0] ^ 0x01]) + data[1:] if data else data
        return bytes(data)

    def exists(self, path: str) -> bool:
        return path in self.store


class StubCursor:
    """Records SQL; serves canned rows keyed by statement prefix."""

    def __init__(self, canned: dict[str, list[tuple]]) -> None:
        self._canned = canned
        self.statements: list[str] = []
        self._rows: list[tuple] = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql: str, *args):
        self.statements.append(sql)
        for prefix, rows in self._canned.items():
            if sql.startswith(prefix):
                self._rows = list(rows)
                return
        raise AssertionError(f"unstubbed SQL: {sql!r}")

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class StubConnection:
    """Single reusable stub cursor; records rollback/close."""

    def __init__(self, canned: dict[str, list[tuple]]) -> None:
        self.cursor_obj = StubCursor(canned)
        self.rollbacks = 0
        self.commits = 0
        self.closes = 0

    def cursor(self):
        return self.cursor_obj

    def rollback(self):
        self.rollbacks += 1

    def commit(self):
        self.commits += 1

    def close(self):
        self.closes += 1


def canned_scratch_db() -> dict[str, list[tuple]]:
    """Minimal synthetic scratch database behind the stub connection."""
    doc = {"id": "synthetic", "ok": True}
    return {
        "SET TRANSACTION": [],
        "SELECT value FROM schema_meta": [("5.1.0",)],
        "SELECT document FROM": [(doc,)],
        "SELECT COUNT(*) FROM": [(1,)],
        "SELECT target_id": [("txn_84721", "transaction", 35),
                             ("txn_84721", "network", 84)],
        "SELECT COUNT(*), MAX(seq)": [(5, 5)],
        "SELECT audit_event_id": [("audit_0005",)],
        "SELECT package_id": [("evidence_pkg_scn_primary_v1", "b" * 64)],
    }


def null_logger() -> logging.Logger:
    logger = logging.getLogger("test-p2-null")
    logger.handlers = []
    logger.propagate = False
    logger.setLevel(logging.CRITICAL + 1)
    return logger


FAKE_SECRET = "TEST-ONLY-NOT-A-CREDENTIAL"

BACKUP_ID = "csbk-20261030-020000Z"
CREATED_AT = "20261030-020000Z"


def ephemeral_keys():
    """Fresh (private, public, signing_seed, verify_key), test-only."""
    priv, pub = crypto_mod.generate_keypair()
    seed, verify = signing_mod.generate_signing_keypair()
    return priv, pub, seed, verify


def make_snapshot(**over):
    """Synthetic valid snapshot (manifest-schema-clean metadata)."""
    kwargs = {
        "dump": b'{"synthetic":true}',
        "schema_version": "5.1.0",
        "table_counts": {"audit_events": 5, "cases": 1},
        "risk": {"txn_84721": {"transaction": 35, "network": 84}},
        "audit": {"count": 5, "head_id": "audit_0005"},
        "package_hashes": {"evidence_pkg_scn_primary_v1": "b" * 64},
    }
    kwargs.update(over)
    return produce_mod.Snapshot(**kwargs)


def produce_once(targets, *, snapshot=None, keys=None, backup_id=BACKUP_ID,
                 created_at=CREATED_AT, **over):
    """Run the real producer once against fake targets (no sleeping)."""
    if keys is None:
        keys = ephemeral_keys()
    _, pub, seed, verify = keys
    kwargs = {
        "snapshot": snapshot or make_snapshot(),
        "recipient_pubkeys": [pub], "signing_seed": seed,
        "signing_verify_key": verify, "targets": targets,
        "backup_id": backup_id, "created_at": created_at,
        "source": "scratch", "producer": "manual",
        "sleep": lambda s: None, "logger": null_logger(),
    }
    kwargs.update(over)
    report = produce_mod.produce_backup(**kwargs)
    return report, keys
