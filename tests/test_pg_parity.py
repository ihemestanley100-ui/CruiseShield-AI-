"""Phase 5.2: request-path parity between JSON and scratch PostgreSQL.

Strategy: seed a JSON Store and a scratch PG from the SAME bytes, then run
identical API requests and operations against both and compare. Reads must
be byte-identical; mutations must match modulo wall-clock fields only.

Live PG tests require SCRATCH_DATABASE_URL, else they skip (reported, never
green). The live data/state.json is never touched; seeds use tmp files.
"""
import copy
import os
import threading

import pytest
from env_probe import CAN_SOCKETS
from fastapi.testclient import TestClient

import app.config as config_mod
import app.main as main
from app.store import Store

SCRATCH_URL = os.environ.get("SCRATCH_DATABASE_URL", "")
needs_scratch_pg = pytest.mark.skipif(
    not SCRATCH_URL, reason="SCRATCH_DATABASE_URL not set (no scratch PG)")

CLOCK_KEYS = {"created_at", "updated_at", "timestamp", "completed_at",
              "started_at", "computed_at"}


def norm(obj, extra=()):
    """Deep-copy dropping wall-clock fields (and any extras)."""
    drop = CLOCK_KEYS | set(extra)
    if isinstance(obj, dict):
        return {k: norm(v, extra) for k, v in obj.items() if k not in drop}
    if isinstance(obj, list):
        return [norm(v, extra) for v in obj]
    return obj


def canon(state):
    """Canonicalize list order (IDs) so backend order is never compared."""
    state = copy.deepcopy(state)

    def sort_by(items, *keys):
        return sorted(items, key=lambda d: tuple(d.get(k, "") for k in keys))

    state["transactions"] = sort_by(state["transactions"], "transaction_id")
    state["events"] = sort_by(state["events"], "occurred_at", "event_id")
    state["seen_event_ids"] = sorted(state["seen_event_ids"])
    state["nodes"] = sort_by(state["nodes"], "node_id")
    state["edges"] = sort_by(state["edges"], "edge_id")
    state["rule_results"] = {
        k: sort_by(v, "rule_result_id")
        for k, v in state["rule_results"].items()}
    state["alerts"] = sort_by(state["alerts"], "alert_id")
    state["investigations"] = sort_by(state["investigations"],
                                      "investigation_id")
    state["cases"] = sort_by(state["cases"], "case_id")
    state["decisions"] = sort_by(state["decisions"], "decision_id")
    state["audits"] = sort_by(state["audits"], "audit_event_id")
    state["ai_runs"] = sort_by(state["ai_runs"], "agent_run_id")
    state["simulations"] = sort_by(state["simulations"], "simulation_id")
    return state


@pytest.fixture()
def pair(tmp_path, monkeypatch):
    """(json_store, pg_store) seeded from identical bytes on scratch PG."""
    from app import db as db_mod
    from migrations.loader import run_migration

    seed_file = tmp_path / "seed.json"
    json_store = Store(seed_file)  # auto-seeds scn_primary to tmp file
    conn = db_mod.connect(SCRATCH_URL)
    try:
        db_mod.init_schema(conn)
        db_mod.clear_database(conn)
    finally:
        conn.close()
    run_migration(seed_file, SCRATCH_URL, init_schema=False)
    monkeypatch.setattr(config_mod, "DATABASE_URL", SCRATCH_URL)
    pg_store = db_mod.PgStore()
    yield json_store, pg_store
    conn = db_mod.connect(SCRATCH_URL)
    try:
        db_mod.clear_database(conn)
    finally:
        conn.close()


@pytest.fixture()
def pair_request(pair, monkeypatch):
    """Run one request against JSON then PG, fully isolated per side.

    Returns ((json_status, json_body), (pg_status, pg_body)).
    """
    json_store, pg_store = pair

    def go(method, path, body=None, headers=None):
        monkeypatch.setattr(main, "store", json_store)
        with TestClient(main.app) as client:
            left = client.request(method, path, json=body,
                                  headers=headers)
            left_pair = (left.status_code, left.json())
        monkeypatch.setattr(main, "store", pg_store)
        with TestClient(main.app) as client:
            right = client.request(method, path, json=body,
                                   headers=headers)
            right_pair = (right.status_code, right.json())
        return left_pair, right_pair

    return go


