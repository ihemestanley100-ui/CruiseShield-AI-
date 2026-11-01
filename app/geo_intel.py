"""Geolocation Intelligence Foundation (DI-05, additive derived layer).

Provider-neutral contracts for IP-derived approximate geolocation and
permission-based device location, plus validation, confidence/freshness
classification, and safe comparison logic. Reuses DI-04 IP parsing and
classification; introduces no second IP system.

Honesty rules: the default NullProvider reports unavailable/unknown and
performs zero network calls; non-public IPs are never resolved; unknown
stays unknown; approximate locations are never presented as verified
physical locations. No persistence, no risk changes, no evidence or
graph writes. Device-location collection is NOT implemented here:
only the permission/consent contract exists, and actual collection
needs separate approval plus privacy review.
"""
from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Any, Optional, Protocol

from pydantic import BaseModel, Field

from app import ip_intel as ip_mod

LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
COUNTRY_RE = re.compile(r"^[A-Z]{2}$")

UNKNOWN = "unknown"

# Freshness policy (seconds); configurable, documented, conservative.
FRESH_WITHIN_S = 24 * 3600
STALE_WITHIN_S = 30 * 24 * 3600

# Non-public IP categories the engine must never resolve (§4.1).
UNRESOLVABLE_CATEGORIES = {
    "private", "loopback", "link_local", "reserved", "multicast", UNKNOWN,
}

PERMISSION_STATES = {"granted", "denied", "prompt", "unsupported",
                     "revoked", UNKNOWN}
CONSENT_STATES = {"granted", "denied", "withdrawn", "not_requested",
                  UNKNOWN}
CONFIDENCE_LEVELS = {"high", "medium", "low", "none", UNKNOWN}
FRESHNESS_LEVELS = {"fresh", "stale", "expired", UNKNOWN}


class GeoResult(BaseModel):
    """One IP-geolocation lookup outcome (approximate, never exact)."""

    status: str = "unavailable"  # "resolved" | "unavailable"
    reason: str = ""
    source: str = "none"  # provider name or "none"
    ip: str = ""
    country_code: str = UNKNOWN
    country: str = UNKNOWN
    region: str = UNKNOWN
    city: str = UNKNOWN
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: str = UNKNOWN
    accuracy_radius_km: Optional[float] = None
    confidence: str = UNKNOWN
    provider: str = "null_provider"
    dataset_version: str = UNKNOWN
    observed_at: str = ""
    external_lookup_performed: bool = False
    approximate_only: bool = True


class DeviceLocation(BaseModel):
    """Permission-based device-location contract (no collection here)."""

    permission: str = UNKNOWN
    consent: str = UNKNOWN
    collection_method: str = UNKNOWN
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy_radius_m: Optional[float] = None
    observed_at: str = ""
    device_ref: str = ""
    session_ref: str = ""
    source: str = UNKNOWN
    provenance: str = ""
    synthetic: bool = True


class LocationObservation(BaseModel):
    """One location observation for comparison (either pathway)."""

    obs_id: str
    pathway: str = UNKNOWN  # "ip_derived" | "device" | "unknown"
    label: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    observed_at: str = ""
    confidence: str = UNKNOWN
    source: str = UNKNOWN
    synthetic: bool = True


class GeoProvider(Protocol):
    """Vendor-neutral IP-geolocation interface (offline-safe)."""

    name: str

    def lookup(self, ip: str) -> Optional[dict[str, Any]]:
        """Return a raw provider record, or None when out of scope."""
        ...  # pragma: no cover - interface


class NullProvider:
    """Safe default: unknown/unavailable, zero network calls."""

    name = "null_provider"

    def lookup(self, ip: str) -> Optional[dict[str, Any]]:
        return None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(value: str) -> Optional[datetime]:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(
            tzinfo=timezone.utc)
    except (ValueError, AttributeError, TypeError):
        return None


