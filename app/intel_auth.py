"""Intelligence authorizations (§12.8) + shared consent records.

Authorizations gate sensitive identity/location/address processing.
Consent reuses the telecom_consents table (ONE consent system):
records gain consent_method + withdrawn_at additively; the telecom
endpoint and readers are unchanged and backward compatible.
"""
from __future__ import annotations

import time
from typing import Any

from app import intel_common as common

PENDING = "PENDING"
APPROVED = "APPROVED"
REVOKED = "REVOKED"
EXPIRED_VIEW = "EXPIRED"


def create_authorization(store, tenant_id: str, investigation_id: str,
                         requester: str, subject_ref: str,
                         purpose: str, legal_basis: str,
                         country: str, scope: str,
                         ttl_days: int = 30,
                         now: float | None = None) -> dict[str, Any]:
    purpose = common.check_purpose(purpose)
    basis = (legal_basis or "").strip()
    if not basis or len(basis) > 120:
        raise ValueError("LEGAL_BASIS_REQUIRED: documented basis "
                         "1..120 chars (country-specific, never "
                         "defaulted)")
    scope = (scope or "").strip()
    if not scope or len(scope) > 200:
        raise ValueError("SCOPE_REQUIRED: 1..200 chars")
    moment = time.time() if now is None else now
    seq = int(store.state.get("intel_authz_seq", 0)) + 1
    store.state["intel_authz_seq"] = seq
    record = {
        "authorization_id": "iauth_%06d" % seq,
        "tenant_id": tenant_id,
        "investigation_id": (investigation_id or "").strip()[:80],
        "requester_id": (requester or "").strip()[:80],
        "subject_hash": common.subject_hash(subject_ref),
        "subject_masked": common.mask_ref(subject_ref),
        "purpose": purpose, "legal_basis_type": basis,
        "country": (country or "").strip().upper()[:2],
        "authorization_status": PENDING, "approving_authority": "",
        "authorization_reference": "",
        "scope": scope, "issued_at": moment,
        "expires_at": moment + max(1, min(ttl_days, 365)) * 86400,
        "revoked_at": 0.0,
        "created_at": common.utc(moment),
    }
    common.seal(record)
    store.state.setdefault("intel_authorizations", {})[
        record["authorization_id"]] = record
    store._save()
    return record


def decide_authorization(store, authorization_id: str, approver: str,
                         approve: bool,
                         reference: str = "") -> dict[str, Any] | None:
    record = store.state.get("intel_authorizations", {}).get(
        authorization_id)
    if not isinstance(record, dict):
        return None
    if record.get("authorization_status") != PENDING:
        raise ValueError("AUTHORIZATION_DECIDED: already %s"
                         % record.get("authorization_status"))
    record["authorization_status"] = APPROVED if approve else REVOKED
    record["approving_authority"] = (approver or "").strip()[:80]
    record["authorization_reference"] = (reference or "").strip()[:120]
    if not approve:
        import time as _time

        record["revoked_at"] = _time.time()
    common.seal(record)
    store._save()
    return record


def valid_authorization(store, subject_hash: str, purpose: str,
                        now: float | None = None) -> dict[str, Any] | None:
    moment = time.time() if now is None else now
    for record in store.state.get("intel_authorizations", {}).values():
        if not isinstance(record, dict):
            continue
        if record.get("subject_hash") != subject_hash:
            continue
        if record.get("purpose") != purpose:
            continue
        if record.get("authorization_status") != APPROVED:
            continue
        if float(record.get("expires_at", 0.0)) <= moment:
            continue
        return record
    return None


def record_consent(store, tenant_id: str, subject_ref: str,
                   purpose: str, consent_method: str,
                   granted_by: str, org: str,
                   ttl_days: int = 30,
                   now: float | None = None) -> dict[str, Any]:
    """Shared consent record (telecom_consents table, extended fields)."""
    purpose = common.check_purpose(purpose)
    method = (consent_method or "").strip()
    if not method or len(method) > 80:
        raise ValueError("CONSENT_METHOD_REQUIRED: 1..80 chars")
    moment = time.time() if now is None else now
    record = {"consent_id": "tcon_%06d" % store.telecom_next_seq(),
              "subject_hash": common.subject_hash(subject_ref),
              "subject_masked": common.mask_ref(subject_ref),
              "purpose": purpose, "org": (org or "").strip()[:80],
              "granted_by": (granted_by or "").strip()[:80],
              "granted_at": moment,
              "expires_ts": moment + max(1, min(ttl_days, 90)) * 86400,
              "revoked": False, "tenant_id": tenant_id,
              "consent_method": method, "withdrawn_at": 0.0}
    store.telecom_consent_save(record)
    return record


def withdraw_consent(store, subject_hash: str,
                     purpose: str) -> dict[str, Any] | None:
    import time as _time

    for record in store.state.get("telecom_consents", {}).values():
        if not isinstance(record, dict):
            continue
        if record.get("subject_hash") != subject_hash:
            continue
        if record.get("purpose") != purpose:
            continue
        if record.get("revoked"):
            continue
        record["revoked"] = True
        record["withdrawn_at"] = _time.time()
        store._save()
        return record
    return None


def valid_consent(store, subject_hash: str, purpose: str,
                  now: float | None = None) -> dict[str, Any] | None:
    moment = time.time() if now is None else now
    consent = store.telecom_consent_for(subject_hash, purpose)
    if consent is None:
        return None
    try:
        if float(consent.get("expires_ts", 0.0)) <= moment:
            return None
    except (TypeError, ValueError):
        return None
    return consent