@pytest.fixture()
def headers():
    return {"X-Request-ID": "parity-trace-001"}


# -- read parity: byte-identical -----------------------------------------
@needs_scratch_pg
def test_state_materialization_matches(pair):
    json_store, pg_store = pair
    assert canon(pg_store.state) == canon(json_store.state)


@needs_scratch_pg
@pytest.mark.parametrize("method,path", [
    ("GET", "/api/v1/transactions/txn_84721"),
    ("GET", "/api/v1/graph/txn_84721"),
    ("GET", "/api/v1/risk/txn_84721?scope=transaction"),
    ("GET", "/api/v1/risk/txn_84721?scope=network"),
    ("GET", "/api/v1/alerts"),
    ("GET", "/api/v1/investigations/inv_84721"),
    ("GET", "/api/v1/investigations/inv_84721/evidence-package"),
    ("POST", "/api/v1/investigations/inv_84721/evidence-package"),
    ("GET", "/api/v1/replay/scn_primary?cursor=0"),
    ("GET", "/api/v1/replay/scn_primary?cursor=3"),
    ("GET", "/api/v1/replay/scn_primary?cursor=999"),
    ("GET", "/api/v1/cases"),
    ("GET", "/api/v1/cases/case_84721"),
    ("GET", "/api/v1/cases/case_84721/audit"),
])
def test_read_parity(pair_request, headers, method, path):
    left, right = pair_request(method, path, headers=headers)
    assert right == left


@needs_scratch_pg
@pytest.mark.parametrize("method,path,body", [
    ("GET", "/api/v1/transactions/txn_nope", None),
    ("GET", "/api/v1/graph/txn_nope", None),
    ("GET", "/api/v1/risk/txn_nope", None),
    ("GET", "/api/v1/risk/txn_84721?scope=bogus", None),
    ("GET", "/api/v1/investigations/inv_nope", None),
    ("GET", "/api/v1/investigations/inv_nope/evidence-package", None),
    ("GET", "/api/v1/replay/scn_nope", None),
    ("GET", "/api/v1/cases/case_nope", None),
    ("GET", "/api/v1/cases/case_nope/audit", None),
    ("GET", "/api/v1/ai-runs/agentrun_nope", None),
    ("POST", "/api/v1/investigations/inv_nope/ai-followup",
     {"question": "q"}),
    ("POST", "/api/v1/investigations/inv_nope/ai-followup", "not-a-dict"),
    ("POST", "/api/v1/cases/case_nope/decisions", {"decision": "x"}),
    ("POST", "/api/v1/simulations", {"ignored_edge_ids": "nope"}),
    ("POST", "/api/v1/simulations", "not-a-dict"),
    ("POST", "/api/v1/events", {"event_id": ""}),
])
def test_error_parity(pair_request, headers, method, path, body):
    (left_status, left_body), (right_status, right_body) = \
        pair_request(method, path, body=body, headers=headers)
    assert right_status == left_status
    assert norm(right_body) == norm(left_body)


@needs_scratch_pg
def test_empty_states_parity(pair_request):
    (_, left), (_, right) = pair_request("GET", "/api/v1/cases/case_84721")
    for case in (left, right):
        assert case["decisions"] == []
        assert case["latest_ai_run"] is None


# -- mutation parity: identical modulo wall-clock ------------------------
def _event_body(suffix):
    return {
        "event_id": f"evt_parity_{suffix}",
        "occurred_at": "2026-03-01T12:00:00Z",
        "transaction": {
            "transaction_id": f"txn_parity_{suffix}",
            "amount_minor": 250000,
            "channel": "TRANSFER_NIP",
            "sender_account_id": "acc_p1",
            "receiver_account_id": "acc_p2",
        },
    }


