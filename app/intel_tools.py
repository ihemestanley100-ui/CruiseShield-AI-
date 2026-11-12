"""Read-only investigation-intel tools for the governed agent kernel.

Handlers follow the kernel (store, args, ctx) contract and reuse the UFI
engines: tracing, typologies, monitoring, industry adapters, reports.
Every handler enforces tenant scope and returns evidence-grounded rows;
nothing here plans, writes, or calls a model (model planning stays
pending per manifest). report.build assembles its bundle from stored
tenant-visible rows only.
"""
from __future__ import annotations

from typing import Any

from app import industry_adapters as _adapters
from app import intel_common as _common
from app import monitoring as _monitoring
from app import parties as _parties
from app import payment_methods as _paymethods
from app import reports as _reports
from app import tenancy as _tenancy
from app import typologies as _typo


def _tenant_id(ctx: Any) -> str:
    return getattr(ctx, "tenant_id", None) or _tenancy.DEFAULT_TENANT


def _visible_txns(store: Any, ctx: Any) -> list[dict[str, Any]]:
    return _tenancy.filter_visible(
        [t for t in store.state.get("transactions", [])
         if isinstance(t, dict)], ctx)


def _signals(store: Any, txns: list[dict]) -> list[dict[str, Any]]:
    from app import detection as det_mod
    result = det_mod.evaluate_all(txns, store.state.get("edges", []))
    return result.get("signals", [])


def txn_search(store: Any, args: dict, ctx: Any) -> dict:
    """Filtered transaction search; account ids masked by default."""
    txns = _visible_txns(store, ctx)
    channel = args.get("channel")
    account = args.get("account")
    text = (args.get("text", "") or "").lower()
    try:
        minimum = int(args.get("min_amount_minor", 0) or 0)
    except (TypeError, ValueError):
        raise ValueError("AGENT_ARGS: bad min_amount_minor")
    try:
        limit = max(1, min(int(args.get("limit", 50)), 200))
    except (TypeError, ValueError):
        raise ValueError("AGENT_ARGS: bad limit")
    rows = []
    for txn in txns:
        if channel and txn.get("channel") != channel:
            continue
        if (txn.get("amount_minor") or 0) < minimum:
            continue
        if args.get("currency") and txn.get("currency") != args[
                "currency"]:
            continue
        if account and account not in (txn.get("sender_account_id"),
                                       txn.get("receiver_account_id")):
            continue
        if text and text not in str(txn).lower():
            continue
        rows.append({
            "transaction_id": txn.get("transaction_id"),
            "channel": txn.get("channel"),
            "amount_minor": txn.get("amount_minor"),
            "currency": txn.get("currency"),
            "occurred_at": txn.get("occurred_at"),
            "sender_masked": _common.mask_ref(
                txn.get("sender_account_id")),
            "receiver_masked": _common.mask_ref(
                txn.get("receiver_account_id"))})
    return {"count": len(rows[:limit]), "total": len(rows),
            "transactions": rows[:limit]}


def case_create(store: Any, args: dict, ctx: Any) -> dict:
    """Open an investigation case (approval-gated manifests only)."""
    from app import cases as cases_mod

    title = (args.get("title", "") or "").strip()
    if not title:
        raise ValueError("AGENT_ARGS: title required")
    try:
        record, _ = cases_mod.create_case(
            store, title, args.get("description", ""),
            args.get("priority", "MEDIUM"), args.get("assignee", ""),
            args.get("due_date", ""), args.get("notes", ""),
            args.get("investigation_id", ""),
            actor_id=getattr(ctx, "actor", "") or "agent",
            tenant=ctx)
    except ValueError as exc:
        raise ValueError("AGENT_ARGS: %s" % exc)
    return {"case_id": record.get("case_id"), "status": record.get(
        "status"), "title": record.get("title")}


def recovery_eligibility(store: Any, args: dict, ctx: Any) -> dict:
    """Assess recovery eligibility for a visible transaction."""
    from app import recovery as recovery_mod
    from app import recovery_caps as caps_mod

    txns = _visible_txns(store, ctx)
    txn = next((t for t in txns
                if t.get("transaction_id") == args.get(
                    "transaction_id")), None)
    if txn is None:
        raise ValueError("AGENT_ARGS: transaction not visible")
    connector_id = args.get("connector_id", "")
    provider_available = any(
        caps_mod.verified(store, connector_id, cap)
        for cap in ("recall", "reversal", "dispute_submission",
                    "refund", "cancellation")) if connector_id else False
    return recovery_mod.assess(
        store, txn, args.get("reason", ""),
        args.get("evidence", []), provider_available,
        args.get("funds_record"))


def recovery_rules(store: Any, args: dict, ctx: Any) -> dict:
    """List or match scheme rules (verification states included)."""
    from app import recovery_rules as rules_mod

    if args.get("rule_id"):
        rule = rules_mod.get_rule(store, args["rule_id"])
        if rule is None:
            return {"found": False, "rule_id": args["rule_id"]}
        return {"found": True, "rule": rule}
    method = args.get("method_id", "")
    reason = args.get("reason", "")
    rules = rules_mod.match(store, method, reason) if method else \
        rules_mod.all_rules(store)
    return {"count": len(rules), "rules": rules}


