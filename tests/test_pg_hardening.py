"""Phase 5.3: L1-L6 hardening + connection lifecycle tests.

Live PG tests use a private fresh database per test (CREATE-only; teardown
removes everything). Requires SCRATCH_DATABASE_URL, else skips honestly.
"""
import copy
import json
import os
import threading
import uuid
from contextlib import contextmanager

import pytest

SCRATCH_URL = os.environ.get("SCRATCH_DATABASE_URL", "")
needs_scratch_pg = pytest.mark.skipif(
    not SCRATCH_URL, reason="SCRATCH_DATABASE_URL not set (no scratch PG)")


def _base_url():
    base, _, _ = SCRATCH_URL.rpartition("/")
    return base


@pytest.fixture()
def hard(tmp_path):
    """(json_store, pg_store, pg_url) on a private fresh database."""
    import psycopg

    from app import db as db_mod
    from app.store import Store
    from migrations.loader import run_migration

    name = f"cs53_{uuid.uuid4().hex[:12]}"
    admin = psycopg.connect(_base_url() + "/postgres", autocommit=True)
    try:
        admin.execute(f'CREATE DATABASE "{name}"')
    finally:
        admin.close()
    url = _base_url() + f"/{name}"
    seed_file = tmp_path / "seed.json"
    json_store = Store(seed_file)
    run_migration(seed_file, url, init_schema=True)
    return json_store, db_mod.PgStore(url), url


def _event(event_id, txn_id, amount=1000):
    return {
        "event_id": event_id, "occurred_at": "2026-04-01T10:00:00Z",
        "transaction": {"transaction_id": txn_id, "amount_minor": amount,
                        "channel": "TRANSFER_NIP",
                        "sender_account_id": "acc_h1",
                        "receiver_account_id": "acc_h2"},
    }


# -- L1: atomic duplicate detection --------------------------------------
@needs_scratch_pg
def test_concurrent_duplicate_ingest_exactly_one_accepted(hard):
    _, pg, _ = hard
    body = _event("evt_l1_race", "txn_l1_race")
    outcomes: list = []
    errors: list = []

    def worker():
        try:
            outcomes.append(pg.ingest_event(copy.deepcopy(body))[0])
        except Exception as exc:  # noqa: BLE001 - asserted empty below
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []  # losers get "duplicate", never an error
    assert sorted(outcomes) == ["accepted"] + ["duplicate"] * 7
    counts = pg.counts()
    assert counts["events"] == 12  # 11 seed + 1
    assert counts["transactions"] == 12


# -- L2: canonical transaction dedupe ------------------------------------
def test_l2_json_dedupes_shared_transaction(tmp_path):
    from app.store import Store

    store = Store(tmp_path / "s.json")
    before = len(store.state["transactions"])
    assert store.ingest_event(_event("evt_l2_a", "txn_l2_shared", 111))[0] \
        == "accepted"
    assert store.ingest_event(_event("evt_l2_b", "txn_l2_shared", 222))[0] \
        == "accepted"
    # two events, ONE transaction row, first-wins
    assert len(store.state["events"]) == before + 2
    assert len(store.state["transactions"]) == before + 1
    kept = next(t for t in store.state["transactions"]
                if t["transaction_id"] == "txn_l2_shared")
    assert kept["amount_minor"] == 111


@needs_scratch_pg
def test_l2_pg_matches_json_dedupe(hard):
    json_store, pg, _ = hard
    for store in (json_store, pg):
        assert store.ingest_event(_event("evt_l2_a", "txn_l2_shared",
                                         111))[0] == "accepted"
        assert store.ingest_event(_event("evt_l2_b", "txn_l2_shared",
                                         222))[0] == "accepted"
    assert pg.counts()["transactions"] == len(json_store.state["transactions"])
    assert pg.counts()["events"] == len(json_store.state["events"])
    assert pg.get_transaction("txn_l2_shared")["amount_minor"] == 111


# -- L3: honest audit-sequence terminology -------------------------------
@needs_scratch_pg
def test_l3_no_hash_chain_overclaim(hard, tmp_path):
    from app import db as db_mod
    from migrations.loader import run_migration

    _, _, url = hard
    assert hasattr(db_mod.PgStore, "audit_sequence")
    assert not hasattr(db_mod.PgStore, "audit_chain")
    seed_file = tmp_path / "seed2.json"
    from app.store import Store

    Store(seed_file)
    report = run_migration(seed_file, url, init_schema=False)
    assert "audit_sequence_ok" in report["checks"]
    assert "audit_chain_ok" not in report["checks"]
    assert report["checks"]["audit_sequence_ok"] is True


# -- L4: failure-safe schema init ----------------------------------------
@needs_scratch_pg
def test_l4_failed_init_leaves_no_schema(hard, tmp_path, monkeypatch):
    import psycopg

    from app import db as db_mod
    from app.models_pg import LOAD_ORDER
    from app.store import Store
    from migrations.loader import MigrationError, run_migration

    _, _, url = hard
    seed_file = tmp_path / "seed3.json"
    Store(seed_file)
    name = f"cs53_{uuid.uuid4().hex[:12]}"
    admin = psycopg.connect(_base_url() + "/postgres", autocommit=True)
    try:
        admin.execute(f'CREATE DATABASE "{name}"')
    finally:
        admin.close()
    fresh_url = _base_url() + f"/{name}"

    def tables_present():
        conn = psycopg.connect(fresh_url)
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT tablename FROM pg_tables"
                            " WHERE schemaname = 'public'")
                names = {r[0] for r in cur.fetchall()}
        finally:
            conn.close()
        return names & (set(LOAD_ORDER) | {"schema_meta"})

    monkeypatch.setattr(db_mod, "DDL", "GARBAGE SYNTAX (((")
    with pytest.raises(MigrationError):
        run_migration(seed_file, fresh_url, init_schema=True)
    assert tables_present() == set()  # DDL rolled back with the failure
    monkeypatch.undo()
    report = run_migration(seed_file, fresh_url, init_schema=True)
    assert report["passed"] is True  # retry succeeds from clean slate


