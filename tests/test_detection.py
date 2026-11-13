"""Detection intelligence: detectors, idempotency, channels, matrix."""
import pytest
from env_probe import CAN_SOCKETS
from starlette.requests import Request

import app.config as config_mod
import app.main as main
from app import auth as auth_mod
from app import channels as chan_mod
from app import detection as det_mod
from app.tenancy import TenantContext, register_tenant

needs_sockets = pytest.mark.skipif(
    not CAN_SOCKETS,
    reason="socket creation forbidden in this sandbox; runs in CI/user envs")

_ARM_SECRET = "test-secret-detection-slice3-32ch!"
_ARM_TOKEN = "test-platform-token-detection-not-secret"
_ARM_RECORD = auth_mod.hash_password("pw-detection")


@pytest.fixture()
def txns(tmp_store):
    return tmp_store.state["transactions"]


@pytest.fixture()
def edges(tmp_store):
    return tmp_store.state["edges"]


def test_registry_lists_14_families_with_honest_status():
    # MS-DETECT-001 + MS-DETECT-003: 11 + STRUCT + DECLINE + MULE.
    body = main.list_detectors()
    assert len(body["detectors"]) == 14
    by_fam = {d["family"]: d for d in body["detectors"]}
    assert by_fam["ML_ANOMALY"]["status"] == "NOT_IMPLEMENTED"
    for fam, row in by_fam.items():
        if fam != "ML_ANOMALY":
            assert row["status"] == "OPERATIONAL", fam
        assert row["description"] and row["version"] == "1.0"


def test_rule_mapped_detectors_fire_on_seed(txns, edges):
    result = det_mod.evaluate_all(txns, edges)
    fams = {s["detector_family"] for s in result["signals"]}
    assert "RULE_MATCH" in fams
    assert result["meta"]["transactions_evaluated"] == len(txns)
    assert result["meta"]["latency_ms"] >= 0


def test_signals_pin_versions_and_provenance(txns, edges):
    result = det_mod.evaluate_all(txns, edges)
    assert result["signals"]
    for sig in result["signals"]:
        assert sig["detector_version"] == "1.0"
        assert sig["transaction_id"] and sig["occurred_at"]
        assert sig["outcome"] == "PENDING"
        if sig["rule_id"]:
            assert sig["rule_version"] == det_mod.RULE_VERSIONS.get(
                sig["rule_id"], "1.0")


def test_evaluation_is_idempotent(txns, edges):
    first = det_mod.evaluate_all(txns, edges)["signals"]
    second = det_mod.evaluate_all(txns, edges)["signals"]
    assert [s["signal_id"] for s in first] == [s["signal_id"]
                                               for s in second]


def test_cross_channel_fires_for_multichannel_senders(txns, edges):
    result = det_mod.evaluate_all(txns, edges)
    hits = [s for s in result["signals"]
            if s["detector_family"] == "CROSS_CHANNEL_PATTERN"]
    assert hits, "seed has multi-channel senders (acct_A/C/D)"
    assert all(len(s["evidence"]["channels"]) >= 2 for s in hits)


def test_geographic_zero_on_thin_seed_but_logic_works(txns, edges):
    result = det_mod.evaluate_all(txns, edges)
    assert [s for s in result["signals"]
            if s["detector_family"] == "GEOGRAPHIC_ANOMALY"] == []
    assert result["meta"]["unknown_location_txns"] == 10
    made = [
        {"transaction_id": "t1", "sender_account_id": "a",
         "receiver_account_id": "b", "channel": "WEB",
         "occurred_at": "2026-01-01T00:00:00Z", "location_id": "L1",
         "amount_minor": 1},
        {"transaction_id": "t2", "sender_account_id": "a",
         "receiver_account_id": "b", "channel": "WEB",
         "occurred_at": "2026-01-01T01:00:00Z", "location_id": "L2",
         "amount_minor": 1},
    ]
    hits = [s for s in det_mod.evaluate_all(made, [])["signals"]
            if s["detector_family"] == "GEOGRAPHIC_ANOMALY"]
    assert len(hits) == 2


def test_network_proximity_deterministic_and_shaped(txns, edges):
    first = [s for s in det_mod.evaluate_all(txns, edges)["signals"]
             if s["detector_family"] == "NETWORK_PROXIMITY"]
    second = [s for s in det_mod.evaluate_all(txns, edges)["signals"]
              if s["detector_family"] == "NETWORK_PROXIMITY"]
    assert [s["signal_id"] for s in first] == [s["signal_id"]
                                               for s in second]
    for sig in first:
        assert sig["evidence"]["shared"]


