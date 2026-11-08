"""Tenant scoping layer (Level 14 §C, dev-environment implementation).

Single-tenant records (no ``tenant_id`` key) belong to the default
tenant, so every existing test and seed keeps working unchanged.
Once a record carries another tenant id, access through this layer
is strictly isolated: cross-tenant reads look like NOT FOUND (no
enumeration oracle) and cross-tenant writes raise.

API-boundary wiring resolves request context from sessions via
the D-014 user→tenant map (USER_TENANTS); unknown users stay on
the default tenant, so single-org behavior is unchanged.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEFAULT_TENANT = "org_primary"

_TENANTS: set[str] = {DEFAULT_TENANT}


class TenantDeniedError(ValueError):
    """Cross-tenant write attempt. ValueError so domain mapping holds."""


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str = DEFAULT_TENANT
    actor: str = "system"


def register_tenant(tenant_id: str) -> str:
    """Register an additional tenant id (slug: [a-z0-9_-], 1..64)."""
    import re

    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", tenant_id or ""):
        raise ValueError(f"TENANT_ID_INVALID: {tenant_id!r}")
    _TENANTS.add(tenant_id)
    return tenant_id


def known_tenants() -> frozenset[str]:
    return frozenset(_TENANTS)


def parse_user_tenants(env_value: str) -> dict[str, str]:
    """Parse USER_TENANTS into {username: tenant_id}. Skips bad entries.

    Format mirrors DEMO_USERS: "alice:org_acme,bob:org_beta".
    Empty usernames, empty tenants, and malformed entries are
    skipped (fail-safe: affected users keep the default tenant).
    """
    mapping: dict[str, str] = {}
    for entry in (env_value or "").split(","):
        parts = entry.strip().split(":", 1)
        if len(parts) != 2:
            continue
        user, tenant = parts[0].strip(), parts[1].strip()
        if not user or not tenant:
            continue
        mapping[user] = tenant
    return mapping


def tenant_for_user(username: str,
                    mapping: dict[str, str] | None) -> str:
    """D-014: resolve a user's tenant id.

    Unknown user, missing map, or invalid tenant slug returns
    DEFAULT_TENANT. Valid mapped slugs auto-register so records
    stamped with them stay owned (never silently defaulted).
    """
    claimed = (mapping or {}).get(username or "")
    if not claimed:
        return DEFAULT_TENANT
    try:
        return register_tenant(claimed)
    except ValueError:
        return DEFAULT_TENANT


def context_for_user(username: str,
                     mapping: dict[str, str] | None,
                     actor: str | None = None) -> TenantContext:
    """TenantContext for a username (actor defaults to username)."""
    user = username or ""
    return TenantContext(
        tenant_id=tenant_for_user(user, mapping),
        actor=actor or user or "anonymous")


def tenant_of(record: dict[str, Any] | None) -> str | None:
    """Owning tenant of a record; None only when the record is None.

    Connection records predate the canonical ``tenant_id`` key and use
    ``tenant``; recognize that legacy key so old records stay owned.
    """
    if record is None:
        return None
    claimed = record.get("tenant_id") or record.get("tenant",
                                                  DEFAULT_TENANT)
    return claimed if claimed in _TENANTS else DEFAULT_TENANT


def enforce_read(record: dict[str, Any] | None,
                 ctx: TenantContext) -> dict[str, Any] | None:
    """Return the record iff visible to ctx, else None (no oracle)."""
    if record is None:
        return None
    if tenant_of(record) != ctx.tenant_id:
        return None
    return record


def enforce_write(record: dict[str, Any] | None,
                  ctx: TenantContext) -> None:
    """Raise TenantDeniedError when ctx may not mutate the record."""
    if record is not None and tenant_of(record) != ctx.tenant_id:
        raise TenantDeniedError(
            f"TENANT_DENIED: {ctx.tenant_id} may not write "
            f"{tenant_of(record)} record")


def filter_visible(records: list[dict[str, Any]],
                   ctx: TenantContext) -> list[dict[str, Any]]:
    """Enumeration-safe listing: only ctx-tenant records survive."""
    return [r for r in records if tenant_of(r) == ctx.tenant_id]


def stamp(record: dict[str, Any], ctx: TenantContext) -> dict[str, Any]:
    """Tag a new record with its owning tenant (server-side)."""
    record["tenant_id"] = ctx.tenant_id
    return record


def visible_graph(state: dict[str, Any], ctx: TenantContext) -> tuple[
        list[dict[str, Any]], list[dict[str, Any]],
        list[dict[str, Any]]]:
    """Tenant-visible (transactions, nodes, edges) of a state dict.

    Edges inherit ownership from their source events' transactions;
    nodes survive when they terminate a visible transaction or edge.
    """
    txns = filter_visible(
        [t for t in state.get("transactions", []) if isinstance(t, dict)],
        ctx)
    visible_txn_ids = {t.get("transaction_id") for t in txns}
    event_txn: dict[str, str] = {}
    for event in state.get("events", []) or []:
        if not isinstance(event, dict):
            continue
        txn = event.get("transaction") or {}
        if event.get("event_id") and txn.get("transaction_id"):
            event_txn[event["event_id"]] = txn["transaction_id"]
    edges = [
        edge for edge in state.get("edges", []) or []
        if isinstance(edge, dict) and any(
            event_txn.get(source) in visible_txn_ids
            for source in edge.get("source_event_ids") or [])]
    node_ids = {t.get("sender_account_id") for t in txns}
    node_ids |= {t.get("receiver_account_id") for t in txns}
    for edge in edges:
        node_ids.add(edge.get("source_node_id"))
        node_ids.add(edge.get("target_node_id"))
    nodes = [n for n in state.get("nodes", []) or []
             if isinstance(n, dict) and n.get("node_id") in node_ids]
    return txns, nodes, edges


def visible_state(state: dict[str, Any],
                  ctx: TenantContext) -> dict[str, Any]:
    """Shallow state view limited to ctx-visible records.

    Transactions/nodes/edges come from visible_graph; events keep
    entries whose transaction is visible; investigations keep owned
    records. All other keys pass through by reference. Derived
    intel readers use exactly the covered keys.
    """
    txns, nodes, edges = visible_graph(state, ctx)
    visible_txn_ids = {t.get("transaction_id") for t in txns}
    view = dict(state)
    view["transactions"] = txns
    view["nodes"] = nodes
    view["edges"] = edges
    view["events"] = [
        e for e in state.get("events", []) or []
        if isinstance(e, dict) and (e.get("transaction") or {}).get(
            "transaction_id") in visible_txn_ids]
    view["investigations"] = filter_visible(
        [i for i in state.get("investigations", [])
         if isinstance(i, dict)], ctx)
    return view