@needs_scratch_pg
def test_l4_unstamped_schema_never_reports_success(hard):
    import psycopg

    from app import db as db_mod
    from app.models_pg import DDL

    _, _, url = hard
    name = f"cs53_{uuid.uuid4().hex[:12]}"
    admin = psycopg.connect(_base_url() + "/postgres", autocommit=True)
    try:
        admin.execute(f'CREATE DATABASE "{name}"')
    finally:
        admin.close()
    partial_url = _base_url() + f"/{name}"
    conn = psycopg.connect(partial_url)
    try:  # simulate a crash between DDL and version stamp
        with conn.cursor() as cur:
            cur.execute(DDL)
        conn.commit()
    finally:
        conn.close()
    probe = db_mod.database_health(partial_url)
    assert probe["reachable"] is True
    assert probe["schema_version"] is None


# -- L5: persist-before-snapshot ------------------------------------------
@needs_scratch_pg
def test_l5_failed_write_leaves_snapshot_clean(hard):
    _, pg, _ = hard
    case = pg.get_case("case_84721")
    assert case["status"] == "NEW"

    def boom(doc):
        raise RuntimeError("INJECTED_PERSIST_FAILURE")

    case._persist = boom
    with pytest.raises(RuntimeError, match="INJECTED_PERSIST_FAILURE"):
        case["status"] = "TRIAGED"
    assert case["status"] == "NEW"  # local snapshot untouched
    assert pg.get_case("case_84721")["status"] == "NEW"
    assert pg.has_open_batch is False


@needs_scratch_pg
def test_l5_abort_batch_safety_valve(hard):
    from app import db as db_mod

    _, pg, _ = hard
    assert pg.abort_batch() is False  # nothing open
    case = pg.get_case("case_84721")
    case["status"] = "TRIAGED"  # stages a batch, deliberately no audit
    assert pg.has_open_batch is True
    assert pg.abort_batch() is True
    assert pg.has_open_batch is False
    fresh = db_mod.PgStore(pg._url)
    assert fresh.get_case("case_84721")["status"] == "NEW"  # rolled back


# -- L6: empty-history fail-closed -----------------------------------------
@needs_scratch_pg
def test_l6_empty_audit_history_fails_migration(hard, tmp_path):
    from app.store import Store
    from migrations.loader import MigrationError, run_migration

    _, _, url = hard
    seed_file = tmp_path / "seed4.json"
    Store(seed_file)
    state = json.loads(seed_file.read_text(encoding="utf-8"))
    state["audits"] = []
    state["audit_counter"] = 0
    empty_file = tmp_path / "empty-audit.json"
    empty_file.write_text(json.dumps(state), encoding="utf-8")
    with pytest.raises(MigrationError, match="RECONCILIATION_FAILED"):
        run_migration(empty_file, url, init_schema=False)


@needs_scratch_pg
def test_l6_counter_mismatch_fails_migration(hard, tmp_path):
    from app.store import Store
    from migrations.loader import MigrationError, run_migration

    _, _, url = hard
    seed_file = tmp_path / "seed5.json"
    Store(seed_file)
    state = json.loads(seed_file.read_text(encoding="utf-8"))
    state["audit_counter"] = 99
    bad_file = tmp_path / "bad-counter.json"
    bad_file.write_text(json.dumps(state), encoding="utf-8")
    with pytest.raises(MigrationError, match="RECONCILIATION_FAILED"):
        run_migration(bad_file, url, init_schema=False)


# -- connection lifecycle --------------------------------------------------
def test_dead_database_fails_closed_without_leaking_url():
    from app import db as db_mod

    dead = "postgresql://user:SECRETpw@127.0.0.1:9/scratch"
    probe = db_mod.database_health(dead)
    assert probe["reachable"] is False
    blob = json.dumps(probe)
    assert "SECRETpw" not in blob and "127.0.0.1" not in blob
    with pytest.raises(db_mod.PGConnectionError) as excinfo:
        db_mod.connect(dead)
    assert "SECRETpw" not in str(excinfo.value)


@needs_scratch_pg
def test_recovery_after_connection_failure(hard, monkeypatch):
    from app import db as db_mod

    _, pg, url = hard
    monkeypatch.setattr("app.config.DATABASE_URL",
                        "postgresql://127.0.0.1:9/scratch")
    dead_store = db_mod.PgStore()  # construction is lazy; op must fail
    with pytest.raises(db_mod.PGConnectionError):
        dead_store.counts()
    healthy = db_mod.PgStore(url)  # explicit good URL still works
    assert healthy.counts()["cases"] == 1


def test_live_source_untouched():
    import hashlib

    from app import config as config_mod

    raw = config_mod.STATE_PATH.read_bytes()
    assert len(raw) == 101417
    assert hashlib.sha256(raw).hexdigest().upper() == (
        "BA1D4DB4BB4DBC6FC3ACA346664A539610CCC6460CCD530F523C8043453790FE")
