"""Provider-neutral data-source connector framework (v14.0 §04/§F).

Registry + connection lifecycle + health + audit for authorized
financial-data integrations (banking, NIP, POS, mobile, USSD, web, ATM,
transfer, agent networks, insurance, markets, digital assets,
government, trade, telecom).

Credential VALUES never persist and never appear in responses, logs, or
audit records: a connection stores server-side env-var REFERENCES plus
non-secret parameters only. A connection reaches CONNECTED only after a
successful live handshake — without partner credentials and an
implemented handshake, real adapters honestly report what is missing.
The loopback adapter is an explicitly labeled test harness proving the
lifecycle/health/audit machinery; it carries synthetic=true and must
never be mistaken for a provider connection.
"""
from __future__ import annotations

import os
import time
import uuid
from typing import Any

STATUSES = ("DRAFT", "CONFIGURED", "VERIFYING", "CONNECTED", "FAILED",
            "SUSPENDED", "REVOKED")

# status -> statuses it may move to (reason + evidence enforced by API).
_TRANSITIONS = {
    "DRAFT": ("CONFIGURED", "VERIFYING", "REVOKED"),
    "CONFIGURED": ("VERIFYING", "REVOKED"),
    "VERIFYING": ("CONNECTED", "FAILED", "REVOKED"),
    "CONNECTED": ("SUSPENDED", "REVOKED"),
    "FAILED": ("CONFIGURED", "VERIFYING", "REVOKED"),
    "SUSPENDED": ("VERIFYING", "REVOKED"),
    "REVOKED": (),
}

HEALTH_FAIL_SUSPEND = 3


def _spec(adapter: str, name: str, category: str, auth: str,
          params: tuple[str, ...], secrets: tuple[str, ...],
          capabilities: tuple[str, ...],
          synthetic: bool = False) -> dict[str, Any]:
    return {"adapter": adapter, "name": name, "category": category,
            "auth": auth, "config_params": list(params),
            "secret_refs": list(secrets),
            "capabilities": list(capabilities), "synthetic": synthetic}


