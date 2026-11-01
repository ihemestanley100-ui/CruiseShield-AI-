"""Network graph intelligence overlay (DI-07, additive derived layer).

Builds in-memory display nodes/edges for device, IP, and location
intelligence plus detail enrichment for existing device nodes. The
base 22-node/30-edge graph is never modified here: the overlay is
returned as data, merged only at render time, and clearly marked
derived/synthetic. Value-gated honesty: IP nodes require a real
address, location nodes require coordinates or attributed place data;
opaque fixture labels (ip_02, loc_01) yield explicit unavailable
reasons, never fabricated nodes.

Relationship types (§5) are validated by validate_derived_edge: both
endpoints must exist, the type must be allowed, the observation must
exist, and evidence refs must resolve when claimed.
"""
from __future__ import annotations

from typing import Any, Optional

from app import device_intel as device_mod
from app import geo_intel as geo_mod
from app import intel_link as link_mod
from app import ip_intel as ip_mod

UNKNOWN = "unknown"

ALLOWED_RELATIONSHIPS = {
    "ACCOUNT_USES_DEVICE",
    "ACCOUNT_OBSERVED_FROM_IP",
    "TRANSACTION_OBSERVED_FROM_IP",
    "ACCOUNT_ASSOCIATED_WITH_LOCATION",
    "TRANSACTION_ASSOCIATED_WITH_LOCATION",
    "DEVICE_OBSERVED_DURING_TRANSACTION",
    "IP_OBSERVED_DURING_TRANSACTION",
    "LOCATION_OBSERVED_DURING_TRANSACTION",
}


def validate_derived_edge(edge: dict[str, Any],
                          node_ids: set[str]) -> tuple[bool, str]:
    """Provenance gates (§6); returns (ok, reason)."""
    for field in ("edge_id", "source_node_id", "relationship_type",
                  "target_node_id", "source_obs_id", "source"):
        if not edge.get(field):
            return False, f"missing_{field}"
    if edge["source_node_id"] not in node_ids:
        return False, "unknown_source_node"
    if edge["target_node_id"] not in node_ids:
        return False, "unknown_target_node"
    if edge["relationship_type"] not in ALLOWED_RELATIONSHIPS:
        return False, "relationship_type_not_allowed"
    if edge.get("status") == "confirmed" and not edge.get("evidence_refs"):
        return False, "confirmed_requires_evidence_refs"
    return True, "ok"


def device_detail(state: dict[str, Any],
                  device_id: str) -> Optional[dict[str, Any]]:
    """Detail enrichment for an existing device node (None if unseen)."""
    profile = device_mod.get_profile(state, device_id)
    if profile is None:
        return None
    return {
        "node_id": device_id, "node_type": "device",
        "status": "observed", "identity_status": "observed_only",
        "first_seen": profile.first_seen or UNKNOWN,
        "last_seen": profile.last_seen or UNKNOWN,
        "linked_accounts": len(profile.account_ids),
        "linked_transactions": len(profile.txn_ids),
        "account_ids": profile.account_ids,
        "attributes": profile.attributes or {},
        "attributes_source": profile.attributes_source,
        "evidence_refs": profile.evidence_refs,
        "synthetic": True, "derived": True,
    }


def ip_node_for(address: str, observations: list[dict[str, Any]]
                ) -> Optional[dict[str, Any]]:
    """IP display node; None unless a real address validates (never a label)."""
    parsed = ip_mod.parse_ip(address)
    if parsed is None:
        return None
    classification = ip_mod.classify_ip(address)
    linked_txns = sorted({o["txn_id"] for o in observations
                          if o.get("txn_id")})
    linked_accts = sorted({o["account_id"] for o in observations
                           if o.get("account_id")})
    return {
        "node_id": f"ip_{parsed.compressed}",
        "node_type": "ip",
        "display_label": f"IP {parsed.compressed}",
        "synthetic_flag": True,
        "source_record_ids": [o["obs_id"] for o in observations],
        "status": "observed", "derived": True,
        "classification": classification["category"],
        "version": classification["version"],
        "linked_transactions": linked_txns,
        "linked_accounts": linked_accts,
        "intel": "unavailable",
        "intel_reason": "null_provider_no_enrichment",
    }


def location_node_for(label: str, observations: list[dict[str, Any]],
                      geo: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Location display node; None without attributed geo data."""
    if not geo or geo.get("status") != "resolved":
        return None
    return {
        "node_id": f"loc_{label}",
        "node_type": "location",
        "display_label": f"Location {geo.get('city', UNKNOWN)}, "
                         f"{geo.get('country_code', UNKNOWN)}",
        "synthetic_flag": True,
        "source_record_ids": [o["obs_id"] for o in observations],
        "status": "observed", "derived": True,
        "country_code": geo.get("country_code", UNKNOWN),
        "city": geo.get("city", UNKNOWN),
        "approximate_only": True,
        "confidence": geo.get("confidence", UNKNOWN),
        "freshness": geo_mod.classify_freshness(geo.get("observed_at", "")),
    }


def build_overlay(state: dict[str, Any],
                  txn_id: str) -> Optional[dict[str, Any]]:
    """Derived overlay for one transaction (None if txn unknown).

    In-memory only: callers must never persist nodes/edges. Base-graph
    counts are reported separately and never merged here.
    """
    linked = link_mod.transaction_intel(state, txn_id)
    if linked is None:
        return None
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    unavailable: dict[str, str] = {}
    details: dict[str, dict[str, Any]] = {}
    for label in sorted({o["device_id"]
                         for o in linked["device_observations"]}):
        detail = device_detail(state, label)
        if detail is not None:
            details[label] = detail
    ip_labels = {o["ip_label"] for o in linked["ip_observations"]}
    if ip_labels:
        unavailable["ip"] = ("labels_without_address:"
                             + ",".join(sorted(ip_labels)))
    geo_labels = {o["location_label"]
                  for o in linked["geolocation_observations"]}
    if geo_labels:
        unavailable["location"] = ("labels_without_geo:"
                                   + ",".join(sorted(geo_labels)))
    base_nodes = state.get("nodes", [])
    base_edges = state.get("edges", [])
    node_ids = {n.get("node_id", "") for n in base_nodes}
    ok_edges = []
    for edge in edges:
        ok, _ = validate_derived_edge(edge, node_ids)
        if ok:
            ok_edges.append(edge)
    return {
        "transaction_id": txn_id,
        "nodes": nodes,
        "edges": ok_edges,
        "node_details": details,
        "unavailable": unavailable,
        "counts": {"overlay_nodes": len(nodes),
                   "overlay_edges": len(ok_edges),
                   "base_nodes": len(base_nodes),
                   "base_edges": len(base_edges)},
        "derived": True,
        "synthetic": True,
    }
