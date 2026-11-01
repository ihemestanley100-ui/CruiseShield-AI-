"""Phase 5.2.1 M1: record_decision commits case+decision+audit in ONE txn.

Isolation uses a fresh database per test (CREATE only). No reset, clear,
delete, or drop appears in this file; scratch teardown removes everything.

Requires SCRATCH_DATABASE_URL, else skips (reported, never green).
"""
import os
import threading
import uuid
from contextlib import contextmanager

import pytest

SCRATCH_URL = os.environ.get("SCRATCH_DATABASE_URL", "")
needs_scratch_pg = pytest.mark.skipif(
    not SCRATCH_URL, reason="SCRATCH_DATABASE_URL not set (no scratch PG)")


def _admin_url():
    base, _, _ = SCRATCH_URL.rpartition("/")
    return base + "/postgres"


@pytest.fixture()
def atom(tmp_path):
    """(json_store, pg_store) on a private fresh database. Create-only."""
    import psycopg

    from app import db as db_mod
    from app.store import Store
    from migrations.loader import run_migration

    name = f"cs521_{uuid.uuid4().hex[:12]}"
    admin = psycopg.connect(_admin_url(), autocommit=True)
    try:
        admin.execute(f'CREATE DATABASE "{name}"')
    finally:
        admin.close()
    url = _admin_url().rpartition("/")[0] + f"/{name}"
    seed_file = tmp_path / "seed.json"
    json_store = Store(seed_file)
    run_migration(seed_file, url, init_schema=True)
    pg_store = db_mod.PgStore(url)
    assert pg_store.has_open_batch is False
    # NOTE: no DROP (deletion prohibited); container teardown removes all.
    return json_store, pg_store


def _decision_kwargs(**over):
    kwargs = {"case_id": "case_84721", "decision": "Escalate",
              "target_status": "TRIAGED", "reason": "m1 probe",
              "actor_id": "m1", "trace_id": "trace_m1"}
    kwargs.update(over)
    return kwargs


class _FailingCursor:
    """Cursor proxy raising RuntimeError on the Nth execute (crash sim)."""

    def __init__(self, real, counter, kill_at):
        self._real = real
        self._counter = counter
        self._kill_at = kill_at

    def __enter__(self):
        self._real.__enter__()
        return self

    def __exit__(self, *exc):
        return self._real.__exit__(*exc)

    def execute(self, *args, **kwargs):
        self._counter[0] += 1
        if self._counter[0] == self._kill_at:
            raise RuntimeError(f"INJECTED_FAILURE_AT_{self._kill_at}")
        return self._real.execute(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._real, name)


class _FailingConn:
    def __init__(self, real, kill_at):
        self._real = real
        self._counter = [0]
        self._kill_at = kill_at

    def cursor(self, *args, **kwargs):
        return _FailingCursor(self._real.cursor(*args, **kwargs),
                              self._counter, self._kill_at)

    def __getattr__(self, name):
        return getattr(self._real, name)


@contextmanager
def _crash_at(pg_store, kill_at):
    """The batch connection fails its kill_at-th execute (crash sim).

    Hooks _join (not _conn) so validation reads keep working and only
    the decision batch runs on the failing connection.
    """
    from app import db as db_mod

    real_conn = db_mod.connect(pg_store._url)
    proxy = _FailingConn(real_conn, kill_at)
    original = pg_store._join

    def fake_join():
        conn, owns = original()
        if owns:
            conn.close()  # discard; the batch runs on the proxy
            return proxy, True
        return conn, owns

    pg_store._join = fake_join
    try:
        yield
    finally:
        pg_store._join = original
        real_conn.close()


def _consistent(pg_store, *, decisions, status, audits):
    from app import db as db_mod

    fresh = db_mod.PgStore(pg_store._url)
    try:
        assert fresh.get_case("case_84721")["status"] == status
        assert fresh.counts()["decisions"] == decisions
        chain = fresh.audit_sequence()
        assert len(chain) == audits
        assert [a["audit_event_id"] for a in chain] == \
            [f"audit_{n:04d}" for n in range(1, audits + 1)]
    finally:
        pass
    assert pg_store.has_open_batch is False


