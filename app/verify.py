"""Contact verification tokens (Phase 5, D-038). Delivery: BLOCKED_EXTERNAL.

Single-use HMAC-bound tokens (purpose email|phone, 24 h TTL). The
request endpoint records issuance and reports delivery BLOCKED; it
never returns the token. Tests exercise issue/parse/spend directly.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from app.auth import b64d, b64e

VERIFY_TTL_SECONDS = 24 * 3600
PURPOSES = ("email", "phone", "invite")


def issue_token(session_secret: str, username: str, purpose: str,
                target: str, now: float | None = None,
                ttl_seconds: int | None = None) -> str:
    """Mint one purpose-bound verification token."""
    moment = time.time() if now is None else now
    ttl = VERIFY_TTL_SECONDS if ttl_seconds is None else int(ttl_seconds)
    payload = b64e(json.dumps(
        {"u": username, "p": purpose, "t": target,
         "exp": int(moment) + ttl,
         "n": secrets.token_hex(8)},
        separators=(",", ":")).encode())
    sig = b64e(hmac.new(session_secret.encode(), payload.encode(),
                        hashlib.sha256).digest())
    return payload + "." + sig


def parse_token(token: str, session_secret: str,
                now: float | None = None) -> dict[str, Any] | None:
    """Validate signature + expiry + shape; claims or None (never raises)."""
    try:
        payload, sig = str(token or "").split(".", 1)
        expect = b64e(hmac.new(session_secret.encode(), payload.encode(),
                               hashlib.sha256).digest())
        if not hmac.compare_digest(expect, sig):
            return None
        data = json.loads(b64d(payload).decode())
        moment = time.time() if now is None else now
        if int(data.get("exp", 0)) < int(moment):
            return None
        user, purpose = str(data.get("u", "")), str(data.get("p", ""))
        if not user or purpose not in PURPOSES:
            return None
        return {"user": user, "purpose": purpose,
                "target": str(data.get("t", "")),
                "nonce": str(data.get("n", "")),
                "exp": int(data.get("exp", 0))}
    except (ValueError, TypeError):
        return None


def spend_token(store, purpose: str, nonce: str, exp: float) -> bool:
    """Single-use guard (namespaced nonces share the ticket table)."""
    return store.spend_mfa_ticket("verify:%s:%s" % (purpose, nonce), exp)


def mask_contact(target: str) -> str:
    """Privacy-safe display form (first/last chars only)."""
    text = str(target or "")
    if "@" in text:
        local, _, domain = text.partition("@")
        return "%s***@%s" % (local[:1], domain[-7:] if len(domain) > 7
                             else domain)
    if len(text) <= 4:
        return "***"
    return "%s***%s" % (text[:4], text[-2:])
