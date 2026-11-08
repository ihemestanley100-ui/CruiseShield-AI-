"""Per-client API credentials + service identities (SEC-CRED).

Replaces the shared DEMO_WRITE_TOKEN pattern for service callers: each
client gets a unique id, a one-time secret (csc_ + 32 hex), an explicit
scope set, and independent revocation. Secrets persist as PBKDF2 hashes
only (auth.hash_password); verification reuses verify_password.
Scopes are a subset of {read, write, ai_run, audit_read} - never manage.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from app import auth as _auth

PREFIX = "csc_"
ALLOWED_SCOPES = frozenset({"read", "write", "ai_run", "audit_read"})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def issue(store: Any, client_name: str, scopes: list[str],
          actor: str) -> dict[str, Any]:
    """Create a credential. The secret is returned once, never stored."""
    name = (client_name or "").strip()
    if not name or len(name) > 80:
        raise ValueError("CLIENT_NAME_INVALID")
    clean = sorted(set(scopes or []))
    if not clean or not set(clean) <= ALLOWED_SCOPES:
        raise ValueError("CLIENT_SCOPES_INVALID")
    secret = PREFIX + secrets.token_hex(16)
    record = {
        "client_id": "client_%s" % secrets.token_hex(6),
        "name": name,
        "scopes": clean,
        "secret_hash": _auth.hash_password(secret),
        "created_at": _now(),
        "created_by": actor,
        "revoked_at": None,
        "revoked_by": None,
    }
    store.cred_save(record)
    return {"client_id": record["client_id"], "name": name,
            "scopes": clean, "secret": secret,
            "warning": "store this secret now; it cannot be retrieved"}


def verify(store: Any, presented: str | None) -> dict[str, Any] | None:
    """Verify a presented secret. Returns the live record or None."""
    if not presented or not presented.startswith(PREFIX):
        return None
    for record in store.api_credentials():
        if not isinstance(record, dict) or record.get("revoked_at"):
            continue
        try:
            if _auth.verify_password(presented,
                                     record.get("secret_hash", "")):
                return record
        except Exception:
            continue
    return None


def revoke(store: Any, client_id: str, actor: str) -> dict[str, Any]:
    """Revoke a credential. Idempotent on missing ids? No - raises."""
    record = store.cred_get(client_id)
    if record is None:
        raise ValueError("CLIENT_UNKNOWN: %s" % client_id)
    if not record.get("revoked_at"):
        record["revoked_at"] = _now()
        record["revoked_by"] = actor
        store.cred_save(record)
    return record


def redacted(record: dict[str, Any]) -> dict[str, Any]:
    """List-safe view: no hash material, ever."""
    return {k: v for k, v in record.items() if k != "secret_hash"}
