"""Idempotent JSON-state to PostgreSQL loader (Phase 5.1 scratch only).

Safety rules:
- ``source_path`` is REQUIRED and must be a separately verified COPY. The
  loader refuses to read the live ``data/state.json`` directly.
- ``expected_hash`` (SHA-256) is verified before any write when supplied.
- All writes happen in ONE transaction: any error rolls everything back.
- Upserts (ON CONFLICT DO UPDATE) make re-runs idempotent; the loader only
  ever adds/refreshes rows, never deletes.
- Nothing here touches the active JSON backend or any production resource.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from app import config as config_mod
from app import db as db_mod


class MigrationError(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_source_copy(source_path: str | Path,
                     expected_hash: str | None = None) -> tuple[dict, int, str]:
    """Read + verify a source COPY. Refuses the live state file."""
    path = Path(source_path).resolve()
    live = Path(config_mod.STATE_PATH).resolve()
    if path == live:
        raise MigrationError(
            "SOURCE_MUST_BE_COPY",
            f"refusing to migrate from live state file {live}; "
            "copy it elsewhere first")
    if not path.exists():
        raise MigrationError("SOURCE_NOT_FOUND", str(path))
    raw = path.read_bytes()
    digest = _sha256_bytes(raw)
    if expected_hash and digest.lower() != expected_hash.lower():
        raise MigrationError(
            "SOURCE_HASH_MISMATCH",
            f"expected {expected_hash} got {digest}")
    try:
        state = json.loads(raw.decode("utf-8"))
    except ValueError as exc:
        raise MigrationError("SOURCE_NOT_JSON", str(exc)) from None
    if not isinstance(state, dict) or "scenario_id" not in state:
        raise MigrationError("SOURCE_BAD_SHAPE", "missing scenario_id")
    return state, len(raw), digest


def _upsert(cur: psycopg.Cursor, table: str, columns: list[str],
            pk: str, rows: list[tuple]) -> int:
    if not rows:
        return 0
    cols = ", ".join(f'"{c}"' for c in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    updates = ", ".join(f'"{c}" = EXCLUDED."{c}"'
                        for c in columns if c != pk)
    sql = (f'INSERT INTO "{table}" ({cols}) VALUES ({placeholders})'
           f' ON CONFLICT ("{pk}") DO UPDATE SET {updates}')
    cur.executemany(sql, rows)
    return len(rows)


def _doc(value: Any) -> Jsonb:
    return Jsonb(value)


def migrate_state(state: dict, conn: psycopg.Connection) -> dict[str, Any]:
    """Upsert one state dict into PG inside the caller's transaction.

    Raises MigrationError (caller rolls back) on any integrity failure.
    Returns the reconciliation report (counts + checks).
    """
    cur = conn.cursor()
    expected: dict[str, int] = {}
    try:
        # scenarios (single row for the active scenario)
        _upsert(cur, "scenarios",
                ["scenario_id", "scenario_version", "seed_hash", "document"],
                "scenario_id", [(
                    state["scenario_id"], state["scenario_version"],
                    state["seed_hash"],
                    _doc({"scenario_id": state["scenario_id"],
                          "scenario_version": state["scenario_version"],
                          "seed_hash": state["seed_hash"],
                          "manifest": state["manifest"],
                          "primary_transaction_id":
                              state["primary_transaction_id"]}),
                )])
        expected["scenarios"] = 1

        # transactions
        _upsert(cur, "transactions",
                ["transaction_id", "amount_minor", "channel",
                 "sender_account_id", "receiver_account_id", "occurred_at",
                 "document"], "transaction_id", [(
                    t["transaction_id"], t["amount_minor"], t["channel"],
                    t["sender_account_id"], t["receiver_account_id"],
                    t["occurred_at"], _doc(t),
                ) for t in state["transactions"]])
        expected["transactions"] = len(state["transactions"])

        # graph_nodes
        _upsert(cur, "graph_nodes", ["node_id", "node_type", "document"],
                "node_id", [(
                    n["node_id"], n["node_type"], _doc(n),
                ) for n in state["nodes"]])
        expected["graph_nodes"] = len(state["nodes"])

        # events
        _upsert(cur, "events",
                ["event_id", "transaction_id", "occurred_at", "document"],
                "event_id", [(
                    e["event_id"], e["transaction"]["transaction_id"],
                    e["occurred_at"], _doc(e),
                ) for e in state["events"]])
        expected["events"] = len(state["events"])

        # graph_edges
        _upsert(cur, "graph_edges",
                ["edge_id", "source_node_id", "target_node_id",
                 "relationship_type", "document"], "edge_id", [(
                    e["edge_id"], e["source_node_id"], e["target_node_id"],
                    e["relationship_type"], _doc(e),
                ) for e in state["edges"]])
        expected["graph_edges"] = len(state["edges"])

        # rule_results (nested {txn_id: [results]})
        rr_rows = [(
            r["rule_result_id"], txn_id, r["rule_id"], r["rule_version"],
            r["triggered"], _doc(r),
        ) for txn_id, results in state["rule_results"].items()
            for r in results]
        _upsert(cur, "rule_results",
                ["rule_result_id", "transaction_id", "rule_id",
                 "rule_version", "triggered", "document"],
                "rule_result_id", rr_rows)
        expected["rule_results"] = len(rr_rows)

        # risk_assessments (nested {txn_id: {scope: assessment}})
        risk_rows = [(
            a["risk_assessment_id"], txn_id, scope, a["score"], a["band"],
            _doc(a),
        ) for txn_id, scopes in state["risk"].items()
            for scope, a in scopes.items()]
        _upsert(cur, "risk_assessments",
                ["risk_assessment_id", "target_id", "target_type", "score",
                 "band", "document"], "risk_assessment_id", risk_rows)
        expected["risk_assessments"] = len(risk_rows)

        # alerts
        _upsert(cur, "alerts",
                ["alert_id", "transaction_id", "status",
                 "risk_assessment_id", "document"], "alert_id", [(
                    a["alert_id"], a["transaction_id"], a["status"],
                    a["risk_assessment_id"], _doc(a),
                ) for a in state["alerts"]])
        expected["alerts"] = len(state["alerts"])

        # investigations
        _upsert(cur, "investigations",
                ["investigation_id", "alert_id", "transaction_id", "status",
                 "document"], "investigation_id", [(
                    i["investigation_id"], i["alert_id"], i["transaction_id"],
                    i["status"], _doc(i),
                ) for i in state["investigations"]])
        expected["investigations"] = len(state["investigations"])

        # evidence_packages + evidence_items (nested {inv_id: package})
        pkg_rows, item_rows = [], []
        for inv_id, pkg in state["evidence_packages"].items():
            pkg_rows.append((pkg["package_id"], inv_id, pkg["package_hash"],
                             _doc(pkg)))
            for item in pkg["items"]:
                item_rows.append((item["evidence_id"], pkg["package_id"],
                                  item["evidence_type"], _doc(item)))
        _upsert(cur, "evidence_packages",
                ["package_id", "investigation_id", "package_hash",
                 "document"], "package_id", pkg_rows)
        expected["evidence_packages"] = len(pkg_rows)
        _upsert(cur, "evidence_items",
                ["evidence_id", "package_id", "evidence_type", "document"],
                "evidence_id", item_rows)
        expected["evidence_items"] = len(item_rows)

        # ai_runs
        _upsert(cur, "ai_runs",
                ["agent_run_id", "evidence_package_id", "status", "model_id",
                 "document"], "agent_run_id", [(
                    r["agent_run_id"], r["evidence_package_id"], r["status"],
                    r["model_id"], _doc(r),
                ) for r in state["ai_runs"]])
        expected["ai_runs"] = len(state["ai_runs"])

        # cases
        _upsert(cur, "cases",
                ["case_id", "investigation_id", "status", "document"],
                "case_id", [(
                    c["case_id"], c["investigation_id"], c["status"], _doc(c),
                ) for c in state["cases"]])
        expected["cases"] = len(state["cases"])

        # decisions
        _upsert(cur, "decisions", ["decision_id", "case_id", "document"],
                "decision_id", [(
                    d["decision_id"], d["case_id"], _doc(d),
                ) for d in state["decisions"]])
        expected["decisions"] = len(state["decisions"])

        # audit_events (sequence = position; append-only order)
        audits = state["audits"]
        _upsert(cur, "audit_events",
                ["audit_event_id", "seq", "action", "target_type",
                 "target_id", "occurred_at", "document"],
                "audit_event_id", [(
                    a["audit_event_id"], seq + 1, a["action"],
                    a["target_type"], a["target_id"], a["timestamp"], _doc(a),
                ) for seq, a in enumerate(audits)])
        expected["audit_events"] = len(audits)

        # simulations
        _upsert(cur, "simulations",
                ["simulation_id", "target_transaction_id", "baseline_score",
                 "simulated_score", "document"], "simulation_id", [(
                    s["simulation_id"], s["target_transaction_id"],
                    s["baseline_score"], s["simulated_score"], _doc(s),
                ) for s in state["simulations"]])
        expected["simulations"] = len(state["simulations"])
    except KeyError as exc:
        raise MigrationError("SOURCE_MISSING_FIELD", str(exc)) from None

    # runtime identity (needed for full state materialization on PG)
    for key in ("run_id", "trace_id", "created_at"):
        cur.execute(
            "INSERT INTO schema_meta (key, value) VALUES (%s, %s)"
            " ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
            (key, state[key]))

    report = reconcile(cur, state, expected)
    failures = [k for k, v in report["checks"].items() if v is not True]
    if failures:
        raise MigrationError("RECONCILIATION_FAILED", ", ".join(failures))
    return report


def _dup_pks(cur: psycopg.Cursor, table: str, pk: str) -> int:
    cur.execute(f'SELECT COUNT(*) FROM (SELECT "{pk}" FROM "{table}"'
                f' GROUP BY "{pk}" HAVING COUNT(*) > 1) dups')
    row = cur.fetchone()
    return int(row[0]) if row else 0


def _missing_fk(cur: psycopg.Cursor, table: str, fk: str,
                parent: str, parent_pk: str) -> int:
    cur.execute(
        f'SELECT COUNT(*) FROM "{table}" c LEFT JOIN "{parent}" p'
        f' ON c."{fk}" = p."{parent_pk}" WHERE p."{parent_pk}" IS NULL')
    row = cur.fetchone()
    return int(row[0]) if row else 0


# (child table, child pk, child fk, parent table, parent pk)
_FK_CHECKS = [
    ("events", "event_id", "transaction_id", "transactions",
     "transaction_id"),
    ("graph_edges", "edge_id", "source_node_id", "graph_nodes", "node_id"),
    ("graph_edges", "edge_id", "target_node_id", "graph_nodes", "node_id"),
    ("rule_results", "rule_result_id", "transaction_id", "transactions",
     "transaction_id"),
    ("alerts", "alert_id", "transaction_id", "transactions",
     "transaction_id"),
    ("alerts", "alert_id", "risk_assessment_id", "risk_assessments",
     "risk_assessment_id"),
    ("investigations", "investigation_id", "alert_id", "alerts", "alert_id"),
    ("investigations", "investigation_id", "transaction_id", "transactions",
     "transaction_id"),
    ("evidence_packages", "package_id", "investigation_id", "investigations",
     "investigation_id"),
    ("evidence_items", "evidence_id", "package_id", "evidence_packages",
     "package_id"),
    ("cases", "case_id", "investigation_id", "investigations",
     "investigation_id"),
    ("decisions", "decision_id", "case_id", "cases", "case_id"),
]

_PK_COLUMNS = {
    "scenarios": "scenario_id", "transactions": "transaction_id",
    "graph_nodes": "node_id", "events": "event_id",
    "graph_edges": "edge_id", "rule_results": "rule_result_id",
    "risk_assessments": "risk_assessment_id", "alerts": "alert_id",
    "investigations": "investigation_id",
    "evidence_packages": "package_id", "evidence_items": "evidence_id",
    "ai_runs": "agent_run_id", "cases": "case_id",
    "decisions": "decision_id", "audit_events": "audit_event_id",
    "simulations": "simulation_id",
}


def _package_hash_ok(items: list[dict], package_hash: str) -> bool:
    """Recompute the canonical evidence package hash (mirrors build_package)."""
    canonical = json.dumps(sorted(items, key=lambda i: i["evidence_id"]),
                           sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest() == package_hash


def reconcile(cur: psycopg.Cursor, state: dict,
              expected: dict[str, int]) -> dict[str, Any]:
    """Verify PG contents against the source state. Returns report dict."""
    actual: dict[str, int] = {}
    for table in expected:
        cur.execute(f'SELECT COUNT(*) FROM "{table}"')
        row = cur.fetchone()
        actual[table] = int(row[0]) if row else 0

    dup_pks = {t: _dup_pks(cur, t, pk) for t, pk in _PK_COLUMNS.items()}
    missing_fks = {
        f"{child}.{fk}": _missing_fk(cur, child, fk, parent, parent_pk)
        for child, _, fk, parent, parent_pk in _FK_CHECKS
    }

    # risk scores byte-exact per transaction + scope
    risk_ok: dict[str, dict[str, dict[str, Any]]] = {}
    for txn_id, scopes in state["risk"].items():
        risk_ok[txn_id] = {}
        for scope, assessment in scopes.items():
            cur.execute(
                "SELECT score, band FROM risk_assessments"
                " WHERE target_id = %s AND target_type = %s",
                (txn_id, scope))
            row = cur.fetchone()
            risk_ok[txn_id][scope] = {
                "expected_score": assessment["score"],
                "actual_score": row[0] if row else None,
                "expected_band": assessment["band"],
                "actual_band": row[1] if row else None,
            }

    # audit sequence (Phase 5.3 L3: ordered append-only sequencing, not
    # cryptographic hash-chaining): contiguous seq 1..N, IDs audit_NNNN,
    # counter matches, and history is never empty (L6 fail-closed: every
    # valid state carries seed audits, so empty history always fails).
    cur.execute("SELECT seq, audit_event_id FROM audit_events ORDER BY seq")
    seq_rows = cur.fetchall()
    audit_ids_ok = all(aid == f"audit_{seq:04d}" for seq, aid in seq_rows)
    seqs = [seq for seq, _ in seq_rows]
    contiguous = seqs == list(range(1, len(seqs) + 1))
    counter_ok = len(seqs) == state.get("audit_counter", len(seqs))
    history_present = len(seqs) > 0

    # evidence package hashes recomputed from migrated items
    package_ok: dict[str, bool] = {}
    for inv_id, pkg in state["evidence_packages"].items():
        cur.execute("SELECT document FROM evidence_items"
                    " WHERE package_id = %s", (pkg["package_id"],))
        items = [r[0] for r in cur.fetchall()]
        package_ok[pkg["package_id"]] = _package_hash_ok(
            items, pkg["package_hash"])

    # runtime identity round-trip
    cur.execute("SELECT key, value FROM schema_meta"
                " WHERE key IN ('run_id', 'trace_id', 'created_at')")
    meta = {k: v for k, v in cur.fetchall()}
    meta_ok = all(state.get(k) == meta.get(k)
                  for k in ("run_id", "trace_id", "created_at"))

    checks = {
        "counts_match": actual == expected,
        "duplicate_pks_zero": all(v == 0 for v in dup_pks.values()),
        "missing_fks_zero": all(v == 0 for v in missing_fks.values()),
        "risk_scores_exact": all(
            s["expected_score"] == s["actual_score"]
            and s["expected_band"] == s["actual_band"]
            for scopes in risk_ok.values() for s in scopes.values()),
        "audit_sequence_ok": bool(
            audit_ids_ok and contiguous and counter_ok and history_present),
        "package_hashes_ok": all(package_ok.values()),
        "runtime_meta_ok": bool(meta_ok),
    }
    return {"tables_expected": expected, "tables_actual": actual,
            "duplicate_pks": dup_pks, "missing_fks": missing_fks,
            "risk": risk_ok,
            "audit": {"count": len(seqs),
                      "counter": state.get("audit_counter"),
                      "contiguous": contiguous, "ids_match": audit_ids_ok},
            "package_hashes": package_ok, "checks": checks,
            "passed": all(checks.values())}


def run_migration(source_path: str | Path, database_url: str,
                  expected_hash: str | None = None,
                  init_schema: bool = True) -> dict[str, Any]:
    """Load a source COPY into PG atomically. Returns the report.

    Any failure rolls the transaction back (database left unchanged) and
    raises MigrationError. Never touches the live JSON store.
    """
    state, size, digest = load_source_copy(source_path, expected_hash)
    conn = db_mod.connect(database_url)
    try:
        if init_schema:
            # Phase 5.3 L4: DDL joins this transaction, so a failed load
            # rolls the schema back too — the database is truly unchanged.
            db_mod.init_schema(conn, commit=False)
        report = migrate_state(state, conn)
        conn.commit()
    except MigrationError:
        conn.rollback()
        raise
    except Exception as exc:
        conn.rollback()
        raise MigrationError("LOAD_FAILED", type(exc).__name__) from None
    finally:
        conn.close()
    report["source_size"] = size
    report["source_hash"] = digest
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Migrate a JSON state COPY into PostgreSQL (scratch).")
    parser.add_argument("--source", required=True,
                        help="path to a verified COPY of state.json")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--expected-hash", default=None)
    parser.add_argument("--no-init-schema", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = run_migration(args.source, args.database_url,
                               args.expected_hash,
                               init_schema=not args.no_init_schema)
    except (MigrationError, db_mod.PGError) as exc:
        print(f"MIGRATION_FAILED {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
