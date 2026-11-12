"""Location observations (§6.2/§6.3, §12.4): authorized sources only.

Accepted sources: explicitly consented app sharing, authorized
operator location services, approved institutional feeds, lawfully
acquired terminal data, or a documented other source with a
reference. Unknown accuracy stays unknown. Every observation needs
an approved authorization; consented-app sources additionally need
a live consent record. No tracking from phone numbers alone —
no such source exists here.
"""
from __future__ import annotations

import time
from typing import Any

from app import intel_common as common

SOURCES = (
    "consented-app",
    "operator-service",
    "institutional-feed",
    "terminal-data",
    "documented-other",
)

METHODS = ("gnss", "network", "terminal", "geocode", "manual", "unknown")

TTL_DAYS = 90


def validate_observation(payload: dict[str, Any]) -> list[str]:
    problems = []
    if not isinstance(payload, dict):
        return ["observation-must-be-object"]
    if payload.get("source_type") not in SOURCES:
        problems.append("source-type-not-authorized")
    else:
        if payload["source_type"] == "documented-other" and not str(
                payload.get("source_reference", "") or "").strip():
            problems.append("documented-other-needs-reference")
    from app import geo_intel as geo_mod

    try:
        numbers = (float(payload.get("latitude")),
                   float(payload.get("longitude")))
    except (TypeError, ValueError):
        problems.append("coordinates-required-numeric")
    else:
        valid, reason = geo_mod.validate_coordinates(*numbers)
        if not valid:
            problems.append(reason.lower().replace("_", "-"))
    accuracy = payload.get("accuracy_meters")
    if accuracy not in (None, "", "unknown"):
        try:
            candidate = float(accuracy)
        except (TypeError, ValueError):
            problems.append("accuracy-not-numeric")
        else:
            from app import geo_intel as geo_mod

            if not geo_mod.validate_accuracy_radius(candidate):
                problems.append("accuracy-invalid")
    if payload.get("method", "unknown") not in METHODS:
        problems.append("method-unknown-vocabulary")
    observed = str(payload.get("observed_at", "") or "")
    received = str(payload.get("received_at", "") or "")
    if not observed or not received:
        problems.append("observed-and-received-required")
    elif received < observed:
        problems.append("received-before-observed")
    return problems


def record_observation(store, payload: dict[str, Any],
                       subject_ref: str, purpose: str, org: str,
                       user: str, tenant_id: str,
                       investigation_id: str = "",
                       device_ref: str = "",
                       now: float | None = None) -> dict[str, Any]:
    from app import intel_auth as authz_mod

    purpose = common.check_purpose(purpose)
    org, user = common.actor_name(org, user)
    subject_ref = (subject_ref or "").strip()
    if not subject_ref or len(subject_ref) > 120:
        raise ValueError("SUBJECT_REQUIRED: subject ref 1..120 chars")
    problems = validate_observation(payload or {})
    if problems:
        raise ValueError("OBSERVATION_INVALID: %s"
                         % (", ".join(problems),))
    moment = time.time() if now is None else now
    digest = common.subject_hash(subject_ref)
    if authz_mod.valid_authorization(store, digest, purpose,
                                     moment) is None:
        raise ValueError("AUTHORIZATION_REQUIRED: approved "
                         "intelligence authorization required")
    if payload["source_type"] == "consented-app" and (
            authz_mod.valid_consent(store, digest, purpose,
                                    moment) is None):
        raise ValueError("CONSENT_REQUIRED: live subject consent "
                         "required for app-shared location")
    seq = int(store.state.get("location_seq", 0)) + 1
    store.state["location_seq"] = seq
    accuracy = payload.get("accuracy_meters")
    record = {
        "observation_id": "loc_%06d" % seq,
        "tenant_id": tenant_id, "investigation_id": investigation_id[:80],
        "subject_hash": digest,
        "subject_masked": common.mask_ref(subject_ref),
        "device_reference": (device_ref or "").strip()[:80],
        "source_type": payload["source_type"],
        "provider_id": str(payload.get("provider_id", ""))[:80],
        "latitude": float(payload["latitude"]),
        "longitude": float(payload["longitude"]),
        "accuracy_meters": ("unknown" if accuracy in (None, "", "unknown")
                            else float(accuracy)),
        "observed_at": str(payload["observed_at"]),
        "received_at": str(payload["received_at"]),
        "timezone": str(payload.get("timezone", ""))[:40],
        "method": payload.get("method", "unknown"),
        "verification_status": "AUTHORIZED_OBSERVATION",
        "authorization_reference": "",
        "consent_reference": "",
        "evidence_reference": str(payload.get("evidence_reference",
                                              ""))[:120],
        "expires_at": moment + TTL_DAYS * 86400,
        "created_at": common.utc(moment),
    }
    authz = authz_mod.valid_authorization(store, digest, purpose, moment)
    record["authorization_reference"] = authz["authorization_id"]
    consent = authz_mod.valid_consent(store, digest, purpose, moment)
    if consent is not None:
        record["consent_reference"] = consent["consent_id"]
    common.seal(record)
    store.state.setdefault("location_observations", {})[
        record["observation_id"]] = record
    store._save()
    return record