_SPECS: tuple[dict[str, Any], ...] = (
    _spec("banking-rest", "Core banking API", "banking", "api-key",
          ("base_url", "institution_id"), ("CS_CONN_BANKING_KEY",),
          ("poll", "webhook", "batch")),
    _spec("nip-transfer", "NIP interbank transfers", "nip", "mtls",
          ("base_url", "institution_code"), ("CS_CONN_NIP_CERT",),
          ("poll", "batch")),
    _spec("pos-acquirer", "POS acquirer feed", "pos", "api-key",
          ("base_url", "merchant_id"), ("CS_CONN_POS_KEY",),
          ("batch", "poll")),
    _spec("mobile-banking", "Mobile banking channel", "mobile-app",
          "oauth2", ("base_url", "client_id"),
          ("CS_CONN_MOBILE_SECRET",), ("poll", "webhook")),
    _spec("ussd-gateway", "USSD session gateway", "ussd", "api-key",
          ("base_url", "service_code"), ("CS_CONN_USSD_KEY",),
          ("webhook",)),
    _spec("web-banking", "Web banking channel", "web", "oauth2",
          ("base_url", "client_id"), ("CS_CONN_WEB_SECRET",),
          ("poll", "webhook")),
    _spec("atm-switch", "ATM switch journal", "atm", "mtls",
          ("host", "port"), ("CS_CONN_ATM_CERT",), ("batch",)),
    _spec("transfer-batch", "Transfer batch files", "transfer",
          "api-key", ("base_url", "account_id"),
          ("CS_CONN_TRANSFER_KEY",), ("batch",)),
    _spec("agent-network", "Agent banking network", "agent", "api-key",
          ("base_url", "aggregator_id"), ("CS_CONN_AGENT_KEY",),
          ("batch", "poll")),
    _spec("insurance-core", "Insurance policy/claims core", "insurance",
          "api-key", ("base_url", "tenant_id"),
          ("CS_CONN_INSURANCE_KEY",), ("poll", "batch")),
    _spec("markets-feed", "Capital-markets data feed", "markets",
          "api-key", ("base_url",), ("CS_CONN_MARKETS_KEY",), ("poll",)),
    _spec("digital-assets", "Digital-asset custodian", "digital-assets",
          "api-key", ("base_url", "vault_id"),
          ("CS_CONN_DIGITAL_ASSETS_KEY",), ("poll", "webhook")),
    _spec("gov-financial", "Government financial system", "government",
          "mtls", ("base_url", "agency_code"),
          ("CS_CONN_GOV_CERT",), ("batch", "poll")),
    _spec("trade-erp", "Trade / ERP connector", "trade", "api-key",
          ("base_url", "company_id"), ("CS_CONN_TRADE_KEY",),
          ("batch", "poll")),
    _spec("telecom-cdr", "Telecom CDR feed (lawful access)", "telecom",
          "api-key", ("base_url", "operator_id"),
          ("CS_CONN_TELECOM_KEY",), ("batch",)),
    _spec("camara-number-verification", "CAMARA Number Verification",
          "camara", "oauth2", ("base_url", "aggregator_id"),
          ("CS_CONN_CAMARA_SECRET",), ("verify",)),
    _spec("camara-sim-swap", "CAMARA SIM Swap", "camara", "oauth2",
          ("base_url", "aggregator_id"), ("CS_CONN_CAMARA_SECRET",),
          ("verify",)),
    _spec("camara-device-swap", "CAMARA Device Swap", "camara",
          "oauth2", ("base_url", "aggregator_id"),
          ("CS_CONN_CAMARA_SECRET",), ("verify",)),
    _spec("camara-kyc-match", "CAMARA KYC Match", "camara", "oauth2",
          ("base_url", "aggregator_id"), ("CS_CONN_CAMARA_SECRET",),
          ("verify",)),
    _spec("camara-number-recycling", "CAMARA Number Recycling",
          "camara", "oauth2", ("base_url", "aggregator_id"),
          ("CS_CONN_CAMARA_SECRET",), ("verify",)),
    _spec("camara-device-identifier", "CAMARA Device Identifier",
          "camara", "oauth2", ("base_url", "aggregator_id"),
          ("CS_CONN_CAMARA_SECRET",), ("verify",)),
    _spec("mtn-sim-verification", "MTN SIM Verification",
          "operator-direct", "api-key", ("base_url", "country"),
          ("CS_CONN_MTN_KEY",), ("verify",)),
    _spec("hlr-lookup", "Carrier / HLR lookup service", "carrier-lookup",
          "api-key", ("base_url",), ("CS_CONN_HLR_KEY",),
          ("lookup",)),
    _spec("identity-document", "Government ID document verification",
          "identity", "api-key", ("base_url", "country"),
          ("CS_CONN_IDENTITY_KEY",), ("verify",)),
    _spec("identity-kyc", "KYC record matching service", "identity",
          "api-key", ("base_url", "country"), ("CS_CONN_IDENTITY_KEY",),
          ("verify",)),
    _spec("address-validation", "Authorized address validation",
          "address", "api-key", ("base_url", "country"),
          ("CS_CONN_ADDRESS_KEY",), ("verify",)),
    _spec("ip-geolocation", "IP geolocation data service",
          "ip-geolocation", "api-key", ("base_url",),
          ("CS_CONN_IPGEO_KEY",), ("lookup",)),
    _spec("ip-reputation", "IP reputation data service",
          "ip-geolocation", "api-key", ("base_url",),
          ("CS_CONN_IPGEO_KEY",), ("lookup",)),
    _spec("mapping-tiles", "Map tile renderer (free-tier only)",
          "mapping", "none", ("tile_url_template",), (), ("render",)),
    _spec("mapping-geocode", "Authorized geocoding service",
          "mapping", "api-key", ("base_url",), ("CS_CONN_GEOCODE_KEY",),
          ("geocode",)),
    _spec("location-operator", "Authorized operator location service",
          "location", "oauth2", ("base_url", "country"),
          ("CS_CONN_LOCATION_SECRET",), ("locate",)),
    _spec("location-consented-app", "Consented app location intake",
          "location", "app-attestation", ("app_id",),
          ("CS_CONN_LOCATION_SECRET",), ("ingest",)),
    _spec("loopback", "Loopback test harness", "harness", "harness",
          (), (), ("poll",), synthetic=True),
)


