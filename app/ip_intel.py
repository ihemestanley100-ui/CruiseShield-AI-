"""IP Intelligence Foundation (DI-04, additive derived layer).

Parsing/validation/classification of IPv4/IPv6, secure client-IP
extraction behind an explicit trusted-proxy list, label observations
derived from existing event entities, shared-IP attribution, and a
provider adapter interface whose default implementation reports
UNKNOWN for everything (never SAFE or MALICIOUS).

Derived layer only: no store writes, no migrations, no risk-rule
changes, no evidence-package changes, no network calls. Fixture labels
such as "ip_02" are opaque references, not addresses: address-bearing
facts appear only when a real capture or a verified source provides
them (neither exists yet).
"""
from __future__ import annotations

import ipaddress
import os
import re
from typing import Any, Optional, Protocol

from pydantic import BaseModel, Field

LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")

UNKNOWN = "unknown"


def trusted_proxies() -> list[str]:
    """Explicit trusted-proxy list (comma-separated IPs/networks).

    Empty by default: with no configured proxies every forwarding
    header is ignored and the direct peer is used.
    """
    raw = os.environ.get("TRUSTED_PROXIES", "")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _trusted_networks(entries: list[str]) -> list[Any]:
    nets = []
    for entry in entries:
        try:
            nets.append(ipaddress.ip_network(entry, strict=False))
        except ValueError:
            continue
    return nets


def parse_ip(value: str) -> Optional[Any]:
    """Parse an IPv4/IPv6 literal; None when invalid (never raises)."""
    if not isinstance(value, str):
        return None
    try:
        return ipaddress.ip_address(value.strip())
    except ValueError:
        return None


def classify_ip(value: str) -> dict[str, Any]:
    """Classify an IP literal; invalid input yields status unknown."""
    addr = parse_ip(value)
    if addr is None:
        return {"input": value, "valid": False, "status": UNKNOWN}
    if addr.is_loopback:
        category = "loopback"
    elif addr.is_reserved or addr.is_unspecified:
        category = "reserved"
    elif addr.is_link_local:
        category = "link_local"
    elif addr.is_multicast:
        category = "multicast"
    elif addr.is_private:
        category = "private"
    elif addr.is_global:
        category = "public"
    else:
        category = UNKNOWN
    return {"input": value, "valid": True, "version": addr.version,
            "category": category, "compressed": addr.compressed}


def extract_client_ip(headers: dict[str, str], peer: str,
                      trusted: Optional[list[str]] = None) -> dict[str, Any]:
    """Secure client-IP extraction with spoof protection.

    - The direct peer is used unless it belongs to the trusted list.
    - Forwarding headers are honored only from trusted peers, walking
      X-Forwarded-For right-to-left past trusted hops.
    - Anything invalid or untrusted resolves to status unknown.
    """
    if trusted is None:
        trusted = trusted_proxies()
    nets = _trusted_networks(trusted)
    peer_addr = parse_ip(peer)

    def is_trusted(addr: Optional[Any]) -> bool:
        return addr is not None and any(addr in net for net in nets)

    if not is_trusted(peer_addr):
        return {"ip": peer_addr.compressed if peer_addr else None,
                "source": "direct_peer",
                "trusted_path": False,
                "status": "peer_untrusted_headers_ignored"
                          if peer_addr else UNKNOWN}
    chain = [h.strip() for h in headers.get("x-forwarded-for", "").split(",")
             if h.strip()]
    for candidate in reversed(chain):
        addr = parse_ip(candidate)
        if addr is None:
            continue
        if not is_trusted(addr):
            return {"ip": addr.compressed, "source": "x-forwarded-for",
                    "trusted_path": True, "status": "extracted"}
    if chain:
        first = parse_ip(chain[0])
        if first is not None:
            return {"ip": first.compressed, "source": "x-forwarded-for",
                    "trusted_path": True, "status": "all_hops_trusted"}
    return {"ip": peer_addr.compressed if peer_addr else None,
            "source": "direct_peer", "trusted_path": True,
            "status": "no_forwarding_header" if peer_addr else UNKNOWN}


class IpObservation(BaseModel):
    """One observed IP-label reference (label, not an address)."""

    obs_id: str
    ip_label: str
    address: Optional[str] = None
    address_status: str = UNKNOWN
    account_id: Optional[str] = None
    txn_id: Optional[str] = None
    observed_at: str = ""
    source: str = "seed_event"
    source_ref: str = ""
    synthetic: bool = True


