"""AI Agent OS orchestration engine (deterministic, governed).

Central runtime over the existing agent kernel: classifies intent with
transparent rules, selects a runtime manifest, plans bounded tool
steps, executes via propose/execute, and persists a traceable
execution record. Budgets: max 8 tool calls, max depth 2 plans per
turn, per-step error capture with dependent-step cancellation.
Approval-gated manifests pause the execution at APPROVAL_REQUIRED;
resume() continues after the existing approve flow records the run.

Lifecycle: RECEIVED -> AUTHENTICATED -> AUTHORISED -> CLASSIFIED ->
PLANNED -> EXECUTING -> VALIDATING -> COMPLETED | PARTIAL | FAILED |
APPROVAL_REQUIRED. No model is invoked: classification, planning,
and summaries are deterministic over verified tool outputs.
"""
from __future__ import annotations

import time
import uuid
from typing import Any

from app import agents as _agents

STATES = (
    "RECEIVED", "AUTHENTICATED", "AUTHORISED", "CLASSIFIED", "PLANNED",
    "EXECUTING", "VALIDATING", "COMPLETED", "PARTIAL", "FAILED",
    "APPROVAL_REQUIRED",
)

INTENTS = (
    "TRANSACTION_SEARCH", "FRAUD_EXPLAIN", "TRACE", "CASE_SUMMARY",
    "REPORT", "INDUSTRY_INFO", "MONITORING", "RECOVERY", "UNKNOWN",
)

MAX_TOOL_CALLS = 8

# Intent -> (manifest, ordered tool pipeline). Pipelines stay shallow
# (depth <= 2): a second step may only refine the first step's output.
PIPELINES: dict[str, tuple[str, tuple[str, ...]]] = {
    "TRANSACTION_SEARCH": ("txn-intel", ("txn.search",)),
    "FRAUD_EXPLAIN": ("txn-intel", ("signal.search", "typology.match")),
    "TRACE": ("graph-investigator", ("trace.read",)),
    "CASE_SUMMARY": ("case-assistant", ("case.read", "report.build")),
    "REPORT": ("evidence-analyst", ("report.build",)),
    "INDUSTRY_INFO": ("industry-intel", ("industry.coverage",)),
    "MONITORING": ("txn-intel", ("monitoring.status",)),
    "RECOVERY": ("case-assistant", ("recovery.eligibility",)),
}

_INTENT_KEYWORDS = (
    ("RECOVERY", ("recover", "recovery", "recall", "reversal", "refund",
                  "dispute", "chargeback")),
    ("TRACE", ("trace", "tracing", "money flow", "follow the funds",
               "fund movement")),
    ("FRAUD_EXPLAIN", ("fraud", "suspicious", "alert", "signal",
                       "why flagged", "explain")),
    ("TRANSACTION_SEARCH", ("transaction", "transfer", "payment",
                            "find", "search", "show", "list")),
    ("CASE_SUMMARY", ("case", "investigation", "summar")),
    ("REPORT", ("report",)),
    ("INDUSTRY_INFO", ("industry", "sector", "banking", "fintech",
                       "insurance", "telecom")),
    ("MONITORING", ("monitor", "queue", "status", "dashboard")),
)


def _now() -> float:
    return time.time()


def classify(text: str) -> dict[str, Any]:
    """Rule-based intent classification with a transparent rationale."""
    lowered = (text or "").lower()
    for intent, keywords in _INTENT_KEYWORDS:
        hits = [kw for kw in keywords if kw in lowered]
        if hits:
            return {"intent": intent, "rationale":
                    "matched keywords: %s" % ", ".join(hits)}
    return {"intent": "UNKNOWN",
            "rationale": "no intent keywords matched"}


def _execution_id() -> str:
    return "exec_%s" % uuid.uuid4().hex[:12]


