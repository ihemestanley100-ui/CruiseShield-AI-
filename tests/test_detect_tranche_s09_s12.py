"""MS-DETECT-001: structuring (R-009) + decline repetition (R-010)."""
from datetime import datetime, timedelta, timezone

import pytest

import app.config as config_mod
import app.main as main
from app import detection as det_mod
from app import graph as graph_mod

_BASE = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)


def _ts(minutes: int) -> str:
    return (_BASE + timedelta(minutes=minutes)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _txn(tid: str, sender: str = "acct_S", amount: int = 15000000,
         at: int = 0, tenant: str = "org_primary",
         provider: str | None = None,
         status: str | None = None) -> dict:
    txn = {"transaction_id": tid, "sender_account_id": sender,
           "receiver_account_id": "acct_R", "amount_minor": amount,
           "occurred_at": _ts(at), "channel": "NIP",
           "tenant_id": tenant}
    if provider is not None:
        txn["provider"] = provider
    if status is not None:
        txn["provider_status"] = status
    return txn


def _struct_txns(amounts=(15000000, 15000000, 15000000),
                 ats=(0, 400, 800), sender="acct_S",
                 tenant="org_primary"):
    return [_txn(f"txn_s{i}", sender, amt, at, tenant)
            for i, (amt, at) in enumerate(zip(amounts, ats))]


def _decline_txns(n=3, ats=(0, 400, 800), sender="acct_D",
                  tenant="org_primary"):
    return [_txn(f"txn_d{i}", sender, 1000, ats[i], tenant,
                 "card", "declined") for i in range(n)]


def _fams(signals, family):
    return [s for s in signals if s["detector_family"] == family]


def _run(txns):
    return det_mod.evaluate_all(txns, [])["signals"]


# --- R-009 structuring: positive / negative ------------------------------


def test_structuring_positive_fires_on_each_member():
    txns = _struct_txns()
    hits = _fams(_run(txns), "STRUCTURING_PATTERN")
    assert {s["transaction_id"] for s in hits} == {
        "txn_s0", "txn_s1", "txn_s2"}
    first = hits[0]
    assert first["rule_id"] == "R-009"
    assert first["rule_version"] == "1.0"
    assert first["severity"] == "high"
    assert first["evidence"]["count"] == 3
    assert first["evidence"]["total_minor"] == 45000000
    assert first["evidence"]["transaction_ids"] == [
        "txn_s0", "txn_s1", "txn_s2"]
    assert "3" in first["reason"] and "45000000" in first["reason"]


def test_structuring_below_count_stays_silent():
    txns = _struct_txns()[:2]
    assert _fams(_run(txns), "STRUCTURING_PATTERN") == []


def test_structuring_below_total_stays_silent():
    txns = _struct_txns(amounts=(10000000, 10000000, 10000000))
    assert _fams(_run(txns), "STRUCTURING_PATTERN") == []


def test_structuring_target_must_be_in_pattern():
    txns = _struct_txns()
    big = _txn("txn_big", "acct_S", 48000000, 200)
    hits = _fams(_run(txns + [big]), "STRUCTURING_PATTERN")
    assert "txn_big" not in {s["transaction_id"] for s in hits}
    assert len(hits) == 3


def test_structuring_boundary_total_exact_line_fires():
    txns = _struct_txns(amounts=(20000000, 10000000, 10000000))
    assert len(_fams(_run(txns), "STRUCTURING_PATTERN")) == 3


def test_structuring_boundary_total_one_kobo_short_silent():
    txns = _struct_txns(amounts=(20000000, 10000000, 9999999))
    assert _fams(_run(txns), "STRUCTURING_PATTERN") == []


def test_structuring_boundary_amount_at_line_excluded():
    txns = _struct_txns(amounts=(40000000, 15000000, 15000000))
    assert _fams(_run(txns), "STRUCTURING_PATTERN") == []


def test_structuring_window_edge_included_outside_excluded():
    # Center on txn_e1 (t=720): peers at -720 and +1440 edge.
    txns = [_txn("txn_e0", "acct_S", 15000000, 0),
            _txn("txn_e1", "acct_S", 15000000, 720),
            _txn("txn_e2", "acct_S", 15000000, 2160),   # +1440 edge
            _txn("txn_e3", "acct_S", 15000000, 2161)]   # +1441 outside
    peers = graph_mod.sender_window_peers(
        txns[1], txns, graph_mod.STRUCTURING_WINDOW_MINUTES)
    assert [p["transaction_id"] for p in peers] == [
        "txn_e0", "txn_e1", "txn_e2"]
    hits = _fams(_run(txns), "STRUCTURING_PATTERN")
    # e0 sees {e0,e1} only (e2 beyond +1440m); e3 sees {e2,e3}.
    assert {s["transaction_id"] for s in hits} == {
        "txn_e1", "txn_e2"}


def test_structuring_duplicate_ids_not_counted():
    txns = _struct_txns()[:2]
    dup = dict(txns[0])
    assert _fams(_run(txns + [dup]), "STRUCTURING_PATTERN") == []


def test_structuring_tenant_isolated():
    txns = ([_txn(f"txn_a{i}", "acct_S", 15000000, i * 400,
                  "org_acme") for i in range(2)] +
            [_txn(f"txn_b{i}", "acct_S", 15000000, i * 400 + 100,
                  "org_beta") for i in range(2)])
    assert _fams(_run(txns), "STRUCTURING_PATTERN") == []


def test_structuring_bad_timestamps_excluded():
    txns = _struct_txns()
    txns[2]["occurred_at"] = "not-a-timestamp"
    assert _fams(_run(txns), "STRUCTURING_PATTERN") == []
    bad_target = _txn("txn_bad", "acct_S", 15000000, 0)
    bad_target["occurred_at"] = "garbage"
    assert graph_mod.sender_window_peers(
        bad_target, txns, graph_mod.STRUCTURING_WINDOW_MINUTES) == []


# --- R-010 decline repetition ---------------------------------------------


def test_decline_positive_fires_with_provenance():
    txns = _decline_txns()
    hits = _fams(_run(txns), "DECLINE_REPETITION")
    assert len(hits) == 3
    first = hits[0]
    assert first["rule_id"] == "R-010"
    assert first["rule_version"] == "1.0"
    assert first["severity"] == "medium"
    assert first["evidence"]["count"] == 3
    assert first["evidence"]["provider_statuses"] == ["declined"]
    assert first["evidence"]["transaction_ids"] == [
        "txn_d0", "txn_d1", "txn_d2"]


def test_decline_below_count_stays_silent():
    assert _fams(_run(_decline_txns(n=2)), "DECLINE_REPETITION") == []


def test_decline_target_must_be_declined():
    txns = _decline_txns()
    settled = _txn("txn_ok", "acct_D", 1000, 200, "org_primary",
                   "card", "approved")
    hits = _fams(_run(txns + [settled]), "DECLINE_REPETITION")
    assert "txn_ok" not in {s["transaction_id"] for s in hits}
    assert len(hits) == 3


def test_decline_non_declined_statuses_not_counted():
    txns = [_txn("txn_x0", "acct_D", 1000, 0, "org_primary",
                 "card", "declined"),
            _txn("txn_x1", "acct_D", 1000, 400, "org_primary",
                 "card", "approved"),
            _txn("txn_x2", "acct_D", 1000, 800, "org_primary",
                 "nip", "failed"),
            _txn("txn_x3", "acct_D", 1000, 900, "org_primary",
                 "mystery", "weird")]
    assert _fams(_run(txns), "DECLINE_REPETITION") == []


def test_decline_duplicate_ids_not_counted():
    txns = _decline_txns(n=2)
    dup = dict(txns[0])
    assert _fams(_run(txns + [dup]), "DECLINE_REPETITION") == []


def test_decline_tenant_isolated():
    txns = ([_txn(f"txn_c{i}", "acct_D", 1000, i * 400, "org_acme",
                  "card", "declined") for i in range(2)] +
            [_txn(f"txn_e{i}", "acct_D", 1000, i * 400 + 100, "org_beta",
                  "card", "declined") for i in range(2)])
    assert _fams(_run(txns), "DECLINE_REPETITION") == []


# --- Determinism / versions / thresholds ----------------------------------


def test_tranche_signals_deterministic():
    txns = _struct_txns() + _decline_txns()
    first = det_mod.evaluate_all(txns, [])["signals"]
    second = det_mod.evaluate_all(txns, [])["signals"]
    assert first == second
    assert len({s["signal_id"] for s in first}) == len(first)


def test_rule_versions_registered():
    # MS-DETECT-003: R-011 joins the versioned aggregate-detector rules.
    assert det_mod.RULE_VERSIONS == {"R-009": "1.0", "R-010": "1.0",
                                     "R-011": "1.0"}


def test_threshold_constants_match_register():
    assert graph_mod.STRUCTURING_WINDOW_MINUTES == 1440
    assert graph_mod.STRUCTURING_MIN_COUNT == 3
    assert graph_mod.STRUCTURING_AMOUNT_LINE == 40000000
    assert graph_mod.STRUCTURING_MIN_TOTAL == 40000000
    assert graph_mod.DECLINE_WINDOW_MINUTES == 1440
    assert graph_mod.DECLINE_MIN_COUNT == 3


# --- Kill switches ---------------------------------------------------------


def test_kill_switches_independent(monkeypatch):
    txns = _struct_txns() + _decline_txns()
    monkeypatch.setattr(
        config_mod, "DETECTOR_STRUCTURING_ENABLED", "0")
    assert det_mod.family_enabled("STRUCTURING_PATTERN") is False
    assert det_mod.family_enabled("DECLINE_REPETITION") is True
    result = det_mod.evaluate_all(txns, [])
    assert _fams(result["signals"], "STRUCTURING_PATTERN") == []
    assert len(_fams(result["signals"], "DECLINE_REPETITION")) == 3
    assert result["meta"]["family_runs"]["STRUCTURING_PATTERN"] == 0
    assert result["meta"]["family_runs"]["DECLINE_REPETITION"] == 6
    body = main.list_detectors()
    by_fam = {d["family"]: d for d in body["detectors"]}
    assert by_fam["STRUCTURING_PATTERN"]["status"] == "DISABLED"
    assert by_fam["DECLINE_REPETITION"]["status"] == "OPERATIONAL"
    cells = [c for c in main.detection_matrix()["cells"]
             if c["family"] == "STRUCTURING_PATTERN"]
    assert cells and {c["status"] for c in cells} == {
        "SUPPORTED_BUT_DISABLED"}


def test_kill_switch_decline_only(monkeypatch):
    txns = _struct_txns() + _decline_txns()
    monkeypatch.setattr(
        config_mod, "DETECTOR_DECLINE_REPETITION_ENABLED", "0")
    result = det_mod.evaluate_all(txns, [])
    assert _fams(result["signals"], "DECLINE_REPETITION") == []
    assert len(_fams(result["signals"], "STRUCTURING_PATTERN")) == 3
    assert result["meta"]["family_runs"]["DECLINE_REPETITION"] == 0


def test_kill_switch_garbage_stays_enabled(monkeypatch):
    monkeypatch.setattr(
        config_mod, "DETECTOR_STRUCTURING_ENABLED", "banana")
    monkeypatch.setattr(
        config_mod, "DETECTOR_DECLINE_REPETITION_ENABLED", "")
    assert det_mod.family_enabled("STRUCTURING_PATTERN") is True
    assert det_mod.family_enabled("DECLINE_REPETITION") is True
    assert det_mod.family_enabled("VELOCITY") is True


# --- Registry / matrix / seed ----------------------------------------------


def test_registry_matrix_cover_new_families():
    body = main.list_detectors()
    by_fam = {d["family"]: d for d in body["detectors"]}
    for fam in ("STRUCTURING_PATTERN", "DECLINE_REPETITION"):
        assert by_fam[fam]["status"] == "OPERATIONAL"
        assert by_fam[fam]["description"]
    assert set(det_mod.DESCRIPTIONS) == set(det_mod.FAMILIES)
    cells = main.detection_matrix()["cells"]
    assert len(cells) == len(det_mod.FAMILIES) * 9
    vocab = {"SUPPORTED_AND_ACTIVE", "SUPPORTED_BUT_DISABLED",
             "UNSUPPORTED", "AWAITING_DATA_SOURCE",
             "NOT_YET_IMPLEMENTED", "ERROR"}
    for fam in ("STRUCTURING_PATTERN", "DECLINE_REPETITION"):
        fam_cells = [c for c in cells if c["family"] == fam]
        assert len(fam_cells) == 9
        assert all(c["status"] in vocab for c in fam_cells)
        assert any(c["status"] == "SUPPORTED_AND_ACTIVE"
                   for c in fam_cells)


def test_seed_stays_silent_for_new_families(tmp_store):
    signals = det_mod.evaluate_all(
        tmp_store.state["transactions"],
        tmp_store.state["edges"])["signals"]
    assert _fams(signals, "STRUCTURING_PATTERN") == []
    assert _fams(signals, "DECLINE_REPETITION") == []


def test_missing_sender_yields_no_peers_or_signals():
    no_sender = {"transaction_id": "txn_ns0",
                 "receiver_account_id": "acct_R",
                 "amount_minor": 15000000,
                 "occurred_at": _ts(0), "channel": "NIP",
                 "tenant_id": "org_primary"}
    empty_sender = dict(no_sender, transaction_id="txn_ns1",
                        sender_account_id="")
    txns = [no_sender, empty_sender, _txn("txn_ns2")]
    assert graph_mod.sender_window_peers(
        no_sender, txns, graph_mod.STRUCTURING_WINDOW_MINUTES) == []
    assert graph_mod.sender_window_peers(
        empty_sender, txns, graph_mod.DECLINE_WINDOW_MINUTES) == []
    signals = _run(txns)
    assert _fams(signals, "STRUCTURING_PATTERN") == []
    assert _fams(signals, "DECLINE_REPETITION") == []