class NetworkIntel(BaseModel):
    """Provider enrichment result; every field defaults to unknown."""

    ip: str
    asn: Optional[str] = None
    isp: Optional[str] = None
    org: Optional[str] = None
    network_type: str = UNKNOWN
    vpn_indicator: str = UNKNOWN
    proxy_indicator: str = UNKNOWN
    tor_indicator: str = UNKNOWN
    reputation: str = UNKNOWN
    provider: str = UNKNOWN
    intel_at: str = ""
    fresh_until: str = ""


class IntelProvider(Protocol):
    """Vendor-neutral enrichment interface (DI-04; offline-safe)."""

    name: str

    def enrich_ip(self, ip: str) -> Optional[NetworkIntel]:
        """Return enrichment, or None when the IP is out of scope."""
        ...  # pragma: no cover - interface


class NullProvider:
    """Default provider: reports UNKNOWN for everything, no calls."""

    name = "null"

    def enrich_ip(self, ip: str) -> Optional[NetworkIntel]:
        if parse_ip(ip) is None:
            return None
        return NetworkIntel(ip=parse_ip(ip).compressed, provider="null")


def validate_label(label: str) -> str:
    """Validate an IP fixture label; raise ValueError when malformed."""
    if not isinstance(label, str) or not LABEL_RE.match(label):
        raise ValueError(f"INVALID_IP_LABEL: {label!r}")
    return label


def build_observations(state: dict[str, Any]) -> list[IpObservation]:
    """Derive label observations from event entities (no writes)."""
    observations: list[IpObservation] = []
    for event in state.get("events", []):
        entities = event.get("entities", {}) or {}
        label = entities.get("ip_id")
        if not label:
            continue
        txn = event.get("transaction", {}) or {}
        observations.append(IpObservation(
            obs_id=f"obs_ip_{event.get('event_id', '?')}",
            ip_label=str(label),
            address=None, address_status=UNKNOWN,
            account_id=txn.get("sender_account_id"),
            txn_id=txn.get("transaction_id"),
            observed_at=str(event.get("occurred_at", "")),
            source="seed_event",
            source_ref=str(event.get("event_id", "")),
            synthetic=True))
    observations.sort(key=lambda o: (o.observed_at, o.obs_id))
    return observations


def shared_ips(state: dict[str, Any]) -> list[dict[str, Any]]:
    """IP labels observed on 2+ accounts, with attribution (derived)."""
    by_label: dict[str, dict[str, Any]] = {}
    for obs in build_observations(state):
        slot = by_label.setdefault(
            obs.ip_label, {"ip_label": obs.ip_label, "accounts": set(),
                           "txn_ids": set(), "event_ids": set()})
        if obs.account_id:
            slot["accounts"].add(obs.account_id)
        if obs.txn_id:
            slot["txn_ids"].add(obs.txn_id)
        slot["event_ids"].add(obs.source_ref)
    out = []
    for label in sorted(by_label):
        slot = by_label[label]
        if len(slot["accounts"]) < 2:
            continue
        out.append({"ip_label": label,
                    "address_status": UNKNOWN,
                    "account_ids": sorted(slot["accounts"]),
                    "txn_ids": sorted(slot["txn_ids"]),
                    "event_ids": sorted(slot["event_ids"]),
                    "synthetic": True})
    return out


def proposed_edges(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Proposed (never inserted) graph edges for future DI-07 use.

    Returned as data so DI-07 can review and insert them under its own
    authorization. Callers must not write these into any store.
    """
    edges = []
    for obs in build_observations(state):
        if obs.txn_id:
            edges.append({
                "edge_id": f"proposed_conn_{obs.obs_id}",
                "source_node_id": obs.txn_id,
                "target_node_id": obs.ip_label,
                "relationship_type": "CONNECTED_FROM_IP",
                "source_event_ids": [obs.source_ref],
                "confidence": UNKNOWN,
                "status": "proposed_not_inserted",
                "synthetic": True})
        if obs.account_id:
            edges.append({
                "edge_id": f"proposed_assoc_{obs.obs_id}",
                "source_node_id": obs.account_id,
                "target_node_id": obs.ip_label,
                "relationship_type": "ASSOCIATED_WITH_IP",
                "source_event_ids": [obs.source_ref],
                "confidence": UNKNOWN,
                "status": "proposed_not_inserted",
                "synthetic": True})
    edges.sort(key=lambda e: e["edge_id"])
    return edges
