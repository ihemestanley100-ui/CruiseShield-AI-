"""Tenant scoping layer (Level 14 §C, dev-environment implementation).

Single-tenant records (no ``tenant_id`` key) belong to the default
tenant, so every existing test and seed keeps working unchanged.
Once a record carries another tenant id, access through this layer
is strictly isolated: cross-tenant reads look like NOT FOUND (no
enumeration oracle) and cross-tenant writes raise.

API-boundary wiring (resolving the context from sessions/tokens)
lands after D-014 is recorded; this module is the enforcement
core it will call.
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


def tenant_of(record: dict[str, Any] | None) -> str | None:
    """Owning tenant of a record; None only when the record is None."""
    if record is None:
        return None
    claimed = record.get("tenant_id", DEFAULT_TENANT)
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