def start(store: Any, text: str, subject: dict[str, Any],
          args: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run one orchestrated turn. Returns the execution record."""
    args = dict(args or {})
    record: dict[str, Any] = {
        "execution_id": _execution_id(), "input": (text or "")[:2000],
        "subject": {"user": subject.get("user", ""),
                    "tenant": subject.get("tenant", "")},
        "state": "RECEIVED", "steps": [], "error": "",
        "started_at": _now(), "ended_at": None,
    }
    record["state"] = "AUTHENTICATED"
    record["state"] = "AUTHORISED"
    try:
        classification = classify(text)
    except Exception as exc:  # pragma: no cover - pure function
        return _fail(store, record, "CLASSIFY: %s" % exc)
    record["classification"] = classification
    record["state"] = "CLASSIFIED"
    intent = classification["intent"]
    if intent == "UNKNOWN" or intent not in PIPELINES:
        return _fail(store, record,
                     "INTENT_UNKNOWN: ask for transactions, fraud, "
                     "traces, cases, reports, industry, or monitoring")
    manifest, pipeline = PIPELINES[intent]
    record["manifest"] = manifest
    record["pipeline"] = list(pipeline)
    record["state"] = "PLANNED"
    _continue(store, record, subject, args, pipeline, 0)
    store.agent_exec_save(record)
    return record


def _fail(store: Any, record: dict, error: str) -> dict[str, Any]:
    record["state"] = "FAILED"
    record["error"] = error[:300]
    record["ended_at"] = _now()
    store.agent_exec_save(record)
    return record


def _continue(store: Any, record: dict, subject: dict,
              args: dict, pipeline: tuple[str, ...] | list[str],
              index: int) -> None:
    record["state"] = "EXECUTING"
    calls = len(record["steps"])
    while index < len(pipeline):
        if calls >= MAX_TOOL_CALLS:
            record["state"] = "PARTIAL"
            record["error"] = "BUDGET_EXCEEDED: max %d tool calls" % (
                MAX_TOOL_CALLS)
            break
        tool = pipeline[index]
        step_args = _step_args(tool, args, record)
        started = time.perf_counter()
        try:
            plan, run = _agents.propose(store, record["manifest"],
                                        tool, step_args, subject)
        except ValueError as exc:
            record["steps"].append(
                {"tool": tool, "status": "DENIED",
                 "error": str(exc)[:300],
                 "latency_ms": _elapsed_ms(started)})
            record["state"] = "PARTIAL"
            record["error"] = "STEP_DENIED: %s" % tool
            break
        calls += 1
        if run is None:
            record["steps"].append(
                {"tool": tool, "status": "PENDING_APPROVAL",
                 "plan_id": plan["plan_id"],
                 "latency_ms": _elapsed_ms(started)})
            record["state"] = "APPROVAL_REQUIRED"
            record["pending"] = {"plan_id": plan["plan_id"],
                                 "next_index": index + 1,
                                 "args": args}
            break
        record["steps"].append(
            {"tool": tool, "status": run.get("status", "OK"),
             "output_ref": run.get("run_id"),
             "output": run.get("output", {}),
             "latency_ms": _elapsed_ms(started)})
        if run.get("status") != "OK":
            record["state"] = "PARTIAL"
            record["error"] = "STEP_FAILED: %s" % tool
            break
        index += 1
    else:
        record["state"] = "VALIDATING"
        record["state"] = "COMPLETED"
    record["ended_at"] = _now()


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 2)


def _step_args(tool: str, args: dict,
               record: dict) -> dict[str, Any]:
    """Second-step refinement: feed first-step ids forward when the
    caller did not supply them (depth-2 chaining, explicit)."""
    out = dict(args.get(tool, args))
    if out or not record["steps"]:
        return out
    first = record["steps"][0].get("output", {})
    if tool == "typology.match" and first.get("signals"):
        out = {"typology_id": args.get("typology_id", "T-01")}
    if tool == "report.build":
        if args.get("investigation_id"):
            out = {"report_type": args.get("report_type", "transaction"),
                   "investigation_id": args["investigation_id"]}
    return out


def resume(store: Any, execution_id: str,
           subject: dict[str, Any]) -> dict[str, Any]:
    """Continue an APPROVAL_REQUIRED execution after the kernel
    approve flow recorded the run."""
    record = store.agent_exec_get(execution_id)
    if record is None:
        raise ValueError("EXECUTION_UNKNOWN: %s" % execution_id)
    if record.get("state") != "APPROVAL_REQUIRED":
        raise ValueError("EXECUTION_STATE: %s" % record.get("state"))
    pending = record.get("pending", {})
    run = _find_run(store, pending.get("plan_id", ""))
    if run is None:
        raise ValueError("EXECUTION_NO_RUN: approve the plan first")
    for step in record["steps"]:
        if step.get("plan_id") == pending.get("plan_id"):
            step["status"] = run.get("status", "OK")
            step["output_ref"] = run.get("run_id")
            step["output"] = run.get("output", {})
    record["pending"] = None
    pipeline = record.get("pipeline", [])
    _continue(store, record, subject, pending.get("args", {}),
              pipeline, pending.get("next_index", 0))
    store.agent_exec_save(record)
    return record


def _find_run(store: Any, plan_id: str) -> dict | None:
    for run in store.agent_run_list():
        if isinstance(run, dict) and run.get("plan_id") == plan_id:
            return run
    return None


def metrics(store: Any) -> dict[str, Any]:
    """Execution metrics from stored rows only."""
    rows = store.agent_executions()
    by_state: dict[str, int] = {}
    by_intent: dict[str, int] = {}
    tool_calls = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        state = row.get("state", "?")
        by_state[state] = by_state.get(state, 0) + 1
        intent = (row.get("classification") or {}).get("intent", "?")
        by_intent[intent] = by_intent.get(intent, 0) + 1
        tool_calls += len(row.get("steps", []))
    return {"total": len(rows), "by_state": by_state,
            "by_intent": by_intent, "tool_calls": tool_calls,
            "window": "stored agent executions"}
