"""Intelligence association layer (DI-06, additive read-only).

Links existing DI-03 device, DI-04 IP, and DI-05 geolocation
observations to transactions, accounts, and investigations by
reference. Nothing is duplicated, persisted, scored, or decided
here: unknown stays UNKNOWN, conflicts stay visible, and every
association carries provenance plus a synthetic flag.

Isolation: each summary contains only data reachable from its own
subject id through verified relationships (event entities and
investigation transaction linkage). Unknown subjects yield None
(served as 404); no cross-subject leakage by construction.
"""
from __future__ import annotations

from typing import Any, Optional

from app import device_intel as device_mod
from app import geo_intel as geo_mod
from app import ip_intel as ip_mod

UNKNOWN = "unknown"
NOT_AVAILABLE = "not_available"

_COMPARE_MAP = {
    "same_location": "SAME_LOCATION",
    "different_location": "DIFFERENT_LOCATION",
    "conflicting": "CONFLICTING_LOCATION",
    "stale_input": "STALE_OBSERVATION",
    "insufficient_evidence": "INSUFFICIENT_EVIDENCE",
}


def _events_for_txn(state: dict[str, Any],
                    txn_id: str) -> list[dict[str, Any]]:
    return [e for e in state.get("events", [])
            if (e.get("transaction", {}) or {}).get("transaction_id")
            == txn_id]


def _first_last(values: list[str]) -> tuple[str, str]:
    stamped = sorted(v for v in values if v)
    return (stamped[0], stamped[-1]) if stamped else ("", "")


def transaction_intel(state: dict[str, Any],
                      txn_id: str) -> Optional[dict[str, Any]]:
    """Read-only intel summary for one transaction (None if unknown)."""
    txn = next((t for t in state.get("transactions", [])
                if t.get("transaction_id") == txn_id), None)
    if txn is None:
        return None
    device_obs = [o.model_dump() for o in
                  device_mod.build_observations(state)
                  if o.txn_id == txn_id]
    ip_obs = [o.model_dump() for o in ip_mod.build_observations(state)
              if o.txn_id == txn_id]
    geo_obs = [o for o in geo_mod.build_label_observations(state)
               if o["txn_id"] == txn_id]
    seen = [o["observed_at"] for o in device_obs + ip_obs + geo_obs]
    first, last = _first_last(seen)
    graph_refs: dict[str, list[str]] = {}
    for label in sorted({o["device_id"] for o in device_obs}):
        profile = device_mod.get_profile(state, label)
        if profile is not None:
            graph_refs[label] = profile.evidence_refs.get(
                "graph_edge_ids", [])
    return {
        "transaction_id": txn_id,
        "source_account_id": txn.get("sender_account_id", UNKNOWN),
        "destination_account_id": txn.get("receiver_account_id", UNKNOWN),
        "transaction_time": txn.get("occurred_at", ""),
        "device_observations": device_obs,
        "ip_observations": ip_obs,
        "geolocation_observations": geo_obs,
        "device_graph_refs": graph_refs,
        "observation_first_seen": first or NOT_AVAILABLE,
        "observation_last_seen": last or NOT_AVAILABLE,
        "provenance": {
            "event_ids": sorted({o.get("source_ref", "")
                                 for o in device_obs + ip_obs + geo_obs
                                 if o.get("source_ref")}),
        },
        "synthetic": True,
        "limitations": [
            "Observations are fixture-derived references, not verified "
            "identity.",
            "IP/geolocation values are unavailable without a provider.",
        ],
    }


