"""PostgreSQL adapter (Phase 5.2, scratch verification only).

Uses psycopg directly. No connection pooling (scratch scope; production
pooling is Phase 5.3+). DATABASE_URL values are never logged, never raised
in messages, and never returned by any API.

PgStore mirrors the JSON Store interface: ``.state`` materializes the full
state dict from SQL on every access (read-your-writes; demo scale only),
mutations run in single transactions, and audit appends are serialized with
an advisory lock. JSON remains the active backend; PG serves parity
verification with zero production cutover.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from typing import Any, Callable

import psycopg
from psycopg.types.json import Jsonb

from app import config as config_mod
from app.models_pg import DDL, LOAD_ORDER, SCHEMA_VERSION


class PGError(Exception):
    """Base PostgreSQL adapter error (carries a code, never a secret)."""


class PGNotConfigured(PGError):
    def __init__(self) -> None:
        super().__init__("PG_NOT_CONFIGURED: DATABASE_URL is not set")


class PGConnectionError(PGError):
    def __init__(self, detail: str) -> None:
        super().__init__(f"PG_CONNECTION_FAILED: {detail}")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def connect(database_url: str | None = None,
            timeout: int | None = None) -> psycopg.Connection:
    """Open a PostgreSQL connection (autocommit off; caller commits)."""
    url = database_url if database_url is not None else config_mod.DATABASE_URL
    if not url:
        raise PGNotConfigured()
    try:
        return psycopg.connect(
            url,
            connect_timeout=(timeout if timeout is not None
                             else config_mod.PG_CONNECT_TIMEOUT),
            autocommit=False)
    except PGError:
        raise
    except Exception as exc:  # never leak the URL or driver internals
        raise PGConnectionError(type(exc).__name__) from None


def init_schema(conn: psycopg.Connection, *, commit: bool = True) -> str:
    """Create all tables idempotently; stamp schema version last.

    Phase 5.3 L4: with commit=False the DDL joins the caller's transaction,
    so a failed migration rolls the schema back too (database truly
    unchanged). Standalone callers keep commit=True. The version stamp is
    always written last, so a partial schema never reports success.
    """
    with conn.cursor() as cur:
        cur.execute(DDL)
        cur.execute(
            "INSERT INTO schema_meta (key, value) VALUES ('schema_version', %s)"
            " ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
            (SCHEMA_VERSION,))
    if commit:
        conn.commit()
    return SCHEMA_VERSION


def clear_database(conn: psycopg.Connection) -> None:
    """Delete all domain rows + runtime meta (FK-safe). Commits."""
    with conn.cursor() as cur:
        for table in reversed(LOAD_ORDER):
            cur.execute(f'DELETE FROM "{table}"')
        cur.execute("DELETE FROM schema_meta"
                    " WHERE key IN ('run_id', 'trace_id', 'created_at')")
    conn.commit()


def table_counts(conn: psycopg.Connection) -> dict[str, int]:
    """Row counts for every domain table (schema_meta excluded)."""
    counts: dict[str, int] = {}
    with conn.cursor() as cur:
        for table in LOAD_ORDER:
            cur.execute(f'SELECT COUNT(*) FROM "{table}"')
            row = cur.fetchone()
            counts[table] = int(row[0]) if row else 0
    return counts


def database_health(database_url: str | None = None) -> dict[str, Any]:
    """Reachability + schema + counts probe. Never raises, never leaks."""
    url = database_url if database_url is not None else config_mod.DATABASE_URL
    if not url:
        return {"reachable": False, "reason": "PG_NOT_CONFIGURED"}
    try:
        conn = connect(url)
    except PGError as exc:
        return {"reachable": False, "reason": str(exc).split(":")[0]}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            server = str(cur.fetchone()[0]).split(",")[0]
            cur.execute(
                "SELECT value FROM schema_meta WHERE key = 'schema_version'")
            row = cur.fetchone()
        return {"reachable": True, "server": server,
                "schema_version": row[0] if row else None,
                "counts": table_counts(conn)}
    except Exception as exc:  # e.g. schema not initialized yet
        return {"reachable": True, "reason": type(exc).__name__,
                "schema_version": None}
    finally:
        conn.close()


class _PgDoc(dict):
    """Case document with write-through persistence (for cases.record_decision).

    Only top-level field assignment writes through; nothing else in the
    codebase mutates case documents in place (verified by scan).
    """

    def __init__(self, doc: dict, persist: Callable[[dict], None]) -> None:
        super().__init__(doc)
        self._persist = persist

    def __setitem__(self, key: str, value: Any) -> None:
        # Phase 5.3 L5: persist the candidate BEFORE touching the local
        # snapshot, so a failed write never leaves a dirty snapshot.
        candidate = dict(self)
        candidate[key] = value
        self._persist(candidate)
        super().__setitem__(key, value)

    def __copy__(self) -> dict:
        return dict(self)

    def __deepcopy__(self, memo: dict) -> dict:
        import copy as copy_mod

        return copy_mod.deepcopy(dict(self), memo)


class _PgList(list):
    """Decisions list with write-through INSERT (for cases.record_decision)."""

    def __init__(self, items: list, insert: Callable[[dict], None]) -> None:
        super().__init__(items)
        self._insert = insert

    def append(self, record: dict) -> None:
        self._insert(record)
        super().append(record)

    def __copy__(self) -> list:
        return list(self)

    def __deepcopy__(self, memo: dict) -> list:
        import copy as copy_mod

        return copy_mod.deepcopy(list(self), memo)


class PgStore:
    """Phase 5.2 PostgreSQL store with JSON-Store interface parity.

    ``.state`` materializes a fresh snapshot per access. Mutations persist
    in single transactions. JSON remains the active backend; this class
    exists for parity verification on isolated scratch resources.
    """

    backend = "pg"

    def __init__(self, database_url: str | None = None) -> None:
        url = (database_url if database_url is not None
               else config_mod.DATABASE_URL)
        if not url:
            raise PGNotConfigured()
        self._url = url
        # Ambient batch transaction (Phase 5.2.1 M1 fix). Thread-local so
        # concurrent record_decision flows never share a batch.
        self._local = threading.local()

    def _conn(self) -> psycopg.Connection:
        return connect(self._url)

    @property
    def has_open_batch(self) -> bool:
        """True while a multi-statement batch is mid-flight (tests use)."""
        return getattr(self._local, "batch", None) is not None

    def _join(self) -> tuple[psycopg.Connection, bool]:
        """Join the ambient batch or open a fresh owned connection.

        Returns (conn, owns): owns=True means the caller must commit or
        roll back; owns=False means the batch owner (append_audit) commits.
        """
        batch = getattr(self._local, "batch", None)
        if batch is not None:
            return batch, False
        return self._conn(), True

    def _open_batch(self, conn: psycopg.Connection) -> None:
        self._local.batch = conn

    def abort_batch(self) -> bool:
        """Discard any open ambient batch (misuse recovery safety valve).

        Normal flows never need this: record_decision always closes its
        batch via append_audit, and failures auto-discard. Returns True if
        a batch was actually aborted.
        """
        batch = getattr(self._local, "batch", None)
        if batch is None:
            return False
        self._close_batch(batch, commit=False)
        return True

    def _close_batch(self, conn: psycopg.Connection,
                     commit: bool) -> None:
        """Commit/roll back the ambient batch and release it (idempotent)."""
        try:
            if commit:
                conn.commit()
            else:
                conn.rollback()
        finally:
            self._local.batch = None
            conn.close()

    @staticmethod
    def _doc(value: Any) -> dict:
        return value if isinstance(value, dict) else json.loads(value)

    # -- materialized state ------------------------------------------------
    @property
    def state(self) -> dict:
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT scenario_id, scenario_version, seed_hash,"
                            " document FROM scenarios")
                row = cur.fetchone()
                if row is None:
                    raise PGError("PG_EMPTY: no scenario loaded")
                scenario_id, version, seed_hash, scn = row
                scn = self._doc(scn)
                cur.execute("SELECT key, value FROM schema_meta WHERE key IN"
                            " ('run_id', 'trace_id', 'created_at')")
                meta = {k: v for k, v in cur.fetchall()}

                def docs(sql: str, params: tuple = ()) -> list[dict]:
                    cur.execute(sql, params)
                    return [self._doc(r[0]) for r in cur.fetchall()]

                transactions = docs("SELECT document FROM transactions"
                                    " ORDER BY transaction_id")
                events = docs("SELECT document FROM events"
                              " ORDER BY occurred_at, event_id")
                nodes = docs("SELECT document FROM graph_nodes"
                             " ORDER BY node_id")
                edges = docs("SELECT document FROM graph_edges"
                             " ORDER BY edge_id")
                cur.execute("SELECT event_id FROM events"
                            " ORDER BY occurred_at, event_id")
                seen = [r[0] for r in cur.fetchall()]
                cur.execute("SELECT transaction_id, document FROM rule_results"
                            " ORDER BY rule_result_id")
                rule_results: dict[str, list] = {}
                for txn_id, doc in cur.fetchall():
                    rule_results.setdefault(txn_id, []).append(self._doc(doc))
                cur.execute("SELECT target_id, target_type, document"
                            " FROM risk_assessments")
                risk: dict[str, dict] = {}
                for txn_id, scope, doc in cur.fetchall():
                    risk.setdefault(txn_id, {})[scope] = self._doc(doc)
                alerts = docs("SELECT document FROM alerts ORDER BY alert_id")
                investigations = docs("SELECT document FROM investigations"
                                      " ORDER BY investigation_id")
                cur.execute("SELECT investigation_id, document"
                            " FROM evidence_packages")
                packages = {inv: self._doc(doc)
                            for inv, doc in cur.fetchall()}
                cur.execute("SELECT document FROM cases ORDER BY case_id")
                cases = [_PgDoc(self._doc(r[0]), self._persist_case)
                         for r in cur.fetchall()]
                decisions = _PgList(
                    docs("SELECT document FROM decisions ORDER BY decision_id"),
                    self._persist_decision)
                audits = docs("SELECT document FROM audit_events ORDER BY seq")
                ai_runs = docs("SELECT document FROM ai_runs"
                               " ORDER BY agent_run_id")
                simulations = docs("SELECT document FROM simulations"
                                   " ORDER BY simulation_id")
                cur.execute("SELECT COALESCE(MAX(seq), 0) FROM audit_events")
                counter_row = cur.fetchone()
        finally:
            conn.close()
        return {
            "scenario_id": scenario_id, "scenario_version": version,
            "run_id": meta.get("run_id", ""),
            "trace_id": meta.get("trace_id", ""),
            "seed_hash": seed_hash, "manifest": scn.get("manifest", {}),
            "transactions": transactions, "events": events, "nodes": nodes,
            "edges": edges, "seen_event_ids": seen,
            "primary_transaction_id": scn.get("primary_transaction_id", ""),
            "rule_results": rule_results, "risk": risk, "alerts": alerts,
            "investigations": investigations, "evidence_packages": packages,
            "cases": cases, "decisions": decisions, "audits": audits,
            "ai_runs": ai_runs, "simulations": simulations,
            "audit_counter": int(counter_row[0]) if counter_row else 0,
            "replay": {"cursor": 0}, "created_at": meta.get("created_at", ""),
        }

    def _persist_case(self, doc: dict) -> None:
        """Stage a case UPDATE in the ambient batch (no commit).

        The batch commits atomically in append_audit (the guaranteed tail
        of record_decision). Any failure discards the whole batch.
        """
        conn, owns = self._join()
        if owns:
            self._open_batch(conn)
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE cases SET investigation_id = %s,"
                            " status = %s, document = %s"
                            " WHERE case_id = %s",
                            (doc["investigation_id"], doc["status"],
                             Jsonb(dict(doc)), doc["case_id"]))
        except Exception:
            self._close_batch(conn, commit=False)
            raise

    def _persist_decision(self, record: dict) -> None:
        """Stage a decision INSERT in the ambient batch (no commit)."""
        conn, owns = self._join()
        if owns:
            self._open_batch(conn)
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO decisions (decision_id, case_id,"
                            " document) VALUES (%s, %s, %s)",
                            (record["decision_id"], record["case_id"],
                             Jsonb(record)))
        except Exception:
            self._close_batch(conn, commit=False)
            raise

    # -- reads -------------------------------------------------------------
    def counts(self) -> dict[str, int]:
        conn = self._conn()
        try:
            return table_counts(conn)
        finally:
            conn.close()

    def _one(self, sql: str, params: tuple) -> dict | None:
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                row = cur.fetchone()
        finally:
            conn.close()
        if row is None:
            return None
        return self._doc(row[0])

    def get_transaction(self, txn_id: str) -> dict | None:
        return self._one(
            "SELECT document FROM transactions WHERE transaction_id = %s",
            (txn_id,))

    def get_investigation(self, inv_id: str) -> dict | None:
        return self._one(
            "SELECT document FROM investigations WHERE investigation_id = %s",
            (inv_id,))

    def get_case(self, case_id: str) -> dict | None:
        doc = self._one("SELECT document FROM cases WHERE case_id = %s",
                        (case_id,))
        if doc is None:
            return None
        return _PgDoc(doc, self._persist_case)

    def risk_scores(self, txn_id: str) -> dict[str, dict]:
        """{scope: assessment document} for transaction + network scopes."""
        out: dict[str, dict] = {}
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT target_type, document FROM risk_assessments"
                    " WHERE target_id = %s", (txn_id,))
                for target_type, doc in cur.fetchall():
                    out[target_type] = self._doc(doc)
        finally:
            conn.close()
        return out

    def audit_sequence(self) -> list[dict]:
        """Audit documents in sequence order (sequence verification input).

        Phase 5.3 L3: renamed from audit_chain. The guarantee is ordered
        append-only sequencing, not cryptographic hash-chaining.
        """
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT document FROM audit_events ORDER BY seq")
                rows = cur.fetchall()
        finally:
            conn.close()
        return [self._doc(r[0]) for r in rows]

    # -- mutations (single-transaction each; scratch parity scope) ---------
    def append_audit(self, actor_type: str, actor_id: str, action: str,
                     target_type: str, target_id: str, previous: str, new: str,
                     reason: str, trace_id: str, request_id: str) -> dict:
        """Append one audit event, committing any staged batch atomically.

        Standalone calls commit just the audit row (previous behavior).
        When record_decision staged case + decision writes, this call joins
        that batch: case update, decision insert and audit insert commit in
        ONE transaction, or roll back together on any failure (M1 fix).
        Sequencing stays serialized via the advisory lock.
        """
        conn, owns = self._join()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT pg_advisory_xact_lock("
                            "hashtext('cruiseshield.audit'))")
                cur.execute("SELECT COALESCE(MAX(seq), 0) FROM audit_events")
                seq_row = cur.fetchone()
                seq = (int(seq_row[0]) if seq_row else 0) + 1
                entry = {
                    "audit_event_id": f"audit_{seq:04d}",
                    "actor_type": actor_type, "actor_id": actor_id,
                    "action": action, "target_type": target_type,
                    "target_id": target_id,
                    "previous_state_reference": previous,
                    "new_state_reference": new, "reason": reason,
                    "timestamp": _now(), "trace_id": trace_id,
                    "request_id": request_id,
                }
                cur.execute(
                    "INSERT INTO audit_events (audit_event_id, seq, action,"
                    " target_type, target_id, occurred_at, document)"
                    " VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (entry["audit_event_id"], seq, action, target_type,
                     target_id, entry["timestamp"], Jsonb(entry)))
            if owns:
                conn.commit()
                conn.close()
            else:
                self._close_batch(conn, commit=True)
            return entry
        except Exception:
            if owns:
                conn.rollback()
                conn.close()
            else:
                self._close_batch(conn, commit=False)
            raise

    def ingest_event(self, raw: dict) -> tuple[str, dict, list[str]]:
        """Validate + persist an event (same contract as Store.ingest_event).

        Phase 5.3 L1: duplicate detection is atomic (INSERT .. ON CONFLICT
        DO NOTHING + rowcount). Concurrent ingests of the same event yield
        exactly one "accepted"; losers get "duplicate", never an error.
        """
        from app.events import validate_and_normalize

        event, warnings = validate_and_normalize(raw)
        dumped = event.model_dump()
        txn = dumped["transaction"]
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO transactions (transaction_id, amount_minor,"
                    " channel, sender_account_id, receiver_account_id,"
                    " occurred_at, document) VALUES"
                    " (%s, %s, %s, %s, %s, %s, %s)"
                    " ON CONFLICT (transaction_id) DO NOTHING",
                    (txn["transaction_id"], txn["amount_minor"],
                     txn["channel"], txn["sender_account_id"],
                     txn["receiver_account_id"], txn["occurred_at"],
                     Jsonb(txn)))
                cur.execute(
                    "INSERT INTO events (event_id, transaction_id,"
                    " occurred_at, document) VALUES (%s, %s, %s, %s)"
                    " ON CONFLICT (event_id) DO NOTHING",
                    (dumped["event_id"], txn["transaction_id"],
                     dumped["occurred_at"], Jsonb(dumped)))
                duplicate = cur.rowcount == 0
            if duplicate:
                conn.rollback()
                return "duplicate", dumped, warnings
            conn.commit()
            return "accepted", dumped, warnings
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def save_ai_run(self, run: dict) -> None:
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO ai_runs (agent_run_id, evidence_package_id,"
                    " status, model_id, document) VALUES (%s, %s, %s, %s, %s)",
                    (run["agent_run_id"], run["evidence_package_id"],
                     run["status"], run["model_id"], Jsonb(run)))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def save_simulation(self, sim: dict) -> None:
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO simulations (simulation_id,"
                    " target_transaction_id, baseline_score, simulated_score,"
                    " document) VALUES (%s, %s, %s, %s, %s)",
                    (sim["simulation_id"], sim["target_transaction_id"],
                     sim["baseline_score"], sim["simulated_score"],
                     Jsonb(sim)))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def reset(self, scenario_id: str) -> dict:
        """Reseed scratch PG from the canonical JSON seed path (no duplication).

        Builds the scenario with Store.reset on a temp file, clears PG, then
        loads via the idempotent migration loader. Returns the same receipt
        shape as Store.reset.
        """
        import tempfile
        from pathlib import Path

        from app.store import Store
        from migrations.loader import run_migration

        with tempfile.TemporaryDirectory(prefix="cs52-") as tmp:
            seed_file = Path(tmp) / "seed.json"
            receipt = Store(seed_file).reset(scenario_id)
            conn = self._conn()
            try:
                clear_database(conn)
            finally:
                conn.close()
            run_migration(seed_file, self._url, init_schema=False)
        return receipt