def registry() -> list[dict[str, Any]]:
    """All adapter specs (deep copies; loopback flagged synthetic)."""
    import copy

    return copy.deepcopy(list(_SPECS))


def get_adapter(name: str) -> dict[str, Any] | None:
    for spec in _SPECS:
        if spec["adapter"] == name:
            return spec
    return None


def _stamp(record: dict[str, Any], status: str, reason: str) -> dict:
    record["status"] = status
    record["status_reason"] = reason
    record["updated_at"] = time.time()
    return record


def create_connection(adapter: str, name: str,
                      tenant: str = "") -> dict[str, Any]:
    """Create a DRAFT connection. Raises ValueError on unknown adapter.

    Callers pass the server-derived tenant. New records carry both the
    canonical ``tenant_id`` and the legacy response-facing ``tenant``.
    """
    from app import tenancy as tenancy_mod

    tenant = tenant or tenancy_mod.DEFAULT_TENANT
    spec = get_adapter(adapter)
    if spec is None:
        raise ValueError("CONNECTOR_UNKNOWN: %s" % adapter)
    now = time.time()
    return {"id": "conn_" + uuid.uuid4().hex[:12], "adapter": adapter,
            "name": (name or "").strip() or spec["name"],
            "tenant": tenant, "tenant_id": tenant,
            "status": "DRAFT", "status_reason": "",
            "params": {}, "secret_refs": list(spec["secret_refs"]),
            "synthetic": spec["synthetic"], "created_at": now,
            "updated_at": now, "last_verified_at": 0.0,
            "last_health_at": 0.0, "health": None,
            "consecutive_failures": 0}


def configure(record: dict[str, Any],
              params: dict[str, Any]) -> dict[str, Any]:
    """Attach non-secret params; DRAFT/FAILED/CONFIGURED -> CONFIGURED."""
    spec = get_adapter(record["adapter"])
    assert spec is not None  # created via create_connection
    if record["status"] not in ("DRAFT", "CONFIGURED", "FAILED"):
        raise ValueError("CONNECTOR_STATUS: cannot configure from %s"
                         % record["status"])
    given = params if isinstance(params, dict) else {}
    missing = [p for p in spec["config_params"] if not given.get(p)]
    if missing:
        raise ValueError("CONNECTOR_CONFIG: missing params: %s"
                         % ",".join(missing))
    unknown = [k for k in given if k not in spec["config_params"]]
    if unknown:
        raise ValueError("CONNECTOR_CONFIG: unknown params: %s"
                         % ",".join(sorted(unknown)))
    record["params"] = {p: str(given[p]) for p in spec["config_params"]}
    return _stamp(record, "CONFIGURED", "parameters stored")


def begin_verify(record: dict[str, Any]) -> dict[str, Any]:
    """Enter VERIFYING from a legal predecessor state."""
    if record["status"] not in ("DRAFT", "CONFIGURED", "FAILED",
                                "SUSPENDED"):
        raise ValueError("CONNECTOR_STATUS: cannot verify from %s"
                         % record["status"])
    return _stamp(record, "VERIFYING", "verification started")


def _secret_present(ref: str) -> bool:
    return bool((os.environ.get(ref) or "").strip())


def secret_presence(record: dict[str, Any]) -> dict[str, bool]:
    """Per-ref presence booleans (never values)."""
    return {ref: _secret_present(ref)
            for ref in record.get("secret_refs", [])}


def _loopback_handshake(record: dict[str, Any]) -> tuple[bool, str]:
    _ = record
    return True, "harness echo ok"


def _awaiting_handshake(record: dict[str, Any]) -> tuple[bool, str]:
    return (False, "live handshake for '%s' needs partner endpoint "
            "authorization; no provider contacted"
            % record.get("adapter", "?"))


_HANDSHAKES = {"loopback": _loopback_handshake}


