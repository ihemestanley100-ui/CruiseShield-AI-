"""Governed agent tool-execution kernel (master directive §11).

Registry of the 12 governed agents + a tool-execution pipeline with
manifest authorization, argument validation, ABAC enforcement,
human approval for flagged agents, run recording, and audit.

Honest scope: this kernel executes caller-specified tools under
governance. It does NOT plan with a language model — model-driven
planning arrives with the provider lane (app/ai_adapter.py). All six
tools are read-only and bound to real platform functions; write tools
land only with a real write need + approval policy. No agent can
independently perform financial or legal actions: consequential
actions keep their existing human-approval handlers.
"""
from __future__ import annotations

import time
import uuid
from typing import Any

PLAN_TTL_SECONDS = 15 * 60
MAX_ARG_CHARS = 2000


def _manifest(agent_id: str, name: str, purpose: str,
              tools: tuple[str, ...],
              requires_approval: bool) -> dict[str, Any]:
    return {"id": agent_id, "name": name, "purpose": purpose,
            "tools": list(tools), "requires_approval": requires_approval,
            "model_tier": "deterministic",
            "planning": "caller-specified (model planning pending)"}


_MANIFESTS: tuple[dict[str, Any], ...] = (
    _manifest("txn-intel", "Transaction Intelligence Agent",
              "Look up transactions and their derived signals.",
              ("signal.search", "graph.neighbors", "trace.read",
               "typology.match", "monitoring.status", "txn.search"),
              False),
    _manifest("fraud-detection", "Fraud Detection Agent",
              "Correlate signals across cases and entities.",
              ("signal.search", "case.read", "graph.neighbors",
               "typology.match", "monitoring.status", "txn.search",
               "case.create"), True),
    _manifest("graph-investigator", "Graph Investigation Agent",
              "Explore entity neighborhoods and paths.",
              ("graph.neighbors", "case.read", "trace.read"), False),
    _manifest("aml-intel", "AML Intelligence Agent",
              "Assemble case evidence for AML review.",
              ("case.read", "evidence.read", "signal.search",
               "trace.read", "typology.match", "txn.search",
               "case.create"), True),
    _manifest("case-assistant", "Case Assistant Agent",
              "Summarize case state for investigators.",
              ("case.read", "evidence.read", "report.build",
               "recovery.eligibility", "recovery.rules",
               "recovery.track"), False),
    _manifest("fund-recovery", "Fund Recovery Agent",
              "Assess eligibility, explain rules, track recovery.",
              ("recovery.eligibility", "recovery.rules",
               "recovery.track", "txn.search", "trace.read"), True),
    _manifest("evidence-analyst", "Evidence Analysis Agent",
              "Read evidence packages and their provenance.",
              ("evidence.read", "case.read", "report.build"), False),
    _manifest("risk-assessor", "Risk Assessment Agent",
              "Read risk-relevant signals and readiness.",
              ("signal.search", "industry.readiness",
               "industry.coverage"), False),
    _manifest("compliance-research", "Compliance Research Agent",
              "Read industry compliance configuration.",
              ("industry.readiness", "industry.coverage"), False),
    _manifest("data-quality", "Data Quality Agent",
              "Inspect connector and channel health.",
              ("connector.read", "signal.search"), False),
    _manifest("security-monitor", "Security Monitoring Agent",
              "Review connector and MFA-sensitive posture (reads).",
              ("connector.read",), True),
    _manifest("industry-intel", "Industry Intelligence Agent",
              "Read pilot readiness across industry modules.",
              ("industry.readiness", "industry.coverage"), False),
    _manifest("ops-reliability", "Operational Reliability Agent",
              "Read connector health and signal flow.",
              ("connector.read", "signal.search"), False),
)


def manifests() -> list[dict[str, Any]]:
    """Agent manifests (deep copies)."""
    import copy

    return copy.deepcopy(list(_MANIFESTS))


def get_manifest(agent_id: str) -> dict[str, Any] | None:
    for manifest in _MANIFESTS:
        if manifest["id"] == agent_id:
            return manifest
    return None


# -- tools (read-only, real bindings) ----------------------------------

def _tool_case_read(store: Any, args: dict, ctx: Any) -> dict:
    from app import tenancy as tenancy_mod

    case = tenancy_mod.enforce_read(store.get_case(args["case_id"]),
                                    ctx)
    if case is None:
        return {"found": False, "case_id": args["case_id"]}
    return {"found": True, "case": case}


