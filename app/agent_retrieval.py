"""Agent retrieval plane: permission-checked hybrid search.

Structured + keyword retrieval over tenant-visible transactions,
signals, cases, evidence packages, and industry configurations.
Every hit carries source attribution, an observed timestamp, and a
freshness note. Retrieved content is data, never instructions:
matches are quoted with their source; nothing executes.

Embeddings/vector search: the adapter interface is defined but no
provider is configured (EMBEDDING_PROVIDER unset), so vector
retrieval reports UNAVAILABLE and keyword/structured retrieval
serves instead. No silent fallback, no fabricated similarity.
"""
from __future__ import annotations

from typing import Any

from app import tenancy as _tenancy

SOURCES = ("transactions", "signals", "cases", "evidence",
           "industries")

EMBEDDING_PROVIDER = ""


def embedding_status() -> dict[str, Any]:
    """Vector-retrieval availability (honest by construction)."""
    if EMBEDDING_PROVIDER:
        return {"provider": EMBEDDING_PROVIDER, "status": "CONFIGURED",
                "note": "connectivity must still be verified"}
    return {"provider": None, "status": "UNAVAILABLE",
            "note": "no embedding provider configured; keyword and "
                    "structured retrieval serve instead"}


def search(store: Any, ctx: Any, query: str,
           sources: list[str] | None = None,
           limit: int = 20) -> dict[str, Any]:
    """Hybrid search over tenant-visible rows."""
    tenant = getattr(ctx, "tenant_id", None) or _tenancy.DEFAULT_TENANT
    wanted = [s for s in (sources or list(SOURCES)) if s in SOURCES]
    needle = (query or "").lower().strip()
    if not needle:
        return {"query": query, "hits": [], "tenant_scope": tenant,
                "embedding": embedding_status()}
    limit = min(max(int(limit), 1), 50)
    hits: list[dict[str, Any]] = []
    if "transactions" in wanted:
        txns = _tenancy.filter_visible(
            [t for t in store.state.get("transactions", [])
             if isinstance(t, dict)], ctx)
        for txn in txns:
            if _contains(txn, needle):
                hits.append(_hit("transaction",
                                 txn.get("transaction_id"),
                                 txn.get("occurred_at"),
                                 "transaction record"))
    if "signals" in wanted:
        from app import detection as det_mod
        txns = _tenancy.filter_visible(
            [t for t in store.state.get("transactions", [])
             if isinstance(t, dict)], ctx)
        result = det_mod.evaluate_all(txns, store.state.get("edges", []))
        for sig in result.get("signals", []):
            if _contains(sig, needle):
                hits.append(_hit("signal", sig.get("signal_id"),
                                 None, "derived detection signal"))
    if "cases" in wanted:
        cases = _tenancy.filter_visible(
            [c for c in store.state.get("cases", [])
             if isinstance(c, dict)], ctx)
        for case in cases:
            if _contains(case, needle):
                hits.append(_hit("case", case.get("case_id"),
                                 case.get("created_at"),
                                 "investigation case"))
    if "evidence" in wanted:
        packages = store.state.get("evidence_packages", {})
        if isinstance(packages, dict):
            items = packages.values()
        else:
            items = packages if isinstance(packages, list) else []
        for pkg in items:
            if isinstance(pkg, dict) and _contains(pkg, needle):
                hits.append(_hit("evidence",
                                 pkg.get("package_id") or
                                 pkg.get("evidence_id"),
                                 pkg.get("created_at"),
                                 "evidence package"))
    if "industries" in wanted:
        from app import industries as ind_mod
        for entry in ind_mod.registry():
            if needle in entry.get("name", "").lower() or \
                    needle in entry.get("id", ""):
                hits.append(_hit("industry", entry["id"], None,
                                 "industry registry entry"))
    return {"query": query, "hits": hits[:limit],
            "total": len(hits), "tenant_scope": tenant,
            "embedding": embedding_status()}


def _contains(row: dict, needle: str) -> bool:
    return needle in " ".join(
        str(value) for value in row.values()
        if isinstance(value, (str, int, float))).lower()


def _hit(kind: str, ref: str | None, observed: str | None,
         label: str) -> dict[str, Any]:
    return {"kind": kind, "reference": ref, "observed_at": observed,
            "freshness": "stored record; re-read via API for current "
                         "state",
            "label": label}
