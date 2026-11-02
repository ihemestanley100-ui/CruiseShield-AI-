"""J6 disposable backup/restore drill (live-DB-gated, no owner backup).

Snapshots the scratch PG (seeded from live-shape bytes by the J5
rehearsal path), seals with EPHEMERAL keys into in-memory fake
targets, then restores: manifest chain, signature, cross-copy,
decrypt, snapshot equality. Nothing leaves the test process.
"""
import os

import pytest

SCRATCH_URL = os.environ.get("SCRATCH_DATABASE_URL", "")
needs_scratch_pg = pytest.mark.skipif(
    not SCRATCH_URL, reason="SCRATCH_DATABASE_URL not set (no scratch PG)")


@needs_scratch_pg
def test_j6_disposable_roundtrip_drill(tmp_path):
    import backup_fakes as fakes
    from app import db as db_mod
    from backups import crypto as crypto_mod
    from backups import produce as produce_mod
    from backups import restore as restore_mod
    from backups import signing as signing_mod
    from migrations.loader import run_migration

    raw = open("data/state.json", "rb").read()  # read-only source bytes
    copy = tmp_path / "state-copy.json"
    copy.write_bytes(raw)
    conn = db_mod.connect(SCRATCH_URL)
    try:
        db_mod.clear_database(conn)
    finally:
        conn.close()
    report = run_migration(copy, SCRATCH_URL)
    assert report["passed"] is True

    snap = produce_mod.PostgresSnapshotter(
        lambda: db_mod.connect(SCRATCH_URL)).capture()
    assert snap.schema_version == "5.1.0"
    assert snap.dump  # canonical snapshot bytes exist

    priv, pub = crypto_mod.generate_keypair()
    seed, verify = signing_mod.generate_signing_keypair()
    targets = {"c2": fakes.FakeTarget(), "c3": fakes.FakeTarget()}
    made = produce_mod.produce_backup(
        snapshot=snap, recipient_pubkeys=[pub], signing_seed=seed,
        signing_verify_key=verify, targets=targets,
        backup_id="csbk-20261101-000001Z", created_at="20261101-000001Z",
        source="scratch")
    assert made["promoted"] is True
    assert made["checks"]["cross_copy_ok"] is True

    ok = restore_mod.verify_backup_set(
        targets=targets, backup_id="csbk-20261101-000001Z",
        verify_key=verify)
    assert ok["verified"] is True
    assert ok["cross_copy_ok"] is True
    plan = restore_mod.plan_restore(
        target=targets["c2"], target_name="c2",
        backup_id="csbk-20261101-000001Z", verify_key=verify,
        private_key=priv)
    assert plan.plaintext == snap.dump
    assert plan.manifest["backup_id"] == "csbk-20261101-000001Z"