def validate_coordinates(latitude: Any,
                         longitude: Any) -> tuple[bool, str]:
    """Validate a coordinate pair; never coerce invalid into valid."""
    for name, value in (("latitude", latitude), ("longitude", longitude)):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False, f"INVALID_{name.upper()}_TYPE"
        if not math.isfinite(value):
            return False, f"NON_FINITE_{name.upper()}"
    if not -90 <= latitude <= 90:
        return False, "LATITUDE_OUT_OF_RANGE"
    if not -180 <= longitude <= 180:
        return False, "LONGITUDE_OUT_OF_RANGE"
    return True, "ok"


def validate_country_code(value: Any) -> bool:
    """ISO-3166 alpha-2 shape check (unknown handled by callers)."""
    return isinstance(value, str) and COUNTRY_RE.match(value) is not None


def validate_accuracy_radius(value: Any) -> bool:
    """Non-negative finite number (None means not supplied)."""
    if value is None:
        return True
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value) and value >= 0


def classify_confidence(record: dict[str, Any]) -> str:
    """Conservative confidence from source metadata (never from coords).

    High requires explicit provider accuracy data; bare coordinates
    without provenance cap at low; nothing supplied yields unknown.
    """
    if not record:
        return UNKNOWN
    if record.get("confidence_override") in CONFIDENCE_LEVELS:
        return str(record["confidence_override"])
    accuracy = record.get("accuracy_radius_km")
    provider = record.get("provider")
    if provider and validate_accuracy_radius(accuracy) \
            and accuracy is not None and accuracy <= 25:
        return "high"
    if provider and accuracy is not None \
            and validate_accuracy_radius(accuracy):
        return "medium"
    if record.get("latitude") is not None \
            and record.get("longitude") is not None:
        return "low"
    return UNKNOWN


def classify_freshness(observed_at: str,
                       now: Optional[datetime] = None) -> str:
    """Freshness from observation timestamp; missing/future is unknown."""
    parsed = _parse_ts(observed_at)
    if parsed is None:
        return UNKNOWN
    ref = now or _now()
    age = (ref - parsed).total_seconds()
    if age < 0:
        return UNKNOWN
    if age <= FRESH_WITHIN_S:
        return "fresh"
    if age <= STALE_WITHIN_S:
        return "stale"
    return "expired"


def resolve_ip(ip: str,
               provider: Optional[GeoProvider] = None) -> GeoResult:
    """Resolve public IPs via provider; everything else is unavailable."""
    active = provider or NullProvider()
    classification = ip_mod.classify_ip(ip)
    if not classification["valid"]:
        return GeoResult(status="unavailable", reason="invalid_ip", ip=ip)
    if classification["category"] != "public":
        return GeoResult(status="unavailable",
                         reason=f"unsupported_category:"
                                f"{classification['category']}", ip=ip)
    try:
        record = active.lookup(classification["compressed"])
    except Exception as exc:  # provider failure is unavailable, not fatal
        return GeoResult(status="unavailable", reason="provider_error",
                         ip=ip, provider=active.name)
    if not record:
        return GeoResult(status="unavailable", reason="no_provider_data",
                         ip=ip, provider=active.name)
    lat, lon = record.get("latitude"), record.get("longitude")
    ok, _ = validate_coordinates(lat, lon)
    if not ok:
        return GeoResult(status="unavailable",
                         reason="provider_malformed_coordinates",
                         ip=ip, provider=active.name)
    country = record.get("country_code", UNKNOWN)
    return GeoResult(
        status="resolved", reason="ok", source=active.name, ip=ip,
        country_code=country if validate_country_code(country) else UNKNOWN,
        country=str(record.get("country", UNKNOWN)),
        region=str(record.get("region", UNKNOWN)),
        city=str(record.get("city", UNKNOWN)),
        latitude=float(lat), longitude=float(lon),
        timezone=str(record.get("timezone", UNKNOWN)),
        accuracy_radius_km=record.get("accuracy_radius_km"),
        confidence=classify_confidence({**record, "provider": active.name}),
        provider=active.name,
        dataset_version=str(record.get("dataset_version", UNKNOWN)),
        observed_at=str(record.get("observed_at", "")),
        external_lookup_performed=bool(
            record.get("external_lookup_performed", False)),
        approximate_only=True)


