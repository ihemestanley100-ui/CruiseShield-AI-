"""Location observations: validation, gates, unknown accuracy."""
import pytest

from app import intel_auth as authz_mod
from app import location_obs as loc

PURPOSE = "AUTHORIZED_FRAUD_INVESTIGATION"
SUBJECT = "SUBJ-UNIT-001"
GOOD = {"source_type": "terminal-data", "latitude": 6.5244,
        "longitude": 3.3792, "accuracy_meters": 150.0,
        "observed_at": "2026-11-01T10:00:00Z",
        "received_at": "2026-11-01T10:05:00Z", "method": "terminal",
        "provider_id": "terminal-feed", "evidence_reference": "t-9"}


def _authorize(store, subject=SUBJECT):
    record = authz_mod.create_authorization(
        store, "org_primary", "inv_84721", "investigator-1", subject,
        PURPOSE, "court order CO-12", "NG", "location evidence")
    return authz_mod.decide_authorization(
        store, record["authorization_id"], "boss", True, "CO-12")


def _record(store, payload=None, subject=SUBJECT):
    return loc.record_observation(
        store, GOOD if payload is None else payload, subject,
        PURPOSE, "org_primary", "investigator-1", "org_primary",
        investigation_id="inv_84721", device_ref="dev_04")


def test_validation_matrix(tmp_store):
    cases = [
        (dict(GOOD, source_type="phone-number-ping"),
         "source-type-not-authorized"),
        (dict(GOOD, latitude=91), "latitude-out-of-range"),
        (dict(GOOD, longitude="far"), "coordinates-required-numeric"),
        (dict(GOOD, observed_at="", received_at=""),
         "observed-and-received-required"),
        (dict(GOOD, observed_at="2026-11-02T00:00:00Z",
              received_at="2026-11-01T00:00:00Z"),
         "received-before-observed"),
        (dict(GOOD, accuracy_meters=-5), "accuracy-invalid"),
        (dict(GOOD, source_type="documented-other"),
         "documented-other-needs-reference"),
    ]
    for payload, problem in cases:
        assert problem in loc.validate_observation(payload), payload


def test_requires_authorization(tmp_store):
    with pytest.raises(ValueError) as exc:
        _record(tmp_store)
    assert "AUTHORIZATION_REQUIRED" in str(exc.value)


def test_consented_app_needs_live_consent(tmp_store):
    _authorize(tmp_store)
    payload = dict(GOOD, source_type="consented-app")
    with pytest.raises(ValueError) as exc:
        _record(tmp_store, payload=payload)
    assert "CONSENT_REQUIRED" in str(exc.value)
    authz_mod.record_consent(
        tmp_store, "org_primary", SUBJECT, PURPOSE,
        "in-app prompt v3", "investigator-1", "org_primary")
    record = _record(tmp_store, payload=payload)
    assert record["consent_reference"].startswith("tcon_")


def test_unknown_accuracy_preserved(tmp_store):
    _authorize(tmp_store)
    payload = dict(GOOD)
    del payload["accuracy_meters"]
    record = _record(tmp_store, payload=payload)
    assert record["accuracy_meters"] == "unknown"


def test_record_fields_and_refs(tmp_store):
    _authorize(tmp_store)
    record = _record(tmp_store)
    assert record["observation_id"].startswith("loc_")
    assert record["authorization_reference"].startswith("iauth_")
    assert record["verification_status"] == "AUTHORIZED_OBSERVATION"
    assert record["device_reference"] == "dev_04"
    assert SUBJECT not in str(record)
    from app import intel_common as common

    assert common.check_integrity(record) is True
