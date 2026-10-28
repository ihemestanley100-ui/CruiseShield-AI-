"""T-002/T-003: idempotency, channel handling, schema rejection."""
import pytest

from app.events import normalize_channel, validate_and_normalize
from app.store import Store


def _raw(channel="MOBILE_APP", event_id="evt_x1", amount=1000):
    return {
        "event_id": event_id, "occurred_at": "2026-10-27T11:00:00Z",
        "transaction": {"transaction_id": "txn_x1", "amount_minor": amount,
                        "channel": channel, "sender_account_id": "acct_A",
                        "receiver_account_id": "acct_B"},
    }


def test_duplicate_event_is_idempotent(tmp_path):
    store = Store(tmp_path / "state.json")
    status, _, _ = store.ingest_event(_raw())
    assert status == "accepted"
    status, _, _ = store.ingest_event(_raw())
    assert status == "duplicate"
    assert len([e for e in store.state["events"] if e["event_id"] == "evt_x1"]) == 1


def test_unknown_channel_maps_with_warning():
    channel, warning = normalize_channel("PIGEON")
    assert channel == "UNKNOWN"
    assert warning and "PIGEON" in warning


def test_channel_alias_normalizes_silently():
    channel, warning = normalize_channel("mobile")
    assert channel == "MOBILE_APP"
    assert warning is None


def test_schema_rejection(tmp_path):
    store = Store(tmp_path / "state.json")
    with pytest.raises(ValueError, match="SCHEMA_INVALID"):
        store.ingest_event({"event_id": "evt_bad"})
    with pytest.raises(ValueError, match="SCHEMA_INVALID"):
        store.ingest_event(_raw(amount=-5))


def test_ingest_warns_on_unknown_channel(tmp_path):
    store = Store(tmp_path / "state.json")
    status, event, warnings = store.ingest_event(_raw(channel="PIGEON"))
    assert status == "accepted"
    assert event["transaction"]["channel"] == "UNKNOWN"
    assert warnings
