"""Bounded what-if simulation. Never mutates baseline state."""
from __future__ import annotations

from datetime import datetime, timezone

from app import rules as rules_mod
from app.models import RuleResult


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run(state: dict, target_transaction_id: str, ignored_edge_ids: list[str],
        assumption: str, trace_id: str) -> dict:
    known = {e["edge_id"] for e in state["edges"]}
    unknown = sorted(set(ignored_edge_ids) - known)
    if unknown:
        raise ValueError(f"UNKNOWN_EDGE: {', '.join(unknown)}")
    if target_transaction_id not in state["risk"]:
        raise ValueError(f"UNKNOWN_TRANSACTION: {target_transaction_id}")
    baseline = state["risk"][target_transaction_id]["network"]
    kept = [e for e in state["edges"] if e["edge_id"] not in set(ignored_edge_ids)]
    results = rules_mod.evaluate(target_transaction_id, state["transactions"],
                                 kept, trace_id)
    simulated = rules_mod.assess(target_transaction_id, "network",
                                 state["transactions"], kept, results, trace_id)
    return {
        "simulation_id": f"sim_{len(state['simulations']) + 1:04d}",
        "scenario_id": state["scenario_id"],
        "target_transaction_id": target_transaction_id,
        "ignored_edge_ids": sorted(ignored_edge_ids),
        "assumption": assumption or "Ignored relationships treated as absent.",
        "baseline_score": baseline["score"],
        "simulated_score": simulated["score"],
        "baseline_band": baseline["band"],
        "simulated_band": simulated["band"],
        "limitations": ("Hypothetical recomputation on a filtered edge set. "
                        "Not a prediction of real-world crime."),
        "created_at": _now(), "trace_id": trace_id,
    }
