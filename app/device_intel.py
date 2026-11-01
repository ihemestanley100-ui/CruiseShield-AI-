"""Device Intelligence Foundation (DI-03, additive derived layer).

Builds device observations, profiles, history, and shared-device
attribution purely from existing state (events + USES_DEVICE graph
edges). Nothing here persists: no store writes, no migrations, no
risk-rule changes, no evidence-package changes. Observations are
explicitly distinguished from verified identity: a `device_id` seen in
demo fixtures is an observed label, never proof of identity.

Synthetic fixture attributes (type/OS/browser) are seed-gated declared
demo values for known `dev_*` ids, always labelled synthetic. Unknown
ids carry no attributes (unknown, never a negative signal).
"""
from __future__ import annotations

import re
from typing import Any, Optional

from pydantic import BaseModel, Field

DEVICE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")

IDENTITY_DISCLAIMER = (
    "Observed device label from demo fixtures; not verified device "
    "identity. Attributes below are declared synthetic demo values, "
    "not measured fingerprints."
)

# Seed-gated synthetic attributes for known demo device ids (DI-03).
# Declared values for investigator-UX demonstration only.
SYNTHETIC_DEVICE_ATTRS: dict[str, dict[str, str]] = {
    "dev_01": {"device_type": "mobile", "os_family": "Android",
               "browser_family": "Chrome"},
    "dev_02": {"device_type": "mobile", "os_family": "Android",
               "browser_family": "Chrome"},
    "dev_03": {"device_type": "desktop", "os_family": "Windows",
               "browser_family": "Edge"},
    "dev_04": {"device_type": "mobile", "os_family": "Android",
               "browser_family": "Chrome"},
    "dev_09": {"device_type": "desktop", "os_family": "Windows",
               "browser_family": "Firefox"},
}


class DeviceObservation(BaseModel):
    """One observed device reference (fact, not identity proof)."""

    obs_id: str
    device_id: str
    account_id: Optional[str] = None
    txn_id: Optional[str] = None
    observed_at: str = ""
    source: str = ""  # "seed_event" | "graph_edge"
    source_ref: str = ""  # event_id or edge_id
    synthetic: bool = True


class DeviceProfile(BaseModel):
    """Aggregated observed history for one device label."""

    device_id: str
    identity_status: str = "observed_only"
    disclaimer: str = IDENTITY_DISCLAIMER
    first_seen: str = ""
    last_seen: str = ""
    account_ids: list[str] = Field(default_factory=list)
    txn_ids: list[str] = Field(default_factory=list)
    observation_count: int = 0
    shared: bool = False
    attributes: Optional[dict[str, str]] = None
    attributes_source: str = "unknown"
    observations: list[DeviceObservation] = Field(default_factory=list)
    evidence_refs: dict[str, list[str]] = Field(default_factory=dict)


def validate_device_id(device_id: str) -> str:
    """Validate a device label; raise ValueError when malformed."""
    if not isinstance(device_id, str) or not DEVICE_ID_RE.match(device_id):
        raise ValueError(f"INVALID_DEVICE_ID: {device_id!r}")
    return device_id


def build_observations(state: dict[str, Any]) -> list[DeviceObservation]:
    """Derive observations from events + USES_DEVICE edges (no writes)."""
    observations: list[DeviceObservation] = []
    for event in state.get("events", []):
        entities = event.get("entities", {}) or {}
        device_id = entities.get("device_id")
        if not device_id:
            continue
        txn = event.get("transaction", {}) or {}
        observations.append(DeviceObservation(
            obs_id=f"obs_evt_{event.get('event_id', '?')}",
            device_id=str(device_id),
            account_id=txn.get("sender_account_id"),
            txn_id=txn.get("transaction_id"),
            observed_at=str(event.get("occurred_at", "")),
            source="seed_event",
            source_ref=str(event.get("event_id", "")),
            synthetic=True))
    for edge in state.get("edges", []):
        if edge.get("relationship_type") != "USES_DEVICE":
            continue
        observations.append(DeviceObservation(
            obs_id=f"obs_edge_{edge.get('edge_id', '?')}",
            device_id=str(edge.get("target_node_id", "")),
            account_id=str(edge.get("source_node_id", "")),
            txn_id=None,
            observed_at="",
            source="graph_edge",
            source_ref=str(edge.get("edge_id", "")),
            synthetic=True))
    observations.sort(key=lambda o: (o.observed_at, o.obs_id))
    return observations


def get_profile(state: dict[str, Any],
                device_id: str) -> Optional[DeviceProfile]:
    """Aggregate the observed profile for one device label (None if unseen)."""
    validate_device_id(device_id)
    mine = [o for o in build_observations(state) if o.device_id == device_id]
    if not mine:
        return None
    stamped = sorted(o.observed_at for o in mine if o.observed_at)
    accounts = sorted({o.account_id for o in mine if o.account_id})
    txns = sorted({o.txn_id for o in mine if o.txn_id})
    attrs = SYNTHETIC_DEVICE_ATTRS.get(device_id)
    edge_refs = sorted({o.source_ref for o in mine
                        if o.source == "graph_edge"})
    event_refs = sorted({o.source_ref for o in mine
                         if o.source == "seed_event"})
    return DeviceProfile(
        device_id=device_id,
        first_seen=stamped[0] if stamped else "",
        last_seen=stamped[-1] if stamped else "",
        account_ids=accounts, txn_ids=txns,
        observation_count=len(mine), shared=len(accounts) >= 2,
        attributes=dict(attrs) if attrs else None,
        attributes_source=("synthetic_demo_fixture" if attrs else "unknown"),
        observations=mine,
        evidence_refs={"graph_edge_ids": edge_refs,
                       "event_ids": event_refs})


def shared_devices(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Devices observed on 2+ accounts, with attribution (derived)."""
    by_device: dict[str, dict[str, Any]] = {}
    for obs in build_observations(state):
        if not obs.account_id:
            continue
        slot = by_device.setdefault(
            obs.device_id, {"device_id": obs.device_id, "accounts": set(),
                            "txn_ids": set(), "edge_ids": set(),
                            "event_ids": set()})
        slot["accounts"].add(obs.account_id)
        if obs.txn_id:
            slot["txn_ids"].add(obs.txn_id)
        if obs.source == "graph_edge":
            slot["edge_ids"].add(obs.source_ref)
        else:
            slot["event_ids"].add(obs.source_ref)
    out = []
    for device_id in sorted(by_device):
        slot = by_device[device_id]
        if len(slot["accounts"]) < 2:
            continue
        out.append({"device_id": device_id,
                    "account_ids": sorted(slot["accounts"]),
                    "txn_ids": sorted(slot["txn_ids"]),
                    "graph_edge_ids": sorted(slot["edge_ids"]),
                    "event_ids": sorted(slot["event_ids"]),
                    "identity_status": "observed_only",
                    "synthetic": True})
    return out
