"""Scratch-load path: verified plan -> fresh scratch Store + counts."""
import json

import pytest

import backup_fakes as fakes
from app import config as config_mod
from backups import load_scratch as load_mod
from backups import restore as restore_mod


def _plan(dump, counts, tmp_path):
    snapshot = fakes.make_snapshot(dump=dump, table_counts=counts)
    targets = {"c2": fakes.FakeTarget()}
    _, keys = fakes.produce_once(targets, snapshot=snapshot)
    return restore_mod.plan_restore(
        target=targets["c2"], target_name="c2",
        backup_id=fakes.BACKUP_ID, verify_key=keys[3],
        private_key=keys[0], logger=fakes.null_logger())


def _fixture_bytes():
    from fixtures.canonical_seed import fixture_bytes

    return fixture_bytes()


def test_load_verifies_counts_into_fresh_scratch(tmp_path):
    dump = _fixture_bytes()
    doc = json.loads(dump)
    counts = {k: len(v) for k, v in doc.items() if isinstance(v, list)}
    plan = _plan(dump, counts, tmp_path)
    report = load_mod.load_plan_into_scratch(plan, tmp_path / "scratch.json")
    assert report["scenario_id"] == doc["scenario_id"]
    assert "transactions" in report["checked_tables"]
    assert json.loads((tmp_path / "scratch.json").read_bytes()) == doc


def test_count_mismatch_fails_closed_without_writing(tmp_path):
    dump = _fixture_bytes()
    plan = _plan(dump, {"transactions": 999999}, tmp_path)
    dest = tmp_path / "scratch.json"
    with pytest.raises(load_mod.LoadError, match="COUNT_MISMATCH"):
        load_mod.load_plan_into_scratch(plan, dest)
    assert not dest.exists()


def test_live_path_refused(tmp_path):
    dump = _fixture_bytes()
    doc = json.loads(dump)
    counts = {k: len(v) for k, v in doc.items() if isinstance(v, list)}
    plan = _plan(dump, counts, tmp_path)
    with pytest.raises(load_mod.LoadError, match="LIVE_PATH_REFUSED"):
        load_mod.load_plan_into_scratch(plan, config_mod.STATE_PATH)


def test_existing_dest_never_overwritten(tmp_path):
    dump = _fixture_bytes()
    doc = json.loads(dump)
    counts = {k: len(v) for k, v in doc.items() if isinstance(v, list)}
    plan = _plan(dump, counts, tmp_path)
    dest = tmp_path / "scratch.json"
    dest.write_bytes(b"original")
    with pytest.raises(load_mod.LoadError, match="DEST_EXISTS"):
        load_mod.load_plan_into_scratch(plan, dest)
    assert dest.read_bytes() == b"original"


def test_garbage_plaintext_rejected(tmp_path):
    plan = _plan(b"not-json{{{", {"transactions": 1}, tmp_path)
    with pytest.raises(load_mod.LoadError, match="PLAINTEXT_INVALID"):
        load_mod.load_plan_into_scratch(plan, tmp_path / "s.json")
