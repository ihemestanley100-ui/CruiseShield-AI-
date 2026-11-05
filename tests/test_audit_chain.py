"""Tamper-evident audit chain tests (GAP-002)."""
import pytest

from app import audit_chain
from app.audit_chain import GENESIS_HASH, export_chain, seal, verify_chain

KEY_A = b"a" * 32
KEY_B = b"b" * 32


def _chain(n=4, key_id="k1", key=KEY_A):
    records, prev = [], GENESIS_HASH
    for seq in range(n):
        record = seal({"action": f"a{seq}", "actor": "u"}, prev,
                      key_id, key, seq)
        records.append(record)
        prev = record["audit_digest"]
    return records


def test_valid_chain_verifies():
    records = _chain()
    report = verify_chain(records, {"k1": KEY_A})
    assert report["events"] == 4 and report["head"] == records[-1][
        "audit_digest"]


def test_payload_tamper_detected():
    records = _chain()
    records[2]["action"] = "forged"
    with pytest.raises(ValueError, match="AUDIT_TAMPER"):
        verify_chain(records, {"k1": KEY_A})


def test_deletion_detected_via_seq_link():
    records = _chain()
    del records[1]
    with pytest.raises(ValueError, match="AUDIT_(SEQ|LINK)_BREAK"):
        verify_chain(records, {"k1": KEY_A})


def test_reorder_detected():
    records = _chain()
    records[1], records[2] = records[2], records[1]
    with pytest.raises(ValueError, match="AUDIT_(SEQ|LINK)_BREAK"):
        verify_chain(records, {"k1": KEY_A})


def test_wrong_key_rejected():
    records = _chain()
    with pytest.raises(ValueError, match="AUDIT_SIG_INVALID"):
        verify_chain(records, {"k1": KEY_B})


def test_unknown_key_id_rejected():
    records = _chain()
    with pytest.raises(ValueError, match="AUDIT_KEY_UNKNOWN"):
        verify_chain(records, {"other": KEY_A})


def test_rotation_keyring_accepts_both_epochs():
    old = _chain(2, "k1", KEY_A)
    new = _chain(2, "k2", KEY_B)
    # re-sequence second epoch onto the first head
    records, prev = list(old), old[-1]["audit_digest"]
    for offset, record in enumerate(new, start=len(old)):
        fixed = dict(record)
        fixed["audit_seq"] = offset
        fixed["audit_prev"] = prev
        resealed = seal({k: v for k, v in fixed.items()
                         if not k.startswith("audit_")},
                        prev, "k2", KEY_B, offset)
        records.append(resealed)
        prev = resealed["audit_digest"]
    report = verify_chain(records, {"k1": KEY_A, "k2": KEY_B})
    assert report["events"] == 4


def test_seal_requires_key():
    with pytest.raises(ValueError, match="AUDIT_KEY_REQUIRED"):
        seal({"a": 1}, GENESIS_HASH, "k1", b"", 0)


def test_export_is_canonical_bytes():
    blob = export_chain(_chain(2))
    assert blob == export_chain(_chain(2))
    assert b"audit_chain" in blob
