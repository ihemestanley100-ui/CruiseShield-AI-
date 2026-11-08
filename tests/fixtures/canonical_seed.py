"""Deterministic canonical migration-test fixture (F-CI-01).

The migration/parity/hardening tests must NEVER depend on the live,
gitignored ``data/state.json``: CI checkouts do not contain it, so the
tests failed there while passing on developer machines.

Recorded source-integrity discrepancy (preserved, not erased):
  historical live anchor ... 101417 bytes / BA1D4DB4...3790FE
  CI-observed value ........ 70567 bytes (fresh import-time seed, LF)
  root cause ............... ``app.main`` import seeds ``STATE_PATH`` when
                             the file is absent; the fixed live anchor
                             cannot hold where the live file never existed.

This module generates the INDEPENDENT canonical fixture from the
deterministic ``scn_primary`` seed plus fixed synthetic records. No live
file bytes are used. Output is byte-identical on every platform
(explicit LF serialization; volatile ids/timestamps normalized), so
FIXTURE_SIZE/FIXTURE_HASH are valid anchors everywhere.

Change control: ``canonical-state.json`` (committed, gitattributes-pinned
binary) may only change together with this generator; the regeneration
test fails otherwise. Never hand-edit the committed bytes.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

FIXTURE_PATH = Path(__file__).with_name("canonical-state.json")

# Anchors for the COMMITTED fixture bytes (bootstrapped once from the
# generator output, verified on every run by the regeneration test).
FIXTURE_SIZE = 75242
FIXTURE_HASH = ("36D55C94B2CB9030C5F6A78F92EBB2C7193F4CE18D5E2FD"
                "972168D1BF3F41AF9")

FIXED_TS = "2026-01-01T00:00:00Z"
FIXED_RUN = "run_canonical_fixture_001"
FIXED_TRACE = "trace_canonical_fixture_001"

_VOLATILE_TS = {"created_at", "updated_at", "timestamp", "started_at",
                "completed_at", "computed_at"}


def _normalize(obj):
    """Fix run/trace ids and timestamps recursively (in place)."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "run_id":
                obj[key] = FIXED_RUN
            elif key in ("trace_id", "request_id"):
                obj[key] = FIXED_TRACE
            elif key in _VOLATILE_TS:
                obj[key] = FIXED_TS
            else:
                _normalize(value)
    elif isinstance(obj, list):
        for item in obj:
            _normalize(item)
    return obj


def _fixture_ai_runs(package_id: str, evidence_ids: list[str]) -> list[dict]:
    base = {
        "evidence_package_id": package_id,
        "evidence_ids_sent": evidence_ids[:2],
        "status": "COMPLETED",
        "model_id": "muse-spark-1.3",
        "provider": "meta",
        "prompt_version": "risk-explain-v1",
        "started_at": FIXED_TS,
        "completed_at": FIXED_TS,
        "latency_ms": 1234,
        "finish_reason": "stop",
        "error_code": None,
        "usage": {"input_tokens": 1500, "output_tokens": 800,
                  "total_tokens": 2300},
        "result": {"summary": "Canonical fixture analysis (synthetic).",
                   "risk_band": "HIGH", "confidence": "high"},
        "structured_output": {
            "findings": ["Deterministic rule hits explain the score."],
            "recommended_action": "Monitor"},
        "diagnostics": {"retries": 0, "timeout_seconds": 30},
        "response_reference": "fixture-response",
        "followup_question": "",
        "schema_validation_status": "PASS",
        "evidence_reference_validation_status": "PASS",
        "synthetic_data_flag": True,
        "trace_id": FIXED_TRACE,
    }
    runs = []
    for num in (1, 2):
        run = dict(base)
        run["agent_run_id"] = f"agent_run_canon_{num:03d}"
        run["request_id"] = f"req_canon_{num:03d}"
        run["response_reference"] = f"fixture-response-{num:03d}"
        runs.append(run)
    return runs


def _fixture_simulation(first_edge_id: str) -> dict:
    return {
        "simulation_id": "sim_canon_001",
        "target_transaction_id": "txn_84721",
        "scenario_id": "scn_primary",
        "baseline_score": 84,
        "baseline_band": "HIGH",
        "simulated_score": 10,
        "simulated_band": "LOW",
        "ignored_edge_ids": [first_edge_id],
        "assumption": "Canonical fixture: ring edge removed (synthetic).",
        "limitations": "Synthetic simulation, not evidence of intent.",
        "created_at": FIXED_TS,
        "trace_id": FIXED_TRACE,
    }


def _fixture_audits() -> list[dict]:
    specs = [
        ("audit_0003", "ai.run.recorded", "ai_run", "agent_run_canon_001"),
        ("audit_0004", "ai.run.recorded", "ai_run", "agent_run_canon_002"),
        ("audit_0005", "simulation.recorded", "simulation", "sim_canon_001"),
    ]
    return [{
        "audit_event_id": event_id,
        "actor_type": "system",
        "actor_id": "canonical-fixture",
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "previous_state_reference": "",
        "new_state_reference": "RECORDED",
        "reason": "Canonical fixture record (synthetic).",
        "timestamp": FIXED_TS,
        "trace_id": FIXED_TRACE,
        "request_id": FIXED_TRACE,
    } for event_id, action, target_type, target_id in specs]


def _recompute_package_hashes(state: dict) -> None:
    """Re-hash evidence packages after normalization (loader semantics)."""
    for package in state["evidence_packages"].values():
        canonical = json.dumps(
            sorted(package["items"], key=lambda i: i["evidence_id"]),
            sort_keys=True, separators=(",", ":"))
        package["package_hash"] = hashlib.sha256(
            canonical.encode("utf-8")).hexdigest()


def build_canonical_bytes() -> bytes:
    """Generate the canonical fixture bytes (deterministic, LF)."""
    from app.store import Store

    with tempfile.TemporaryDirectory(prefix="cs-canon-") as tmp:
        store = Store(Path(tmp) / "seed.json")
        store.reset("scn_primary")
        state = store.state
    _normalize(state)
    # The scenario.reset audit records the uuid run_id as its
    # new_state_reference; pin it to the fixed run id.
    for entry in state["audits"]:
        if entry.get("action") == "scenario.reset":
            entry["new_state_reference"] = FIXED_RUN
    package_id = next(iter(state["evidence_packages"]))
    items = state["evidence_packages"][package_id]["items"]
    evidence_ids = [i["evidence_id"] for i in items]
    state["ai_runs"] = _fixture_ai_runs(package_id, evidence_ids)
    state["simulations"] = [
        _fixture_simulation(state["edges"][0]["edge_id"])]
    state["audits"].extend(_fixture_audits())
    state["audit_counter"] = len(state["audits"])
    _recompute_package_hashes(state)
    # Explicit LF: identical bytes on Windows and Linux (Store._save
    # layout is json.dumps(..., indent=2) with no trailing newline).
    return json.dumps(state, indent=2).encode("utf-8")


def fixture_bytes() -> bytes:
    """Read the COMMITTED canonical fixture bytes."""
    return FIXTURE_PATH.read_bytes()
