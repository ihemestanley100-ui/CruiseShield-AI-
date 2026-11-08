"""Address verification engine: structure, gates, geocode cap."""
import pytest

from app import address_verify as addr
from app import intel_auth as authz_mod
from app import intel_common as common

PURPOSE = "CUSTOMER_IDENTITY_VERIFICATION"
SUBJECT = "CUST-UNIT-001"
GOOD = {"country": "NG", "city": "Lagos", "street": "1 Marina Rd",
        "latitude": 6.45, "longitude": 3.39}


def _authorize(store, subject=SUBJECT):
    record = authz_mod.create_authorization(
        store, "org_primary", "inv_84721", "investigator-1", subject,
        PURPOSE, "NDPA s.25 KYC onboarding", "NG",
        "address verification")
    return authz_mod.decide_authorization(
        store, record["authorization_id"], "boss", True, "ref-2")


def _run(store, address=None, subject=SUBJECT, geocoded_only=False,
         responder=None):
    return addr.run_verification(
        store, GOOD if address is None else address, subject,
        "kyc-record-match", PURPOSE, "org_primary",
        "investigator-1", "org_primary",
        investigation_id="inv_84721", geocoded_only=geocoded_only,
        responder=responder)


def test_states_enumerated():
    assert len(addr.STATES) == 9


def test_structural_failures_not_matched(tmp_store):
    for bad in ({"country": "NG"}, {"country": "XX", "city": "x",
                                    "street": "y"},
                dict(GOOD, latitude=999),
                dict(GOOD, latitude="far"),
                "not-a-dict"):
        record = _run(tmp_store, address=bad)
        assert record["verification_status"] == addr.NOT_MATCHED
        assert record["match_result"]["structural_problems"]


def test_requires_authorization(tmp_store):
    record = _run(tmp_store)
    assert record["verification_status"] == addr.AUTHORIZATION_REQUIRED


def test_geocoded_only_caps_at_unverified(tmp_store):
    _authorize(tmp_store)
    record = _run(tmp_store, geocoded_only=True)
    assert record["verification_status"] == addr.UNVERIFIED
    assert "never verifies" in " ".join(record["limitations"])


def test_unavailable_without_provider(tmp_store):
    _authorize(tmp_store)
    record = _run(tmp_store)
    assert record["verification_status"] == addr.UNAVAILABLE


def test_responder_mapping_and_bad_states(tmp_store):
    _authorize(tmp_store)
    record = _run(tmp_store, responder=lambda req: {
        "state": "PARTIALLY_VERIFIED", "provider": "test-double",
        "synthetic": True, "match": {"city": "match"},
        "limitations": ["street unmatched"]})
    assert record["verification_status"] == addr.PARTIALLY_VERIFIED
    assert record["match_result"] == {"city": "match"}
    assert record["synthetic"] is True
    record = _run(tmp_store, responder=lambda req: {"state": "MAYBE"})
    assert record["verification_status"] == addr.PROVIDER_ERROR


def test_masked_view_hides_street(tmp_store):
    masked = addr.mask_address(GOOD)
    assert masked["city"] == "Lagos"
    assert masked["country"] == "NG"
    assert "Marina" not in masked["street_masked"]
    assert masked["has_coordinates"] is True


def test_expiry_and_integrity(tmp_store):
    _authorize(tmp_store)
    record = _run(tmp_store)
    assert common.check_integrity(record) is True
    assert addr.is_expired(record) is False
    assert addr.is_expired(record, record["expires_at"] + 1) is True


def test_input_validation(tmp_store):
    with pytest.raises(ValueError):
        addr.run_verification(tmp_store, GOOD, SUBJECT,
                              "kyc-record-match", "BOGUS", "o", "u",
                              "org_primary")
    with pytest.raises(ValueError):
        _run(tmp_store, subject="")
