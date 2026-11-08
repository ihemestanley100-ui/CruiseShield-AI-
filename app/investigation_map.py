"""Investigation map orchestration: payloads, relationships, summaries.

Not to be confused with app/geo_intel.py (DI-05 coordinate/provider
contracts, reused here for validation vocabulary).

Derived read-only aggregation over real records (verifications,
observations, transactions, graph edges). Layers with no backing
records are present-but-empty with a reason — never synthesized.
Relationship vocabulary caps derived links at OBSERVED; nothing
reports DIRECTLY_VERIFIED without live provider evidence (none
exists). Summaries are deterministic and evidence-cited (no model).
"""
from __future__ import annotations

from typing import Any

LAYERS = (
    "identity_evidence",
    "device_observations",
    "telecom_observations",
    "ip_estimates",
    "verified_addresses",
    "transaction_origins",
    "transaction_destinations",
    "merchant_locations",
    "atm_pos_locations",
    "relationship_connections",
    "historical_observations",
    "investigator_annotations",
)

# Relationship strength vocabulary (§13), strongest first.
DIRECTLY_VERIFIED = "DIRECTLY_VERIFIED"
PROVIDER_REPORTED = "PROVIDER_REPORTED"
OBSERVED = "OBSERVED"
INFERRED = "INFERRED"
UNVERIFIED = "UNVERIFIED"


def _for_investigation(records: dict, investigation_id: str) -> list[dict]:
    out = []
    for record in (records or {}).values():
        if not isinstance(record, dict):
            continue
        if record.get("investigation_id") != investigation_id:
            continue
        out.append(record)
    return out


def investigation_map(state: dict[str, Any], investigation_id: str,
                      masked: bool) -> dict[str, Any]:
    """Twelve evidence layers; coordinates only when unmasked."""
    layers: dict[str, Any] = {}
    identities = _for_investigation(
        state.get("identity_verifications"), investigation_id)
    addresses = _for_investigation(
        state.get("address_verifications"), investigation_id)
    locations = _for_investigation(
        state.get("location_observations"), investigation_id)
    netgeos = _for_investigation(
        state.get("network_geo_observations"), investigation_id)
    telecoms = _for_investigation(
        state.get("telecom_verifications"), investigation_id)
    for name in LAYERS:
        layers[name] = {"items": [], "item_count": 0,
                        "reason_if_empty": ""}
    layers["identity_evidence"]["items"] = [
        {"verification_id": r.get("verification_id", ""),
         "kind": "IDENTITY",
         "status": r.get("verification_status", ""),
         "masked": True}
        for r in identities]
    layers["verified_addresses"]["items"] = [
        {"verification_id": r.get("verification_id", ""),
         "kind": ("VERIFIED_ADDRESS"
                  if r.get("verification_status") == "VERIFIED"
                  else "UNVERIFIED_ADDRESS"),
         "status": r.get("verification_status", ""),
         "coordinates": None if masked else {
             "latitude": (r.get("address") or {}).get("latitude", ""),
             "longitude": (r.get("address") or {}).get("longitude", "")},
         "masked": masked}
        for r in addresses]
    layers["telecom_observations"]["items"] = [
        {"verification_id": r.get("verification_id", ""),
         "kind": "TELECOM", "status": r.get("state", ""),
         "masked": True}
        for r in telecoms]
    layers["ip_estimates"]["items"] = [
        {"observation_id": r.get("observation_id", ""),
         "kind": "IP_ESTIMATE", "status": r.get("status", ""),
         "masked": True}
        for r in netgeos]
    layers["historical_observations"]["items"] = [
        {"observation_id": r.get("observation_id", ""),
         "kind": "AUTHORIZED_OBSERVATION",
         "status": r.get("verification_status", ""),
         "coordinates": None if masked else {
             "latitude": r.get("latitude"),
             "longitude": r.get("longitude"),
             "accuracy_meters": r.get("accuracy_meters")},
         "observed_at": r.get("observed_at", ""),
         "masked": masked}
        for r in locations]
    txns = [t for t in state.get("transactions", []) or []
            if isinstance(t, dict)]
    layers["transaction_origins"]["items"] = [
        {"transaction_id": t.get("transaction_id", ""),
         "kind": "TRANSACTION_LOCATION",
         "location_id": t.get("location_id", ""), "masked": True}
        for t in txns if t.get("location_id")]
    layers["transaction_destinations"]["items"] = list(
        layers["transaction_origins"]["items"])
    for name, reason in (
            ("device_observations",
             "device evidence carries no coordinates; see device graph"),
            ("merchant_locations", "no merchant coordinate source"),
            ("atm_pos_locations", "no terminal coordinate feed"),
            ("relationship_connections",
             "see relationships endpoint for edges"),
            ("investigator_annotations", "no annotation store")):
        layers[name]["reason_if_empty"] = reason
    for name, layer in layers.items():
        layer["item_count"] = len(layer["items"])
        if not layer["items"] and not layer["reason_if_empty"]:
            layer["reason_if_empty"] = "no records for this " \
                "investigation"
    return {"investigation_id": investigation_id, "layers": layers,
            "masked": masked, "map_provider_note":
            "renderer configured separately; payload is "
            "provider-neutral"}


