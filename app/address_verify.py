"""Global Address Verification Engine (§8).

Verifies a SUPPLIED address against authorized sources. Never
discovers addresses, never upgrades geocoding to VERIFIED, never
claims occupancy. Provider matching needs a live adapter (none
connected: UNAVAILABLE); structural checks alone cap at UNVERIFIED.
Full-address disclosure is role-tiered at the API layer.
"""
from __future__ import annotations

import time
from typing import Any
from collections.abc import Callable

from app import intel_common as common

VERIFIED = "VERIFIED"
PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
UNVERIFIED = "UNVERIFIED"
NOT_MATCHED = "NOT_MATCHED"
UNAVAILABLE = "UNAVAILABLE"
PROVIDER_ERROR = "PROVIDER_ERROR"
MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
EXPIRED = "EXPIRED"
AUTHORIZATION_REQUIRED = "AUTHORIZATION_REQUIRED"

STATES = (VERIFIED, PARTIALLY_VERIFIED, UNVERIFIED, NOT_MATCHED,
          UNAVAILABLE, PROVIDER_ERROR, MANUAL_REVIEW_REQUIRED,
          EXPIRED, AUTHORIZATION_REQUIRED)

FIELDS = ("country", "region", "state_province", "district",
          "city", "postal_code", "street", "building",
          "unit", "latitude", "longitude", "classification")

SUPPORTED_COUNTRIES = ("NG", "US", "UK", "FR", "KE", "ZW", "ZA")
TTL_DAYS = 30

Responder = Callable[[dict[str, Any]], dict[str, Any]]


def validate_structure(address: dict[str, Any]) -> list[str]:
    """Structural problems (format only; never a verification)."""
    problems = []
    if not isinstance(address, dict):
        return ["address-must-be-object"]
    country = str(address.get("country", "") or "").strip().upper()
    if country not in SUPPORTED_COUNTRIES:
        problems.append("country-unsupported-or-missing")
    if not str(address.get("city", "") or "").strip():
        problems.append("city-missing")
    if not str(address.get("street", "") or "").strip():
        problems.append("street-missing")
    from app import geo_intel as geo_mod

    lat = address.get("latitude")
    lon = address.get("longitude")
    if lat not in (None, "") or lon not in (None, ""):
        try:
            numbers = (float(lat), float(lon))
        except (TypeError, ValueError):
            problems.append("coordinates-not-numeric")
            return problems
        valid, reason = geo_mod.validate_coordinates(*numbers)
        if not valid:
            problems.append(reason.lower().replace("_", "-"))
    return problems


def mask_address(address: dict[str, Any]) -> dict[str, Any]:
    """Minimized view: city/region/country + masked street only."""
    if not isinstance(address, dict):
        return {"country": "", "region": "", "state_province": "",
                "district": "", "city": "", "street_masked": "",
                "has_coordinates": False}
    street = str(address.get("street", "") or "")
    masked = common.mask_ref(street, keep=0) if street else ""
    return {"country": address.get("country", ""),
            "region": address.get("region", ""),
            "state_province": address.get("state_province", ""),
            "district": address.get("district", ""),
            "city": address.get("city", ""),
            "street_masked": masked,
            "has_coordinates": address.get("latitude") not in (None, "")
            and address.get("longitude") not in (None, "")}


