"""Universal core: taxonomy, institutions, parties, typologies, alerts,
tracing, alt-payments, reports. Real modules, tmp_store persistence."""
from __future__ import annotations

import pytest

import app.main as main  # noqa: F401  (store fixture binding)
from app import alerts, altpayments, institutions, parties
from app import payment_methods as pm
from app import reports, tracing, typologies


def _txn(**kw):
    base = {"transaction_id": "t1", "channel": "NIP",
            "amount_minor": 1000, "currency": "NGN",
            "sender_account_id": "a1", "receiver_account_id": "a2"}
    base.update(kw)
    return base


# -- payment taxonomy -------------------------------------------------
def test_taxonomy_nine_families():
    assert len(pm.FAMILIES) == 9
    assert len(pm.LIFECYCLE) == 14
    assert len(pm.list_methods()) >= 13


def test_classify_provider_reported_ok():
    out = pm.classify(_txn(payment_method="nip_instant"))
    assert out["method_id"] == "nip_instant"
    assert out["confidence"] == "provider-reported"


def test_classify_unknown_brand_stays_unknown():
    out = pm.classify(_txn(payment_method="BogusPay"))
    assert out["method_id"] == "UNKNOWN"


def test_classify_channel_hint_labelled():
    out = pm.classify(_txn())
    assert out["method_id"] == "nip_instant"
    assert out["confidence"] == "inferred-from-channel"


def test_classify_no_evidence_unknown():
    out = pm.classify({"transaction_id": "x"})
    assert out["method_id"] == "UNKNOWN"


def test_classify_qr_channel_hint():
    # E-1: QR channel infers the registered qr_checkout method.
    out = pm.classify(_txn(channel="QR"))
    assert out["method_id"] == "qr_checkout"
    assert out["confidence"] == "inferred-from-channel"


def test_lifecycle_mapping_preserves_original():
    mapped = pm.map_lifecycle("nip", "successful")
    assert mapped["canonical"] == "SETTLED" and mapped["mapped"] is True
    unmapped = pm.map_lifecycle("mystery", "weird")
    assert unmapped["canonical"] == "UNKNOWN"
    assert unmapped["provider_status"] == "weird"


# -- institutions ------------------------------------------------------
def test_networks_honest_status():
    rows = institutions.list_networks()
    assert len(rows) >= 8
    assert all(r["verification_status"] == "UNVERIFIED" for r in rows)
    assert all(r["integration_status"] in ("NOT_INTEGRATED", "REGISTERED")
               for r in rows)


def test_identify_unknown_network():
    out = institutions.identify(_txn(network="Bank of Atlantis"))
    assert out["institution_id"] == "UNKNOWN"
    out2 = institutions.identify(_txn())
    assert out2["institution_id"] == "UNKNOWN"


def test_identify_known_network():
    out = institutions.identify(_txn(network="net_nip"))
    assert out["institution_id"] == "net_nip"


# -- parties ------------------------------------------------------------
def test_extract_parties_masked():
    found = parties.extract_parties(
        _txn(merchant_id="m9", sender_name="Ada"))
    roles = {p["role"] for p in found}
    assert {"SENDER", "RECIPIENT", "MERCHANT"} <= roles
    sender = next(p for p in found if p["role"] == "SENDER")
    assert sender["reference_masked"] != "a1"
    assert sender["verification"] == "UNVERIFIED"


def test_resolve_exact_match():
    out = parties.resolve({"sender_account_id": "a1"},
                          {"sender_account_id": "a1"})
    assert out["decision"] == "RESOLVED"
    assert out["human_review"] is False


def test_resolve_conflict_ambiguous():
    out = parties.resolve(
        {"sender_account_id": "a1", "customer_id": "c1"},
        {"sender_account_id": "a1", "customer_id": "c2"})
    assert out["decision"] == "AMBIGUOUS"
    assert out["human_review"] is True
    assert out["evidence"] and out["conflicts"]


def test_resolve_conflict_only_no_match():
    out = parties.resolve({"sender_account_id": "a1"},
                          {"sender_account_id": "a2"})
    assert out["decision"] == "NO_MATCH"
    assert out["conflicts"]


def test_resolve_shared_signal_only_supported():
    out = parties.resolve({"device_id": "d1"}, {"device_id": "d1"})
    assert out["decision"] == "SUPPORTED_ONLY"


def test_resolve_no_match():
    assert parties.resolve({"device_id": "d1"},
                           {"device_id": "d2"})["decision"] == "NO_MATCH"


# -- typologies ----------------------------------------------------------
def test_forty_typologies_valid_mapping():
    rows = typologies.list_typologies()
    assert len(rows) == 40
    assert all(not t["mapping_errors"] for t in rows)
    gaps = [t for t in rows if t["detection_gap"]]
    assert gaps, "gap typologies must be honestly flagged"
    assert all(t["typology_id"] for t in gaps)


def test_signals_for_gap_typology_empty():
    gap = next(t for t in typologies.list_typologies()
               if t["detection_gap"])
    sig = {"signal_id": "s1", "detector_family": "VELOCITY",
           "detail": "R-002 x"}
    assert typologies.signals_for_typology(gap["typology_id"], [sig]) == []


def test_signals_for_mapped_typology():
    sig = {"signal_id": "s1", "detector_family": "VELOCITY",
           "detail": "R-002 rapid", "transaction_id": "t1"}
    matched = typologies.signals_for_typology("T-01", [sig])
    assert len(matched) == 1


