"""Store-level audit sealing: opt-in, tamper-detecting, legacy-safe."""
import pytest

from app.store import Store

KEY = b"s" * 32


def _audit(store, action="case.decision"):
    return store.append_audit("human", "u1", action, "case", "c1",
                              "NEW", "TRIAGED", "reason", "t", "t")


def test_unsealed_by_default(tmp_store):
    entry = _audit(tmp_store)
    assert "audit_digest" not in entry
    assert tmp_store.verify_audit_chain({"k1": KEY})["events"] == 0


def test_sealed_sequence_verifies(tmp_store):
    tmp_store.audit_chain_key = KEY
    for _ in range(3):
        _audit(tmp_store)
    report = tmp_store.verify_audit_chain({"k1": KEY})
    assert report["events"] == 3
    assert report["head"] == tmp_store.state["audits"][-1]["audit_digest"]


def test_tamper_detected(tmp_store):
    tmp_store.audit_chain_key = KEY
    _audit(tmp_store)
    _audit(tmp_store)
    tmp_store.state["audits"][-1]["reason"] = "forged"
    with pytest.raises(ValueError, match="AUDIT_TAMPER"):
        tmp_store.verify_audit_chain({"k1": KEY})


def test_mixed_legacy_and_sealed(tmp_store):
    _audit(tmp_store)  # legacy, unsealed
    tmp_store.audit_chain_key = KEY
    _audit(tmp_store)
    _audit(tmp_store)
    report = tmp_store.verify_audit_chain({"k1": KEY})
    assert report["events"] == 2


def test_wrong_key_rejected(tmp_store):
    tmp_store.audit_chain_key = KEY
    _audit(tmp_store)
    with pytest.raises(ValueError, match="AUDIT_SIG_INVALID"):
        tmp_store.verify_audit_chain({"k1": b"w" * 32})


def test_seal_persists_across_reopen(tmp_path):
    first = Store(tmp_path / "s.json")
    first.audit_chain_key = KEY
    _audit(first)
    second = Store(tmp_path / "s.json")
    assert second.verify_audit_chain({"k1": KEY})["events"] == 1
