"""Multi-factor authentication: TOTP enrollment/verification + recovery.

Stdlib only. TOTP secrets are *derived* (HMAC-SHA256) from
SESSION_SECRET per username + enrollment counter, so no plaintext
secret is persisted; a counter bump on every (re-)enrollment retires
the previous secret. Recovery codes are stored as SHA-256 hashes.
Step-up uses single-use signed login tickets (5 min TTL), mirroring
the app.auth session codec.

Replay protection: the last accepted TOTP counter is persisted per
user; a code must match a strictly newer counter. Brute force is
bounded by per-account lockout (5 failures -> 15 min) plus the
existing login rate limiter on the challenge endpoint.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from urllib.parse import quote

TOTP_DIGITS = 6
TOTP_PERIOD = 30
TOTP_WINDOW = 1  # accept previous/current/next step (clock skew)
TOTP_SECRET_BYTES = 20  # 160-bit, per RFC 4226 minimum
MFA_TICKET_TTL_SECONDS = 5 * 60
MFA_MAX_FAILED = 5
MFA_LOCKOUT_SECONDS = 15 * 60
RECOVERY_CODE_COUNT = 10

STATUS_NONE = "NONE"
STATUS_PENDING = "PENDING"
STATUS_ACTIVE = "ACTIVE"


def blank_state() -> dict:
    """Fresh per-user MFA record (JSON-serializable)."""
    return {"status": STATUS_NONE, "counter": 0, "last_counter": -1,
            "recovery_hashes": [], "failed": 0, "locked_until": 0.0,
            "enrolled_at": 0.0, "confirmed_at": 0.0}


def normalize_state(raw: object) -> dict:
    """Fill missing keys of a stored record (forward-compatible)."""
    state = blank_state()
    if isinstance(raw, dict):
        for key in state:
            if key in raw:
                state[key] = raw[key]
    return state


def derive_secret(session_secret: str, username: str,
                  counter: int) -> bytes:
    """Derive this enrollment's 160-bit TOTP secret (deterministic)."""
    msg = "cruiseshield-mfa-v1:%s:%d" % (username, counter)
    return hmac.new(session_secret.encode(), msg.encode(),
                    hashlib.sha256).digest()[:TOTP_SECRET_BYTES]


def secret_b32(secret: bytes) -> str:
    """Base32 enrollment secret for authenticator apps (no padding)."""
    return base64.b32encode(secret).decode().rstrip("=")


def provisioning_uri(username: str, secret: bytes,
                     issuer: str = "CruiseShield AI") -> str:
    """otpauth:// URI for QR-code enrollment."""
    return ("otpauth://totp/%s:%s?secret=%s&issuer=%s&digits=%d&period=%d"
            % (quote(issuer, safe=""), quote(username, safe=""),
               secret_b32(secret), quote(issuer, safe=""),
               TOTP_DIGITS, TOTP_PERIOD))


def _hotp(secret: bytes, counter: int) -> str:
    """RFC 4226 dynamic truncation -> zero-padded decimal code."""
    mac = hmac.new(secret, counter.to_bytes(8, "big"),
                   hashlib.sha1).digest()
    offset = mac[-1] & 0x0F
    code = int.from_bytes(mac[offset:offset + 4], "big") & 0x7FFFFFFF
    return str(code % (10 ** TOTP_DIGITS)).zfill(TOTP_DIGITS)


def totp(secret: bytes, now: float | None = None) -> str:
    """Current TOTP code for `secret`."""
    moment = time.time() if now is None else now
    return _hotp(secret, int(moment) // TOTP_PERIOD)


def verify_totp(secret: bytes, code: str, now: float | None,
                last_counter: int) -> int | None:
    """Verify a code; return matched counter or None.

    Accepts counters within TOTP_WINDOW of now, skipping negatives,
    and requires the match to be strictly newer than `last_counter`
    (replay protection). Never raises on bad input.
    """
    cleaned = "".join(str(code or "").split())
    if not cleaned.isdigit() or len(cleaned) != TOTP_DIGITS:
        return None
    moment = time.time() if now is None else now
    center = int(moment) // TOTP_PERIOD
    for counter in range(center - TOTP_WINDOW, center + TOTP_WINDOW + 1):
        if counter < 0 or counter <= last_counter:
            continue
        try:
            if hmac.compare_digest(_hotp(secret, counter), cleaned):
                return counter
        except (ValueError, TypeError):
            return None
    return None


def new_recovery_codes(count: int = RECOVERY_CODE_COUNT) -> list[str]:
    """One-time recovery codes, grouped hex ("abcdef-123456")."""
    codes = []
    for _ in range(count):
        raw = secrets.token_hex(6)
        codes.append(raw[:6] + "-" + raw[6:])
    return codes


def normalize_code(code: str) -> str:
    """Canonical form for recovery-code comparison."""
    return "".join(str(code or "").split()).replace("-", "").lower()


def hash_recovery_code(code: str) -> str:
    """SHA-256 hash of the normalized code (what is stored)."""
    return hashlib.sha256(normalize_code(code).encode()).hexdigest()


# BATCH-1: base64 helpers are canonical in app.auth (was byte-identical
# duplication); mfa keeps its `base64` import for secret_b32 only.
from app.auth import b64d as _b64d
from app.auth import b64e as _b64e


def create_ticket(session_secret: str, username: str,
                  now: float | None = None) -> str:
    """Single-use step-up ticket binding username + expiry + nonce."""
    moment = time.time() if now is None else now
    payload = _b64e(json.dumps(
        {"u": username, "exp": int(moment) + MFA_TICKET_TTL_SECONDS,
         "n": secrets.token_hex(8)}, separators=(",", ":")).encode())
    sig = _b64e(hmac.new(session_secret.encode(), payload.encode(),
                         hashlib.sha256).digest())
    return payload + "." + sig


def parse_ticket(ticket: str, session_secret: str,
                 now: float | None = None) -> dict | None:
    """Validate signature + expiry; return claims or None (never raises)."""
    try:
        payload, sig = str(ticket or "").split(".", 1)
        expect = _b64e(hmac.new(session_secret.encode(), payload.encode(),
                               hashlib.sha256).digest())
        if not hmac.compare_digest(expect, sig):
            return None
        data = json.loads(_b64d(payload).decode())
        moment = time.time() if now is None else now
        if int(data.get("exp", 0)) < int(moment):
            return None
        user = str(data.get("u", ""))
        if not user:
            return None
        return {"user": user, "nonce": str(data.get("n", "")),
                "exp": int(data.get("exp", 0))}
    except (ValueError, TypeError):
        return None


def locked(state: dict, now: float | None = None) -> bool:
    """True while the account lockout is in force."""
    moment = time.time() if now is None else now
    try:
        return float(state.get("locked_until", 0.0)) > moment
    except (TypeError, ValueError):
        return False