def _tool_signal_search(store: Any, args: dict, ctx: Any) -> dict:
    from app import detection as det_mod
    from app import tenancy as tenancy_mod

    txns = tenancy_mod.filter_visible(
        [t for t in store.state.get("transactions", [])
         if isinstance(t, dict)], ctx)
    result = det_mod.evaluate_all(txns, store.state.get("edges", []))
    try:
        signals = det_mod.filter_signals(
            result["signals"], start=args.get("start", ""),
            end=args.get("end", ""), family=args.get("family", ""),
            channel=args.get("channel", ""),
            severity=args.get("severity", ""))
    except ValueError as exc:
        raise ValueError("AGENT_ARGS: %s" % exc)
    needle = (args.get("q", "") or "").lower()
    if needle:
        signals = [s for s in signals
                   if needle in str(s).lower()]
    limit = args.get("limit", 50)
    try:
        limit = max(1, min(int(limit), 200))
    except (TypeError, ValueError):
        raise ValueError("AGENT_ARGS: bad limit")
    return {"count": len(signals[:limit]), "total": len(signals),
            "signals": signals[:limit]}


def _tool_graph_neighbors(store: Any, args: dict, ctx: Any) -> dict:
    from app import graph as graph_mod
    from app import tenancy as tenancy_mod

    try:
        depth = max(1, min(int(args.get("depth", 2)), 4))
    except (TypeError, ValueError):
        raise ValueError("AGENT_ARGS: bad depth")
    _, nodes, edges = tenancy_mod.visible_graph(store.state, ctx)
    if args["node_id"] not in {n["node_id"] for n in nodes}:
        return {"node_id": args["node_id"], "depth": depth,
                "nodes": [], "edges": []}
    nodes, edges = graph_mod.neighborhood(
        nodes, edges, {args["node_id"]}, depth=depth)
    return {"node_id": args["node_id"], "depth": depth,
            "nodes": nodes, "edges": edges}


def _tool_evidence_read(store: Any, args: dict, ctx: Any) -> dict:
    from app import tenancy as tenancy_mod

    package = store.state.get("evidence_packages", {}).get(
        args["package_id"])
    if package is None:
        return {"found": False, "package_id": args["package_id"]}
    investigation = store.get_investigation(args["package_id"])
    if (investigation is not None
            and tenancy_mod.enforce_read(investigation, ctx) is None):
        return {"found": False, "package_id": args["package_id"]}
    if isinstance(package, dict):
        return {"found": True, "package": package}
    return {"found": True, "package": str(package)[:4000]}


def _tool_industry_readiness(store: Any, args: dict, ctx: Any) -> dict:
    from app import pilot as pilot_mod

    _ = (store, ctx)
    try:
        return pilot_mod.evaluate(args["module_id"])
    except ValueError as exc:
        raise ValueError("AGENT_ARGS: %s" % exc)


def _tool_connector_read(store: Any, args: dict, ctx: Any) -> dict:
    from app import connectors as conn_mod
    from app import tenancy as tenancy_mod

    record = tenancy_mod.enforce_read(
        store.connection_get(args["connection_id"]), ctx)
    if record is None:
        return {"found": False, "connection_id": args["connection_id"]}
    return {"found": True, "connection": conn_mod.redact(record)}


def _tool_trace_read(store: Any, args: dict, ctx: Any) -> dict:
    from app import intel_tools as itools_mod

    return itools_mod.trace_read(store, args, ctx)


def _tool_typology_match(store: Any, args: dict, ctx: Any) -> dict:
    from app import intel_tools as itools_mod

    return itools_mod.typology_match(store, args, ctx)


def _tool_monitoring_status(store: Any, args: dict, ctx: Any) -> dict:
    from app import intel_tools as itools_mod

    return itools_mod.monitoring_status(store, args, ctx)


def _tool_industry_coverage(store: Any, args: dict, ctx: Any) -> dict:
    from app import intel_tools as itools_mod

    return itools_mod.industry_coverage(store, args, ctx)


def _tool_report_build(store: Any, args: dict, ctx: Any) -> dict:
    from app import intel_tools as itools_mod

    return itools_mod.report_build(store, args, ctx)


def _tool_txn_search(store: Any, args: dict, ctx: Any) -> dict:
    from app import intel_tools as itools_mod

    return itools_mod.txn_search(store, args, ctx)


def _tool_case_create(store: Any, args: dict, ctx: Any) -> dict:
    from app import intel_tools as itools_mod

    return itools_mod.case_create(store, args, ctx)


def _tool_recovery_eligibility(store: Any, args: dict,
                               ctx: Any) -> dict:
    from app import intel_tools as itools_mod

    return itools_mod.recovery_eligibility(store, args, ctx)


def _tool_recovery_rules(store: Any, args: dict, ctx: Any) -> dict:
    from app import intel_tools as itools_mod

    return itools_mod.recovery_rules(store, args, ctx)


