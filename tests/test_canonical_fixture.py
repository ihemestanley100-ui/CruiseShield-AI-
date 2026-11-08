"""F-CI-01: canonical fixture determinism, anchoring, and content shape.

Guards the independent migration-test fixture WITHOUT PostgreSQL:
regeneration must be byte-exact (no silent drift), the committed bytes
must match the hardcoded anchors, and the JSON content must satisfy
every non-PG assertion the migration tests make (counts, risk scores,
audit sequence, evidence items). PG-load behavior itself is covered by
the scratch-gated migration tests wherever SCRATCH_DATABASE_URL exists.
"""
import hashlib
import json

from fixtures.canonical_seed import (
    FIXTURE_HASH,
    FIXTURE_SIZE,
    build_canonical_bytes,
    fixture_bytes,
)


def test_regeneration_is_byte_exact():
    assert build_canonical_bytes() == build_canonical_bytes()


def test_committed_fixture_matches_anchors():
    raw = fixture_bytes()
    assert len(raw) == FIXTURE_SIZE
    assert hashlib.sha256(raw).hexdigest().upper() == FIXTURE_HASH


def test_committed_fixture_matches_generator():
    assert fixture_bytes() == build_canonical_bytes()


def test_fixture_content_shape():
    state = json.loads(fixture_bytes().decode("utf-8"))
    assert len(state["transactions"]) == 11
    assert len(state["events"]) == 11
    assert len(state["nodes"]) == 22
    assert len(state["edges"]) == 30
    assert sum(len(v) for v in state["rule_results"].values()) == 8
    assert len(state["alerts"]) == 1
    assert len(state["investigations"]) == 1
    assert len(state["cases"]) == 1
    assert len(state["decisions"]) == 0
    assert len(state["ai_runs"]) == 2
    assert len(state["simulations"]) == 1
    assert len(state["audits"]) == 5
    assert state["audit_counter"] == 5
    assert state["risk"]["txn_84721"]["transaction"]["score"] == 35
    assert state["risk"]["txn_84721"]["network"]["score"] == 84
    assert [a["audit_event_id"] for a in state["audits"]] == [
        "audit_%04d" % i for i in (1, 2, 3, 4, 5)]
    assert len(state["evidence_packages"]["inv_84721"]["items"]) == 39
    assert state["cases"][0]["case_id"] == "case_84721"
    assert state["cases"][0]["status"] == "NEW"
    assert state["transactions"][0]["transaction_id"] == "txn_84721"
