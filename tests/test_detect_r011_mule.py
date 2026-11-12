"""MS-DETECT-003: R-011 mule pass-through (MULE_PASSTHROUGH)."""
from datetime import datetime, timedelta, timezone

import app.config as config_mod
import app.main as main
from app import detection as det_mod
from app import graph as graph_mod

_BASE = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)


def _ts(minutes: int) -> str:
    return (_BASE + timedelta(minutes=minutes)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _txn(tid: str, sender: str, receiver: str, amount: int,
         at: int, tenant: str = "org_primary",
         provider: str | None = None,
         status: str | None = None) -> dict:
    txn = {"transaction_id": tid, "sender_account_id": sender,
           "receiver_account_id": receiver, "amount_minor": amount,
           "occurred_at": _ts(at), "channel": "NIP",
           "tenant_id": tenant}
    if provider is not None:
        txn["provider"] = provider
    if status is not None:
        txn["provider_status"] = status
    return txn


def _mule_txns(out_amount: int = 12000000, out_at: int = 180):
    return [_txn("txn_mi0", "S1", "M", 5000000, 0),
            _txn("txn_mi1", "S2", "M", 5000000, 60),
            _txn("txn_mi2", "S3", "M", 5000000, 120),
            _txn("txn_mo0", "M", "Z", out_amount, out_at)]


def _fams(signals, family="MULE_PASSTHROUGH"):
    return [s for s in signals if s["detector_family"] == family]


def _run(txns):
    return det_mod.evaluate_all(txns, [])["signals"]


# --- A. Positive -----------------------------------------------------------


def test_mule_positive_fires_with_full_evidence():
    hits = _fams(_run(_mule_txns()))
    assert {s["transaction_id"] for s in hits} == {
        "txn_mi0", "txn_mi1", "txn_mi2", "txn_mo0"}
    first = hits[0]
    assert first["rule_id"] == "R-011"
    assert first["rule_version"] == "1.0"
    assert first["severity"] == "high"
    ev = first["evidence"]
    assert ev["account"] == "M"
    assert ev["distinct_senders"] == 3
    assert ev["sender_ids"] == ["S1", "S2", "S3"]
    assert ev["total_in"] == 15000000
    assert ev["total_out"] == 12000000
    assert ev["forwarded_ratio"] == 0.8
    assert ev["over_forward"] is False
    assert ev["unattested_count"] == 4
    assert ev["thresholds"] == {"min_senders": 3,
                                "min_incoming": 10000000,
                                "min_ratio": 0.8}
    assert "does not establish that specific funds are " \
        "criminal proceeds" in first["reason"]
    for word in ("escrow", "payroll", "marketplace",
                 "payment-processor"):
        assert word in first["reason"]
    assert "Investigator review required" in first["reason"]


# --- B. Negatives ----------------------------------------------------------


def test_mule_two_senders_silent():
    txns = [_txn("txn_n0", "S1", "M", 8000000, 0),
            _txn("txn_n1", "S2", "M", 8000000, 60),
            _txn("txn_n2", "M", "Z", 14000000, 120)]
    assert _fams(_run(txns)) == []


def test_mule_below_floor_silent():
    txns = [_txn("txn_f0", "S1", "M", 3000000, 0),
            _txn("txn_f1", "S2", "M", 3000000, 60),
            _txn("txn_f2", "S3", "M", 3000000, 120),
            _txn("txn_f3", "M", "Z", 8000000, 180)]
    assert _fams(_run(txns)) == []


def test_mule_below_ratio_silent():
    assert _fams(_run(_mule_txns(out_amount=11000000))) == []


def test_mule_accumulation_without_forward_silent():
    txns = _mule_txns()[:3]
    assert _fams(_run(txns)) == []


def test_mule_out_only_before_in_silent():
    txns = [_txn("txn_b0", "M", "Z", 12000000, 0),
            _txn("txn_b1", "S1", "M", 5000000, 600),
            _txn("txn_b2", "S2", "M", 5000000, 660),
            _txn("txn_b3", "S3", "M", 5000000, 720)]
    assert _fams(_run(txns)) == []


# --- C. Boundaries ---------------------------------------------------------


def test_mule_boundary_floor_exact_fires_one_short_silent():
    base = [_txn("txn_e0", "S1", "M", 4000000, 0),
            _txn("txn_e1", "S2", "M", 3000000, 60),
            _txn("txn_e2", "S3", "M", 3000000, 120)]
    assert len(_fams(_run(
        base + [_txn("txn_e3", "M", "Z", 8000000, 180)]))) == 4
    short = [_txn("txn_e0", "S1", "M", 4000000, 0),
             _txn("txn_e1", "S2", "M", 3000000, 60),
             _txn("txn_e2", "S3", "M", 2999999, 120),
             _txn("txn_e3", "M", "Z", 8000000, 180)]
    assert _fams(_run(short)) == []


def test_mule_boundary_ratio_exact_fires_below_silent():
    assert len(_fams(_run(_mule_txns(out_amount=12000000)))) == 4
    assert _fams(_run(_mule_txns(out_amount=11999999))) == []


def test_mule_boundary_window_edge_in_out():
    # OUT at +1440m from earliest IN is in scope for centered
    # windows of the middle members.
    txns = [_txn("txn_w0", "S1", "M", 5000000, 0),
            _txn("txn_w1", "S2", "M", 5000000, 60),
            _txn("txn_w2", "S3", "M", 5000000, 120),
            _txn("txn_w3", "M", "Z", 12000000, 1440)]
    hits = _fams(_run(txns))
    # +1440 edge is inside every centered window here.
    assert {s["transaction_id"] for s in hits} == {
        "txn_w0", "txn_w1", "txn_w2", "txn_w3"}
    far = [_txn("txn_w0", "S1", "M", 5000000, 0),
           _txn("txn_w1", "S2", "M", 5000000, 60),
           _txn("txn_w2", "S3", "M", 5000000, 120),
           _txn("txn_w3", "M", "Z", 12000000, 1441)]
    # At +1441 the OUT leaves w0's window and w0 leaves w3's.
    assert {s["transaction_id"] for s in _fams(_run(far))} == {
        "txn_w1", "txn_w2"}


# --- D. Chronology ---------------------------------------------------------


def test_mule_out_after_in_fires():
    assert len(_fams(_run(_mule_txns()))) == 4


def test_mule_equal_timestamps_deterministic():
    txns = [_txn("txn_t0", "S1", "M", 5000000, 100),
            _txn("txn_t1", "S2", "M", 5000000, 100),
            _txn("txn_t2", "S3", "M", 5000000, 100),
            _txn("txn_t3", "M", "Z", 12000000, 100)]
    first = _fams(det_mod.evaluate_all(txns, [])["signals"])
    second = _fams(det_mod.evaluate_all(
        list(reversed(txns)), [])["signals"])
    assert len(first) == 4
    assert [s["signal_id"] for s in first] == [
        s["signal_id"] for s in second]


def test_mule_target_membership_enforced():
    txns = _mule_txns()
    outsider = _txn("txn_out", "QX", "QY", 1000, 60)
    hits = _fams(_run(txns + [outsider]))
    assert "txn_out" not in {s["transaction_id"] for s in hits}
    assert len(hits) == 4


def test_mule_excluded_out_not_a_member():
    # Early OUT is guard-excluded, so no signal on it even though
    # the account pattern fires for other members.
    txns = [_txn("txn_g0", "M", "Z", 1000000, 0),
            _txn("txn_g1", "S1", "M", 5000000, 600),
            _txn("txn_g2", "S2", "M", 5000000, 660),
            _txn("txn_g3", "S3", "M", 5000000, 720),
            _txn("txn_g4", "M", "Z", 12000000, 780)]
    hits = _fams(_run(txns))
    assert "txn_g0" not in {s["transaction_id"] for s in hits}
    assert len(hits) == 4


# --- E. Lifecycle ----------------------------------------------------------


def test_mule_settled_legs_count():
    txns = [_txn("txn_s0", "S1", "M", 5000000, 0, "org_primary",
                 "nip", "successful"),
            _txn("txn_s1", "S2", "M", 5000000, 60, "org_primary",
                 "card", "settled"),
            _txn("txn_s2", "S3", "M", 5000000, 120, "org_primary",
                 "chain", "confirmed"),
            _txn("txn_s3", "M", "Z", 12000000, 180, "org_primary",
                 "nip", "successful")]
    hits = _fams(_run(txns))
    assert len(hits) == 4
    assert hits[0]["evidence"]["unattested_count"] == 0


def test_mule_non_settled_legs_excluded():
    txns = [_txn("txn_l0", "S1", "M", 5000000, 0, "org_primary",
                 "card", "approved"),
            _txn("txn_l1", "S2", "M", 5000000, 60, "org_primary",
                 "nip", "pending"),
            _txn("txn_l2", "S3", "M", 5000000, 120, "org_primary",
                 "card", "declined"),
            _txn("txn_l3", "S4", "M", 5000000, 130, "org_primary",
                 "nip", "failed"),
            _txn("txn_l4", "S5", "M", 5000000, 140, "org_primary",
                 "card", "chargeback"),
            _txn("txn_l5", "M", "Z", 20000000, 180)]
    assert _fams(_run(txns)) == []


def test_mule_unmapped_unknown_excluded():
    txns = [_txn("txn_u0", "S1", "M", 5000000, 0, "org_primary",
                 "mystery", "weird"),
            _txn("txn_u1", "S2", "M", 5000000, 60),
            _txn("txn_u2", "S3", "M", 5000000, 120),
            _txn("txn_u3", "M", "Z", 12000000, 180)]
    assert _fams(_run(txns)) == []


def test_mule_partial_provider_info_excluded():
    txns = [_txn("txn_p0", "S1", "M", 5000000, 0),
            _txn("txn_p1", "S2", "M", 5000000, 60),
            _txn("txn_p2", "S3", "M", 5000000, 120, "org_primary",
                 None, "successful"),
            _txn("txn_p3", "M", "Z", 12000000, 180)]
    assert _fams(_run(txns)) == []


# --- F. Security -----------------------------------------------------------


def test_mule_tenant_isolated():
    txns = ([_txn("txn_a%d" % i, "S%d" % i, "M", 5000000, i * 60,
                  "org_acme") for i in range(2)] +
            [_txn("txn_b%d" % i, "S%d" % i, "M", 5000000,
                  i * 60 + 30, "org_beta") for i in range(2)] +
            [_txn("txn_a9", "M", "Z", 12000000, 240, "org_acme"),
             _txn("txn_b9", "M", "Z", 12000000, 240, "org_beta")])
    assert _fams(_run(txns)) == []


def test_mule_cross_tenant_collision_only_fires_where_qualified():
    txns = ([_txn("txn_c%d" % i, "S%d" % i, "M", 5000000, i * 60,
                  "org_acme") for i in range(3)] +
            [_txn("txn_c9", "M", "Z", 12000000, 240, "org_acme"),
             _txn("txn_d0", "S9", "M", 5000000, 60, "org_beta")])
    hits = _fams(_run(txns))
    assert {s["transaction_id"] for s in hits} == {
        "txn_c0", "txn_c1", "txn_c2", "txn_c9"}
    assert all(s["tenant_id"] == "org_acme" for s in hits)


def test_mule_duplicate_ids_not_counted():
    txns = _mule_txns()[:3]
    dup = dict(txns[0])
    dup["transaction_id"] = "txn_mi0"
    out = _txn("txn_mo0", "M", "Z", 12000000, 180)
    # 2 unique senders + duplicate of one of them.
    few = [txns[0], txns[1], dup, out]
    assert _fams(_run(few)) == []


def test_mule_self_transfer_excluded():
    txns = [_txn("txn_f0", "S1", "M", 5000000, 0),
            _txn("txn_f1", "S2", "M", 5000000, 60),
            _txn("txn_self", "M", "M", 5000000, 90),
            _txn("txn_f3", "M", "Z", 12000000, 180)]
    assert _fams(_run(txns)) == []


# --- G. Ratio --------------------------------------------------------------


def test_mule_over_forward_fires_flagged():
    hits = _fams(_run(_mule_txns(out_amount=20000000)))
    assert len(hits) == 4
    assert hits[0]["evidence"]["over_forward"] is True
    assert "OVER_FORWARD / BALANCE_CONFOUNDED" in hits[0]["reason"]
    assert hits[0]["evidence"]["forwarded_ratio"] > 1.0


def test_mule_zero_incoming_protected():
    txns = [_txn("txn_z0", "M", "Z", 12000000, 0),
            _txn("txn_z1", "M", "Y", 5000000, 60)]
    assert _fams(_run(txns)) == []


def test_mule_unrelated_outlets_inflate_transparently():
    txns = _mule_txns(out_amount=6000000) + [
        _txn("txn_x0", "M", "W", 6000000, 200)]
    hits = _fams(_run(txns))
    assert len(hits) == 5
    assert hits[0]["evidence"]["total_out"] == 12000000
    assert sorted(hits[0]["evidence"]["out_ids"]) == [
        "txn_mo0", "txn_x0"]


# --- H. Governance ---------------------------------------------------------


def test_mule_rule_version_registered():
    assert det_mod.RULE_VERSIONS["R-011"] == "1.0"


def test_mule_threshold_constants():
    assert graph_mod.MULE_WINDOW_MINUTES == 1440
    assert graph_mod.MULE_MIN_SENDERS == 3
    assert graph_mod.MULE_MIN_INCOMING == 10000000
    assert graph_mod.MULE_MIN_RATIO == 0.8


def test_mule_kill_switch_independent(monkeypatch):
    txns = _mule_txns()
    monkeypatch.setattr(config_mod, "DETECTOR_MULE_ENABLED", "0")
    assert det_mod.family_enabled("MULE_PASSTHROUGH") is False
    assert det_mod.family_enabled("STRUCTURING_PATTERN") is True
    result = det_mod.evaluate_all(txns, [])
    assert _fams(result["signals"]) == []
    assert result["meta"]["family_runs"]["MULE_PASSTHROUGH"] == 0
    body = main.list_detectors()
    by_fam = {d["family"]: d for d in body["detectors"]}
    assert by_fam["MULE_PASSTHROUGH"]["status"] == "DISABLED"
    cells = [c for c in main.detection_matrix()["cells"]
             if c["family"] == "MULE_PASSTHROUGH"]
    assert cells and {c["status"] for c in cells} == {
        "SUPPORTED_BUT_DISABLED"}


def test_mule_registry_matrix_cover_family():
    by_fam = {d["family"]: d
              for d in main.list_detectors()["detectors"]}
    assert by_fam["MULE_PASSTHROUGH"]["status"] == "OPERATIONAL"
    assert by_fam["MULE_PASSTHROUGH"]["description"]
    assert set(det_mod.DESCRIPTIONS) == set(det_mod.FAMILIES)
    cells = [c for c in main.detection_matrix()["cells"]
             if c["family"] == "MULE_PASSTHROUGH"]
    assert len(cells) == 9
    assert any(c["status"] == "SUPPORTED_AND_ACTIVE"
               for c in cells)


def test_mule_seed_silent(tmp_store):
    signals = det_mod.evaluate_all(
        tmp_store.state["transactions"],
        tmp_store.state["edges"])["signals"]
    assert _fams(signals) == []


# --- I. Prior-tranche regression -------------------------------------------


def test_mule_leaves_r009_r010_untouched():
    assert det_mod.RULE_VERSIONS["R-009"] == "1.0"
    assert det_mod.RULE_VERSIONS["R-010"] == "1.0"
    assert det_mod.family_enabled("STRUCTURING_PATTERN") is True
    assert det_mod.family_enabled("DECLINE_REPETITION") is True
