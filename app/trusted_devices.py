"""Trusted-device register + revocation (SEC-DEV).

Builds on login_risk.session_fingerprint (coarse UA class + network
digest - no new hardware identifiers, no covert tracking). Devices
register on successful login; users list/trust/revoke their own;
revoked devices are denied at the next login with an audit row.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def key(username: str, ua_class: str, net_digest: str) -> str:
    return "%s|%s|%s" % (username, ua_class, net_digest)


def touch(store: Any, username: str, ua_class: str,
          net_digest: str) -> dict[str, Any]:
    """Record a successful-login device sighting (upsert)."""
    record = store.device_get(key(username, ua_class, net_digest))
    if record is None:
        record = {"device_key": key(username, ua_class, net_digest),
                  "user": username, "ua_class": ua_class,
                  "net_digest": net_digest, "first_seen": _now(),
                  "trusted": False, "revoked_at": None}
    record["last_seen"] = _now()
    store.device_save(record)
    return record


def set_trusted(store: Any, username: str, device_key: str,
                trusted: bool) -> dict[str, Any]:
    """Trust or untrust one of the caller's devices."""
    record = store.device_get(device_key)
    if record is None or record.get("user") != username:
        raise ValueError("DEVICE_UNKNOWN")
    record["trusted"] = bool(trusted)
    store.device_save(record)
    return record


def revoke(store: Any, username: str, device_key: str) -> dict[str, Any]:
    """Revoke one of the caller's devices (login-denying)."""
    record = store.device_get(device_key)
    if record is None or record.get("user") != username:
        raise ValueError("DEVICE_UNKNOWN")
    record["revoked_at"] = _now()
    record["trusted"] = False
    store.device_save(record)
    return record


def revoked(store: Any, username: str, ua_class: str,
            net_digest: str) -> bool:
    """True when this exact device is revoked for the user."""
    record = store.device_get(key(username, ua_class, net_digest))
    return bool(record and record.get("revoked_at"))