@needs_scratch_pg
def test_success_commits_all_four(atom):
    from app import cases as cases_mod

    _, pg = atom
    record, audit = cases_mod.record_decision(pg, **_decision_kwargs())
    assert record["decision_id"] == "decision_0001"
    assert audit["audit_event_id"] == "audit_0003"
    assert pg.get_case("case_84721")["status"] == "TRIAGED"
    _consistent(pg, decisions=1, status="TRIAGED", audits=3)


@needs_scratch_pg
@pytest.mark.parametrize("kill_at", [1, 2, 3, 4, 5, 6])
def test_failure_at_each_statement_rolls_back_all(atom, kill_at):
    """Kill U1/U2(case UPDATEs), I1(decision), LOCK/MAX/audit INSERT."""
    from app import cases as cases_mod

    _, pg = atom
    with _crash_at(pg, kill_at):
        with pytest.raises(RuntimeError, match="INJECTED_FAILURE"):
            cases_mod.record_decision(pg, **_decision_kwargs())
    _consistent(pg, decisions=0, status="NEW", audits=2)


@needs_scratch_pg
def test_crash_leaves_no_partial_decision(atom):
    """A fresh reader after a mid-flush crash sees pristine state."""
    from app import cases as cases_mod

    _, pg = atom
    with _crash_at(pg, 6):  # die on the audit INSERT itself
        with pytest.raises(RuntimeError):
            cases_mod.record_decision(pg, **_decision_kwargs())
    _consistent(pg, decisions=0, status="NEW", audits=2)


@needs_scratch_pg
def test_concurrent_decisions_exactly_one_wins(atom):
    from app import cases as cases_mod

    _, pg = atom
    outcomes: list = []

    def worker(n):
        try:
            record, _ = cases_mod.record_decision(
                pg, **_decision_kwargs(reason=f"racer {n}"))
            outcomes.append(("won", record["decision_id"]))
        except Exception as exc:  # noqa: BLE001 - outcome asserted below
            outcomes.append(("lost", type(exc).__name__))

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(o[0] for o in outcomes) == ["lost"] * 3 + ["won"]
    _consistent(pg, decisions=1, status="TRIAGED", audits=3)


@needs_scratch_pg
def test_standalone_audit_unchanged(atom):
    _, pg = atom
    entry = pg.append_audit("human", "m1", "probe", "case", "case_84721",
                            "", "", "r", "t", "t")
    assert entry["audit_event_id"] == "audit_0003"
    _consistent(pg, decisions=0, status="NEW", audits=3)


@needs_scratch_pg
def test_second_decision_reuses_closed_batch(atom):
    from app import cases as cases_mod

    _, pg = atom
    cases_mod.record_decision(pg, **_decision_kwargs())
    assert pg.has_open_batch is False
    record, audit = cases_mod.record_decision(
        pg, **_decision_kwargs(decision="Monitor",
                               target_status="INVESTIGATING"))
    assert record["decision_id"] == "decision_0002"
    assert audit["audit_event_id"] == "audit_0004"
    _consistent(pg, decisions=2, status="INVESTIGATING", audits=4)


def test_json_record_decision_unchanged(tmp_path):
    from app import cases as cases_mod
    from app.store import Store

    store = Store(tmp_path / "json.json")
    record, audit = cases_mod.record_decision(store, **_decision_kwargs())
    assert record["decision_id"] == "decision_0001"
    assert audit["audit_event_id"] == "audit_0003"
    assert store.get_case("case_84721")["status"] == "TRIAGED"
    reread = Store(tmp_path / "json.json")
    assert reread.get_case("case_84721")["status"] == "TRIAGED"
    assert len(reread.state["decisions"]) == 1


def test_live_source_untouched():
    import hashlib

    from app import config as config_mod

    raw = config_mod.STATE_PATH.read_bytes()
    assert len(raw) == 101417
    assert hashlib.sha256(raw).hexdigest().upper() == (
        "BA1D4DB4BB4DBC6FC3ACA346664A539610CCC6460CCD530F523C8043453790FE")
