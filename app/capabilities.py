"""Product-intelligence capability registry (master directive §14).

Each A–O capability maps to its canonical implementation (reuse, never
duplication) with an honest status: HAVE (implemented + tested),
PARTIAL (some implementation, stated gap), MISSING (no implementation,
next action). verify() resolves every HAVE/PARTIAL reference against
the live codebase — a claimed capability whose code is absent fails
the check instead of passing on documentation.
"""
from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

# id, name, status, implements refs, evidence refs, gap, next action.
# Ref grammar: "path/to/file.py" or "path/to/file.py:Symbol.attr".
_CAPABILITIES: tuple[tuple[str, ...], ...] = (
    ("A", "Universal Financial Crime Immune System", "PARTIAL",
     "app/seed.py app/rules.py app/cases.py app/detection.py",
     "tests/test_api_flow.py",
     "pipeline operational; continuous learning loop is procedural",
     "automate detection-review feedback (L14 cycle §15)"),
    ("B", "Financial Crime Knowledge Graph", "PARTIAL",
     "app/graph.py app/graph_intel.py",
     "tests/test_graph_rules_risk.py",
     "unified + provenance; no temporal snapshots/versioning",
     "add graph snapshots + time-travel queries"),
    ("C", "Universal Signal Intelligence Fabric", "HAVE",
     "app/detection.py app/channels.py",
     "tests/test_detection.py",
     "", ""),
    ("D", "Cross-Industry Risk Translation Engine", "MISSING",
     "", "",
     "no cross-sector pattern-mapping engine exists",
     "design translation framework on pilot evaluator evidence"),
    ("E", "Financial Crime Attack-Path Reconstruction", "PARTIAL",
     "app/replay.py app/cases.py",
     "tests/test_api_flow.py",
     "replay + case history exist; no automated path reconstruction",
     "build evidence-linked path builder on graph.neighborhood"),
    ("F", "Early Warning Intelligence", "PARTIAL",
     "app/rules.py", "tests/test_api_flow.py",
     "alerts + velocity detection; no escalating-risk tracker",
     "add threshold-breach trending over signal time-series"),
    ("G", "Universal Evidence Chain", "HAVE",
     "app/evidence.py app/audit_chain.py",
     "tests/test_evidence.py", "", ""),
    ("H", "Detection Explainability Engine", "HAVE",
     "app/models.py:RuleResult app/rules.py",
     "tests/test_detection.py", "", ""),
    ("I", "Investigation Copilot", "PARTIAL",
     "app/agents.py", "tests/test_agents.py",
     "governed read tools; no model synthesis",
     "add model lane via provider gateway (D-016)"),
    ("J", "Financial Crime Resilience Simulator", "HAVE",
     "app/simulate.py", "tests/test_api_flow.py", "", ""),
    ("K", "Detection Effectiveness Intelligence", "HAVE",
     "app/main.py", "tests/test_detection.py", "", ""),
    ("L", "Universal Industry Adaptation Engine", "HAVE",
     "app/industries.py app/pilot.py",
     "tests/test_pilot.py", "", ""),
    ("M", "Continuous Control Assurance Engine", "HAVE",
     "app/capabilities.py scripts/zero_gap_matrix.py",
     "tests/test_capabilities.py", "", ""),
    ("N", "Data Provenance and Trust Engine", "HAVE",
     "app/graph.py app/evidence.py app/store.py",
     "tests/test_graph_rules_risk.py", "", ""),
    ("O", "Universal Threat Evolution Engine", "PARTIAL",
     "app/rules.py:SCORE_VERSION", "tests/test_graph_rules_risk.py",
     "rule/model versioning; no drift detection",
     "add detection-yield trending + drift alerts"),
)


def registry() -> list[dict[str, Any]]:
    """All 15 capability entries as dicts."""
    return [{"id": cid, "name": name, "status": status,
             "implements": impl.split(), "evidence": evid.split(),
             "gap": gap, "next": nxt}
            for cid, name, status, impl, evid, gap, nxt in _CAPABILITIES]


def _resolve(ref: str) -> tuple[bool, str]:
    path, _, symbol = ref.partition(":")
    full = ROOT / path
    if not full.is_file():
        return False, "missing file %s" % path
    if not symbol:
        return True, ""
    module = path[:-3].replace("/", ".") if path.endswith(".py") else ""
    try:
        obj: Any = importlib.import_module(module)
        for attr in symbol.split("."):
            obj = getattr(obj, attr)
    except (ImportError, AttributeError) as exc:
        return False, "%s: %s" % (ref, exc)
    return True, ""


def verify() -> dict[str, Any]:
    """Resolve every HAVE/PARTIAL reference; report failures honestly."""
    failures: list[str] = []
    counts: dict[str, int] = {"HAVE": 0, "PARTIAL": 0, "MISSING": 0}
    for entry in registry():
        counts[entry["status"]] = counts.get(entry["status"], 0) + 1
        if entry["status"] == "MISSING":
            if not entry["next"]:
                failures.append("%s: MISSING without next action"
                                % entry["id"])
            continue
        for ref in entry["implements"] + entry["evidence"]:
            ok, problem = _resolve(ref)
            if not ok:
                failures.append(problem)
        if entry["status"] == "PARTIAL" and not entry["gap"]:
            failures.append("%s: PARTIAL without stated gap"
                            % entry["id"])
    return {"counts": counts, "failures": failures,
            "verified": not failures}
