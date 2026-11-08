"""Global Identity Verification Engine (§4).

Twelve evidence categories, twelve result statuses, explainable
factor-based assessment — no numeric score implying legal certainty.
Reference checks need an authorized provider (none connected:
UNAVAILABLE); record_consistency evaluates INTERNAL logic of
supplied attributes only (never a positive identity proof).
Supplied PII values are never persisted: factors cite attribute
NAMES + results, subjects persist masked + hashed.
"""
from __future__ import annotations

import time
from typing import Any, Callable

from app import intel_common as common

TYPES = (
    "gov_id",
    "national_id",
    "passport",
    "drivers_licence",
    "business_identity",
    "bank_kyc",
    "name_match",
    "dob_match",
    "address_match",
    "phone_match",
    "document_authenticity",
    "record_consistency",
)

VERIFIED = "VERIFIED"
PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
NOT_VERIFIED = "NOT_VERIFIED"
UNVERIFIED = "UNVERIFIED"
UNAVAILABLE = "UNAVAILABLE"
PROVIDER_ERROR = "PROVIDER_ERROR"
AUTHORIZATION_REQUIRED = "AUTHORIZATION_REQUIRED"
CONSENT_REQUIRED = "CONSENT_REQUIRED"
UNSUPPORTED_COUNTRY = "UNSUPPORTED_COUNTRY"
UNSUPPORTED_DOCUMENT = "UNSUPPORTED_DOCUMENT"
EXPIRED_EVIDENCE = "EXPIRED_EVIDENCE"
MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"

STATES = (VERIFIED, PARTIALLY_VERIFIED, NOT_VERIFIED, UNVERIFIED,
          UNAVAILABLE, PROVIDER_ERROR, AUTHORIZATION_REQUIRED,
          CONSENT_REQUIRED, UNSUPPORTED_COUNTRY, UNSUPPORTED_DOCUMENT,
          EXPIRED_EVIDENCE, MANUAL_REVIEW_REQUIRED)

SUPPORTED_COUNTRIES = ("NG", "US", "UK", "FR", "KE", "ZW", "ZA")
TTL_DAYS = 30

TYPE_ADAPTERS: dict[str, tuple[str, ...]] = {
    "gov_id": ("identity-document",),
    "national_id": ("identity-document",),
    "passport": ("identity-document",),
    "drivers_licence": ("identity-document",),
    "business_identity": ("identity-kyc",),
    "bank_kyc": ("identity-kyc",),
    "name_match": ("identity-kyc",),
    "dob_match": ("identity-kyc",),
    "address_match": ("identity-kyc", "address-validation"),
    "phone_match": ("identity-kyc",),
    "document_authenticity": ("identity-document",),
    "record_consistency": (),
}

Responder = Callable[[dict[str, Any]], dict[str, Any]]


def _factors_consistency(attributes: dict[str, Any]):
    """Internal-logic contradictions in SUPPLIED attributes only."""
    factors = []
    contradictions = []
    dob = str(attributes.get("dob", "") or "")
    if dob:
        from datetime import date as _date

        if len(dob) != 10 or dob[4] != "-" or dob[7] != "-":
            contradictions.append("dob-malformed")
        elif dob > _date.today().isoformat():
            contradictions.append("dob-in-future")
        else:
            factors.append({"factor": "dob-plausible", "result": "pass",
                            "evidence_ref": "supplied:dob",
                            "reliability": "supplied-only"})
    issued = str(attributes.get("issued_at", "") or "")
    expires = str(attributes.get("expires_at", "") or "")
    if issued and expires and expires < issued:
        contradictions.append("expiry-before-issue")
    for name in contradictions:
        factors.append({"factor": name, "result": "fail",
                        "evidence_ref": "supplied-attributes",
                        "reliability": "supplied-only"})
    return factors, contradictions


