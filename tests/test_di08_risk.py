"""DI-08 Candidate risk intelligence: isolation, findings, flag, AI shape.

Derived layer only. Uses tmp_store (scratch); live state untouched.
"""
from datetime import datetime, timezone

import pytest

import app.main as main
from app import risk_intel as ri
from app import rules as rules_mod

NOW = datetime(2026, 10, 27, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def flag_on(monkeypatch):
    monkeypatch.setenv("RISK_INTELLIGENCE_V2_ENABLED", "true")


@pytest.fixture()
def flag_off(monkeypatch):
    monkeypatch.delenv("RISK_INTELLIGENCE_V2_ENABLED", raising=False)


# A. Backward compatibility + flag ----------------------------------------
def test_flag_defaults_off(flag_off):
    assert ri.enabled() is False
    body = main.get_risk_intelligence("txn_84721")
    assert body["enabled"] is False
    assert body["findings"] == []
    assert "risk-score-v1" in body["detail"]


def test_flag_on_exposes_findings_only(tmp_store, flag_on):
    body = main.get_risk_intelligence("txn_84721")
    assert body["engine"] == "risk-intelligence-v2-candidate"
    assert body["numeric_score"] is None
    assert body["findings"], "expected candidate findings"


def test_v1_untouched(tmp_store, flag_on):
    assert rules_mod.SCORE_VERSION == "risk-score-v1"
    assert [r.rule_id for r in rules_mod.RULES] == [
        f"R-00{i}" for i in range(1, 9)]
    txn = main.get_transaction("txn_84721")
    assert (txn["risk_transaction"]["score"],
            txn["risk_network"]["score"]) == (35, 84)
    main.get_risk_intelligence("txn_84721")
    again = main.get_transaction("txn_84721")
    assert (again["risk_transaction"]["score"],
            again["risk_network"]["score"]) == (35, 84)


# B/C/D. Signal families ----------------------------------------------------
def test_device_signals(tmp_store):
    out = ri.assess(tmp_store.state, "transaction", "txn_84721", NOW)
    ids = {f["signal_id"] for f in out["findings"]}
    assert "DEV-KNOWN-dev_04" in ids
    assert "DEV-SHARED-dev_04" in ids
    assert "DEV-NEWNESS" in ids
    newness = next(f for f in out["findings"]
                   if f["signal_id"] == "DEV-NEWNESS")
    assert newness["status"] == "INSUFFICIENT_EVIDENCE"
    assert all(f["status"] in ri.STATUSES for f in out["findings"])


def test_ip_signals_unknown_only(tmp_store):
    out = ri.assess(tmp_store.state, "transaction", "txn_84721", NOW)
    ip_fs = [f for f in out["findings"] if f["category"] == "ip"]
    assert any(f["signal_id"] == "IP-LABEL-ip_02" for f in ip_fs)
    provider = next(f for f in ip_fs if f["signal_id"] == "IP-PROVIDER")
    assert provider["status"] == "UNAVAILABLE"
    assert provider["confidence"] == "unknown"
    assert all(f["status"] in ri.STATUSES for f in ip_fs)
    assert "MALICIOUS" not in {f["status"] for f in ip_fs}


def test_geo_signals_no_travel_conclusion(tmp_store):
    out = ri.assess(tmp_store.state, "transaction", "txn_84721", NOW)
    travel = next(f for f in out["findings"]
                  if f["signal_id"] == "GEO-TRAVEL")
    assert travel["status"] == "INSUFFICIENT_EVIDENCE"


def test_missing_coverage_signals(tmp_store):
    out = ri.assess(tmp_store.state, "transaction", "txn_84725", NOW)
    by_id = {f["signal_id"]: f for f in out["findings"]}
    assert by_id["DEV-COVERAGE"]["status"] == "INSUFFICIENT_EVIDENCE"
    assert by_id["IP-COVERAGE"]["status"] == "INSUFFICIENT_EVIDENCE"
    assert by_id["GEO-COVERAGE"]["status"] == "INSUFFICIENT_EVIDENCE"


def test_stale_when_observations_old(tmp_store):
    from datetime import timedelta
    late = NOW + timedelta(days=10)
    out = ri.assess(tmp_store.state, "transaction", "txn_84721", late)
    known = next(f for f in out["findings"]
                 if f["signal_id"] == "DEV-KNOWN-dev_04")
    assert known["status"] == "STALE"
    assert known["freshness"] == "stale"


def test_account_and_investigation_subjects(tmp_store):
    acct = ri.assess(tmp_store.state, "account", "acct_A", NOW)
    assert acct["subject"] == {"type": "account", "id": "acct_A"}
    assert any("DEV-KNOWN" in f["signal_id"] for f in acct["findings"])
    inv_id = tmp_store.state["investigations"][0]["investigation_id"]
    inv = ri.assess(tmp_store.state, "investigation", inv_id, NOW)
    assert inv["subject"]["type"] == "investigation"
    assert ri.assess(tmp_store.state, "txn", "x", NOW) is None
    assert ri.assess(tmp_store.state, "transaction", "txn_nope",
                     NOW) is None


# E. Provenance, isolation, read-only ------------------------------------------
def test_findings_carry_provenance(tmp_store):
    out = ri.assess(tmp_store.state, "transaction", "txn_84721", NOW)
    for finding in out["findings"]:
        assert finding["assessed_at"]
        assert finding["explanation"]
        assert finding["limitations"]


def test_cross_account_isolation(tmp_store):
    mine = ri.assess(tmp_store.state, "account", "acct_K", NOW)
    assert not any("DEV-KNOWN-dev_04" == f["signal_id"]
                   for f in mine["findings"])
    assert any("DEV-KNOWN-dev_01" == f["signal_id"]
               for f in mine["findings"])


def test_cross_findings_scoped_to_subject(tmp_store):
    from app import device_intel as di
    from app import ip_intel as ii
    out = ri.assess(tmp_store.state, "transaction", "txn_84721", NOW)
    xshare = next(f for f in out["findings"]
                  if f["signal_id"] == "XSHARE-SUMMARY")
    linked_dev = {s["device_id"]
                  for s in di.shared_devices(tmp_store.state)
                  if "txn_84721" in s["txn_ids"]}
    linked_ip = {s["ip_label"] for s in ii.shared_ips(tmp_store.state)
                 if "txn_84721" in s["txn_ids"]}
    if linked_dev or linked_ip:
        assert xshare["status"] == "PRESENT"
        for gid in linked_dev | linked_ip:
            assert gid in xshare["explanation"]
        all_dev = {s["device_id"]
                   for s in di.shared_devices(tmp_store.state)}
        all_ip = {s["ip_label"] for s in ii.shared_ips(tmp_store.state)}
        for gid in (all_dev - linked_dev) | (all_ip - linked_ip):
            assert gid not in xshare["explanation"], gid
    else:
        assert xshare["status"] == "UNKNOWN"
    assert "txn_84721" in xshare["explanation"]
    # A subject with no linked sharing reports UNKNOWN, never globals.
    quiet = ri.assess(tmp_store.state, "transaction", "txn_84725", NOW)
    qx = next(f for f in quiet["findings"]
              if f["signal_id"] == "XSHARE-SUMMARY")
    assert qx["status"] == "UNKNOWN"
    assert "txn_84725" in qx["explanation"]


def test_endpoint_errors_and_read_only(tmp_store, flag_on):
    with pytest.raises(main.AppError) as exc:
        main.get_risk_intelligence("xxx")
    assert exc.value.status == 400
    with pytest.raises(main.AppError) as exc2:
        main.get_risk_intelligence("txn_nope")
    assert exc2.value.status == 404
    before = dict(tmp_store.state)
    main.get_risk_intelligence("txn_84721")
    assert tmp_store.state == before
    paths = {route.path for route in main.app.routes}
    assert "/api/v1/risk-intelligence/{identifier}" in paths


# F. AI context ----------------------------------------------------------------------
def test_ai_context_grounded_ids_only(tmp_store):
    out = ri.assess(tmp_store.state, "transaction", "txn_84721", NOW)
    ctx = ri.to_ai_context(out)
    assert ctx["engine"] == ri.ENGINE_ID
    assert all(set(s) == {"signal_id", "category", "status",
                          "evidence_refs", "explanation"}
               for s in ctx["signals"])
    assert "never invent" in ctx["grounding_rule"]
    import inspect
    from app import ai_adapter
    assert "risk_intel" not in inspect.getsource(ai_adapter)


def test_deterministic_findings_without_ai(tmp_store):
    first = ri.assess(tmp_store.state, "transaction", "txn_84721", NOW)
    second = ri.assess(tmp_store.state, "transaction", "txn_84721", NOW)
    assert first == second
