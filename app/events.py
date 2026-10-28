"""Event validation, normalization, and channel handling."""
from __future__ import annotations

from app.models import CHANNEL_ALIASES, Channel, Event


def normalize_channel(value: object) -> tuple[str, str | None]:
    """Return (normalized_channel, warning). Unknown input maps to UNKNOWN."""
    if not isinstance(value, str) or not value.strip():
        return Channel.UNKNOWN.value, "missing channel mapped to UNKNOWN"
    raw = value.strip()
    upper = raw.upper()
    if upper in Channel.__members__:
        return upper, None
    alias = CHANNEL_ALIASES.get(raw.lower())
    if alias:
        return alias, None
    return Channel.UNKNOWN.value, f"unmapped channel '{raw}' mapped to UNKNOWN"


def validate_and_normalize(raw: dict) -> tuple[Event, list[str]]:
    """Validate a raw event dict and return (event, warnings).

    Raises ValueError with a stable code prefix on rejection.
    """
    warnings: list[str] = []
    if not isinstance(raw, dict):
        raise ValueError("SCHEMA_INVALID: event must be an object")
    for field in ("event_id", "occurred_at", "transaction"):
        if not raw.get(field):
            raise ValueError(f"SCHEMA_INVALID: missing required field '{field}'")
    txn = raw["transaction"]
    if not isinstance(txn, dict):
        raise ValueError("SCHEMA_INVALID: transaction must be an object")
    for field in ("transaction_id", "amount_minor", "sender_account_id",
                  "receiver_account_id"):
        if txn.get(field) in (None, ""):
            raise ValueError(f"SCHEMA_INVALID: missing transaction field '{field}'")
    if not isinstance(txn["amount_minor"], int) or txn["amount_minor"] < 0:
        raise ValueError("SCHEMA_INVALID: amount_minor must be a non-negative integer")

    channel, warning = normalize_channel(txn.get("channel"))
    if warning:
        warnings.append(warning)
    normalized = {
        **raw,
        "event_type": raw.get("event_type", "financial.transaction.created"),
        "schema_version": raw.get("schema_version", "1.0"),
        "source": raw.get("source", "synthetic_demo"),
        "trace_id": raw.get("trace_id", f"trace_{raw['event_id']}"),
        "privacy_classification": raw.get("privacy_classification", "synthetic"),
        "transaction": {**txn, "channel": channel,
                        "currency": txn.get("currency", "NGN"),
                        "occurred_at": txn.get("occurred_at", raw["occurred_at"])},
        "entities": raw.get("entities", {}),
    }
    try:
        return Event.model_validate(normalized), warnings
    except Exception as exc:
        raise ValueError(f"SCHEMA_INVALID: {exc}") from exc
