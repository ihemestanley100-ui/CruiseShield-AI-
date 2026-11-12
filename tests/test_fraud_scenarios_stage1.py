"""Stage 1 fraud-scenario acceptance (CS-FRAUD-002, engine-supported gaps).

Socket-free. Each test is one scenario from FRAUD_SCENARIO_REGISTER.md
that the engine supports but no prior test exercised end to end.
Scenarios the engine cannot detect (structuring, insider abuse,
decline-repetition) are documented NOT_IMPLEMENTED in the register
and carry no test here — a test must prove detection, not its absence.
"""
import app.main as main
from app import channels as chan_mod
from app import detection as det_mod


def test_s04_qr_payment_abuse_detected(tmp_store):
    """S-04: large QR payment fires R-001 with QR canonical channel."""
    txns = list(tmp_store.state["transactions"])
    edges = tmp_store.state["edges"]
    assert any(t.get("channel") == "QR" for t in txns)
    txns.append({"transaction_id": "txn_s04_qr_abuse",
                 "amount_minor": 50000000, "currency": "NGN",
                 "channel": "QR", "sender_account_id": "acct_S04",
                 "receiver_account_id": "acct_S04M",
                 "occurred_at": "2026-11-12T00:00:00Z",
                 "tenant_id": "org_primary"})
    result = det_mod.evaluate_all(txns, edges)
    hits = [s for s in result["signals"]
            if s["transaction_id"] == "txn_s04_qr_abuse"
            and s["rule_id"] == "R-001"]
    assert hits, "large QR payment must fire R-001"
    assert all(s["channel_canonical"] == "QR" for s in hits)
    assert all(s["channel_canonical"] in chan_mod.CANONICAL
               for s in hits)
    assert all(s["severity"] in ("low", "medium", "high", "critical")
               for s in hits)
    assert all(s["signal_id"] and s["evidence"] for s in hits)


def test_s04_qr_cells_active_in_matrix():
    """S-04: detection matrix exposes evidenced QR coverage cells."""
    body = main.detection_matrix()
    qr = [c for c in body["cells"] if c["channel"] == "QR"]
    # MS-DETECT-001: 13 families (11 + structuring + decline).
    assert len(qr) == 13
    assert any(c["signals"] > 0 and c["evidence_signal_id"]
               for c in qr if c["family"] != "ML_ANOMALY")
