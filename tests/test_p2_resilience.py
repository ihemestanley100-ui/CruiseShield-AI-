"""P2 resilience tests: partial outages, partial artifacts, termination.

Fake targets, ephemeral keys, synthetic snapshots. Every test proves
the same invariant from a different angle: no incomplete backup is
ever promoted, and existing valid generations stay byte-identical.
"""
import pytest

import backup_fakes as fakes
from backups import produce as produce_mod
from backups import restore as restore_mod
from backups import targets as targets_mod


def _artifacts(target, backup_id):
    return {name: target.store.get(f"{backup_id}/{name}")
            for name in ("dump.csbk1", "manifest.json", "manifest.sig")}


def test_c2_down_c3_healthy_promotes_nothing():
    c2, c3 = fakes.FakeTarget(), fakes.FakeTarget()
    targets = {"c2": c2, "c3": c3}
    keys = fakes.ephemeral_keys()
    snapshot = fakes.make_snapshot()
    first, _ = fakes.produce_once(targets, keys=keys, snapshot=snapshot)
    before_c2 = dict(c2.store)
    before_c3 = dict(c3.store)
    c2.fail_puts = 99  # C2 hard down; C3 fully healthy
    with pytest.raises(produce_mod.ProduceError, match="UPLOAD_FAILED"):
        fakes.produce_once(targets, keys=keys, snapshot=snapshot,
                           backup_id="csbk-20261030-030000Z",
                           created_at="20261030-030000Z",
                           previous_manifest=first["manifest"])
    assert c2.store == before_c2  # failed puts store nothing
    assert c3.store == before_c3  # fail-fast never reaches C3
    assert all(v is None for v in
               _artifacts(c3, "csbk-20261030-030000Z").values())
    plan = restore_mod.plan_restore(
        target=c2, target_name="c2", backup_id=fakes.BACKUP_ID,
        verify_key=keys[3], private_key=keys[0],
        logger=fakes.null_logger())
    assert plan.plaintext == snapshot.dump  # prior generation intact


def test_partial_artifact_set_never_verifies_or_restores():
    target = fakes.FakeTarget()
    keys = fakes.ephemeral_keys()
    fakes.produce_once({"c2": target}, keys=keys)
    del target.store[f"{fakes.BACKUP_ID}/manifest.sig"]
    with pytest.raises(targets_mod.NotFoundError):
        restore_mod.verify_backup_set(
            targets={"c2": target}, backup_id=fakes.BACKUP_ID,
            verify_key=keys[3], logger=fakes.null_logger())
    with pytest.raises(targets_mod.NotFoundError):
        restore_mod.plan_restore(
            target=target, target_name="c2", backup_id=fakes.BACKUP_ID,
            verify_key=keys[3], private_key=keys[0],
            logger=fakes.null_logger())


class _DropsSigTarget(fakes.FakeTarget):
    """Loses the signature between upload and promotion readback."""

    def put(self, path, data):
        receipt = super().put(path, data)
        if path.endswith("/manifest.sig"):
            del self.store[path]
        return receipt


def test_promotion_readback_gap_blocks_promotion():
    target = _DropsSigTarget()
    keys = fakes.ephemeral_keys()
    with pytest.raises(produce_mod.ProduceError,
                        match="PROMOTION_READBACK_FAILED"):
        fakes.produce_once({"c2": target}, keys=keys)
    assert f"{fakes.BACKUP_ID}/manifest.sig" not in target.store


class _DiesMidUploadTarget(fakes.FakeTarget):
    """Process termination during the second upload."""

    def put(self, path, data):
        if len(self.puts) == 1:
            raise KeyboardInterrupt("simulated SIGTERM")
        return super().put(path, data)


def test_termination_mid_upload_is_never_promoted_or_adopted():
    target = _DiesMidUploadTarget()
    keys = fakes.ephemeral_keys()
    snapshot = fakes.make_snapshot()
    with pytest.raises(KeyboardInterrupt):
        fakes.produce_once({"c2": target}, keys=keys, snapshot=snapshot)
    assert len(target.puts) == 1  # died before finishing artifact 2
    with pytest.raises(produce_mod.ProduceError, match="UPLOAD_DIVERGENT"):
        fakes.produce_once({"c2": target}, keys=keys, snapshot=snapshot)
    assert len(target.puts) == 1  # orphan bytes never adopted


def test_recovery_selects_verified_alternative_copy():
    targets = {"c2": fakes.FakeTarget(), "c3": fakes.FakeTarget()}
    keys = fakes.ephemeral_keys()
    snapshot = fakes.make_snapshot()
    fakes.produce_once(targets, keys=keys, snapshot=snapshot)
    bad_path = f"{fakes.BACKUP_ID}/dump.csbk1"
    blob = bytearray(targets["c2"].store[bad_path])
    blob[10] ^= 0x01
    targets["c2"].store[bad_path] = bytes(blob)
    with pytest.raises(Exception):
        restore_mod.plan_restore(
            target=targets["c2"], target_name="c2",
            backup_id=fakes.BACKUP_ID, verify_key=keys[3],
            private_key=keys[0], logger=fakes.null_logger())
    with pytest.raises(Exception):
        restore_mod.verify_backup_set(
            targets=targets, backup_id=fakes.BACKUP_ID,
            verify_key=keys[3], logger=fakes.null_logger())
    plan = restore_mod.plan_restore(
        target=targets["c3"], target_name="c3",
        backup_id=fakes.BACKUP_ID, verify_key=keys[3],
        private_key=keys[0], logger=fakes.null_logger())
    assert plan.plaintext == snapshot.dump
    assert plan.checks["signature_ok"] is True


def test_retries_stay_idempotent_under_flakes():
    target = fakes.FakeTarget()
    target.fail_puts = 4  # faults across artifact boundaries
    keys = fakes.ephemeral_keys()
    report, _ = fakes.produce_once({"c2": target}, keys=keys, attempts=6)
    assert report["promoted"] is True
    assert len(target.store) == 3  # exactly one copy of each artifact
    plan = restore_mod.plan_restore(
        target=target, target_name="c2", backup_id=fakes.BACKUP_ID,
        verify_key=keys[3], private_key=keys[0],
        logger=fakes.null_logger())
    assert plan.plaintext == fakes.make_snapshot().dump
