"""J5 migration rehearsal on disposable scratch PG (live-DB-gated).

Full loop: copy live bytes (read-only) → hash-gated load → idempotent
re-run → count/ID/risk/audit reconciliation → app reads+writes →
restart → concurrent reads → corrupt-source rollback → live file
untouched. Runs where SCRATCH_DATABASE_URL exists (here + CI).
"""
import hashlib
import json
import os
import threading

import pytest

import app.config as config_mod

SCRATCH_URL = os.environ.get("SCRATCH_DATABASE_URL", "")
needs_scratch_pg = pytest.mark.skipif(
    not SCRATCH_URL, reason="SCRATCH_DATABASE_URL not set (no scratch PG)")

LIVE_HASH = ("BA1D4DB4BB4DBC6FC3ACA346664A539610CCC6460CCD530F523C8043"
             "453790FE")

# Manifest pins (docs/J5_MIGRATION_MANIFEST.md).
EXPECT_COUNTS = {"transactions": 11, "graph_nodes": 22, "graph_edges": 30,
                 "events": 11, "rule_results": 8, "evidence_items": 39,
                 "investigations": 1, "cases": 1, "decisions": 0,
                 "audit_events": 5, "ai_runs": 2, "simulations": 1,
                 "alerts": 1}


def _live_copy(tmp_path):
    from app import db as db_mod  # noqa: F401  (import parity)

    raw = config_mod.STATE_PATH.read_bytes()
    assert hashlib.sha256(raw).hexdigest().upper() == LIVE_HASH
    copy = tmp_path / "state-copy.json"
    copy.write_bytes(raw)
    return copy


@needs_scratch_pg
def test_j5_full_rehearsal(tmp_path):
    from app import cases as cases_mod
    from app import db as db_mod
    from migrations.loader import MigrationError, run_migration

    copy = _live_copy(tmp_path)
    conn = db_mod.connect(SCRATCH_URL)
    try:
        db_mod.init_schema(conn)
        db_mod.clear_database(conn)
    finally:
        conn.close()
    report = run_migration(copy, SCRATCH_URL, expected_hash=LIVE_HASH)
    assert report["passed"] is True
    again = run_migration(copy, SCRATCH_URL, expected_hash=LIVE_HASH,
                          init_schema=False)
    assert again["passed"] is True
    assert again["tables_actual"] == report["tables_actual"]  # idempotent

    conn = db_mod.connect(SCRATCH_URL)
    try:
        counts = db_mod.table_counts(conn)
    finally:
        conn.close()
    for table, want in EXPECT_COUNTS.items():
        assert counts[table] == want, (table, counts[table])

    pg = db_mod.PgStore(SCRATCH_URL)
    state = pg.state
    assert state["risk"]["txn_84721"]["transaction"]["score"] == 35
    assert state["risk"]["txn_84721"]["network"]["score"] == 84
    assert [a["audit_event_id"] for a in state["audits"]] == [
        "audit_%04d" % i for i in (1, 2, 3, 4, 5)]
    assert len(state["evidence_packages"]["inv_84721"]["items"]) == 39
    assert pg.get_case("case_84721")["status"] == "NEW"

    record, _ = cases_mod.record_decision(
        pg, case_id="case_84721", decision="Monitor",
        target_status="TRIAGED", reason="J5 rehearsal write",
        actor_id="j5", trace_id="trace_j5_1")
    assert record["decision_id"] == "decision_0001"
    assert db_mod.PgStore(
        SCRATCH_URL).get_case("case_84721")["status"] == "TRIAGED"

    errors = []

    def _read():
        try:
            assert db_mod.PgStore(
                SCRATCH_URL).get_case("case_84721") is not None
        except Exception as exc:  # noqa: BLE001 - collected below
            errors.append(exc)

    threads = [threading.Thread(target=_read) for _ in range(8)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert errors == []

    bad = tmp_path / "state-bad.json"
    broken = json.loads(copy.read_bytes().decode("utf-8"))
    del broken["rule_results"]
    bad.write_text(json.dumps(broken), encoding="utf-8")
    with pytest.raises(MigrationError):
        run_migration(bad, SCRATCH_URL)
    conn = db_mod.connect(SCRATCH_URL)
    try:
        assert db_mod.table_counts(conn)["rule_results"] == 8
    finally:
        conn.close()

    assert hashlib.sha256(
        config_mod.STATE_PATH.read_bytes()).hexdigest().upper() == LIVE_HASH


@needs_scratch_pg
def test_j5_pooler_style_url_fails_closed():
    """Pooling rides on Neon's pooler endpoint (URL-agnostic client).

    An unreachable pooler-style URL must fail closed with a fixed
    reason: no raise, no hang, no credential/host leak.
    """
    from app import db as db_mod

    probe = db_mod.database_health(
        "postgresql://u:SECRETpw@127.0.0.1:9/db"
        "?sslmode=require&options=project%3Dx-pooler")
    assert probe["reachable"] is False
    blob = json.dumps(probe)
    assert "SECRETpw" not in blob and "127.0.0.1" not in blob
