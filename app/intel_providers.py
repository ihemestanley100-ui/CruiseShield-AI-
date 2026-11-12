"""Global Intelligence Provider Registry (§10) + country coverage (§17).

Unified read-only view over the connectors lifecycle registry,
telecom adapters, and intelligence categories (identity, address,
IP geolocation, mapping, location). Lifecycle mapping is explicit;
nothing reports ACTIVE without a CONNECTED, success-observed link.
Country coverage reports operational truth: registry presence is
NOT coverage — all seven assessed countries are PROVIDER_UNAVAILABLE.
"""
from __future__ import annotations

import os
from typing import Any

# Connector status -> §10.2 lifecycle (documented, no invention).
LIFECYCLE = {
    "DRAFT": "DISCOVERED",
    "AWAITING_CREDENTIALS": "CREDENTIALS_REQUIRED",
    "CONFIGURED": "CONFIGURED",
    "VERIFYING": "CONNECTIVITY_TESTED",
    "CONNECTED": "ACTIVE",
    "FAILED": "DEGRADED",
    "SUSPENDED": "DISABLED",
    "REVOKED": "RETIRED",
}

# Best-connection preference (M3: lexicographic max() let SUSPENDED
# outrank CONNECTED). Unknown statuses rank below every known one.
_STATUS_RANK = {
    "CONNECTED": 6,
    "VERIFYING": 5,
    "CONFIGURED": 4,
    "AWAITING_CREDENTIALS": 3,
    "DRAFT": 2,
    "FAILED": 1,
    "SUSPENDED": 0,
    "REVOKED": -1,
}


def _rank(status: str) -> int:
    return _STATUS_RANK.get(status, -2)

INTEL_ADAPTERS = (
    "identity-document",
    "identity-kyc",
    "address-validation",
    "ip-geolocation",
    "ip-reputation",
    "mapping-tiles",
    "mapping-geocode",
    "location-operator",
    "location-consented-app",
)

COVERAGE_STATUSES = (
    "NOT_ASSESSED",
    "RESEARCH_REQUIRED",
    "PROVIDER_UNAVAILABLE",
    "AUTHORIZATION_REQUIRED",
    "CONFIGURATION_REQUIRED",
    "TESTING",
    "LIMITED_COVERAGE",
    "PRODUCTION_VERIFIED",
)

# Assessed registry countries (telecom registry v1.0). Every other
# country is NOT_ASSESSED. Assessed != covered: no live providers.
ASSESSED_COUNTRIES = ("NG", "US", "UK", "FR", "KE", "ZW", "ZA")


def map_provider() -> str:
    """Configured map renderer: none (schematic) or leaflet-osm."""
    value = (os.environ.get("MAP_PROVIDER", "") or "").strip().lower()
    return value if value in ("leaflet-osm",) else "none"


def unified_registry(store, tenant_id: str) -> list[dict[str, Any]]:
    """All adapters with lifecycle, health, cost honesty (no secrets)."""
    from app import connectors as conn_mod
    from app import telecom_providers as telecom_prov

    rows: list[dict[str, Any]] = []
    for spec in conn_mod.registry():
        conns = [c for c in store.connection_list()
                 if isinstance(c, dict)
                 and c.get("adapter") == spec["adapter"]
                 and (c.get("tenant_id") or c.get("tenant")) == tenant_id]
        live = [c for c in conns if c.get("status") == "CONNECTED"
                and not c.get("synthetic")]
        best = max([c.get("status", "") for c in conns], default="",
                     key=_rank)
        observed = any(c.get("last_success_at") for c in live)
        lifecycle = (LIFECYCLE.get(best, "DISCOVERED") if best
                     else "DISCOVERED")
        if best == "CONNECTED" and not observed:
            lifecycle = "CONNECTIVITY_TESTED"
        rows.append({
            "provider_id": spec["adapter"], "name": spec["name"],
            "category": spec["category"], "auth": spec["auth"],
            "capabilities": list(spec.get("capabilities", [])),
            "api_version": "unknown",
            "integration_status": lifecycle,
            "live": bool(live and observed),
            "countries": "unassessed",
            "cost_classification": ("free-synthetic"
                                    if spec.get("synthetic")
                                    else "unknown-unapproved"),
            "limitations": (["synthetic test harness"]
                            if spec.get("synthetic")
                            else ["no credentials, handshake, or live "
                                  "requests observed"]),
            "secret_refs": list(spec.get("secret_refs", [])),
        })
    for adapter in telecom_prov.TELECOM_ADAPTERS:
        if any(r["provider_id"] == adapter for r in rows):
            continue
        rows.append({"provider_id": adapter, "name": adapter,
                     "category": "telecom",
                     "integration_status": "DISCOVERED",
                     "live": False,
                     "limitations": ["adapter declared by telecom "
                                     "engine, no connector spec"]})
    rows.sort(key=lambda r: r["provider_id"])
    return rows


def provider_health(store, tenant_id: str,
                    provider_id: str) -> dict[str, Any] | None:
    """Health for one provider (connection-backed or declared)."""
    from app import connectors as conn_mod

    spec = conn_mod.get_adapter(provider_id)
    if spec is None:
        known = {r["provider_id"]
                 for r in unified_registry(store, tenant_id)}
        if provider_id not in known:
            return None
        return {"provider_id": provider_id, "status": "NO_CONNECTION",
                "integration_status": "DISCOVERED", "live": False}
    conns = [c for c in store.connection_list()
             if isinstance(c, dict) and c.get("adapter") == provider_id
             and (c.get("tenant_id") or c.get("tenant")) == tenant_id]
    if not conns:
        return {"provider_id": provider_id, "status": "NO_CONNECTION",
                "integration_status": "DISCOVERED", "live": False}
    best = max(conns, key=lambda c: _rank(str(c.get("status", ""))))
    return {"provider_id": provider_id,
            "status": best.get("status", ""),
            "integration_status": LIFECYCLE.get(
                best.get("status", ""), "DISCOVERED"),
            "live": bool(best.get("status") == "CONNECTED"
                         and not best.get("synthetic")
                         and best.get("last_success_at")),
            "last_check": best.get("last_health_at", "")}


def country_coverage() -> list[dict[str, Any]]:
    """Per-country operational coverage (honest, no live claims)."""
    from app import telecom_registry as reg_mod

    rows = []
    for code in ASSESSED_COUNTRIES:
        ops = [op["operator_id"] for op in reg_mod.list_operators(code)]
        rows.append({
            "country": code,
            "country_name": reg_mod.COUNTRY_NAMES.get(code, code),
            "identity": "PROVIDER_UNAVAILABLE",
            "telecom": "PROVIDER_UNAVAILABLE",
            "address": "PROVIDER_UNAVAILABLE",
            "ip_geolocation": "PROVIDER_UNAVAILABLE",
            "mapping": "PROVIDER_UNAVAILABLE",
            "location": "PROVIDER_UNAVAILABLE",
            "operators_registered": ops,
            "overall": "PROVIDER_UNAVAILABLE",
            "legal_review": "NOT_ASSESSED",
            "note": "registry presence is not coverage; no live "
                    "provider in any category",
        })
    return rows