@needs_scratch_pg
def test_event_ingest_parity(pair_request, headers, pair):
    body = _event_body("one")
    left, right = pair_request("POST", "/api/v1/events", body=body,
                               headers=headers)
    assert right == left
    assert right[1]["status"] == "accepted"
    # duplicate: identical idempotent response, no new rows either side
    left2, right2 = pair_request("POST", "/api/v1/events", body=body,
                                 headers=headers)
    assert right2 == left2
    assert right2[1]["status"] == "duplicate"
    json_store, pg_store = pair
    assert canon(pg_store.state) == canon(json_store.state)


@needs_scratch_pg
def test_simulation_parity(pair_request, headers):
    body = {"target_transaction_id": "txn_84721", "ignored_edge_ids": [],
            "assumption": "parity probe", "actor_id": "parity"}
    left, right = pair_request("POST", "/api/v1/simulations", body=body,
                               headers=headers)
    assert right[0] == left[0] == 200
    assert norm(right[1]) == norm(left[1])
    assert right[1]["simulation_id"] == "sim_0001"  # fresh seed, no sims
    assert right[1]["baseline_score"] == 84


@needs_scratch_pg
def test_decision_parity(pair_request, headers, pair):
    body = {"decision": "Escalate", "target_status": "TRIAGED",
            "reason": "parity probe", "actor_id": "parity",
            "evidence_viewed": [], "recommendation": ""}
    left, right = pair_request("POST", "/api/v1/cases/case_84721/decisions",
                               body=body, headers=headers)
    assert right[0] == left[0] == 200
    assert norm(right[1]) == norm(left[1])
    assert right[1]["decision"]["decision_id"] == "decision_0001"
    assert right[1]["audit"]["audit_event_id"] == "audit_0003"  # 2 seed + 1
    assert right[1]["case"]["status"] == "TRIAGED"
    # full states match modulo wall-clock after the same mutation
    json_store, pg_store = pair
    assert norm(canon(pg_store.state)) == norm(canon(json_store.state))


@needs_scratch_pg
def test_record_decision_direct_parity(pair):
    from app import cases as cases_mod

    json_store, pg_store = pair
    kwargs = {"case_id": "case_84721", "decision": "Monitor",
              "target_status": "TRIAGED", "reason": "direct parity",
              "actor_id": "parity", "trace_id": "trace_direct_1"}
    record_l, audit_l = cases_mod.record_decision(json_store, **kwargs)
    record_r, audit_r = cases_mod.record_decision(pg_store, **kwargs)
    assert norm(record_r) == norm(record_l)
    assert norm(audit_r) == norm(audit_l)
    assert pg_store.get_case("case_84721")["status"] == "TRIAGED"
    assert norm(canon(pg_store.state)) == norm(canon(json_store.state))


@needs_scratch_pg
def test_ai_run_persistence_parity(pair):
    json_store, pg_store = pair
    run = {"agent_run_id": "agentrun_0001", "provider": "meta",
           "model_id": "muse-spark-1.3", "prompt_version": "cs-prompt-v2",
           "request_id": "req_p1", "trace_id": json_store.state["trace_id"],
           "evidence_package_id": "evidence_pkg_scn_primary_v1",
           "evidence_ids_sent": ["evidence_txn_84721"],
           "started_at": "2026-03-01T12:00:00Z",
           "completed_at": "2026-03-01T12:00:01Z", "latency_ms": 900,
           "status": "SUCCEEDED", "response_reference": "resp_p1",
           "schema_validation_status": "VALID",
           "evidence_reference_validation_status": "VALID",
           "error_code": "", "synthetic_data_flag": True,
           "result": {"conclusion": "parity", "key_findings": [],
                      "missing_information": []}}
    json_store.save_ai_run(copy.deepcopy(run))
    pg_store.save_ai_run(copy.deepcopy(run))
    assert canon(pg_store.state)["ai_runs"] == \
        canon(json_store.state)["ai_runs"]


