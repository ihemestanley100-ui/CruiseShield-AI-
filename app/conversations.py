"""Agent OS conversations: org/user-scoped threads with redaction.

Threads carry context (investigation/transaction/industry) and an
ordered message list. Stored text is redacted for credential-shaped
patterns before persistence. Retention: 90-day expiry with purge;
deletion is owner-invoked. Memory never substitutes for live
permission-checked reads.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

RETENTION_DAYS = 90

_REDACTIONS = (
    (re.compile(r"csc_[0-9a-fA-F]+"), "[REDACTED-CREDENTIAL]"),
    (re.compile(r"(?i)(password\s*[:=]\s*)\S+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(bearer\s+)\S+"), r"\1[REDACTED]"),
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _stamp(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


def redact(text: str) -> str:
    """Redact credential-shaped patterns from stored text."""
    out = text or ""
    for pattern, replacement in _REDACTIONS:
        out = pattern.sub(replacement, out)
    return out


def create(store: Any, tenant_id: str, owner: str,
           context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Open a conversation thread."""
    record = {
        "conversation_id": "conv_%s" % uuid.uuid4().hex[:12],
        "tenant_id": tenant_id, "owner": owner,
        "context": dict(context or {}),
        "messages": [], "created_at": _stamp(_now()),
        "expires_at": _stamp(_now() + timedelta(days=RETENTION_DAYS)),
    }
    store.conversation_save(record)
    return record


def post_message(store: Any, conversation_id: str, role: str,
                 text: str, tenant_id: str,
                 owner: str) -> dict[str, Any]:
    """Append a redacted message; enforces tenant + owner scope."""
    if role not in ("user", "assistant", "system"):
        raise ValueError("CONVERSATION_ROLE_INVALID")
    record = store.conversation_get(conversation_id)
    if record is None or record.get("tenant_id") != tenant_id:
        raise ValueError("CONVERSATION_UNKNOWN")
    if record.get("owner") != owner:
        raise ValueError("CONVERSATION_FORBIDDEN")
    message = {"role": role, "text": redact(text)[:4000],
               "at": _stamp(_now())}
    record.setdefault("messages", []).append(message)
    store.conversation_save(record)
    return message


def get_visible(store: Any, conversation_id: str, tenant_id: str,
                owner: str) -> dict[str, Any] | None:
    """Read one thread iff tenant + owner match."""
    record = store.conversation_get(conversation_id)
    if record is None or record.get("tenant_id") != tenant_id:
        return None
    if record.get("owner") != owner:
        return None
    return record


def purge_expired(store: Any) -> int:
    """Delete threads past expires_at. Returns the purge count."""
    today = _stamp(_now())
    rows = [r for r in store.state.get("conversations", [])
            if isinstance(r, dict)]
    survivors = [r for r in rows if (r.get("expires_at") or "") >= today]
    purged = len(rows) - len(survivors)
    if purged:
        store.state["conversations"] = survivors
        store._save()
    return purged
