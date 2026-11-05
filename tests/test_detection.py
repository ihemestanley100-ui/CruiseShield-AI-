"""Detection intelligence: detectors, idempotency, channels, matrix."""
import pytest

import app.main as main
from app import channels as chan_mod
from app import detection as det_mod
from app.tenancy import TenantContext, register_tenant


@pytest.fixture()
def txns(tmp_store):
    return tmp_store.state["transactions"]


@pytest.fixture()
def edges(tmp_store):
    return tmp_store.state["edges"]


def test_registry_lists_11_families_with_honest_status():
    body = main.list_detectors()
    assert len(body["detectors"]) == 11
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
            assert sig["rule_version"] == "1.0"


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
    assert chan_mod.classify("QR") == "UNMAPPED"
    assert chan_mod.classify("") == "UNMAPPED"
    assert chan_mod.classify(None) == "UNMAPPED"


def test_channels_summary_flags_unmapped_and_zero_transfer(tmp_store):
    txns = tmp_store.state["transactions"]
    result = det_mod.evaluate_all(txns, tmp_store.state["edges"])
    summary = chan_mod.summarize(txns, result["signals"])
    by_ch = {c["channel"]: c for c in summary["channels"]}
    assert summary["unmapped_alert"] is True  # QR present in seed
    assert "QR" in summary["unmapped_raw_codes"]
    assert by_ch["TRANSFER"]["transactions"] == 0
    assert "No qualifying" in by_ch["TRANSFER"]["note"]
    total = sum(c["transactions"] for c in summary["channels"])
    assert total == len(txns)


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


def test_matrix_88_cells_with_honest_statuses():
    body = main.detection_matrix()
    assert len(body["cells"]) == 88
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
