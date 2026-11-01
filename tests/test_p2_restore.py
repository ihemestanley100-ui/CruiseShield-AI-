"""P2 restore tests. Fake targets, ephemeral keys. Restore writes nothing."""
import logging
import pathlib

import pytest

import backup_fakes as fakes
from backups import crypto as crypto_mod
from backups import integrity as integrity_mod
from backups import produce as produce_mod
from backups import restore as restore_mod
from backups import targets as targets_mod


def _plan(target, backup_id, keys, **over):
    priv, _, _, verify = keys
    kwargs = {"target": target, "target_name": "c2",
              "backup_id": backup_id, "verify_key": verify,
              "private_key": priv, "logger": fakes.null_logger()}
    kwargs.update(over)
    return restore_mod.plan_restore(**kwargs)


def test_round_trip_returns_original_plaintext():
    target = fakes.FakeTarget()
    snapshot = fakes.make_snapshot(dump=b'{"canonical":true}')
    _, keys = fakes.produce_once({"c2": target}, snapshot=snapshot)
    plan = _plan(target, fakes.BACKUP_ID, keys)
    assert plan.plaintext == b'{"canonical":true}'
    assert plan.manifest["backup_id"] == fakes.BACKUP_ID
    assert plan.checks == {"signature_ok": True, "dump_sha256_ok": True,
                           "decrypt_ok": True}


def test_wrong_verify_key_rejected():
    target = fakes.FakeTarget()
    _, keys = fakes.produce_once({"c2": target})
    _, other_verify = keys[2], fakes.ephemeral_keys()[3]
    priv = keys[0]
    with pytest.raises(integrity_mod.IntegrityError):
        restore_mod.plan_restore(
            target=target, target_name="c2", backup_id=fakes.BACKUP_ID,
            verify_key=other_verify, private_key=priv,
            logger=fakes.null_logger())


def test_wrong_private_key_rejected():
    target = fakes.FakeTarget()
    _, keys = fakes.produce_once({"c2": target})
    _, _, _, verify = keys
    wrong_priv = fakes.ephemeral_keys()[0]
    with pytest.raises(crypto_mod.CryptoError, match="DECRYPT_FAILED"):
        restore_mod.plan_restore(
            target=target, target_name="c2", backup_id=fakes.BACKUP_ID,
            verify_key=verify, private_key=wrong_priv,
            logger=fakes.null_logger())


def test_tampered_envelope_rejected():
    target = fakes.FakeTarget()
    _, keys = fakes.produce_once({"c2": target})
    path = f"{fakes.BACKUP_ID}/dump.csbk1"
    blob = bytearray(target.store[path])
    blob[10] ^= 0x01
    target.store[path] = bytes(blob)
    with pytest.raises(integrity_mod.IntegrityError, match="SHA_MISMATCH"):
        _plan(target, fakes.BACKUP_ID, keys)


def test_corrupt_manifest_rejected():
    target = fakes.FakeTarget()
    _, keys = fakes.produce_once({"c2": target})
    target.store[f"{fakes.BACKUP_ID}/manifest.json"] = b"{not-json"
    with pytest.raises(restore_mod.RestoreError, match="MANIFEST_INVALID"):
        _plan(target, fakes.BACKUP_ID, keys)


def test_swapped_signatures_rejected():
    target = fakes.FakeTarget()
    _, keys = fakes.produce_once({"c2": target})
    second_id = "csbk-20261030-030000Z"
    fakes.produce_once({"c2": target}, keys=keys, backup_id=second_id,
                       created_at="20261030-030000Z")
    first_sig = f"{fakes.BACKUP_ID}/manifest.sig"
    second_sig = f"{second_id}/manifest.sig"
    target.store[first_sig], target.store[second_sig] = (
        target.store[second_sig], target.store[first_sig])
    with pytest.raises(integrity_mod.IntegrityError):
        _plan(target, fakes.BACKUP_ID, keys)
    with pytest.raises(integrity_mod.IntegrityError):
        _plan(target, second_id, keys)


def test_chain_gap_rejected_and_chain_ok_reported():
    target = fakes.FakeTarget()
    first, keys = fakes.produce_once({"c2": target})
    second_id = "csbk-20261030-030000Z"
    fakes.produce_once({"c2": target}, keys=keys, backup_id=second_id,
                       created_at="20261030-030000Z",
                       previous_manifest=first["manifest"])
    plan = _plan(target, second_id, keys)
    assert plan.checks["chain_ok"] is True
    for suffix in ("dump.csbk1", "manifest.json", "manifest.sig"):
        del target.store[f"{fakes.BACKUP_ID}/{suffix}"]
    with pytest.raises(restore_mod.RestoreError, match="CHAIN_GAP"):
        _plan(target, second_id, keys)


def test_missing_backup_raises_not_found():
    target = fakes.FakeTarget()
    keys = fakes.ephemeral_keys()
    with pytest.raises(targets_mod.NotFoundError):
        _plan(target, fakes.BACKUP_ID, keys)


def test_verify_backup_set_across_targets():
    targets = {"c2": fakes.FakeTarget(), "c3": fakes.FakeTarget()}
    _, keys = fakes.produce_once(targets)
    report = restore_mod.verify_backup_set(
        targets=targets, backup_id=fakes.BACKUP_ID,
        verify_key=keys[3], logger=fakes.null_logger())
    assert report == {"backup_id": fakes.BACKUP_ID,
                      "targets": {"c2": {"signature_ok": True,
                                        "dump_sha256_ok": True},
                                  "c3": {"signature_ok": True,
                                        "dump_sha256_ok": True}},
                      "verified": True, "cross_copy_ok": True}


def test_verify_backup_set_catches_divergent_copy():
    targets = {"c2": fakes.FakeTarget(), "c3": fakes.FakeTarget()}
    _, keys = fakes.produce_once(targets)
    # Divergent but self-consistent copy is impossible (hash binds the
    # manifest), so divergence must surface as a hash failure here.
    path = f"{fakes.BACKUP_ID}/dump.csbk1"
    blob = bytearray(targets["c3"].store[path])
    blob[10] ^= 0x01
    targets["c3"].store[path] = bytes(blob)
    with pytest.raises(integrity_mod.IntegrityError):
        restore_mod.verify_backup_set(
            targets=targets, backup_id=fakes.BACKUP_ID,
            verify_key=keys[3], logger=fakes.null_logger())


def test_private_key_never_reaches_logs():
    target = fakes.FakeTarget()
    _, keys = fakes.produce_once({"c2": target})
    entries: list[str] = []

    class _Handler(logging.Handler):
        def emit(self, record):
            entries.append(record.getMessage())

    logger = logging.getLogger("test-p2-restore-seed")
    logger.handlers = [_Handler()]
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    _plan(target, fakes.BACKUP_ID, keys, logger=logger)
    blob = "\n".join(entries)
    assert keys[0].hex() not in blob
    assert "restore_planned" in blob


def test_restore_module_is_read_only_and_ceremony_free():
    text = (pathlib.Path(__file__).resolve().parent.parent / "backups"
            / "restore.py").read_text(encoding="utf-8")
    assert "shamir" not in text
    assert ".put(" not in text
    assert "psycopg" not in text
    assert "app.db" not in text and "app import db" not in text