def test_empty_input_yields_measured_zero():
    result = det_mod.evaluate_all([], [])
    assert result["signals"] == []
    assert result["meta"]["transactions_evaluated"] == 0


def test_ml_anomaly_never_fires(txns, edges):
    result = det_mod.evaluate_all(txns, edges)
    assert [s for s in result["signals"]
            if s["detector_family"] == "ML_ANOMALY"] == []


def test_channel_taxonomy_mapping():
    assert chan_mod.classify("TRANSFER_NIP") == "NIP"
    assert chan_mod.classify("AGENT_AGENCY") == "AGENT"
    assert chan_mod.classify("POS") == "POS"
    # E-1: QR is the ninth canonical channel (owner-approved).
    assert chan_mod.classify("QR") == "QR"
    assert chan_mod.classify("qr") == "QR"
    assert len(chan_mod.CANONICAL) == 9
    assert chan_mod.classify("") == "UNMAPPED"
    assert chan_mod.classify(None) == "UNMAPPED"
    assert chan_mod.classify("BOGUS_RAIL") == "UNMAPPED"


def test_channels_summary_qr_canonical_zero_unmapped(tmp_store):
    # E-1 regression: the seed classifies with zero UNMAPPED now
    # that QR is canonical (txn_84731); the alert path stays live
    # for genuinely unknown codes (see bogus-rail case below).
    txns = tmp_store.state["transactions"]
    result = det_mod.evaluate_all(txns, tmp_store.state["edges"])
    summary = chan_mod.summarize(txns, result["signals"])
    by_ch = {c["channel"]: c for c in summary["channels"]}
    assert summary["unmapped_alert"] is False
    assert summary["unmapped_raw_codes"] == []
    assert "UNMAPPED" not in by_ch
    assert by_ch["QR"]["transactions"] >= 1
    assert by_ch["TRANSFER"]["transactions"] == 0
    assert "No qualifying" in by_ch["TRANSFER"]["note"]
    total = sum(c["transactions"] for c in summary["channels"])
    assert total == len(txns)
    bogus = [dict(t, transaction_id="txn_bogus", channel="BOGUS_RAIL")
             for t in txns[:1]]
    flagged = chan_mod.summarize(bogus, [])
    assert flagged["unmapped_alert"] is True
    assert flagged["unmapped_raw_codes"] == ["BOGUS_RAIL"]


def test_summary_reconciles_against_source(tmp_store):
    body = main.signals_summary()
    txns = tmp_store.state["transactions"]
    result = det_mod.evaluate_all(txns, tmp_store.state["edges"])
    assert body["total_signals"] == len(result["signals"])
    assert body["total_signals"] == sum(body["by_family"].values())
    assert body["measurement_period"]["start"] <= \
        body["measurement_period"]["end"]
    assert body["generated_at"] and body["tenant_scope"] == "org_primary"


def test_summary_respects_tenant_isolation(tmp_store, monkeypatch):
    register_tenant("org_beta")
    foreign = dict(tmp_store.state["transactions"][0])
    foreign["transaction_id"] = "txn_beta"
    foreign["tenant_id"] = "org_beta"
    tmp_store.state["transactions"].append(foreign)
    alpha = main.signals_summary()
    assert alpha["tenant_scope"] == "org_primary"
    assert alpha["evaluation"]["transactions_evaluated"] == \
        len(tmp_store.state["transactions"]) - 1
    monkeypatch.setattr(
        main, "_request_ctx",
        lambda request=None: TenantContext(tenant_id="org_beta",
                                           actor="bob"))
    beta = main.signals_summary()
    assert beta["evaluation"]["transactions_evaluated"] == 1