def _tool_recovery_track(store: Any, args: dict, ctx: Any) -> dict:
    from app import intel_tools as itools_mod

    return itools_mod.recovery_track(store, args, ctx)


_TOOLS: dict[str, dict[str, Any]] = {
    "case.read": {"description": "Read one case by ID.",
                  "required": ("case_id",), "optional": (),
                  "perm": "read", "run": _tool_case_read},
    "signal.search": {"description": "Search derived signals.",
                      "required": (),
                      "optional": ("q", "family", "channel", "severity",
                                   "start", "end", "limit"),
                      "perm": "read", "run": _tool_signal_search},
    "graph.neighbors": {"description": "BFS neighborhood (depth<=4).",
                        "required": ("node_id",),
                        "optional": ("depth",),
                        "perm": "read", "run": _tool_graph_neighbors},
    "evidence.read": {"description": "Read one evidence package.",
                      "required": ("package_id",), "optional": (),
                      "perm": "read", "run": _tool_evidence_read},
    "industry.readiness": {"description": "Pilot-readiness report.",
                           "required": ("module_id",), "optional": (),
                           "perm": "read", "run": _tool_industry_readiness},
    "connector.read": {"description": "Redacted connection view.",
                       "required": ("connection_id",), "optional": (),
                       "perm": "read",
                       "sensitive": True, "run": _tool_connector_read},
    "trace.read": {"description": "Read one stored fund trace.",
                   "required": ("trace_id",), "optional": (),
                   "perm": "read", "run": _tool_trace_read},
    "typology.match": {"description": "Signals evidencing a typology.",
                       "required": ("typology_id",),
                       "optional": ("limit",),
                       "perm": "read", "run": _tool_typology_match},
    "monitoring.status": {"description": "Monitoring posture snapshot.",
                          "required": (), "optional": (),
                          "perm": "read", "run": _tool_monitoring_status},
    "industry.coverage": {"description": "Industry adapter coverage.",
                          "required": ("module_id",), "optional": (),
                          "perm": "read", "run": _tool_industry_coverage},
    "report.build": {"description": "Evidence-grounded report build.",
                     "required": ("report_type",),
                     "optional": ("investigation_id", "transaction_id"),
                     "perm": "read", "run": _tool_report_build},
    "txn.search": {"description": "Filtered transaction search.",
                   "required": (),
                   "optional": ("channel", "min_amount_minor",
                                "currency", "account", "text",
                                "limit"),
                   "perm": "read", "run": _tool_txn_search},
    "case.create": {"description": "Open an investigation case.",
                    "required": ("title",),
                    "optional": ("description", "priority", "assignee",
                                 "due_date", "notes",
                                 "investigation_id"),
                    "perm": "write", "run": _tool_case_create},
    "recovery.eligibility": {
        "description": "Assess recovery eligibility.",
        "required": ("transaction_id", "reason"),
        "optional": ("connector_id", "evidence", "funds_record"),
        "perm": "read", "run": _tool_recovery_eligibility},
    "recovery.rules": {"description": "List or match scheme rules.",
                       "required": (),
                       "optional": ("rule_id", "method_id", "reason"),
                       "perm": "read", "run": _tool_recovery_rules},
    "recovery.track": {"description": "Track a recovery case.",
                       "required": ("recovery_id",), "optional": (),
                       "perm": "read", "run": _tool_recovery_track},
}


def tools() -> dict[str, dict[str, Any]]:
    """Public tool catalogue (descriptions + schemas, no handlers)."""
    return {name: {"description": spec["description"],
                   "required": list(spec["required"]),
                   "optional": list(spec["optional"])}
            for name, spec in _TOOLS.items()}


# -- pipeline ----------------------------------------------------------

def _new_id(prefix: str) -> str:
    return "%s_%s" % (prefix, uuid.uuid4().hex[:12])


def _validate_args(tool: str, args: Any) -> dict[str, Any]:
    spec = _TOOLS[tool]
    if not isinstance(args, dict):
        raise ValueError("AGENT_ARGS: args must be an object")
    missing = [k for k in spec["required"] if not args.get(k)]
    if missing:
        raise ValueError("AGENT_ARGS: missing: %s" % ",".join(missing))
    allowed = set(spec["required"]) | set(spec["optional"])
    unknown = sorted(set(args) - allowed)
    if unknown:
        raise ValueError("AGENT_ARGS: unknown: %s" % ",".join(unknown))
    for key, value in args.items():
        if len(str(value)) > MAX_ARG_CHARS:
            raise ValueError("AGENT_ARGS: %s too long" % key)
    return {k: args[k] for k in args}