def validate_label(label: str) -> str:
    """Validate a geo fixture label; raise ValueError when malformed."""
    if not isinstance(label, str) or not LABEL_RE.match(label):
        raise ValueError(f"INVALID_GEO_LABEL: {label!r}")
    return label


def build_label_observations(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive label observations from event location_id (unknown geo)."""
    observations = []
    for event in state.get("events", []):
        entities = event.get("entities", {}) or {}
        label = entities.get("location_id")
        if not label:
            continue
        txn = event.get("transaction", {}) or {}
        observations.append({
            "obs_id": f"obs_geo_{event.get('event_id', '?')}",
            "location_label": str(label),
            "geo_status": "unavailable",
            "reason": "no_provider_data",
            "account_id": txn.get("sender_account_id"),
            "txn_id": txn.get("transaction_id"),
            "observed_at": str(event.get("occurred_at", "")),
            "source_ref": str(event.get("event_id", "")),
            "synthetic": True})
    observations.sort(key=lambda o: (o["observed_at"], o["obs_id"]))
    return observations


def haversine_km(lat_a: float, lon_a: float, lat_b: float,
                 lon_b: float) -> float:
    """Great-circle distance in km (analytical helper, not a verdict)."""
    radius = 6371.0
    p1, p2 = math.radians(lat_a), math.radians(lat_b)
    step = math.radians(lon_b - lon_a)
    delta = math.radians(lat_b - lat_a)
    inner = (math.sin(delta / 2) ** 2
             + math.cos(p1) * math.cos(p2) * math.sin(step / 2) ** 2)
    return 2 * radius * math.asin(math.sqrt(inner))


def compare_observations(first: LocationObservation,
                         second: LocationObservation) -> dict[str, Any]:
    """Compare two observations; fail safe with explained gaps.

    Outcomes: same_location | different_location | conflicting |
    stale_input | insufficient_evidence. Analytical only: never a
    fraud determination, never a risk score.
    """
    missing: list[str] = []
    for name, obs in (("first", first), ("second", second)):
        if obs.latitude is None or obs.longitude is None:
            missing.append(f"{name}_coordinates_missing")
        if not obs.observed_at or _parse_ts(obs.observed_at) is None:
            missing.append(f"{name}_timestamp_missing_or_invalid")
    if missing:
        return {"outcome": "insufficient_evidence", "missing": missing,
                "fraud_determination": "none",
                "note": "comparison requires valid coordinates and "
                        "timestamps on both observations"}
    assert first.latitude is not None and first.longitude is not None
    assert second.latitude is not None and second.longitude is not None
    if classify_freshness(first.observed_at) == "expired" \
            or classify_freshness(second.observed_at) == "expired":
        return {"outcome": "stale_input",
                "missing": ["expired_observation_present"],
                "fraud_determination": "none",
                "note": "expired observations cannot support comparison"}
    low_conf = {"low", "none", UNKNOWN}
    if first.confidence in low_conf or second.confidence in low_conf:
        return {"outcome": "insufficient_evidence",
                "missing": ["low_or_unknown_confidence"],
                "fraud_determination": "none",
                "note": "low-confidence inputs cannot support comparison"}
    distance = haversine_km(first.latitude, first.longitude,
                            second.latitude, second.longitude)
    if first.pathway != second.pathway and distance > 100:
        return {"outcome": "conflicting", "distance_km": distance,
                "missing": [],
                "fraud_determination": "none",
                "note": "pathways disagree beyond tolerance; investigate "
                        "sources, do not conclude fraud"}
    if distance <= 100:
        return {"outcome": "same_location", "distance_km": distance,
                "missing": [], "fraud_determination": "none",
                "note": "observations agree within tolerance"}
    return {"outcome": "different_location", "distance_km": distance,
            "missing": [], "fraud_determination": "none",
            "note": "analytical difference only; not proof of anything"}