def investigation_locations(state: dict[str, Any],
                            investigation_id: str,
                            masked: bool,
                            status: str = "",
                            provider: str = "") -> list[dict[str, Any]]:
    """Flat filterable location list across observation stores."""
    out = []
    for key, kind in (("location_observations", "AUTHORIZED"),
                      ("network_geo_observations", "IP_ESTIMATE")):
        for record in _for_investigation(state.get(key),
                                         investigation_id):
            current = record.get("verification_status",
                                 record.get("status", ""))
            if status and current != status:
                continue
            prov = record.get("provider_id", "")
            if provider and prov != provider:
                continue
            item = {"kind": kind,
                    "observation_id": record.get("observation_id", ""),
                    "status": current, "provider_id": prov,
                    "masked": masked}
            if kind == "AUTHORIZED" and not masked:
                item["coordinates"] = {
                    "latitude": record.get("latitude"),
                    "longitude": record.get("longitude"),
                    "accuracy_meters": record.get("accuracy_meters")}
            out.append(item)
    return out


def investigation_relationships(state: dict[str, Any],
                                investigation_id: str
                                ) -> list[dict[str, Any]]:
    """Stored graph edges + derived observation links (capped OBSERVED)."""
    edges = []
    for edge in state.get("edges", []) or []:
        if not isinstance(edge, dict):
            continue
        edges.append({
            "edge_id": edge.get("edge_id", ""),
            "source": edge.get("source_node_id", ""),
            "target": edge.get("target_node_id", ""),
            "relationship_type": edge.get("relationship_type", ""),
            "strength": OBSERVED,
            "evidence_reference": ", ".join(
                edge.get("source_event_ids", []) or []),
            "provider": "platform-graph",
            "valid_from": edge.get("valid_from", ""),
            "valid_to": edge.get("valid_to", ""),
        })
    for record in _for_investigation(
            state.get("location_observations"), investigation_id):
        edges.append({
            "edge_id": "derived_%s" % record.get("observation_id", ""),
            "source": record.get("subject_masked", ""),
            "target": record.get("device_reference", "") or "location",
            "relationship_type": "SUBJECT_TO_LOCATION",
            "strength": OBSERVED,
            "evidence_reference": record.get("observation_id", ""),
            "provider": record.get("provider_id", ""),
            "valid_from": record.get("observed_at", ""),
            "valid_to": "",
        })
    return edges


def summarize_evidence(bundle: dict[str, Any]) -> dict[str, Any]:
    """Deterministic evidence-grounded summary (no model calls).

    Lists discrepancies, uncertainties, missing evidence, and linked
    entities — every statement cites record IDs. Never declares
    guilt, identity, occupancy, or residence.
    """
    records = bundle.get("records", []) or []
    discrepancies = []
    uncertainties = []
    missing = []
    entities: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            continue
        rid = record.get("verification_id",
                         record.get("observation_id", "?"))
        for limit in record.get("limitations", []) or []:
            uncertainties.append({"record_id": rid,
                                  "statement": str(limit)})
        for gap in record.get("missing", []) or []:
            missing.append({"record_id": rid, "missing": str(gap)})
        for factor in record.get("factors", []) or []:
            if isinstance(factor, dict) and factor.get("result") \
                    == "fail":
                discrepancies.append(
                    {"record_id": rid,
                     "factor": str(factor.get("factor", ""))})
        for key in ("subject_masked", "device_reference"):
            if record.get(key):
                entities.add("%s:%s" % (key, record[key]))
    return {"discrepancies": discrepancies,
            "uncertainties": uncertainties,
            "missing_evidence": missing,
            "linked_entities": sorted(entities),
            "records_reviewed": len(records),
            "model_used": None,
            "notice": "deterministic summary; model-backed generation "
                      "is NOT_STARTED pending owner PII-processing "
                      "authorization"}


def metrics(state: dict[str, Any],
            tenant_id: str) -> dict[str, Any]:
    """Derived counts from live records (no history invented)."""
    counts: dict[str, Any] = {}
    for key in ("identity_verifications", "address_verifications",
                "location_observations", "network_geo_observations",
                "telecom_verifications", "intel_authorizations"):
        buckets: dict[str, int] = {}
        total = 0
        for record in (state.get(key) or {}).values():
            if not isinstance(record, dict):
                continue
            if record.get("tenant_id") != tenant_id:
                continue
            total += 1
            status = str(record.get("verification_status",
                                    record.get(
                                        "state",
                                        record.get(
                                            "authorization_status",
                                            "unknown"))))
            buckets[status] = buckets.get(status, 0) + 1
        counts[key] = {"total": total, "by_status": buckets}
    return {"tenant_id": tenant_id, "counts": counts,
            "computed_live": True,
            "history": "none retained; point-in-time counts only"}