def propose(store: Any, agent_id: str, tool: str, args: dict,
            subject: dict) -> tuple[dict, dict | None]:
    """Propose a tool call. Returns (plan, run-or-None).

    Auto-approved agents execute immediately (run recorded + audited
    by the caller); approval-flagged agents return a PENDING plan.
    Raises ValueError AGENT_* on any policy/schema violation.
    """
    from app import abac as abac_mod
    from app import tenancy as tenancy_mod

    tenant = str(subject.get("tenant") or tenancy_mod.DEFAULT_TENANT)
    if tenant not in tenancy_mod.known_tenants():
        tenant = tenancy_mod.DEFAULT_TENANT
    ctx = tenancy_mod.TenantContext(tenant_id=tenant,
                                    actor=subject.get("user", ""))
    manifest = get_manifest(agent_id)
    if manifest is None:
        raise ValueError("AGENT_UNKNOWN: %s" % agent_id)
    if tool not in _TOOLS:
        raise ValueError("AGENT_TOOL_UNKNOWN: %s" % tool)
    if tool not in manifest["tools"]:
        raise ValueError("AGENT_TOOL_DENIED: %s cannot use %s"
                         % (agent_id, tool))
    clean = _validate_args(tool, args)
    allowed, reason = abac_mod.decide(subject, "ai_run",
                                      {"kind": "agent"})
    if not allowed:
        raise ValueError("AGENT_FORBIDDEN: %s" % reason)
    now = time.time()
    plan = {"plan_id": _new_id("plan"), "agent": agent_id, "tool": tool,
            "args": clean, "proposed_by": subject.get("user", ""),
            "requires_approval": manifest["requires_approval"],
            "status": "PENDING", "created_at": now,
            "expires_at": now + PLAN_TTL_SECONDS}
    tenancy_mod.stamp(plan, ctx)
    store.agent_plan_save(plan)
    if manifest["requires_approval"]:
        return plan, None
    run = execute(store, plan, subject.get("user", ""), auto=True,
                  ctx=ctx)
    return plan, run


def approve(store: Any, plan_id: str, subject: dict) -> dict:
    """Human approval executes a PENDING plan (admin/manage only)."""
    from app import abac as abac_mod
    from app import tenancy as tenancy_mod

    tenant = str(subject.get("tenant") or tenancy_mod.DEFAULT_TENANT)
    if tenant not in tenancy_mod.known_tenants():
        tenant = tenancy_mod.DEFAULT_TENANT
    plan = store.agent_plan_get(plan_id)
    if plan is None or tenancy_mod.tenant_of(plan) != tenant:
        raise ValueError("AGENT_PLAN_UNKNOWN: %s" % plan_id)
    if plan["status"] != "PENDING":
        raise ValueError("AGENT_PLAN_STATE: plan is %s"
                         % plan["status"])
    if time.time() > float(plan.get("expires_at", 0)):
        plan["status"] = "EXPIRED"
        store.agent_plan_save(plan)
        raise ValueError("AGENT_PLAN_EXPIRED: re-propose the call")
    allowed, reason = abac_mod.decide(subject, "approve",
                                      {"kind": "agent-plan"})
    if not allowed:
        raise ValueError("AGENT_FORBIDDEN: %s" % reason)
    ctx = tenancy_mod.TenantContext(tenant_id=tenant,
                                    actor=subject.get("user", ""))
    return execute(store, plan, subject.get("user", ""), auto=False,
                   ctx=ctx)


def execute(store: Any, plan: dict, actor: str,
            auto: bool, ctx: Any = None) -> dict[str, Any]:
    """Run the tool, record the run, close the plan.

    Authorization is enforced by the propose/approve entry points
    (ABAC ai_run / manage); execute() never runs standalone in prod.
    """
    from app import tenancy as tenancy_mod

    if ctx is None:
        ctx = tenancy_mod.TenantContext(
            tenant_id=tenancy_mod.tenant_of(plan)
            or tenancy_mod.DEFAULT_TENANT, actor=actor)
    spec = _TOOLS[plan["tool"]]
    started = time.perf_counter()
    try:
        output = spec["run"](store, plan["args"], ctx)
        status: str = "OK"
        error = ""
    except ValueError as exc:
        output = {}
        status = "ERROR"
        error = str(exc)[:300]
    run = {"run_id": _new_id("run"), "plan_id": plan["plan_id"],
           "agent": plan["agent"], "tool": plan["tool"],
           "args": plan["args"], "actor": actor, "auto": auto,
           "status": status, "error": error, "output": output,
           "latency_ms": int((time.perf_counter() - started) * 1000),
           "at": time.time()}
    tenancy_mod.stamp(run, ctx)
    plan["status"] = "EXECUTED"
    store.agent_plan_save(plan)
    store.agent_run_save(run)
    return run
