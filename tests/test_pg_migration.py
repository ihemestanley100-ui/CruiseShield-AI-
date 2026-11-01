"""Phase 5.1: backend selection, health/readiness, scratch PG migration.

Live-PostgreSQL tests require SCRATCH_DATABASE_URL (isolated scratch only,
e.g. a local throwaway container); otherwise they skip with an explicit
reason. A skip is reported as a skip, never as green.

The live source data/state.json is NEVER read or written by these tests.
Migration tests copy its bytes to tmp_path first and verify the copy hash.
"""
import hashlib
import json
import os

import pytest
from env_probe import CAN_SOCKETS

import app.config as config_mod
import app.main as main
from app.store import Store, open_store, storage_backend

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

SCRATCH_URL = os.environ.get("SCRATCH_DATABASE_URL", "")
needs_scratch_pg = pytest.mark.skipif(
    not SCRATCH_URL, reason="SCRATCH_DATABASE_URL not set (no scratch PG)")

# Live-source integrity anchor (Phase 4.4-4.6 verified, re-checked per run).
LIVE_SIZE = 101417
LIVE_HASH = ("BA1D4DB4BB4DBC6FC3ACA346664A539610CCC6460CCD530F523C8043453790FE")


@pytest.fixture()
def source_copy(tmp_path):
    """Byte-copy of the live state (read-only source) with hash receipt."""
    live = config_mod.STATE_PATH
    raw = live.read_bytes()
    assert len(raw) == LIVE_SIZE, "live source size changed - STOP"
    assert hashlib.sha256(raw).hexdigest().upper() == LIVE_HASH, \
        "live source hash changed - STOP"
    dest = tmp_path / "state-copy.json"
    dest.write_bytes(raw)
    assert hashlib.sha256(dest.read_bytes()).hexdigest().upper() == LIVE_HASH
    return dest


@pytest.fixture()
def scratch_db():
    """Clean scratch database: fresh schema per test, dropped after."""
    import psycopg

    from app import db as db_mod

    conn = db_mod.connect(SCRATCH_URL)
    db_mod.init_schema(conn)
    conn.close()
    yield SCRATCH_URL
    conn = psycopg.connect(SCRATCH_URL, autocommit=True)
    try:
        from app.models_pg import LOAD_ORDER

        with conn.cursor() as cur:
            for table in reversed(LOAD_ORDER):
                cur.execute(f'DELETE FROM "{table}"')
            cur.execute("DELETE FROM schema_meta")
    finally:
        conn.close()


# -- backend selection -------------------------------------------------
def test_backend_defaults_to_json(monkeypatch):
    monkeypatch.setattr(config_mod, "STORE_BACKEND", "json")
    assert storage_backend() == "json"
    assert Store.backend == "json"
    assert isinstance(open_store("json"), Store)


def test_backend_selection_validated():
    from app.config import validate_backend

    assert validate_backend("pg") == "pg"
    assert validate_backend(" JSON ") == "json"
    with pytest.raises(ValueError, match="UNKNOWN_STORAGE_BACKEND"):
        validate_backend("oracle")


def test_open_store_pg_requires_url(monkeypatch):
    monkeypatch.setattr(config_mod, "DATABASE_URL", "")
    from app import db as db_mod

    with pytest.raises(db_mod.PGNotConfigured):
        open_store("pg")


# -- health / readiness (no PG needed) ---------------------------------
@pytest.mark.skipif(
    not CAN_SOCKETS,
    reason="socket creation forbidden in this sandbox; runs in CI/user envs")
def test_health_json_default_reports_backend(client):
    body = client.get("/api/v1/health").json()
    assert body["status"] == "healthy"
    assert body["checks"]["storage_backend"] == \
        "PASS active=json selected=json"
    assert body["checks"]["pg"] == "NOT_CONFIGURED"


@pytest.mark.skipif(
    not CAN_SOCKETS,
    reason="socket creation forbidden in this sandbox; runs in CI/user envs")
def test_ready_json_default(client):
    resp = client.get("/api/v1/ready")
    assert resp.status_code == 200
    assert resp.json()["ready"] is True


@pytest.mark.skipif(
    not CAN_SOCKETS,
    reason="socket creation forbidden in this sandbox; runs in CI/user envs")
def test_ready_pg_unreachable_fails_closed(client, monkeypatch):
    monkeypatch.setattr(config_mod, "STORE_BACKEND", "pg")
    monkeypatch.setattr(config_mod, "DATABASE_URL",
                        "postgresql://127.0.0.1:9/scratch")
    monkeypatch.setattr(config_mod, "PG_CONNECT_TIMEOUT", 1)
    resp = client.get("/api/v1/ready")
    assert resp.status_code == 503
    assert resp.json()["ready"] is False
    assert resp.json()["pg"].startswith("FAIL")
    health = client.get("/api/v1/health").json()
    assert health["status"] == "degraded"
    # secret safety: the URL value must never appear in responses
    blob = json.dumps(resp.json()) + json.dumps(health)
    assert "postgresql://" not in blob


# -- loader guards (no PG needed) --------------------------------------
def test_loader_refuses_live_source():
    from migrations.loader import MigrationError, load_source_copy

    with pytest.raises(MigrationError, match="SOURCE_MUST_BE_COPY"):
        load_source_copy(config_mod.STATE_PATH)