def account_intel(state: dict[str, Any],
                  account_id: str) -> Optional[dict[str, Any]]:
    """Read-only intel summary for one account (None if unknown)."""
    txns = [t for t in state.get("transactions", [])
            if t.get("sender_account_id") == account_id
            or t.get("receiver_account_id") == account_id]
    if not txns:
        return None
    device_obs = [o.model_dump() for o in
                  device_mod.build_observations(state)
                  if o.account_id == account_id]
    ip_obs = [o.model_dump() for o in ip_mod.build_observations(state)
              if o.account_id == account_id]
    geo_obs = [o for o in geo_mod.build_label_observations(state)
               if o["account_id"] == account_id]
    devices = sorted({o["device_id"] for o in device_obs})
    ip_labels = sorted({o["ip_label"] for o in ip_obs})
    geo_labels = sorted({o["location_label"] for o in geo_obs})
    seen = [o.get("observed_at", "") for o in
            device_obs + ip_obs + geo_obs]
    first, last = _first_last(seen)
    txn_ids = sorted({t.get("transaction_id", "") for t in txns})
    inv_ids = sorted({i.get("investigation_id", "")
                      for i in state.get("investigations", [])
                      if i.get("transaction_id") in set(txn_ids)})
    shared_devices = [s for s in device_mod.shared_devices(state)
                      if account_id in s["account_ids"]]
    shared_ips = [s for s in ip_mod.shared_ips(state)
                  if account_id in s["account_ids"]]
    return {
        "account_id": account_id,
        "known_devices": devices or [UNKNOWN],
        "known_ip_labels": ip_labels or [UNKNOWN],
        "known_geo_labels": geo_labels or [UNKNOWN],
        "first_seen": first or NOT_AVAILABLE,
        "last_seen": last or NOT_AVAILABLE,
        "shared_devices": shared_devices,
        "shared_ips": shared_ips,
        "transaction_count": len(txns),
        "transaction_ids": txn_ids,
        "investigation_count": len(inv_ids),
        "investigation_ids": inv_ids,
        "provenance": {
            "event_ids": sorted({o.get("source_ref", "")
                                 for o in device_obs + ip_obs + geo_obs
                                 if o.get("source_ref")}),
        },
        "synthetic": True,
        "limitations": [
            "Shared infrastructure is not proof of fraud or malice.",
        ],
    }


def investigation_intel(state: dict[str, Any],
                        inv_id: str) -> Optional[dict[str, Any]]:
    """Read-only intel for one investigation via its transaction."""
    inv = next((i for i in state.get("investigations", [])
                if i.get("investigation_id") == inv_id), None)
    if inv is None:
        return None
    txn_id = inv.get("transaction_id", "")
    linked = transaction_intel(state, txn_id) if txn_id else None
    return {
        "investigation_id": inv_id,
        "transaction_id": txn_id or UNKNOWN,
        "transaction_intel": linked or {"status": NOT_AVAILABLE},
        "isolation": "observations reachable only through this "
                     "investigation's own transaction linkage",
        "synthetic": True,
        "limitations": [
            "No observation from another investigation is included.",
            "IP/geolocation values are unavailable without a provider.",
        ],
    }


def compare_account_geo(state: dict[str, Any],
                        account_id: str) -> dict[str, Any]:
    """Cautious geo comparison over one account's observations.

    Fixture labels carry no coordinates, so fixture input honestly
    yields INSUFFICIENT_EVIDENCE. Coordinate-bearing comparisons run
    only on supplied LocationObservation pairs via compare_pair.
    """
    obs = [o for o in geo_mod.build_label_observations(state)
           if o["account_id"] == account_id]
    if len(obs) < 2:
        return {"outcome": "INSUFFICIENT_EVIDENCE",
                "missing": ["fewer_than_two_observations"],
                "fraud_determination": "none",
                "note": "fixture labels carry no coordinates"}
    return {"outcome": "INSUFFICIENT_EVIDENCE",
            "missing": ["no_coordinate_bearing_observations"],
            "fraud_determination": "none",
            "note": "fixture labels carry no coordinates"}


def compare_pair(first: dict[str, Any],
                 second: dict[str, Any]) -> dict[str, Any]:
    """Compare two supplied observation dicts (analytical, read-only)."""
    try:
        first_obs = geo_mod.LocationObservation(**first)
        second_obs = geo_mod.LocationObservation(**second)
    except Exception as exc:
        return {"outcome": "UNKNOWN", "missing": ["invalid_input"],
                "fraud_determination": "none",
                "note": f"input validation failed: {type(exc).__name__}"}
    raw = geo_mod.compare_observations(first_obs, second_obs)
    return {"outcome": _COMPARE_MAP.get(raw["outcome"], "UNKNOWN"),
            "distance_km": raw.get("distance_km"),
            "missing": raw.get("missing", []),
            "fraud_determination": "none",
            "note": raw.get("note", "")}
