"""DI-09 Evidence/provenance/AI validation: grounding, isolation, pins.

Derived layer only. Uses tmp_store (scratch); live state untouched.
"""
import pytest

import app.main as main
from app import intel_ai as iai
from app import intel_evidence as iev


def _inv(tmp_store):
    return tmp_store.state["investigations"][0]["investigation_id"]


@pytest.fixture()
def flag_on(monkeypatch):
    monkeypatch.setenv("RISK_INTELLIGENCE_V2_ENABLED", "true")


@pytest.fixture()
def flag_off(monkeypatch):
    monkeypatch.delenv("RISK_INTELLIGENCE_V2_ENABLED", raising=False)


def _valid_response(fid, eid):
    return {"key_findings": [{"finding_id": fid, "finding": "noted",
                              "evidence_ids": [eid]}],
            "conclusion": "requires_review",
            "human_review_status": "required"}


# A/B. Grounding + provenance ----------------------------------------------------
def test_findings_grounded_and_provenanced(tmp_store):
    out = iev.build_findings(tmp_store.state, "investigation",
                             _inv(tmp_store))
    assert out, "expected derived findings"
    for record in out:
        assert record["category"] in iev.CATEGORIES
        assert record["provenance"] in iev.PROVENANCE
        assert record["provenance"] != "EXTERNAL_PROVIDER_VERIFIED"
        assert record["synthetic"] is True
        assert record["derivation_method"] == "di08_signal_translation_v1"
        assert record["processed_at"] >= record["observed_at"] or \
            not record["observed_at"]
    assert iev.build_findings(tmp_store.state, "investigation",
                              "inv_nope") is None


def test_trace_chain_links(tmp_store):
    trace = iev.trace_chain(tmp_store.state, _inv(tmp_store))
    assert trace["transaction_id"] == "txn_84721"
    assert trace["findings"], "trace must carry findings"
    assert all("evidence_refs" in f for f in trace["findings"])
    assert iev.trace_chain(tmp_store.state, "inv_nope") is None


def test_audit_descriptor_appends_nothing(tmp_store):
    before = dict(tmp_store.state)
    desc = iev.audit_descriptor("intel_explain", ["DIF-X-000"])
    assert desc["outcome"] == "described_not_recorded"
    assert tmp_store.state == before


# C. AI context + validation ----------------------------------------------------------
def test_di_context_minimized(tmp_store):
    out = iev.build_findings(tmp_store.state, "investigation",
                             _inv(tmp_store))
    ctx = iai.build_di_context(out)
    assert "instruction" in ctx and "never invent" in ctx["instruction"].lower()
    blob = str(ctx)
    for banned in ("MODEL_API_KEY", "x-forwarded-for", "gps"):
        assert banned not in blob
    assert all(set(f) == {"finding_id", "signal_id", "category", "status",
                          "evidence_refs", "provenance", "confidence",
                          "freshness", "explanation", "limitations"}
               for f in ctx["findings"])


def test_response_validation_matrix(tmp_store):
    out = iev.build_findings(tmp_store.state, "investigation",
                             _inv(tmp_store))
    fid = out[0]["finding_id"]
    eids = {e for f in out for e in f["evidence_refs"]} or {"none"}
    eid = sorted(eids)[0]
    known = {"finding_ids": {fid}, "evidence_ids": {eid}}
    assert iai.validate_di_response(_valid_response(fid, eid), known)[0] \
        == "VALIDATED"
    bad_fid = _valid_response("DIF-FAKE-000", eid)
    assert iai.validate_di_response(bad_fid, known)[0] == "INVALID"
    bad_eid = _valid_response(fid, "evidence_fake_1")
    status, problems = iai.validate_di_response(bad_eid, known)
    assert status == "INVALID" and any("evidence" in p for p in problems)
    scored = _valid_response(fid, eid)
    scored["key_findings"][0]["fraud_probability"] = 0.99
    assert iai.validate_di_response(scored, known)[0] == "INVALID"
    enforcer = _valid_response(fid, eid)
    enforcer["key_findings"][0]["finding"] = "Freeze the account now"
    assert iai.validate_di_response(enforcer, known)[0] == "INVALID"
    no_review = _valid_response(fid, eid)
    del no_review["human_review_status"]
    assert iai.validate_di_response(no_review, known)[0] == "UNVERIFIED"
    assert iai.validate_di_response({"nope": True}, known)[0] == "INVALID"
    assert iai.validate_di_response("text", known)[0] == "INVALID"


def test_ai_absent_findings_available(tmp_store, monkeypatch):
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    from app import ai_adapter
    monkeypatch.setattr(ai_adapter, "MODEL_API_KEY", "")
    assert ai_adapter.configured() is False
    out = iev.build_findings(tmp_store.state, "investigation",
                             _inv(tmp_store))
    assert out, "deterministic findings must not need AI"


# D/E. Endpoint, isolation, regression pins -----------------------------------------------
def test_endpoint_flag_gated(tmp_store, flag_off):
    body = main.get_intel_evidence(_inv(tmp_store))
    assert body["enabled"] is False
    assert body["status"] == "disabled_by_flag"
    assert body["findings"] == []
    assert body["investigation_id"] == _inv(tmp_store)
    assert "trace" not in body


def test_endpoint_valid_unknown_read_only(tmp_store, flag_on):
    body = main.get_intel_evidence(_inv(tmp_store))
    assert body["findings"] and body["trace"]["findings"]
    with pytest.raises(main.AppError) as exc:
        main.get_intel_evidence("inv_nope")
    assert exc.value.status == 404
    before = dict(tmp_store.state)
    main.get_intel_evidence(_inv(tmp_store))
    assert tmp_store.state == before
    paths = {route.path for route in main.app.routes}
    assert "/api/v1/investigations/{inv_id}/intel-evidence" in paths


def test_isolation_and_pins(tmp_store):
    out = iev.build_findings(tmp_store.state, "transaction", "txn_84725")
    assert all(f["transaction_ref"] == "txn_84725" for f in out)
    txn = main.get_transaction("txn_84721")
    assert (txn["risk_transaction"]["score"],
            txn["risk_network"]["score"]) == (35, 84)
    assert main.get_graph("txn_84721")["counts"] == {"nodes": 22,
                                                    "edges": 30}
    inv = main.get_investigation("inv_84721")
    assert inv["evidence_count"] == 39
