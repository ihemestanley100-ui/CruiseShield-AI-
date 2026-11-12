"""A-1: qualified health states (availability vs completeness).

Socket-free: direct main.health() calls against tmp_store (runs in
every sandbox). States: healthy | operational_with_gaps | degraded
| unavailable. An unconfigured optional service (AI, audit chain)
is a gap, never a silent healthy; a failed store is unavailable;
any failed check is degraded.
"""
import app.config as config_mod
import app.main as main
from app import ai_adapter

HEX_KEY = "65" * 32


def _clean_audit_env(monkeypatch):
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY", "")
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY_ID", "k1")
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY_PREVIOUS", "")
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY_ID_PREVIOUS", "")


def test_default_unarmed_reports_gaps(tmp_store, monkeypatch):
    _clean_audit_env(monkeypatch)
    body = main.health()
    assert body["checks"]["model_configured"] == "NOT_CONFIGURED"
    assert body["checks"]["audit_chain"].startswith("NOT_CONFIGURED")
    assert body["status"] == "operational_with_gaps"


def test_fully_armed_reports_healthy(tmp_store, monkeypatch):
    _clean_audit_env(monkeypatch)
    monkeypatch.setattr(ai_adapter, "MODEL_API_KEY", "test-key")
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY", HEX_KEY)
    tmp_store.arm_audit_chain(bytes.fromhex(HEX_KEY), "k1")
    tmp_store.append_audit("actor", "action.test", "target", "t1",
                           "OLD", "NEW", "reason",
                           "2026-11-12T00:00:00Z", "trace-1", "req-1")
    body = main.health()
    assert body["checks"]["model_configured"] == "PASS"
    assert body["checks"]["audit_chain_verified"].startswith("PASS")
    assert body["status"] == "healthy"


def test_blocking_failure_reports_degraded(tmp_store, monkeypatch):
    _clean_audit_env(monkeypatch)
    tmp_store.state["transactions"].pop()
    body = main.health()
    assert body["checks"]["seed_integrity"].startswith("FAIL")
    assert body["status"] == "degraded"


def test_missing_store_reports_unavailable(tmp_store, monkeypatch):
    _clean_audit_env(monkeypatch)
    tmp_store.state["scenario_id"] = ""
    body = main.health()
    assert body["checks"]["store"] == "FAIL"
    assert body["status"] == "unavailable"


def test_tamper_reports_degraded(tmp_store, monkeypatch):
    _clean_audit_env(monkeypatch)
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY", HEX_KEY)
    tmp_store.arm_audit_chain(bytes.fromhex(HEX_KEY), "k1")
    tmp_store.append_audit("actor", "action.test", "target", "t1",
                           "OLD", "NEW", "reason",
                           "2026-11-12T00:00:00Z", "trace-1", "req-1")
    sealed = [a for a in tmp_store.state["audits"]
              if "audit_digest" in a]
    assert sealed
    sealed[-1]["reason"] = "forged"
    body = main.health()
    assert body["checks"]["audit_chain_verified"].startswith("FAIL")
    assert body["status"] == "degraded"


def test_misconfigured_audit_reports_degraded(tmp_store, monkeypatch):
    _clean_audit_env(monkeypatch)
    monkeypatch.setattr(main, "store", tmp_store)
    monkeypatch.setattr(config_mod, "AUDIT_CHAIN_KEY", "short")
    body = main.health()
    assert body["checks"]["audit_chain_verified"] == "FAIL misconfigured"
    assert body["status"] == "degraded"

