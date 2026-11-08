"""Telecom verification engine: 11 services, states, evidence, staleness.

Derived paths prove from platform state; provider-only paths without a
provider return UNAVAILABLE. Harness paths prove the live-call shape
with synthetic-labeled responses. Raw E.164 never persists.
"""
import time

import pytest

import app.main as main  # noqa: F401  (store fixture binding)
from app import telecom_providers as prov_mod
from app import telecom_verify as tv

E164 = "+2348031234567"
PURPOSE = "fraud-investigation-case-1"


def _run(store, verify_type, e164=E164, context=None, harness=None,
         script=None, now=None, purpose=PURPOSE):
    return tv.run_verification(
        store, store.state, verify_type, e164, purpose, "org_primary",
        "investigator-1", "org_primary", context=context or {},
        harness=harness, script=script, now=now)


def _loopback(store):
    from app import connectors as conn_mod

    record = conn_mod.create_connection("loopback", "t",
                                        "org_primary")
    conn_mod.begin_verify(record)
    record, ok = conn_mod.complete_verify(record)
    assert ok
    store.connection_save(record)
    return record


def test_all_eleven_types_enumerated():
    assert len(tv.TYPES) == 11
    assert set(tv.TTL_HOURS) == set(tv.TYPES)
    assert len(tv.STATES) == 9


def test_carrier_identification_partial_never_full(tmp_store):
    record = _run(tmp_store, "carrier_identification")
    assert record["state"] == tv.PARTIALLY_VERIFIED
    assert record["operator_id"] == "mtn-ng"
    assert record["source"] == prov_mod.INFERRED
    assert "portability" in " ".join(record["limitations"])


def test_carrier_unknown_market_unavailable(tmp_store):
    record = _run(tmp_store, "carrier_identification",
                  e164="+14155552671")
    assert record["state"] == tv.UNAVAILABLE
    assert record["operator_id"] is None


def test_unsupported_calling_code(tmp_store):
    record = _run(tmp_store, "carrier_identification",
                  e164="+99912345678")
    assert record["state"] == tv.UNSUPPORTED_OPERATOR
    assert record["country"] is None


def test_provider_only_types_unavailable_without_provider(tmp_store):
    # sim_ownership/kyc_match are consent-gated (covered separately).
    for verify_type in ("current_network", "number_verification",
                        "sim_swap", "number_recycling", "device_swap",
                        "roaming", "network_type"):
        record = _run(tmp_store, verify_type)
        assert record["state"] == tv.UNAVAILABLE, verify_type
        assert "no live connection" in " ".join(
            record["limitations"]).lower() or record["limitations"]


def test_kyc_needs_consent_then_provider(tmp_store):
    record = _run(tmp_store, "kyc_match")
    assert record["state"] == tv.CONSENT_REQUIRED
    assert record["provider"] == "none"
    main.telecom_consent_create({"e164": E164, "purpose": PURPOSE},
                                _req())
    record = _run(tmp_store, "kyc_match")
    assert record["state"] == tv.UNAVAILABLE  # consent ok, no provider


def test_sim_ownership_needs_consent(tmp_store):
    record = _run(tmp_store, "sim_ownership")
    assert record["state"] == tv.CONSENT_REQUIRED


def test_tenure_derived_with_label_unavailable_without(tmp_store):
    record = _run(tmp_store, "tenure")
    assert record["state"] == tv.UNAVAILABLE
    assert "phone_label" in " ".join(record["limitations"])
    label = _seeded_phone(tmp_store)
    record = _run(tmp_store, "tenure", context={"phone_label": label})
    assert record["state"] == tv.PARTIALLY_VERIFIED
    assert record["evidence"]["observed_first"] <= record["evidence"][
        "observed_last"]
    assert "not operator billing tenure" in " ".join(
        record["limitations"])


def test_client_reported_paths_are_partial_low_confidence(tmp_store):
    record = _run(tmp_store, "roaming", context={"roaming": "yes"})
    assert record["state"] == tv.PARTIALLY_VERIFIED
    assert record["confidence"] == "LOW"
    assert record["source"] == prov_mod.CLIENT_REPORTED
    record = _run(tmp_store, "network_type",
                  context={"network_type": "4G"})
    assert record["state"] == tv.PARTIALLY_VERIFIED
    record = _run(tmp_store, "sim_swap",
                  context={"last_swap_at": "2026-01-01"})
    assert record["state"] == tv.PARTIALLY_VERIFIED
    assert "unconfirmed" in " ".join(record["limitations"])