def recovery_track(store: Any, args: dict, ctx: Any) -> dict:
    """Track one tenant recovery case (status + history)."""
    tenant = _tenant_id(ctx)
    found = next(
        (c for c in store.recovery_cases()
         if c.get("recovery_id") == args.get("recovery_id")
         and c.get("tenant_id", tenant) == tenant), None)
    if found is None:
        return {"found": False, "recovery_id": args.get("recovery_id")}
    return {"found": True, "case": found}


def trace_read(store: Any, args: dict, ctx: Any) -> dict:
    """Read one stored trace (tenant-checked)."""
    tenant = _tenant_id(ctx)
    found = next(
        (t for t in store.traces()
         if t.get("trace_id") == args.get("trace_id")
         and t.get("tenant_id", _tenancy.DEFAULT_TENANT) == tenant),
        None)
    if found is None:
        return {"found": False, "trace_id": args.get("trace_id")}
    return {"found": True, "trace": found}


def typology_match(store: Any, args: dict, ctx: Any) -> dict:
    """Signals evidencing one typology (tenant-visible only)."""
    typo = _typo.get_typology(args.get("typology_id", ""))
    if typo is None:
        raise ValueError("AGENT_ARGS: unknown typology_id")
    try:
        limit = max(1, min(int(args.get("limit", 50)), 200))
    except (TypeError, ValueError):
        raise ValueError("AGENT_ARGS: bad limit")
    matched = _typo.signals_for_typology(
        typo["typology_id"], _signals(store, _visible_txns(store, ctx)))
    return {"typology_id": typo["typology_id"], "label": typo["label"],
            "detection_gap": typo["detection_gap"],
            "matched_count": len(matched),
            "signals": matched[:limit]}


def monitoring_status(store: Any, args: dict, ctx: Any) -> dict:
    """Monitoring posture over tenant rows."""
    tenant = _tenant_id(ctx)
    txns = _visible_txns(store, ctx)
    return _monitoring.status(store, txns, _signals(store, txns), tenant)


def industry_coverage(store: Any, args: dict, ctx: Any) -> dict:
    """Static adapter coverage + evidence readiness for one industry."""
    try:
        coverage = _adapters.coverage(args.get("module_id", ""))
    except ValueError:
        raise ValueError("AGENT_ARGS: unknown module_id")
    ready = _adapters.readiness(args.get("module_id", ""))
    return {"coverage": coverage, "readiness": ready}


def assemble_bundle(store: Any, txns: list[dict], signals: list[dict],
                    txn_id: str | None) -> dict[str, Any]:
    """Public bundle assembler (agent tool + report route share it)."""
    txns_by_id = {t.get("transaction_id"): t for t in txns}
    if txn_id is not None:
        txn = txns_by_id.get(txn_id)
        if txn is None:
            raise ValueError("AGENT_ARGS: transaction not visible")
        main_txns = [txn]
        txn_signals = [s for s in signals
                       if s.get("transaction_id") == txn_id]
    else:
        main_txns = txns[:25]
        txn_signals = signals[:50]
    bundle: dict[str, Any] = {
        "transactions": main_txns,
        "signals": txn_signals,
    }
    if main_txns:
        first = main_txns[0]
        bundle["payment_methods"] = _paymethods.classify(first)
        bundle["parties"] = _parties.extract_parties(first)
    matched_typos = []
    for typo in _typo.list_typologies():
        hits = _typo.signals_for_typology(typo["typology_id"],
                                          txn_signals)
        if hits:
            matched_typos.append({"typology_id": typo["typology_id"],
                                  "label": typo["label"],
                                  "matched_count": len(hits)})
    bundle["typologies"] = sorted(matched_typos,
                                  key=lambda r: -r["matched_count"])[:10]
    if txn_id is not None:
        trace = next((t for t in store.traces()
                      if t.get("origin_transaction") == txn_id), None)
        if trace is not None:
            bundle["trace"] = trace
    return bundle


def report_build(store: Any, args: dict, ctx: Any) -> dict:
    """Deterministic evidence-grounded report over tenant-visible rows."""
    tenant = _tenant_id(ctx)
    inv_id = args.get("investigation_id")
    txn_id = args.get("transaction_id")
    txns = _visible_txns(store, ctx)
    if inv_id is not None:
        invs = _tenancy.filter_visible(
            [i for i in store.state.get("investigations", [])
             if isinstance(i, dict)], ctx)
        inv = next((i for i in invs
                    if i.get("investigation_id") == inv_id), None)
        if inv is None:
            raise ValueError("AGENT_ARGS: investigation not visible")
        txn_id = inv.get("transaction_id")
    signals = _signals(store, txns)
    bundle = assemble_bundle(store, txns, signals, txn_id)
    try:
        report = _reports.build(args.get("report_type", ""), bundle,
                                inv_id)
    except ValueError:
        raise ValueError("AGENT_ARGS: unknown report_type")
    report["tenant_scope"] = tenant
    return report