def test_matrix_126_cells_with_honest_statuses():
    # E-1 + MS-DETECT-001 + MS-DETECT-003: 14 x 9 channels.
    body = main.detection_matrix()
    assert len(body["cells"]) == 126
    qr = [c for c in body["cells"] if c["channel"] == "QR"]
    assert len(qr) == 14
    assert {c["status"] for c in qr if c["family"] != "ML_ANOMALY"} == \
        {"SUPPORTED_AND_ACTIVE"}
    assert [c["status"] for c in qr if c["family"] == "ML_ANOMALY"] == \
        ["NOT_YET_IMPLEMENTED"]
    vocab = {"SUPPORTED_AND_ACTIVE", "SUPPORTED_BUT_DISABLED",
             "UNSUPPORTED", "AWAITING_DATA_SOURCE",
             "NOT_YET_IMPLEMENTED", "ERROR"}
    for cell in body["cells"]:
        assert cell["status"] in vocab
        if cell["signals"]:
            assert cell["evidence_signal_id"]
            assert cell["status"] == "SUPPORTED_AND_ACTIVE"
    ml = [c for c in body["cells"] if c["family"] == "ML_ANOMALY"]
    assert ml and {c["status"] for c in ml} == {"NOT_YET_IMPLEMENTED"}
    transfer = [c for c in body["cells"] if c["channel"] == "TRANSFER"
                and c["family"] != "ML_ANOMALY"]
    assert {c["status"] for c in transfer} == {"AWAITING_DATA_SOURCE"}
    active = [c for c in body["cells"]
              if c["status"] == "SUPPORTED_AND_ACTIVE" and c["signals"]]
    assert active, "seed must yield at least one evidenced active cell"


def test_drill_down_resolves_full_provenance_chain(tmp_store):
    body = main.signals_by_transaction("txn_84721")
    assert body["transaction_id"] == "txn_84721"
    assert body["signal_count"] == len(body["signals"])
    inv = body["investigation"]
    assert inv is not None
    assert inv["transaction_id"] == "txn_84721"
    case = body["case"]
    assert case is not None
    assert case["investigation_id"] == inv["investigation_id"]
    for audit in body["audits"]:
        assert audit["target_id"] == case["case_id"]
    for sig in body["signals"]:
        assert tmp_store.get_transaction(sig["transaction_id"]) is not None


def test_drill_down_unknown_txn_is_404():
    with pytest.raises(main.AppError) as exc:
        main.signals_by_transaction("txn_nope")
    assert (exc.value.code, exc.value.status) == ("UNKNOWN_TRANSACTION",
                                                  404)


def test_drill_down_foreign_txn_is_404(tmp_store, monkeypatch):
    register_tenant("org_beta")
    monkeypatch.setattr(
        main, "_request_ctx",
        lambda request=None: TenantContext(tenant_id="org_beta",
                                           actor="bob"))
    with pytest.raises(main.AppError) as exc:
        main.signals_by_transaction("txn_84721")
    assert exc.value.status == 404


def test_drill_down_consistent_with_summary():
    summary = main.signals_summary()
    txns = main.store.state["transactions"]
    seen: set[str] = set()
    for txn in txns:
        body = main.signals_by_transaction(txn["transaction_id"])
        for sig in body["signals"]:
            assert sig["transaction_id"] == txn["transaction_id"]
            seen.add(sig["signal_id"])
    assert len(seen) == summary["total_signals"]


# -- slice-3: execution envelope, filters, buckets ----------------------


def test_signals_carry_canonical_channel_and_execution_id(txns, edges):
    result = det_mod.evaluate_all(txns, edges)
    assert result["signals"]
    allowed = set(chan_mod.CANONICAL) | {"UNMAPPED"}
    exec_ids = {s["execution_id"] for s in result["signals"]}
    assert len(exec_ids) == 1
    assert result["meta"]["execution_id"] in exec_ids
    for sig in result["signals"]:
        assert sig["channel_canonical"] in allowed


def test_meta_reports_family_runs_latency_and_no_errors(txns, edges):
    meta = det_mod.evaluate_all(txns, edges)["meta"]
    assert set(meta["family_runs"]) == {
        "RULE_FAMILIES", "NETWORK_PROXIMITY",
        "CROSS_CHANNEL_PATTERN", "GEOGRAPHIC_ANOMALY",
        "STRUCTURING_PATTERN", "DECLINE_REPETITION",
        "MULE_PASSTHROUGH"}
    assert all(v == len(txns) for v in meta["family_runs"].values())
    assert set(meta["family_latency_ms"]) == set(meta["family_runs"])
    assert all(v >= 0 for v in meta["family_latency_ms"].values())
    assert meta["family_errors"] == []


def test_bucketize_day_week_month_and_timezone(txns, edges):
    signals = det_mod.evaluate_all(txns, edges)["signals"]
    assert signals
    shifted = dict(signals[0])
    shifted["signal_id"] = "sig_tz_probe"
    shifted["occurred_at"] = "2026-01-01T00:30:00+02:00"
    day = det_mod.bucketize([shifted], "day")
    assert day == [{"bucket": "2025-12-31", "signals": 1,
                    "unique_txns": 1}]
    week = det_mod.bucketize([shifted], "week")
    assert week[0]["bucket"] == "2026-W01"  # ISO: Wed belongs to 2026-W01
    month = det_mod.bucketize([shifted], "month")
    assert month[0]["bucket"] == "2025-12"
    hour = det_mod.bucketize([shifted], "hour")
    assert hour[0]["bucket"] == "2025-12-31T22:00:00Z"
    assert det_mod.bucketize([], "day") == []