def test_loader_rejects_hash_mismatch(source_copy):
    from migrations.loader import MigrationError, load_source_copy

    with pytest.raises(MigrationError, match="SOURCE_HASH_MISMATCH"):
        load_source_copy(source_copy, expected_hash="0" * 64)


def test_pg_mutations_forbidden_without_url(monkeypatch):
    monkeypatch.setattr(config_mod, "DATABASE_URL", "")
    from app import db as db_mod

    with pytest.raises(db_mod.PGNotConfigured):
        db_mod.PgStore()


# -- live scratch PG migration -----------------------------------------
@needs_scratch_pg
def test_migrate_reconciles_exactly(source_copy, scratch_db):
    from migrations.loader import run_migration

    report = run_migration(source_copy, scratch_db,
                           expected_hash=LIVE_HASH)
    assert report["passed"] is True
    assert report["source_size"] == LIVE_SIZE
    assert report["source_hash"].upper() == LIVE_HASH
    expected = report["tables_expected"]
    assert report["tables_actual"] == expected
    # mandated record counts
    assert expected["investigations"] == 1
    assert expected["cases"] == 1
    assert expected["decisions"] == 0
    assert expected["ai_runs"] == 2
    assert expected["simulations"] == 1
    assert expected["audit_events"] == 5
    assert expected["alerts"] == 1
    assert expected["evidence_items"] == 39
    assert expected["graph_nodes"] == 22
    assert expected["graph_edges"] == 30
    # mandated risk scores (authoritative, byte-exact)
    risk = report["risk"]["txn_84721"]
    assert risk["transaction"]["actual_score"] == 35
    assert risk["network"]["actual_score"] == 84
    # mandated integrity gates
    assert all(v == 0 for v in report["duplicate_pks"].values())
    assert all(v == 0 for v in report["missing_fks"].values())
    assert report["audit"]["contiguous"] is True
    assert report["audit"]["counter"] == 5
    assert all(report["package_hashes"].values())


@needs_scratch_pg
def test_migrate_is_idempotent(source_copy, scratch_db):
    from migrations.loader import run_migration

    first = run_migration(source_copy, scratch_db)
    second = run_migration(source_copy, scratch_db)
    assert second["passed"] is True
    assert second["tables_actual"] == first["tables_actual"]
    assert second["tables_actual"] == first["tables_expected"]
    assert second["risk"] == first["risk"]


@needs_scratch_pg
def test_migrate_rolls_back_on_corruption(source_copy, scratch_db,
                                          tmp_path):
    import psycopg

    from app import db as db_mod
    from migrations.loader import MigrationError, run_migration

    bad = json.loads(source_copy.read_text(encoding="utf-8"))
    # corrupt FK: alert points at a nonexistent transaction
    bad["alerts"][0]["transaction_id"] = "txn_missing"
    bad_path = tmp_path / "state-bad.json"
    bad_path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(MigrationError):
        run_migration(bad_path, scratch_db)
    conn = db_mod.connect(scratch_db)
    try:
        counts = db_mod.table_counts(conn)
    finally:
        conn.close()
    assert all(v == 0 for v in counts.values()), \
        "failed migration must leave the database unchanged"


@needs_scratch_pg
def test_pgstore_reads_and_rollback_to_json(source_copy, scratch_db,
                                            monkeypatch):
    from app import db as db_mod
    from migrations.loader import run_migration

    run_migration(source_copy, scratch_db)
    monkeypatch.setattr(config_mod, "DATABASE_URL", scratch_db)
    pg = open_store("pg")
    assert isinstance(pg, db_mod.PgStore)
    assert pg.get_case("case_84721")["status"] == "NEW"
    assert pg.get_investigation("inv_84721")["status"] == "OPEN"
    assert pg.get_transaction("txn_84721")["amount_minor"] == 48000000
    scores = pg.risk_scores("txn_84721")
    assert scores["transaction"]["score"] == 35
    assert scores["network"]["score"] == 84
    assert len(pg.audit_sequence()) == 5
    # rollback path: JSON backend unaffected and still the default
    monkeypatch.setattr(config_mod, "STORE_BACKEND", "json")
    assert storage_backend() == "json"
    assert isinstance(open_store(), Store)
    # Phase 5.2: PG mutations allowed on scratch (parity scope)
    pg.save_simulation({"simulation_id": "sim_9000",
                        "target_transaction_id": "txn_84721",
                        "baseline_score": 84, "simulated_score": 10})
    assert pg.counts()["simulations"] == 2


@needs_scratch_pg
def test_health_pg_selected_reports_schema(client, source_copy, scratch_db,
                                           monkeypatch):
    from migrations.loader import run_migration

    run_migration(source_copy, scratch_db)
    monkeypatch.setattr(config_mod, "STORE_BACKEND", "pg")
    monkeypatch.setattr(config_mod, "DATABASE_URL", scratch_db)
    body = client.get("/api/v1/health").json()
    assert body["status"] == "healthy"
    assert body["checks"]["pg"].startswith("PASS schema=5.1.0")
    assert client.get("/api/v1/ready").status_code == 200


def test_live_source_untouched_after_suite():
    raw = config_mod.STATE_PATH.read_bytes()
    assert len(raw) == LIVE_SIZE
    assert hashlib.sha256(raw).hexdigest().upper() == LIVE_HASH