@needs_scratch_pg
def test_reset_parity(pair):
    json_store, pg_store = pair
    receipt_l = json_store.reset("scn_false_positive")
    receipt_r = pg_store.reset("scn_false_positive")
    # package_hash embeds the per-reset run trace, and the reset audit's
    # new_state_reference IS the run_id, so both legitimately differ
    extra = ("run_id", "trace_id", "request_id", "package_hash",
             "new_state_reference")
    assert norm(receipt_r, extra) == norm(receipt_l, extra)
    assert norm(canon(pg_store.state), extra) == \
        norm(canon(json_store.state), extra)


# -- determinism, concurrency, transactions ------------------------------
@needs_scratch_pg
def test_deterministic_scores_and_hashes(pair):
    json_store, pg_store = pair
    assert pg_store.risk_scores("txn_84721") == {
        scope: json_store.state["risk"]["txn_84721"][scope]
        for scope in ("transaction", "network")}
    assert pg_store.risk_scores("txn_84721")["network"]["score"] == 84
    pkgs_l = json_store.state["evidence_packages"]
    pkgs_r = pg_store.state["evidence_packages"]
    assert {k: v["package_hash"] for k, v in pkgs_r.items()} == \
        {k: v["package_hash"] for k, v in pkgs_l.items()}


@needs_scratch_pg
def test_concurrent_audit_appends_serialized(pair):
    _, pg_store = pair
    errors: list = []

    def worker(n):
        try:
            for i in range(5):
                pg_store.append_audit("human", f"w{n}", "probe", "case",
                                      "case_84721", "", "", f"{n}-{i}",
                                      "t", "t")
        except Exception as exc:  # noqa: BLE001 - collected, asserted below
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    chain = pg_store.audit_sequence()
    assert len(chain) == 2 + 40  # 2 seed audits + 40 probes
    assert [a["audit_event_id"] for a in chain] == \
        [f"audit_{n:04d}" for n in range(1, 43)]


@needs_scratch_pg
def test_failed_mutation_rolls_back(pair):
    from app import db as db_mod

    _, pg_store = pair
    before = pg_store.counts()
    with pytest.raises(KeyError):
        pg_store.save_ai_run({"agent_run_id": "agentrun_bad"})
    with pytest.raises(ValueError, match="SCHEMA_INVALID"):
        pg_store.ingest_event({"event_id": ""})
    assert pg_store.counts() == before
    assert isinstance(db_mod.PgStore.backend, str)


@needs_scratch_pg
def test_audit_append_only(pair):
    from app import db as db_mod

    _, pg_store = pair
    assert not hasattr(pg_store, "update_audit")
    assert not hasattr(pg_store, "delete_audit")
    pg_store.append_audit("human", "a", "probe", "case", "case_84721",
                          "", "", "r", "t", "t")
    chain = pg_store.audit_sequence()
    assert [a["audit_event_id"] for a in chain] == \
        [f"audit_{n:04d}" for n in range(1, 4)]  # 2 seed + 1


# -- defaults and no-silent-fallback (no PG needed) -----------------------
def test_json_is_default_and_active():
    from app.store import open_store, storage_backend

    assert storage_backend() == "json"
    assert isinstance(main.store, Store)
    assert main.store.backend == "json"
    assert isinstance(open_store(), Store)


@pytest.mark.skipif(
    not CAN_SOCKETS,
    reason="socket creation forbidden in this sandbox; runs in CI/user envs")
def test_pg_selected_unreachable_never_reports_healthy(client, monkeypatch):
    monkeypatch.setattr(config_mod, "STORE_BACKEND", "pg")
    monkeypatch.setattr(config_mod, "DATABASE_URL",
                        "postgresql://127.0.0.1:9/scratch")
    monkeypatch.setattr(config_mod, "PG_CONNECT_TIMEOUT", 1)
    assert client.get("/api/v1/ready").status_code == 503
    assert client.get("/api/v1/health").json()["status"] == "degraded"


def test_live_source_untouched():
    import hashlib

    raw = config_mod.STATE_PATH.read_bytes()
    assert len(raw) == 101417
    assert hashlib.sha256(raw).hexdigest().upper() == (
        "BA1D4DB4BB4DBC6FC3ACA346664A539610CCC6460CCD530F523C8043453790FE")