def test_bucketize_rejects_bad_granularity(txns, edges):
    signals = det_mod.evaluate_all(txns, edges)["signals"]
    with pytest.raises(ValueError, match="FILTER_INVALID"):
        det_mod.bucketize(signals, "fortnight")


def test_filter_signals_range_family_channel_severity(txns, edges):
    signals = det_mod.evaluate_all(txns, edges)["signals"]
    assert signals
    fam = signals[0]["detector_family"]
    by_fam = det_mod.filter_signals(signals, family=fam)
    assert by_fam and all(s["detector_family"] == fam for s in by_fam)
    assert det_mod.filter_signals(signals, family="NOPE") == []
    canon = signals[0]["channel_canonical"]
    by_ch = det_mod.filter_signals(signals, channel=canon)
    assert by_ch and all(s["channel_canonical"] == canon for s in by_ch)
    lo = min(s["occurred_at"] for s in signals)
    hi = max(s["occurred_at"] for s in signals)
    assert det_mod.filter_signals(signals, start=lo, end=hi) == signals
    assert det_mod.filter_signals(signals, start="2030-01-01T00:00:00Z") \
        == []
    with pytest.raises(ValueError, match="FILTER_INVALID"):
        det_mod.filter_signals(signals, start=hi, end=lo)
    with pytest.raises(ValueError, match="FILTER_INVALID"):
        det_mod.filter_signals(signals, start="not-a-time")
    with pytest.raises(ValueError, match="FILTER_INVALID"):
        det_mod.filter_signals([{"occurred_at": "2026-01-01 00:00:00"}])


def test_summary_reports_fp_rate_and_investigations(tmp_store):
    txns = tmp_store.state["transactions"]
    signals = det_mod.evaluate_all(txns, tmp_store.state["edges"])[
        "signals"]
    assert len(signals) >= 2
    tmp_store.set_signal_outcome(signals[0]["signal_id"], "DISMISSED",
                                 "tester-a")
    tmp_store.set_signal_outcome(signals[1]["signal_id"],
                                 "CONFIRMED_SUSPICIOUS", "tester-b")
    body = main.signals_summary()
    assert body["false_positive_rate"] == 0.5
    assert body["false_positive_basis"] == "1 dismissed of 2 reviewed"
    assert body["unique_investigations_created"] >= 1


def test_summary_fp_rate_null_without_reviews(tmp_store):
    body = main.signals_summary()
    assert body["false_positive_rate"] is None
    assert body["false_positive_basis"] == \
        "no reviewed outcomes recorded"


def test_search_pagination_and_q(tmp_store):
    txns = tmp_store.state["transactions"]
    signals = det_mod.evaluate_all(txns, tmp_store.state["edges"])[
        "signals"]
    page = main.signals_search(limit=2, offset=0)
    assert page["total"] == len(signals)
    assert len(page["signals"]) == min(2, len(signals))
    assert page["limit"] == 2 and page["offset"] == 0
    probe = signals[0]["transaction_id"]
    found = main.signals_search(q=probe)
    assert found["total"] >= 1
    assert all(probe in s["transaction_id"]
               for s in found["signals"])
    assert main.signals_search(q="zzz-no-such-signal")["total"] == 0
    assert main.signals_search(limit=200, offset=10_000)["signals"] == []


def test_search_rejects_bad_paging_and_filters(tmp_store):
    with pytest.raises(main.AppError) as exc:
        main.signals_search(limit=0)
    assert (exc.value.code, exc.value.status) == ("FILTER_INVALID",
                                                  400)
    with pytest.raises(main.AppError) as exc:
        main.signals_search(limit=201)
    assert exc.value.status == 400
    with pytest.raises(main.AppError) as exc:
        main.signals_search(offset=-1)
    assert exc.value.status == 400
    with pytest.raises(main.AppError) as exc:
        main.signals_search(start="bogus")
    assert exc.value.status == 400


