"""LocalDirTarget unit tests: round-trip, containment, idempotency."""
import pytest

from backups import local_target as local_mod
from backups import produce as produce_mod
from backups import targets as targets_mod


def test_put_get_exists_round_trip(tmp_path):
    target = local_mod.LocalDirTarget(tmp_path / "bk")
    etag = target.put("csbk-1/dump.csbk1", b"bytes-123")
    assert etag.startswith("local-sha256:")
    assert target.get("csbk-1/dump.csbk1") == b"bytes-123"
    assert target.exists("csbk-1/dump.csbk1")
    assert not target.exists("csbk-1/missing")


def test_get_missing_raises_not_found(tmp_path):
    target = local_mod.LocalDirTarget(tmp_path)
    with pytest.raises(targets_mod.NotFoundError):
        target.get("nope/manifest.json")


def test_path_escape_rejected(tmp_path):
    target = local_mod.LocalDirTarget(tmp_path / "root")
    for evil in ("../escape", "a/../../escape", "/abs/path"):
        with pytest.raises(targets_mod.TargetError):
            target.put(evil, b"x")
    assert not (tmp_path / "escape").exists()


def test_put_idempotent_same_bytes(tmp_path):
    target = local_mod.LocalDirTarget(tmp_path)
    first = produce_mod.put_idempotent(target, "g/manifest.json", b"m")
    second = produce_mod.put_idempotent(target, "g/manifest.json", b"m")
    assert second.startswith("present:")
    assert target.get("g/manifest.json") == b"m"


def test_put_idempotent_divergent_rejected(tmp_path):
    target = local_mod.LocalDirTarget(tmp_path)
    produce_mod.put_idempotent(target, "g/manifest.json", b"m")
    with pytest.raises(produce_mod.ProduceError, match="UPLOAD_DIVERGENT"):
        produce_mod.put_idempotent(target, "g/manifest.json", b"other")


def test_relative_root_does_not_self_escape(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    target = local_mod.LocalDirTarget("rel-bk")
    target.put("csbk-1/dump.csbk1", b"bytes-123")
    assert target.get("csbk-1/dump.csbk1") == b"bytes-123"
    with pytest.raises(targets_mod.TargetError):
        target.put("../escape", b"x")