def test_typology_industry_filter():
    rows = typologies.list_typologies("crypto-assets")
    assert rows and all("crypto-assets" in t["industries"] for t in rows)


# -- alerts ---------------------------------------------------------------
def test_alert_lifecycle(tmp_store):
    sig = {"signal_id": "s9", "transaction_id": "t1",
           "detector_family": "VELOCITY", "severity": "high"}
    first = alerts.open_from_signal(tmp_store, sig)
    assert first["status"] == "opened"
    assert first["alert"]["notified"] is False
    dup = alerts.open_from_signal(tmp_store, sig)
    assert dup["status"] == "duplicate"
    row = alerts.transition(tmp_store, "fraud_s9", "TRIAGED", "analyst")
    assert row["status"] == "TRIAGED"
    with pytest.raises(ValueError):
        alerts.transition(tmp_store, "fraud_s9", "CLOSED", "analyst")
    with pytest.raises(ValueError):
        alerts.transition(tmp_store, "fraud_nope", "TRIAGED", "analyst")
    with pytest.raises(ValueError):
        alerts.open_from_signal(tmp_store, {})


def test_alert_metrics(tmp_store):
    sig = {"signal_id": "s10", "transaction_id": "t1",
           "detector_family": "VELOCITY", "severity": "low"}
    alerts.open_from_signal(tmp_store, sig)
    m = alerts.metrics(tmp_store)
    assert m["total"] >= 1
    assert "calculated_at" in m and "window" in m


# -- tracing ---------------------------------------------------------------
def _legs():
    return [
        _txn(transaction_id="t1", receiver_account_id="mid"),
        _txn(transaction_id="t2", sender_account_id="mid",
             receiver_account_id="end"),
        _txn(transaction_id="t3", sender_account_id="else",
             receiver_account_id="other", currency="USD"),
    ]


def test_link_strength_ladder():
    legs = _legs()
    strong = tracing.link_strength(legs[0], legs[1])
    assert strong["status"] == "STRONGLY_SUPPORTED_LINK"
    none = tracing.link_strength(legs[0], legs[2])
    assert none["status"] == "NO_MATCH"
    a = _txn(provider_reference="px")
    b = _txn(transaction_id="t2", provider_reference="px")
    assert tracing.link_strength(a, b)["status"] == "CONFIRMED_LINK"
    c = _txn(transaction_id="t3", device_id="d1")
    d = _txn(transaction_id="t4", device_id="d1",
             sender_account_id="x", receiver_account_id="y")
    assert tracing.link_strength(c, d)["status"] == "UNVERIFIED_LINK"


def test_build_trace_bfs_and_limits():
    trace = tracing.build_trace(_legs(), [], "t1")
    assert trace["origin_transaction"] == "t1"
    assert len(trace["movements"]) == 1
    assert trace["movements"][0]["status"] == "STRONGLY_SUPPORTED_LINK"
    assert isinstance(trace["limitations"], list)
    capped = tracing.build_trace(_legs(), [], "t1", max_hops=0)
    assert capped["movements"] == []
    assert capped["limitations"], "hop cap must surface unknown downstream"
    with pytest.raises(ValueError):
        tracing.build_trace(_legs(), [], "nope")


def test_trace_persists(tmp_store):
    trace = tracing.build_trace(_legs(), [], "t1")
    tmp_store.trace_save(trace)
    assert any(t["trace_id"] == trace["trace_id"]
               for t in tmp_store.traces())


# -- alt payments ------------------------------------------------------------
def test_alt_capabilities_honest():
    caps = altpayments.capabilities()
    assert caps["crypto"]["chain_data"] == "PROVIDER_UNAVAILABLE"
    assert caps["gift_card"]["issuer_lookup"] == "PROVIDER_UNAVAILABLE"
    assert caps["remittance"]["provider_lookup"] == "PROVIDER_UNAVAILABLE"


def test_crypto_validation_unknown_entity():
    out = altpayments.validate_crypto_transfer(
        "ethereum", "0x" + "ab" * 20)
    assert out["attribution"] == "UNKNOWN_ENTITY"


def test_gift_secrets_rejected():
    with pytest.raises(ValueError):
        altpayments.gift_card_event("issuer", "REDEMPTION", "code: 1234-56")
    with pytest.raises(ValueError):
        altpayments.gift_card_event("issuer", "MINT", "ref")
    ok = altpayments.gift_card_event("issuer", "PURCHASE", "rcpt-1")
    assert ok["final_recipient"] == "UNKNOWN"


def test_remittance_record():
    with pytest.raises(ValueError):
        altpayments.remittance_event("WU", "r1", "TELEPORTED")
    ok = altpayments.remittance_event("WU", "r1", "SENT")
    assert ok["provenance"].startswith("provider-supplied")


# -- reports ------------------------------------------------------------------
def test_reports_all_types_build():
    bundle = {"transactions": [{"id": "t1"}], "limitations": ["none"]}
    for rtype in reports.REPORT_TYPES:
        out = reports.build(rtype, bundle, investigation_id="i1")
        assert out["report_type"] == rtype
        assert "generated_at" in out
    assert len(reports.REPORT_TYPES) == 15


def test_report_gaps_explicit():
    out = reports.build("tracing", {})
    assert "trace" in out["evidence_gaps"]
    with pytest.raises(ValueError):
        reports.build("mind_reading", {})