def test_kyc_rejects_client_self_report(tmp_store):
    main.telecom_consent_create({"e164": E164, "purpose": PURPOSE},
                                _req())
    record = _run(tmp_store, "kyc_match",
                  context={"self_declared_match": "yes"})
    assert record["state"] == tv.UNAVAILABLE


def test_harness_verified_labeled_synthetic(tmp_store):
    _loopback(tmp_store)
    harness = prov_mod.TelecomHarness()
    record = _run(tmp_store, "sim_swap", harness=harness,
                  script={"result": "VERIFIED", "confidence": "HIGH",
                          "api": "sim-swap", "api_version": "v1"})
    assert record["state"] == tv.VERIFIED
    assert record["synthetic"] is True
    assert record["provider"] == "harness-loopback"
    assert record["source"] == prov_mod.HARNESS


def test_harness_bad_script_is_provider_error(tmp_store):
    _loopback(tmp_store)
    harness = prov_mod.TelecomHarness()
    record = _run(tmp_store, "sim_swap", harness=harness,
                  script={"result": "MAYBE"})
    assert record["state"] == tv.PROVIDER_ERROR


def test_harness_outage_is_provider_error(tmp_store):
    _loopback(tmp_store)
    harness = prov_mod.TelecomHarness()
    harness.fail_next()
    record = _run(tmp_store, "sim_swap", harness=harness,
                  script={"result": "VERIFIED"})
    assert record["state"] == tv.PROVIDER_ERROR


def test_harness_without_loopback_refuses(tmp_store):
    harness = prov_mod.TelecomHarness()
    record = _run(tmp_store, "sim_swap", harness=harness,
                  script={"result": "VERIFIED"})
    assert record["state"] == tv.PROVIDER_ERROR


def test_evidence_record_has_all_required_fields(tmp_store):
    record = _run(tmp_store, "carrier_identification")
    for field in ("verification_id", "subject_masked", "subject_hash",
                  "operator_id", "country", "provider", "api",
                  "api_version", "verify_type", "state",
                  "provider_ref", "verified_at", "freshness_ttl_hours",
                  "confidence", "limitations", "consent_id", "purpose",
                  "org", "user", "tenant_id", "record_hash"):
        assert field in record, field
    assert E164 not in str(record)
    assert tv.check_integrity(record) is True


def test_integrity_mismatch_detected(tmp_store):
    record = _run(tmp_store, "carrier_identification")
    tampered = dict(record)
    tampered["state"] = tv.VERIFIED
    assert tv.check_integrity(tampered) is False


def test_stale_evaluation(tmp_store):
    record = _run(tmp_store, "number_verification",
                  harness=None, now=time.time() - 7200)
    assert record["state"] == tv.UNAVAILABLE
    assert tv.is_stale(record) is True  # 1h TTL
    fresh = _run(tmp_store, "carrier_identification")
    assert tv.is_stale(fresh) is False  # 30d TTL


def test_masking_and_hashing():
    masked = tv.mask_e164("+2348031234567")
    assert masked.startswith("+234")
    assert masked.endswith("67")
    assert "0312345" not in masked
    assert tv.hash_subject(E164) == tv.hash_subject(E164)
    assert len(tv.hash_subject(E164)) == 64


def test_input_validation(tmp_store):
    with pytest.raises(ValueError):
        _run(tmp_store, "nope")
    with pytest.raises(ValueError):
        _run(tmp_store, "tenure", e164="bogus")
    with pytest.raises(ValueError):
        _run(tmp_store, "tenure", purpose="")
    with pytest.raises(ValueError):
        tv.run_verification(tmp_store, tmp_store.state, "tenure",
                            E164, PURPOSE, "", "u", "org_primary")


def test_full_evaluation_perf(tmp_store):
    start = time.perf_counter()
    for verify_type in tv.TYPES:
        _run(tmp_store, verify_type)
    elapsed = time.perf_counter() - start
    assert elapsed < 5.0


def _seeded_phone(store):
    for txn in store.state.get("transactions", []) or []:
        if isinstance(txn, dict) and txn.get("phone_id"):
            return str(txn["phone_id"])
    raise AssertionError("seed must contain a phone_id transaction")


def _req():
    from starlette.requests import Request

    return Request({"type": "http", "method": "POST", "scheme": "http",
                    "server": ("t", 80), "client": ("9.9.9.9", 1234),
                    "path": "/x", "query_string": b"",
                    "headers": [(b"host", b"t")]})
