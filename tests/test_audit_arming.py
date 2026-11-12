"""D-1: audit-chain key configuration, arming, and fail-closed behavior.

Socket-free: direct Store construction on tmp paths (runs in every
sandbox). All key material is ephemeral and synthetic — patterns like
b"e" * 32 carry no credential value (D-018 owns any real ceremony).
"""
import base64
import json

import pytest

import app.config as config_mod
import app.main as main
from app.store import Store

HEX_KEY = "65" * 32          # 32 bytes of 0x65
B64_KEY = base64.b64encode(b"c" * 34).decode("ascii")
RAW_KEY = "raw-test-passphrase-for-audit-chain!!"  # 37 chars


def _audit(store):
    return store.append_audit(
        "actor", "action.test", "target", "t1", "OLD", "NEW", "reason",
        "2026-11-12T00:00:00Z", "trace-1", "req-1")


def _clean_env(monkeypatch):
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY", "")
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY_ID", "k1")
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY_PREVIOUS", "")
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY_ID_PREVIOUS", "")


# -- configuration predicates ---------------------------------------------


def test_unset_key_is_unarmed_not_misconfigured(monkeypatch):
    _clean_env(monkeypatch)
    assert config_mod.audit_chain_armed() is False
    assert config_mod.audit_chain_misconfigured() is False
    assert config_mod.audit_chain_key_bytes() is None


def test_hex_key_arms(monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY", HEX_KEY)
    assert config_mod.audit_chain_armed() is True
    assert config_mod.audit_chain_misconfigured() is False
    assert config_mod.audit_chain_key_bytes() == b"\x65" * 32


def test_base64_key_arms(monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY", B64_KEY)
    assert config_mod.audit_chain_armed() is True
    assert config_mod.audit_chain_key_bytes() == b"c" * 34


def test_raw_passphrase_key_arms(monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY", RAW_KEY)
    assert config_mod.audit_chain_armed() is True
    assert config_mod.audit_chain_key_bytes() == RAW_KEY.encode("utf-8")


def test_short_key_is_misconfigured(monkeypatch):
    _clean_env(monkeypatch)
    for raw in ("short", "x" * 31, "abcd", "aGk="):
        monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY", raw)
        assert config_mod.audit_chain_armed() is False
        assert config_mod.audit_chain_misconfigured() is True
    assert config_mod.audit_chain_key_bytes() is None


def test_bad_key_id_is_misconfigured(monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY", HEX_KEY)
    for bad_id in ("", "k 1", "k!1", "k" * 33):
        monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY_ID", bad_id)
        assert config_mod.audit_chain_misconfigured() is True
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY_ID", "k2")
    assert config_mod.audit_chain_misconfigured() is False


def test_rotation_keyring_accepts_both_epochs(monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY", HEX_KEY)
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY_ID", "k2")
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY_PREVIOUS",
                        "66" * 32)
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY_ID_PREVIOUS", "k1")
    assert config_mod.audit_chain_misconfigured() is False
    ring = config_mod.audit_chain_keyring()
    assert ring == {"k2": b"\x65" * 32, "k1": b"\x66" * 32}


def test_previous_without_id_is_misconfigured(monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY", HEX_KEY)
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY_PREVIOUS",
                        "66" * 32)
    assert config_mod.audit_chain_misconfigured() is True
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY_ID", "k2")
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY_ID_PREVIOUS", "k1")
    assert config_mod.audit_chain_misconfigured() is False
    # Previous id must differ from the current id.
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY_ID", "k1")
    assert config_mod.audit_chain_misconfigured() is True


# -- Store arming ----------------------------------------------------------


def test_unarmed_store_writes_legacy(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    store = Store(tmp_path / "s.json")
    assert store.audit_chain_key is None
    entry = _audit(store)
    assert "audit_digest" not in entry
    report = store.audit_verification_report()
    assert report["ok"] is True
    assert report["sealed"] == 0
    assert report["legacy_skipped"] == len(store.state["audits"])


def test_armed_store_seals_appends(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY", HEX_KEY)
    store = Store(tmp_path / "s.json")
    assert store.audit_chain_key == b"\x65" * 32
    assert store.audit_chain_key_id == "k1"
    before = sum(1 for a in store.state["audits"]
                 if "audit_digest" in a)
    first, second = _audit(store), _audit(store)
    assert first["audit_seq"] == before
    assert second["audit_seq"] == before + 1
    assert second["audit_prev"] == first["audit_digest"]
    assert second["audit_key_id"] == "k1"
    report = store.audit_verification_report()
    assert report["ok"] is True
    assert report["sealed"] == before + 2
    assert report["legacy_skipped"] == 0
    assert report["key_ids"] == ["k1"]


def test_misconfigured_key_fails_closed_at_construction(tmp_path,
                                                        monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY", "short")
    with pytest.raises(ValueError, match="AUDIT_CHAIN_MISCONFIGURED"):
        Store(tmp_path / "s.json")


def test_legacy_entries_never_retro_sealed(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    path = tmp_path / "s.json"
    store = Store(path)
    _audit(store)
    assert "audit_digest" not in store.state["audits"][-1]
    # Arm the live store: history stays plaintext, new appends seal.
    store.arm_audit_chain(b"\x65" * 32, "k1")
    _audit(store)
    audits = store.state["audits"]
    sealed = [a for a in audits if "audit_digest" in a]
    assert len(sealed) == 1
    assert sealed[0]["audit_seq"] == 0
    assert all("audit_digest" not in a for a in audits[:-1])


def test_tamper_detected_via_store_report(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY", HEX_KEY)
    store = Store(tmp_path / "s.json")
    _audit(store)
    _audit(store)
    store.state["audits"][-1]["reason"] = "forged"
    report = store.audit_verification_report()
    assert report["ok"] is False
    assert report["error"]["code"] == "AUDIT_CHAIN_INVALID"
    assert "AUDIT_TAMPER" in report["error"]["detail"]


def test_report_never_leaks_key_material(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY", HEX_KEY)
    store = Store(tmp_path / "s.json")
    _audit(store)
    blob = repr(store.audit_verification_report())
    assert HEX_KEY not in blob
    assert (b"\x65" * 32).hex() not in blob


# -- health surfacing ----------------------------------------------------


def test_health_verified_check_pass_and_tamper(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY", HEX_KEY)
    store = Store(tmp_path / "state.json")
    monkeypatch.setattr(main, "store", store)
    body = main.health()
    value = body["checks"]["audit_chain_verified"]
    assert value.startswith("PASS sealed=")
    assert HEX_KEY not in json.dumps(body)
    store.state["audits"][-1]["reason"] = "forged"
    value = main.health()["checks"]["audit_chain_verified"]
    assert value.startswith("FAIL AUDIT_TAMPER")


def test_health_verified_check_legacy_and_misconfigured(tmp_path,
                                                        monkeypatch):
    _clean_env(monkeypatch)
    store = Store(tmp_path / "state.json")
    monkeypatch.setattr(main, "store", store)
    value = main.health()["checks"]["audit_chain_verified"]
    assert value.startswith("NOT_CONFIGURED legacy=")
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY", "short")
    value = main.health()["checks"]["audit_chain_verified"]
    assert value == "FAIL misconfigured"