def run_verification(store, address: dict[str, Any],
                     subject_ref: str, method: str, purpose: str,
                     org: str, user: str, tenant_id: str,
                     investigation_id: str = "",
                     geocoded_only: bool = False,
                     responder: Responder | None = None,
                     now: float | None = None) -> dict[str, Any]:
    from app import intel_auth as authz_mod
    from app import telecom_providers as prov_mod

    purpose = common.check_purpose(purpose)
    org, user = common.actor_name(org, user)
    subject_ref = (subject_ref or "").strip()
    if not subject_ref or len(subject_ref) > 120:
        raise ValueError("SUBJECT_REQUIRED: subject ref 1..120 chars")
    method = (method or "").strip()[:80] or "unspecified"
    moment = time.time() if now is None else now
    seq = int(store.state.get("address_seq", 0)) + 1
    store.state["address_seq"] = seq
    record: dict[str, Any] = {
        "verification_id": "adr_%06d" % seq,
        "tenant_id": tenant_id, "investigation_id": investigation_id[:80],
        "subject_hash": common.subject_hash(subject_ref),
        "subject_masked": common.mask_ref(subject_ref),
        "address": {k: str(address.get(k, ""))[:200] for k in FIELDS
                    if isinstance(address, dict)
                    and k in address},
        "address_masked": mask_address(address or {}),
        "provider_id": "", "verification_method": method,
        "verification_status": UNAVAILABLE, "previous_status": "",
        "match_result": {}, "limitations": [],
        "evidence_reference": "",
        "verified_at": common.utc(moment), "verified_ts": moment,
        "expires_at": moment + TTL_DAYS * 86400,
        "purpose": purpose, "org": org, "user": user,
        "synthetic": False,
    }
    problems = validate_structure(address)
    if problems:
        record["verification_status"] = NOT_MATCHED
        record["match_result"] = {"structural_problems": problems}
        record["limitations"] = ["supplied address fails structural "
                                 "validation; no provider contacted"]
        return _save(store, record)
    if authz_mod.valid_authorization(store, record["subject_hash"],
                                     purpose, moment) is None:
        record["verification_status"] = AUTHORIZATION_REQUIRED
        record["limitations"] = ["approved intelligence authorization "
                                 "required; no provider contacted"]
        return _save(store, record)
    if geocoded_only:
        record["verification_status"] = UNVERIFIED
        record["match_result"] = {"geocoded": True}
        record["limitations"] = ["geocoding only interprets coordinates; "
                                 "it never verifies an address"]
        return _save(store, record)
    conn = prov_mod.live_connection(store, "address-validation",
                                    tenant_id)
    if conn is not None:
        record["provider_id"] = "address-validation"
        record["verification_status"] = PROVIDER_ERROR
        record["limitations"] = ["live connection present but no "
                                 "provider call implementation; no "
                                 "provider contacted"]
        return _save(store, record)
    if responder is None:
        record["verification_status"] = UNAVAILABLE
        record["limitations"] = ["requires live address-validation "
                                 "provider; no live connection"]
        return _save(store, record)
    try:
        response = responder({"method": method,
                              "country": record["address"].get(
                                  "country", "")})
    except Exception:  # noqa: BLE001 - normalized, never leaks
        record["verification_status"] = PROVIDER_ERROR
        record["limitations"] = ["provider failure (type withheld)"]
        return _save(store, record)
    return _save(store, _apply_response(record, response))


def _apply_response(record, response):
    if not isinstance(response, dict):
        record["verification_status"] = PROVIDER_ERROR
        record["limitations"] = ["malformed provider response"]
        return record
    want = str(response.get("state", "PROVIDER_ERROR")).upper()
    if want not in STATES or want in (AUTHORIZATION_REQUIRED,
                                      EXPIRED):
        record["verification_status"] = PROVIDER_ERROR
        record["limitations"] = ["provider returned no usable state"]
        return record
    record["verification_status"] = want
    record["synthetic"] = bool(response.get("synthetic", True))
    record["provider_id"] = str(response.get("provider", ""))[:80]
    record["evidence_reference"] = str(response.get("ref", ""))[:120]
    match = response.get("match", {})
    record["match_result"] = match if isinstance(match, dict) else {}
    limits = response.get("limitations", [])
    record["limitations"] = (limits if isinstance(limits, list)
                             else []) + (["synthetic test response; no "
                                          "live provider contacted"]
                                         if record["synthetic"] else [])
    return record


def _save(store, record):
    common.seal(record)
    store.state.setdefault("address_verifications", {})[
        record["verification_id"]] = record
    store._save()
    return record


def is_expired(record: dict[str, Any],
               now: float | None = None) -> bool:
    import time as _time

    moment = _time.time() if now is None else now
    try:
        return float(record.get("expires_at", 0.0)) <= moment
    except (TypeError, ValueError):
        return True