def run_verification(store, verify_type: str, subject_ref: str,
                     attributes: dict[str, Any] | None,
                     country: str, purpose: str, org: str, user: str,
                     tenant_id: str, investigation_id: str = "",
                     responder: Responder | None = None,
                     now: float | None = None) -> dict[str, Any]:
    from app import intel_auth as authz_mod
    from app import telecom_providers as prov_mod

    if verify_type not in TYPES:
        raise ValueError("VERIFY_TYPE_UNKNOWN: %r" % (verify_type,))
    purpose = common.check_purpose(purpose)
    org, user = common.actor_name(org, user)
    subject_ref = (subject_ref or "").strip()
    if not subject_ref or len(subject_ref) > 120:
        raise ValueError("SUBJECT_REQUIRED: subject ref 1..120 chars")
    country = (country or "").strip().upper()
    moment = time.time() if now is None else now
    seq = int(store.state.get("identity_seq", 0)) + 1
    store.state["identity_seq"] = seq
    record: dict[str, Any] = {
        "verification_id": "idv_%06d" % seq,
        "tenant_id": tenant_id, "investigation_id": investigation_id[:80],
        "subject_hash": common.subject_hash(subject_ref),
        "subject_masked": common.mask_ref(subject_ref),
        "provider_id": "", "verify_type": verify_type,
        "verification_status": UNAVAILABLE, "previous_status": "",
        "country": country, "factors": [], "missing": [],
        "limitations": [], "evidence_reference": "",
        "attributes_checked": sorted((attributes or {}).keys())[:20],
        "verified_at": common.utc(moment), "verified_ts": moment,
        "expires_at": moment + TTL_DAYS * 86400,
        "purpose": purpose, "org": org, "user": user,
        "synthetic": False,
    }
    if country not in SUPPORTED_COUNTRIES:
        record["verification_status"] = UNSUPPORTED_COUNTRY
        record["limitations"] = ["country %s has no assessed provider "
                                 "coverage" % (country or "blank")]
        return _save(store, record)
    if authz_mod.valid_authorization(store, record["subject_hash"],
                                     purpose, moment) is None:
        record["verification_status"] = AUTHORIZATION_REQUIRED
        record["limitations"] = ["approved intelligence authorization "
                                 "required; no provider contacted"]
        return _save(store, record)
    if verify_type == "record_consistency":
        return _save(store, _consistency(record, attributes or {}))
    adapters = TYPE_ADAPTERS[verify_type]
    live = None
    for adapter in adapters:
        live = prov_mod.live_connection(store, adapter, tenant_id)
        if live is not None:
            break
    if live is not None:
        record["provider_id"] = live.get("adapter", "")
        record["verification_status"] = PROVIDER_ERROR
        record["limitations"] = ["live connection present but no "
                                 "provider call implementation; no "
                                 "provider contacted"]
        return _save(store, record)
    if responder is None:
        record["verification_status"] = UNAVAILABLE
        record["missing"] = ["authorized %s provider"
                             % ("/".join(adapters) or "identity")]
        record["limitations"] = ["requires live provider (%s); no "
                                 "live connection"
                                 % (", ".join(adapters))]
        return _save(store, record)
    try:
        response = responder({"verify_type": verify_type,
                              "country": country})
    except Exception as exc:  # noqa: BLE001 - normalized, never leaks
        record["verification_status"] = PROVIDER_ERROR
        record["limitations"] = ["provider failure: %s"
                                 % type(exc).__name__]
        return _save(store, record)
    return _save(store, _apply_response(record, response))


def _consistency(record, attributes):
    factors, contradictions = _factors_consistency(attributes)
    record["factors"] = factors
    if contradictions:
        record["verification_status"] = NOT_VERIFIED
        record["limitations"] = ["supplied record contradicts itself; "
                                 "this is not an identity proof"]
    else:
        record["verification_status"] = UNVERIFIED
        record["missing"] = ["authorized reference source"]
        record["limitations"] = ["internally consistent but confirmed "
                                 "by no source; not an identity proof"]
    return record


def _apply_response(record, response):
    if not isinstance(response, dict):
        record["verification_status"] = PROVIDER_ERROR
        record["limitations"] = ["malformed provider response; "
                                 "treated as provider error"]
        return record
    want = str(response.get("state", "PROVIDER_ERROR")).upper()
    if want not in STATES or want in (AUTHORIZATION_REQUIRED,
                                      CONSENT_REQUIRED,
                                      EXPIRED_EVIDENCE):
        record["verification_status"] = PROVIDER_ERROR
        record["limitations"] = ["provider returned no usable state"]
        return record
    record["verification_status"] = want
    record["synthetic"] = bool(response.get("synthetic", True))
    record["provider_id"] = str(response.get("provider", ""))[:80]
    record["evidence_reference"] = str(response.get("ref", ""))[:120]
    factors = response.get("factors", [])
    record["factors"] = factors if isinstance(factors, list) else []
    missing = response.get("missing", [])
    record["missing"] = missing if isinstance(missing, list) else []
    limits = response.get("limitations", [])
    record["limitations"] = (limits if isinstance(limits, list)
                             else []) + (["synthetic test response; no "
                                          "live provider contacted"]
                                         if record["synthetic"] else [])
    return record


def _save(store, record):
    common.seal(record)
    store.state.setdefault("identity_verifications", {})[
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
