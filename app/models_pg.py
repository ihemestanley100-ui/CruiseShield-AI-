"""PostgreSQL schema for CruiseShield AI (Phase 5.1, scratch verification).

Design: every table carries its natural string primary key, extracted index
columns (IDs, scores, statuses, timestamps) and a ``document JSONB`` column
holding the complete original JSON record. Full-document storage guarantees
zero-field-loss migration: reconciliation compares documents byte-for-byte
against the source copy.

No SQLAlchemy: the adapter uses psycopg directly to avoid introducing a new
framework. Production concerns (pooling, RLS, partitions) are Phase 5.2+.
"""
from __future__ import annotations

SCHEMA_VERSION = "5.1.0"

DDL = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scenarios (
    scenario_id TEXT PRIMARY KEY,
    scenario_version TEXT NOT NULL,
    seed_hash TEXT NOT NULL,
    document JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    amount_minor BIGINT NOT NULL,
    channel TEXT NOT NULL,
    sender_account_id TEXT NOT NULL,
    receiver_account_id TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    document JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS graph_nodes (
    node_id TEXT PRIMARY KEY,
    node_type TEXT NOT NULL,
    document JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL REFERENCES transactions (transaction_id),
    occurred_at TEXT NOT NULL,
    document JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS graph_edges (
    edge_id TEXT PRIMARY KEY,
    source_node_id TEXT NOT NULL REFERENCES graph_nodes (node_id),
    target_node_id TEXT NOT NULL REFERENCES graph_nodes (node_id),
    relationship_type TEXT NOT NULL,
    document JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS rule_results (
    rule_result_id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL REFERENCES transactions (transaction_id),
    rule_id TEXT NOT NULL,
    rule_version TEXT NOT NULL,
    triggered BOOLEAN NOT NULL,
    document JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS risk_assessments (
    risk_assessment_id TEXT PRIMARY KEY,
    target_id TEXT NOT NULL,
    target_type TEXT NOT NULL,
    score INTEGER NOT NULL,
    band TEXT NOT NULL,
    document JSONB NOT NULL,
    UNIQUE (target_id, target_type)
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL REFERENCES transactions (transaction_id),
    status TEXT NOT NULL,
    risk_assessment_id TEXT NOT NULL
        REFERENCES risk_assessments (risk_assessment_id),
    document JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS investigations (
    investigation_id TEXT PRIMARY KEY,
    alert_id TEXT NOT NULL REFERENCES alerts (alert_id),
    transaction_id TEXT NOT NULL REFERENCES transactions (transaction_id),
    status TEXT NOT NULL,
    document JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_packages (
    package_id TEXT PRIMARY KEY,
    investigation_id TEXT NOT NULL
        REFERENCES investigations (investigation_id),
    package_hash TEXT NOT NULL,
    document JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_items (
    evidence_id TEXT PRIMARY KEY,
    package_id TEXT NOT NULL
        REFERENCES evidence_packages (package_id),
    evidence_type TEXT NOT NULL,
    document JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_runs (
    agent_run_id TEXT PRIMARY KEY,
    evidence_package_id TEXT NOT NULL,
    status TEXT NOT NULL,
    model_id TEXT NOT NULL,
    document JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,
    investigation_id TEXT NOT NULL
        REFERENCES investigations (investigation_id),
    status TEXT NOT NULL,
    document JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS decisions (
    decision_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases (case_id),
    document JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
    audit_event_id TEXT PRIMARY KEY,
    seq INTEGER NOT NULL UNIQUE,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    document JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS simulations (
    simulation_id TEXT PRIMARY KEY,
    target_transaction_id TEXT NOT NULL,
    baseline_score INTEGER NOT NULL,
    simulated_score INTEGER NOT NULL,
    document JSONB NOT NULL
);
"""

# Tables in FK-safe load order (parents before children).
LOAD_ORDER = [
    "scenarios",
    "transactions",
    "graph_nodes",
    "events",
    "graph_edges",
    "rule_results",
    "risk_assessments",
    "alerts",
    "investigations",
    "evidence_packages",
    "evidence_items",
    "ai_runs",
    "cases",
    "decisions",
    "audit_events",
    "simulations",
]

# Expected source-state keys per table (for reconciliation inventory).
SOURCE_KEYS = {
    "scenarios": ["scenario_id"],
    "transactions": ["transactions"],
    "graph_nodes": ["nodes"],
    "events": ["events"],
    "graph_edges": ["edges"],
    "rule_results": ["rule_results"],
    "risk_assessments": ["risk"],
    "alerts": ["alerts"],
    "investigations": ["investigations"],
    "evidence_packages": ["evidence_packages"],
    "evidence_items": ["evidence_packages"],
    "ai_runs": ["ai_runs"],
    "cases": ["cases"],
    "decisions": ["decisions"],
    "audit_events": ["audits"],
    "simulations": ["simulations"],
}
