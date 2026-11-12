"""Provider-neutral telecom verification plumbing.

Source vocabulary (every result carries exactly one):
VERIFIED_PROVIDER (live CONNECTED non-synthetic connection),
CLIENT_REPORTED (caller/attestation-supplied, unconfirmed),
INFERRED (derived from platform observations, limitations stated),
UNAVAILABLE (no usable input).

LIVE rule: an integration is live only when a CONNECTED,
non-synthetic connection for its adapter exists in the store AND
a successful request was observed. Nothing here can report live
without that evidence. The TelecomHarness answers only through a
CONNECTED loopback connection and labels every response synthetic.
"""
from __future__ import annotations

from typing import Any

VERIFIED_PROVIDER = "VERIFIED_PROVIDER"
CLIENT_REPORTED = "CLIENT_REPORTED"
INFERRED = "INFERRED"
UNAVAILABLE = "UNAVAILABLE"
# Test-only fifth label: synthetic harness output (never live evidence).
HARNESS = "HARNESS"

TELECOM_ADAPTERS = (
    "camara-number-verification",
    "camara-sim-swap",
    "camara-device-swap",
    "camara-kyc-match",
    "camara-number-recycling",
    "camara-device-identifier",
    "mtn-sim-verification",
    "hlr-lookup",
)

# Verification type -> adapter capable of serving it live.
TYPE_ADAPTERS: dict[str, tuple[str, ...]] = {
    "carrier_identification": ("hlr-lookup",),
    "current_network": ("hlr-lookup", "camara-number-verification"),
    "number_verification": ("camara-number-verification",),
    "sim_ownership": ("camara-number-verification",
                      "mtn-sim-verification"),
    "sim_swap": ("camara-sim-swap", "mtn-sim-verification"),
    "number_recycling": ("camara-number-recycling",),
    "device_swap": ("camara-device-swap", "camara-device-identifier"),
    "kyc_match": ("camara-kyc-match",),
    "tenure": ("hlr-lookup",),
    "roaming": ("camara-number-verification", "hlr-lookup"),
    "network_type": ("camara-device-identifier", "hlr-lookup"),
}


class ProviderOutage(Exception):
    """Simulated or real provider failure (tests + live guard)."""


def live_connection(store, adapter: str,
                    tenant_id: str) -> dict[str, Any] | None:
    """CONNECTED non-synthetic connection for adapter+tenant, else None.

    The loopback harness can never satisfy this: harness responses are
    synthetic evidence, never live verification.
    """
    for record in store.connection_list():
        if not isinstance(record, dict):
            continue
        if record.get("adapter") != adapter:
            continue
        if record.get("status") != "CONNECTED":
            continue
        if record.get("synthetic"):
            continue
        if (record.get("tenant_id") or record.get("tenant")) != tenant_id:
            continue
        return record
    return None


def provider_status(store, tenant_id: str) -> list[dict[str, Any]]:
    """Per-adapter status rows (no secret values, presence only)."""
    from app import connectors as conn_mod

    rows = []
    for adapter in TELECOM_ADAPTERS:
        spec = conn_mod.get_adapter(adapter) or {}
        conns = [c for c in store.connection_list()
                 if isinstance(c, dict) and c.get("adapter") == adapter
                 and (c.get("tenant_id") or c.get("tenant")) == tenant_id]
        live = any(c.get("status") == "CONNECTED" and not c.get("synthetic")
                   for c in conns)
        best = max([c.get("status", "") for c in conns], default="NONE")
        rows.append({"adapter": adapter,
                     "name": spec.get("name", adapter),
                     "status": "NOT_CONNECTED" if best in ("", "NONE")
                     else best,
                     "live": bool(live),
                     "secret_refs": list(spec.get("secret_refs", [])),
                     "secret_present": {r: False
                                        for r in spec.get("secret_refs",
                                                          [])}})
        for conn in conns:
            for ref, present in conn_mod.secret_presence(conn).items():
                rows[-1]["secret_present"][ref] = bool(present)
    return rows


class TelecomHarness:
    """Test-only provider double behind a CONNECTED loopback connection.

    Every response carries synthetic=True and provider=harness-loopback.
    Refuses to answer unless the tenant owns a CONNECTED loopback
    connection (lifecycle proof) and refuses real adapters outright.
    fail_next() arms one ProviderOutage for outage-path tests.
    """

    PROVIDER = "harness-loopback"

    def __init__(self) -> None:
        self._fail_armed = 0

    def fail_next(self, count: int = 1) -> None:
        self._fail_armed = max(0, int(count))

    def _guard(self, store, tenant_id: str) -> None:
        if self._fail_armed > 0:
            self._fail_armed -= 1
            raise ProviderOutage("harness-injected outage")
        for record in store.connection_list():
            if not isinstance(record, dict):
                continue
            if record.get("adapter") != "loopback":
                continue
            if record.get("status") != "CONNECTED":
                continue
            if (record.get("tenant_id")
                    or record.get("tenant")) != tenant_id:
                continue
            return
        raise ProviderOutage("no CONNECTED loopback connection; "
                             "harness refuses to answer")

    def answer(self, store, tenant_id: str, verify_type: str,
             script: dict[str, Any] | None = None) -> dict[str, Any]:
        """Canned synthetic response for verify_type (tests only)."""
        self._guard(store, tenant_id)
        script = script or {}
        return {"provider": self.PROVIDER, "synthetic": True,
                "verify_type": verify_type,
                "provider_ref": "harness-%s" % verify_type,
                "payload": dict(script)}