def test_time_series_reconciles_and_validates(tmp_store):
    for granularity in ("hour", "day", "week", "month"):
        body = main.signals_time_series(granularity=granularity)
        assert body["granularity"] == granularity
        assert sum(b["signals"] for b in body["buckets"]) == \
            body["total_signals"]
        for bucket in body["buckets"]:
            assert bucket["unique_txns"] <= bucket["signals"]
    with pytest.raises(main.AppError) as exc:
        main.signals_time_series(granularity="year")
    assert (exc.value.code, exc.value.status) == ("FILTER_INVALID",
                                                  400)


def test_signal_detail_unknown_is_404(tmp_store):
    with pytest.raises(main.AppError) as exc:
        main.signal_detail("sig_nope")
    assert (exc.value.code, exc.value.status) == ("UNKNOWN_SIGNAL",
                                                  404)


def test_signal_detail_shows_outcome_and_link(tmp_store):
    txns = tmp_store.state["transactions"]
    signals = det_mod.evaluate_all(txns, tmp_store.state["edges"])[
        "signals"]
    sid = signals[0]["signal_id"]
    inv_id = tmp_store.state["investigations"][0]["investigation_id"]
    tmp_store.set_signal_outcome(sid, "DISMISSED", "tester")
    tmp_store.link_signal(sid, inv_id, "tester")
    body = main.signal_detail(sid)
    assert body["signal_id"] == sid
    assert body["outcome"]["current"] == "DISMISSED"
    assert body["link"]["history"][0]["investigation_id"] == inv_id
    assert body["execution_id"]


def test_new_endpoints_respect_tenant_isolation(tmp_store, monkeypatch):
    register_tenant("org_beta")
    foreign = dict(tmp_store.state["transactions"][0])
    foreign["transaction_id"] = "txn_beta"
    foreign["tenant_id"] = "org_beta"
    tmp_store.state["transactions"].append(foreign)
    alpha_sid = det_mod.evaluate_all(
        [t for t in tmp_store.state["transactions"]
         if t.get("tenant_id", "org_primary") == "org_primary"],
        tmp_store.state["edges"])["signals"][0]["signal_id"]
    monkeypatch.setattr(
        main, "_request_ctx",
        lambda request=None: TenantContext(tenant_id="org_beta",
                                           actor="bob"))
    with pytest.raises(main.AppError) as exc:
        main.signal_detail(alpha_sid)
    assert exc.value.status == 404
    assert main.signals_search(q=alpha_sid)["total"] == 0


# -- slice-3: outcome + link writes (direct, socket-free) ----------------


def _bare_request() -> Request:
    return Request({"type": "http", "method": "POST", "path": "/x",
                    "headers": [(b"host", b"t")]})


def test_outcome_direct_persists_truncates_and_audits(tmp_store):
    txns = tmp_store.state["transactions"]
    sid = det_mod.evaluate_all(txns, tmp_store.state["edges"])[
        "signals"][0]["signal_id"]
    body = main.set_signal_outcome(sid, {"outcome": "DISMISSED",
                                         "note": "x" * 600},
                                   _bare_request())
    assert body["outcome"] == "DISMISSED"
    assert body["recorded_at"]
    record = tmp_store.signal_outcome(sid)
    assert record["current"] == "DISMISSED"
    assert len(record["history"][0]["note"]) == 500
    assert any(a["action"] == "signal.outcome" and a["target_id"] == sid
               for a in tmp_store.state["audits"])


def test_outcome_direct_rejects_non_dict_body(tmp_store):
    txns = tmp_store.state["transactions"]
    sid = det_mod.evaluate_all(txns, tmp_store.state["edges"])[
        "signals"][0]["signal_id"]
    with pytest.raises(main.AppError) as exc:
        main.set_signal_outcome(sid, ["not", "a", "dict"],
                                _bare_request())
    assert (exc.value.code, exc.value.status) == ("INVALID_BODY", 400)


def test_link_direct_unknown_investigation_is_404(tmp_store):
    txns = tmp_store.state["transactions"]
    sid = det_mod.evaluate_all(txns, tmp_store.state["edges"])[
        "signals"][0]["signal_id"]
    with pytest.raises(main.AppError) as exc:
        main.link_signal(sid, {"investigation_id": "inv_nope"},
                         _bare_request())
    assert (exc.value.code, exc.value.status) == (
        "UNKNOWN_INVESTIGATION", 404)


# -- slice-3: outcome + link writes over the HTTP stack ------------------


