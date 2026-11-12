"""AUD-03/AUD-04: ingest auditing + health chain-status presence.

Socket-free: direct handler calls against tmp_store (runs in every
sandbox; cf. test_flow_direct.py). Ephemeral sealing key only — no
production keys involved (D-018 owns the ceremony).
"""
import json

import pytest
from starlette.requests import Request

import app.config as config_mod
import app.main as main

KEY = b"e" * 32


def _req(*headers):
    scope = {"type": "http", "method": "POST", "path": "/api/v1/events",
             "headers": [(k.lower().encode("latin-1"), v.encode("latin-1"))
                         for k, v in headers]}
    return Request(scope)


def _event(event_id="evt_aud03_1", txn_id="txn_aud03_1"):
    return {
        "event_id": event_id, "occurred_at": "2026-11-06T12:00:00Z",
        "transaction": {"transaction_id": txn_id, "amount_minor": 1000,
                        "channel": "MOBILE_APP",
                        "sender_account_id": "acct_A",
                        "receiver_account_id": "acct_B"},
    }


def _ingested(store):
    return [a for a in store.state["audits"]
            if a["action"] == "event.ingested"]


# -- AUD-03: ingest writes audit events ------------------------------------


def test_ingest_accepted_writes_audit(tmp_store, monkeypatch):
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "")
    before = len(tmp_store.state["audits"])
    result = main.ingest_event(_event(), _req())
    assert result["status"] == "accepted"
    rows = _ingested(tmp_store)
    assert len(rows) == 1
    row = rows[0]
    assert row["target_type"] == "event"
    assert row["target_id"] == "evt_aud03_1"
    assert row["actor_id"] == "anonymous"
    assert row["previous_state_reference"] == "NONE"
    assert row["new_state_reference"] == "accepted"
    assert "txn_aud03_1" in row["reason"]
    assert "MOBILE_APP" in row["reason"]
    assert len(tmp_store.state["audits"]) == before + 1


def test_ingest_duplicate_audited(tmp_store, monkeypatch):
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "")
    assert main.ingest_event(_event(), _req())["status"] == "accepted"
    result = main.ingest_event(_event(), _req())
    assert result["status"] == "duplicate"
    rows = _ingested(tmp_store)
    assert [r["new_state_reference"] for r in rows] == ["accepted",
                                                       "duplicate"]
    assert all(r["target_id"] == "evt_aud03_1" for r in rows)


def test_ingest_rejection_writes_no_audit(tmp_store, monkeypatch):
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "")
    before = len(tmp_store.state["audits"])
    with pytest.raises(main.AppError) as exc:
        main.ingest_event({"bogus": True}, _req())
    assert exc.value.code == "SCHEMA_INVALID"
    assert _ingested(tmp_store) == []
    assert len(tmp_store.state["audits"]) == before


def test_ingest_token_actor_is_platform_token(tmp_store, monkeypatch):
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN",
                        "tok-audit-test-only")
    result = main.ingest_event(
        _event(), _req(("Authorization", "Bearer tok-audit-test-only")))
    assert result["status"] == "accepted"
    rows = _ingested(tmp_store)
    assert len(rows) == 1
    assert rows[0]["actor_id"] == "platform-token"


# -- AUD-04: health reports chain status (presence-gated) ------------------


def test_health_reports_legacy_chain(tmp_store):
    body = main.health()
    value = body["checks"]["audit_chain"]
    assert value.startswith("NOT_CONFIGURED")
    assert "sealed=" not in value
    # A-1: legacy audit + unconfigured AI is operational_with_gaps —
    # available but incomplete, never an unconditional "healthy".
    assert body["status"] == "operational_with_gaps"


def test_health_reports_sealed_chain(tmp_store, monkeypatch):
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "")
    tmp_store.audit_chain_key = KEY
    main.ingest_event(_event(), _req())
    body = main.health()
    total = len(tmp_store.state["audits"])
    assert body["checks"]["audit_chain"] == f"PASS sealed=1 total={total}"
    assert KEY.hex() not in json.dumps(body)
    sealed = [a for a in tmp_store.state["audits"]
              if "audit_digest" in a]
    assert len(sealed) == 1
    assert sealed[0]["audit_digest"] not in json.dumps(body)


def test_health_chain_check_never_fails(tmp_store):
    value = main.health()["checks"]["audit_chain"]
    assert value.startswith(("PASS", "NOT_CONFIGURED"))