def complete_verify(record: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Run verification; VERIFYING -> CONNECTED or FAILED (honest)."""
    if record["status"] != "VERIFYING":
        raise ValueError("CONNECTOR_STATUS: cannot complete verify from "
                         "%s" % record["status"])
    spec = get_adapter(record["adapter"])
    assert spec is not None
    missing_params = [p for p in spec["config_params"]
                      if not (record.get("params") or {}).get(p)]
    if missing_params:
        _stamp(record, "FAILED", "missing params: %s"
               % ",".join(missing_params))
        return record, False
    missing_secrets = [r for r in spec["secret_refs"]
                       if not _secret_present(r)]
    if missing_secrets:
        _stamp(record, "FAILED", "awaiting credentials: %s (set %s)"
               % (",".join(missing_secrets),
                  "env vars" if len(missing_secrets) > 1 else "env var"))
        return record, False
    handshake = _HANDSHAKES.get(record["adapter"], _awaiting_handshake)
    ok, detail = handshake(record)
    if ok:
        record["last_verified_at"] = time.time()
        record["consecutive_failures"] = 0
        _stamp(record, "CONNECTED", detail)
    else:
        _stamp(record, "FAILED", detail)
    return record, ok


def probe_connection(record: dict[str, Any]) -> tuple[bool, str, int]:
    """One health probe: (ok, detail, latency_ms). CONNECTED only."""
    if record["status"] != "CONNECTED":
        raise ValueError("CONNECTOR_STATUS: health probe needs CONNECTED, "
                         "got %s" % record["status"])
    start = time.perf_counter()
    handshake = _HANDSHAKES.get(record["adapter"], _awaiting_handshake)
    ok, detail = handshake(record)
    latency = int((time.perf_counter() - start) * 1000)
    return ok, detail, latency


def record_health(record: dict[str, Any], ok: bool, latency_ms: int,
                  detail: str) -> bool:
    """Apply a probe result; auto-suspend at 3 consecutive failures.

    Returns True when the probe auto-suspended the connection.
    """
    record["last_health_at"] = time.time()
    if ok:
        record["consecutive_failures"] = 0
        record["health"] = {"ok": True, "latency_ms": latency_ms,
                            "detail": detail,
                            "at": record["last_health_at"]}
        return False
    record["consecutive_failures"] = \
        int(record.get("consecutive_failures", 0)) + 1
    record["health"] = {"ok": False, "latency_ms": latency_ms,
                        "detail": detail,
                        "at": record["last_health_at"]}
    if record["consecutive_failures"] >= HEALTH_FAIL_SUSPEND:
        _stamp(record, "SUSPENDED",
               "auto-suspended after %d failed probes"
               % record["consecutive_failures"])
        return True
    return False


def suspend(record: dict[str, Any], reason: str) -> dict[str, Any]:
    """Operator suspension from a live-ish state (reason required)."""
    if record["status"] not in ("CONFIGURED", "VERIFYING", "CONNECTED",
                                "FAILED"):
        raise ValueError("CONNECTOR_STATUS: cannot suspend from %s"
                         % record["status"])
    if not (reason or "").strip():
        raise ValueError("CONNECTOR_REASON_REQUIRED: suspend needs a "
                         "reason")
    return _stamp(record, "SUSPENDED", reason.strip()[:200])


def revoke(record: dict[str, Any], reason: str) -> dict[str, Any]:
    """Terminal revocation from any non-revoked state (reason required)."""
    if record["status"] == "REVOKED":
        raise ValueError("CONNECTOR_STATUS: already revoked")
    if not (reason or "").strip():
        raise ValueError("CONNECTOR_REASON_REQUIRED: revoke needs a "
                         "reason")
    return _stamp(record, "REVOKED", reason.strip()[:200])


def redact(record: dict[str, Any]) -> dict[str, Any]:
    """Public view: params + ref NAMES + live presence bools, no values."""
    return {"id": record["id"], "adapter": record["adapter"],
            "name": record.get("name", ""),
            "tenant": record.get("tenant", ""),
            "status": record["status"],
            "status_reason": record.get("status_reason", ""),
            "params": dict(record.get("params", {})),
            "secret_refs": list(record.get("secret_refs", [])),
            "secret_present": secret_presence(record),
            "synthetic": bool(record.get("synthetic", False)),
            "created_at": record.get("created_at", 0.0),
            "updated_at": record.get("updated_at", 0.0),
            "last_verified_at": record.get("last_verified_at", 0.0),
            "last_health_at": record.get("last_health_at", 0.0),
            "health": record.get("health"),
            "consecutive_failures": int(
                record.get("consecutive_failures", 0))}
