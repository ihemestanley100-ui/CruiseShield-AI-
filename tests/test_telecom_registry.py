"""Telecom registry: versioning, coverage honesty, numbering, portability.

No live network exists here: every code/range carries provenance and
confidence, and lookups outside registry knowledge return UNKNOWN with
an explicit reason — never invented.
"""
import pytest

from app import telecom_registry as reg


REQUIRED_OPERATORS = (
    "mtn-ng", "glo-ng", "airtel-ng", "t2-ng", "tmobile-us",
    "verizon-us", "att-us", "vodafone-uk", "orange-fr",
    "safaricom-ke", "econet-zw",
)


def test_registry_versioned():
    version = reg.registry_version()
    assert version["version"] == reg.REGISTRY_VERSION
    assert version["updated"] == reg.REGISTRY_UPDATED
    assert int(version["operators"]) == len(reg.OPERATORS)


def test_required_operators_present():
    ids = {op["operator_id"] for op in reg.OPERATORS}
    for required in REQUIRED_OPERATORS:
        assert required in ids


def test_every_record_has_provenance_and_explicit_apis():
    for op in reg.OPERATORS:
        assert op["country"] and op["name"]
        prov = op["provenance"]
        assert prov["source"] and prov["confidence"]
        assert prov["registry_version"] == reg.REGISTRY_VERSION
        assert op["coverage_status"] == "registry-only"
        assert set(op["apis"]) == set(reg.TRACKED_APIS)
        for api, row in op["apis"].items():
            assert row["status"] in ("NOT_CONNECTED", "NOT_APPLICABLE",
                                     "CONNECTED"), api
            assert row["note"]
        assert op["portability_support"] in (True, False, "unknown")


def test_no_operator_claims_live_api():
    for op in reg.OPERATORS:
        for api, row in op["apis"].items():
            assert row["status"] != "CONNECTED", (op["operator_id"], api)


def test_mtn_only_api_scoped():
    assert (reg.get_operator("mtn-ng")["apis"]["mtn_sim_verification"]
            ["status"] == "NOT_CONNECTED")
    assert (reg.get_operator("att-us")["apis"]["mtn_sim_verification"]
            ["status"] == "NOT_APPLICABLE")


def test_list_filter_and_get():
    assert {op["country"] for op in reg.list_operators("ng")} == {"NG"}
    assert len(reg.list_operators("NG")) == 4
    assert reg.get_operator("MTN-NG")["name"] == "MTN Nigeria"
    assert reg.get_operator("nope") is None


def test_normalize_e164_and_local_ng():
    assert reg.normalize_e164("+2348031234567") == "+2348031234567"
    assert reg.normalize_e164("08031234567") == "+2348031234567"
    assert reg.normalize_e164("  +1-415-555-2671 ") == "+14155552671"
    for bad in ("", "abc", "123", "+999", "+" + "1" * 16, None, 42):
        with pytest.raises(ValueError):
            reg.normalize_e164(bad)


def test_country_inference():
    assert reg.country_for_e164("+2348031234567") == "NG"
    assert reg.country_for_e164("+14155552671") == "US"
    assert reg.country_for_e164("+442071234567") == "UK"
    assert reg.country_for_e164("+33123456789") == "FR"
    assert reg.country_for_e164("+254712123456") == "KE"
    assert reg.country_for_e164("+263771234567") == "ZW"
    assert reg.country_for_e164("+27821234567") == "ZA"
    assert reg.country_for_e164("+99912345678") is None


def test_ng_allocation_lookup():
    hit = reg.allocation_lookup("+2348031234567")
    assert hit["operator_id"] == "mtn-ng"
    assert "portability" in hit["limitation"]
    assert reg.allocation_lookup("08051234567")["operator_id"] == "glo-ng"
    assert (reg.allocation_lookup("+2348021234567")["operator_id"]
            == "airtel-ng")
    assert reg.allocation_lookup("08091234567")["operator_id"] == "t2-ng"


def test_non_ng_allocation_unknown_never_guessed():
    for number in ("+14155552671", "+442071234567", "+254712123456"):
        hit = reg.allocation_lookup(number)
        assert hit["operator_id"] is None
        assert hit["country"] is not None
        assert hit["limitation"]


def test_unknown_prefix_and_country_honest():
    hit = reg.allocation_lookup("+2348001234567")
    assert hit["operator_id"] is None
    assert hit["country"] == "NG"
    hit = reg.allocation_lookup("+99912345678")
    assert hit["operator_id"] is None
    assert hit["country"] is None