@needs_sockets
def test_outcome_post_persists_history_and_audits(client, tmp_store):
    txns = tmp_store.state["transactions"]
    sid = det_mod.evaluate_all(txns, tmp_store.state["edges"])[
        "signals"][0]["signal_id"]
    first = client.post("/api/v1/signals/%s/outcome" % sid,
                        json={"outcome": "DISMISSED", "note": "fp"})
    assert first.status_code == 200, first.text
    second = client.post("/api/v1/signals/%s/outcome" % sid,
                         json={"outcome": "CONFIRMED_SUSPICIOUS"})
    assert second.status_code == 200, second.text
    record = tmp_store.signal_outcome(sid)
    assert record["current"] == "CONFIRMED_SUSPICIOUS"
    assert [h["outcome"] for h in record["history"]] == [
        "DISMISSED", "CONFIRMED_SUSPICIOUS"]
    audits = [a for a in tmp_store.state["audits"]
              if a["action"] == "signal.outcome"
              and a["target_id"] == sid]
    assert len(audits) == 2


@needs_sockets
def test_outcome_post_rejects_bad_value_and_unknown(client, tmp_store):
    txns = tmp_store.state["transactions"]
    sid = det_mod.evaluate_all(txns, tmp_store.state["edges"])[
        "signals"][0]["signal_id"]
    bad = client.post("/api/v1/signals/%s/outcome" % sid,
                      json={"outcome": "MAYBE"})
    assert bad.status_code == 400
    assert bad.json()["error"]["code"] == "OUTCOME_INVALID"
    missing = client.post("/api/v1/signals/sig_nope/outcome",
                          json={"outcome": "DISMISSED"})
    assert missing.status_code == 404


@needs_sockets
def test_link_post_idempotent_and_audits(client, tmp_store):
    txns = tmp_store.state["transactions"]
    sid = det_mod.evaluate_all(txns, tmp_store.state["edges"])[
        "signals"][0]["signal_id"]
    inv_id = tmp_store.state["investigations"][0]["investigation_id"]
    body = {"investigation_id": inv_id}
    first = client.post("/api/v1/signals/%s/link" % sid, json=body)
    assert first.status_code == 200, first.text
    second = client.post("/api/v1/signals/%s/link" % sid, json=body)
    assert second.status_code == 200, second.text
    assert len(tmp_store.signal_link(sid)["history"]) == 1
    bad = client.post("/api/v1/signals/%s/link" % sid,
                      json={"investigation_id": "inv_nope"})
    assert bad.status_code == 404


@needs_sockets
def test_outcome_post_armed_requires_credential(client, tmp_store,
                                                monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", _ARM_SECRET)
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:investigator:%s" % _ARM_RECORD)
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", _ARM_TOKEN)
    txns = tmp_store.state["transactions"]
    sid = det_mod.evaluate_all(txns, tmp_store.state["edges"])[
        "signals"][0]["signal_id"]
    anon = client.post("/api/v1/signals/%s/outcome" % sid,
                       json={"outcome": "DISMISSED"})
    assert anon.status_code == 401
    forged = client.post(
        "/api/v1/signals/%s/outcome" % sid,
        json={"outcome": "DISMISSED"},
        headers={"Authorization": "Bearer wrong-token"})
    assert forged.status_code == 401
    authed = client.post(
        "/api/v1/signals/%s/outcome" % sid,
        json={"outcome": "DISMISSED", "actor_id": "mallory"},
        headers={"Authorization": "Bearer " + _ARM_TOKEN})
    assert authed.status_code == 200, authed.text
    history = tmp_store.signal_outcome(sid)["history"]
    assert history[-1]["actor"] == "platform-token"


# -- Phase 3: per-family emission + fault path ---------------------------


def test_per_family_emission_on_seed(txns, edges):
    by_family = {}
    for sig in det_mod.evaluate_all(txns, edges)["signals"]:
        by_family.setdefault(sig["detector_family"], []).append(sig)
    for family in ("RULE_MATCH", "PHONE_REUSE", "GRAPH_PATTERN",
                   "NETWORK_PROXIMITY", "BENEFICIARY_CLUSTER",
                   "SHARED_MERCHANT", "DEVICE_REUSE", "VELOCITY",
                   "CROSS_CHANNEL_PATTERN"):
        assert by_family.get(family), family
    assert "ML_ANOMALY" not in by_family


def test_malformed_rows_skipped_and_surfaced(txns):
    good = dict(txns[0])
    result = det_mod.evaluate_all([good, None, "junk", 42], [])
    assert result["meta"]["transactions_evaluated"] == 1
    assert {"family": "INPUT",
            "error": "NON_DICT_ROWS_SKIPPED: 3"} in result["meta"][
                "family_errors"]
    assert all(isinstance(s, dict) for s in result["signals"])
