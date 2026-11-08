"""Identity verification engine: 12 types, 12 states, no scores."""
import time

import pytest

from app import intel_auth as authz_mod
from app import intel_common as common
from app import identity_verify as idv

PURPOSE = "AUTHORIZED_FRAUD_INVESTIGATION"
SUBJECT = "IDNG-UNIT-001"


def _authorize(store, subject=SUBJECT, purpose=PURPOSE):
    record = authz_mod.create_authorization(
        store, "org_primary", "inv_84721", "investigator-1", subject,
        purpose, "NDPA s.25 fraud investigation", "NG",
        "identity verification")
    return authz_mod.decide_authorization(
        store, record["authorization_id"], "boss", True, "ref-1")


def _run(store, verify_type="passport", subject=SUBJECT,
         attributes=None, country="NG", responder=None):
    return idv.run_verification(
        store, verify_type, subject, attributes or {}, country,
        PURPOSE, "org_primary", "investigator-1", "org_primary",
        investigation_id="inv_84721", responder=responder)


def test_types_and_states_enumerated():
    assert len(idv.TYPES) == 12
    assert len(idv.STATES) == 12
    assert "record_consistency" in idv.TYPES


def test_requires_authorization(tmp_store):
    record = _run(tmp_store)
    assert record["verification_status"] == idv.AUTHORIZATION_REQUIRED
    assert record["provider_id"] == ""


def test_unsupported_country(tmp_store):
    record = _run(tmp_store, country="XX")
    assert record["verification_status"] == idv.UNSUPPORTED_COUNTRY


def test_provider_types_unavailable_without_provider(tmp_store):
    _authorize(tmp_store)
    for verify_type in ("passport", "gov_id", "bank_kyc",
                        "document_authenticity", "name_match"):
        record = _run(tmp_store, verify_type=verify_type)
        assert record["verification_status"] == idv.UNAVAILABLE, \
            verify_type
        assert record["missing"]


def test_consistency_contradiction_not_verified(tmp_store):
    _authorize(tmp_store)
    record = _run(tmp_store, verify_type="record_consistency",
                  attributes={"dob": "not-a-date",
                              "issued_at": "2026-01-01",
                              "expires_at": "2020-01-01"})
    assert record["verification_status"] == idv.NOT_VERIFIED
    assert any(f["result"] == "fail" for f in record["factors"])
    assert "not an identity proof" in " ".join(record["limitations"])


def test_consistency_clean_is_unverified_never_verified(tmp_store):
    _authorize(tmp_store)
    record = _run(tmp_store, verify_type="record_consistency",
                  attributes={"dob": "1990-05-05"})
    assert record["verification_status"] == idv.UNVERIFIED
    assert "confirmed by no source" in " ".join(record["limitations"])


def test_responder_verified_labeled_synthetic(tmp_store):
    _authorize(tmp_store)
    record = _run(tmp_store, responder=lambda req: {
        "state": "VERIFIED", "provider": "test-double",
        "ref": "t-1", "synthetic": True,
        "factors": [{"factor": "doc-check", "result": "pass",
                     "evidence_ref": "t-1",
                     "reliability": "test-double"}]})
    assert record["verification_status"] == idv.VERIFIED
    assert record["synthetic"] is True
    assert record["factors"][0]["factor"] == "doc-check"


def test_responder_garbage_is_provider_error(tmp_store):
    _authorize(tmp_store)
    record = _run(tmp_store, responder=lambda req: {"state": "MAYBE"})
    assert record["verification_status"] == idv.PROVIDER_ERROR
    record = _run(tmp_store, responder="not-callable")
    assert record["verification_status"] == idv.PROVIDER_ERROR


def test_no_numeric_score_no_pii_values(tmp_store):
    _authorize(tmp_store)
    record = _run(tmp_store, verify_type="record_consistency",
                  attributes={"dob": "1990-05-05", "name": "Jane Doe"})
    assert "score" not in record
    assert "1990-05-05" not in str(record)
    assert "Jane Doe" not in str(record)
    assert record["attributes_checked"] == ["dob", "name"]
    assert SUBJECT not in str(record)
    assert record["subject_masked"]


def test_evidence_fields_and_integrity(tmp_store):
    _authorize(tmp_store)
    record = _run(tmp_store)
    for field in ("verification_id", "tenant_id",
                  "investigation_id", "subject_hash", "subject_masked",
                  "provider_id", "verify_type", "verification_status",
                  "factors", "missing", "limitations",
                  "evidence_reference", "verified_at", "expires_at",
                  "purpose", "org", "user", "record_hash"):
        assert field in record, field
    assert common.check_integrity(record) is True


def test_expiry_evaluation(tmp_store):
    _authorize(tmp_store)
    record = _run(tmp_store)
    assert idv.is_expired(record) is False
    assert idv.is_expired(record, record["expires_at"] + 1) is True


def test_input_validation(tmp_store):
    with pytest.raises(ValueError):
        _run(tmp_store, verify_type="nope")
    with pytest.raises(ValueError):
        idv.run_verification(tmp_store, "passport", SUBJECT, {},
                             "NG", "BOGUS_PURPOSE", "o", "u",
                             "org_primary")
    with pytest.raises(ValueError):
        _run(tmp_store, subject="")
