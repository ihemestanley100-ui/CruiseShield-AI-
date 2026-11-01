"""P2 produce tests. Stub PG, fake targets, ephemeral keys. No I/O."""
import logging

import pytest

from backups import crypto as crypto_mod
from backups import integrity as integrity_mod
from backups import logutil as log_mod
from backups import produce as produce_mod
from backups import signing as signing_mod
import backup_fakes as fakes

BACKUP_ID = fakes.BACKUP_ID
_keys = fakes.ephemeral_keys
_snapshot = fakes.make_snapshot


def _produce(snapshot, pub, seed, verify, targets, **over):
    report, _ = fakes.produce_once(
        targets, snapshot=snapshot, keys=(None, pub, seed, verify), **over)
    return report


def test_snapshot_capture_is_single_repeatable_read_txn():
    conn = fakes.StubConnection(fakes.canned_scratch_db())
    snapshot = produce_mod.capture_postgres_snapshot(conn)
    statements = conn.cursor_obj.statements
    assert statements[0] == "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"
    assert conn.rollbacks == 1
    assert conn.commits == 0
    assert snapshot.schema_version == "5.1.0"
    assert snapshot.table_counts["cases"] == 1
    assert snapshot.risk == {"txn_84721": {"transaction": 35,
                                           "network": 84}}
    assert snapshot.audit == {"count": 5, "head_id": "audit_0005"}
    assert snapshot.package_hashes == {
        "evidence_pkg_scn_primary_v1": "b" * 64}
    assert b'"schema_version":"5.1.0"' in snapshot.dump


def test_snapshotter_closes_connection():
    conn = fakes.StubConnection(fakes.canned_scratch_db())
    snapshotter = produce_mod.PostgresSnapshotter(connect=lambda: conn)
    assert snapshotter.capture().schema_version == "5.1.0"
    assert conn.closes == 1


def test_new_backup_id_format():
    backup_id, created_at = produce_mod.new_backup_id()
    assert backup_id == f"csbk-{created_at}"
    assert len(created_at) == 16 and created_at.endswith("Z")


def test_happy_path_promotes_to_both_targets():
    _, pub, seed, verify = _keys()
    targets = {"c2": fakes.FakeTarget(), "c3": fakes.FakeTarget()}
    report = _produce(_snapshot(), pub, seed, verify, targets)
    assert report["promoted"] is True
    assert report["checks"]["cross_copy_ok"] is True
    assert report["checks"]["target_verified:c2"] is True
    assert report["checks"]["target_verified:c3"] is True
    assert report["manifest"]["dump_sha256"] == report["envelope_sha256"]
    assert report["manifest"]["age_recipient_fp"] == (
        crypto_mod.fingerprint(pub))
    for target in targets.values():
        assert f"{BACKUP_ID}/dump.csbk1" in target.store
        assert f"{BACKUP_ID}/manifest.json" in target.store
        assert f"{BACKUP_ID}/manifest.sig" in target.store
    assert len(report["receipts"]) == 6


def test_same_backup_id_is_never_silently_replaced():
    _, pub, seed, verify = _keys()
    targets = {"c2": fakes.FakeTarget()}
    first = _produce(_snapshot(), pub, seed, verify, targets)
    original = targets["c2"].store[f"{BACKUP_ID}/dump.csbk1"]
    with pytest.raises(produce_mod.ProduceError, match="UPLOAD_DIVERGENT"):
        _produce(_snapshot(), pub, seed, verify, targets)
    assert targets["c2"].store[f"{BACKUP_ID}/dump.csbk1"] == original
    assert first["promoted"] is True


def test_put_idempotent_skips_identical_bytes():
    target = fakes.FakeTarget()
    first = produce_mod.put_idempotent(target, "k/dump.csbk1", b"fixed")
    assert target.puts == ["k/dump.csbk1"]
    second = produce_mod.put_idempotent(target, "k/dump.csbk1", b"fixed")
    assert second.startswith("present:")
    assert target.puts == ["k/dump.csbk1"]


def test_divergent_bytes_fail_closed_without_overwrite():
    _, pub, seed, verify = _keys()
    target = fakes.FakeTarget()
    target.store[f"{BACKUP_ID}/dump.csbk1"] = b"someone-elses-bytes"
    with pytest.raises(produce_mod.ProduceError, match="UPLOAD_DIVERGENT"):
        _produce(_snapshot(), pub, seed, verify, {"c2": target})
    assert target.store[f"{BACKUP_ID}/dump.csbk1"] == b"someone-elses-bytes"


def test_retry_succeeds_after_transient_failures():
    _, pub, seed, verify = _keys()
    target = fakes.FakeTarget()
    target.fail_puts = 2
    delays: list[float] = []
    report = _produce(_snapshot(), pub, seed, verify, {"c2": target},
                      sleep=delays.append)
    assert report["promoted"] is True
    assert delays == [1.0, 2.0]


def test_retry_exhaustion_raises_without_promoting():
    _, pub, seed, verify = _keys()
    target = fakes.FakeTarget()
    target.fail_puts = 99
    with pytest.raises(produce_mod.ProduceError, match="UPLOAD_FAILED"):
        _produce(_snapshot(), pub, seed, verify, {"c2": target})


def test_tampered_readback_blocks_promotion():
    _, pub, seed, verify = _keys()
    target = fakes.FakeTarget()
    target.tamper_gets = True
    with pytest.raises(integrity_mod.IntegrityError):
        _produce(_snapshot(), pub, seed, verify, {"c2": target})


def test_second_generation_chains_and_gap_breaks():
    _, pub, seed, verify = _keys()
    targets = {"c2": fakes.FakeTarget()}
    first = _produce(_snapshot(), pub, seed, verify, targets)
    second = _produce(
        _snapshot(), pub, seed, verify, targets,
        backup_id="csbk-20261030-030000Z", created_at="20261030-030000Z",
        previous_manifest=first["manifest"])
    assert second["checks"]["chain_ok"] is True
    assert second["manifest"]["prev_backup_id"] == BACKUP_ID
    corrupt_previous = dict(second["manifest"])
    del corrupt_previous["risk"]  # schema-invalid: unlinkable
    with pytest.raises(integrity_mod.IntegrityError, match="CHAIN_BREAK"):
        _produce(_snapshot(), pub, seed, verify, targets,
                 backup_id="csbk-20261030-040000Z",
                 created_at="20261030-040000Z",
                 previous_manifest=corrupt_previous)


def test_empty_metadata_fails_closed_as_manifest_invalid():
    _, pub, seed, verify = _keys()
    with pytest.raises(produce_mod.ProduceError, match="MANIFEST_INVALID"):
        _produce(_snapshot(risk={}), pub, seed, verify,
                 {"c2": fakes.FakeTarget()})


def test_no_targets_rejected():
    _, pub, seed, verify = _keys()
    with pytest.raises(produce_mod.ProduceError, match="NO_TARGETS"):
        _produce(_snapshot(), pub, seed, verify, {})


def test_signing_seed_never_reaches_logs():
    _, pub, seed, verify = _keys()
    entries: list[str] = []

    class _Handler(logging.Handler):
        def emit(self, record):
            entries.append(record.getMessage())

    logger = logging.getLogger("test-p2-produce-seed")
    logger.handlers = [_Handler()]
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    _produce(_snapshot(), pub, seed, verify, {"c2": fakes.FakeTarget()},
             logger=logger)
    blob = "\n".join(entries)
    assert seed.hex() not in blob
    assert "produce_promoted" in blob
