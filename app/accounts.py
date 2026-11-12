"""Account registry: runtime users over the env seed (Phase 5, D-037).

Effective users = DEMO_USERS seed + registered_users overlay (the
overlay wins, so passwords and roles rotate and users deprovision
at runtime without env edits). Disabled overlay records are
excluded. New identity/commercial state is JSON-canonical; PG
parity follows the GAP-001 cutover decision.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

RUNTIME_MIN_PASSWORD_LENGTH = 12
MAX_USERNAME_CHARS = 64
MAX_CONTACT_CHARS = 254


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_username(name: str) -> str:
    """Clean username or raise USERNAME_INVALID."""
    clean = (name or "").strip()
    if not clean or ":" in clean or "," in clean:
        raise ValueError("USERNAME_INVALID: 1..64 chars, no : or ,")
    if len(clean) > MAX_USERNAME_CHARS:
        raise ValueError("USERNAME_INVALID: exceeds 64 chars")
    return clean


def validate_password(password: str) -> str:
    """Runtime-set passwords need length (env seeds are owner-managed)."""
    if len(password or "") < RUNTIME_MIN_PASSWORD_LENGTH:
        raise ValueError("PASSWORD_TOO_SHORT: need %d+ chars"
                         % RUNTIME_MIN_PASSWORD_LENGTH)
    return password


def validate_email(email: str) -> str:
    """Clean address ("" allowed) or raise EMAIL_INVALID."""
    clean = (email or "").strip()
    if not clean:
        return ""
    local, sep, domain = clean.partition("@")
    if (not sep or not local or "." not in domain
            or len(clean) > MAX_CONTACT_CHARS):
        raise ValueError("EMAIL_INVALID: bad address")
    return clean


def validate_phone(phone: str) -> str:
    """Digits-normalized phone ("" allowed) or raise PHONE_INVALID."""
    clean = (phone or "").strip().replace(" ", "").replace("-", "")
    if not clean:
        return ""
    digits = clean[1:] if clean.startswith("+") else clean
    if not digits.isdigit() or not 7 <= len(digits) <= 15:
        raise ValueError("PHONE_INVALID: use E.164 digits, 7..15")
    return "+" + digits


def resolve_users(store) -> dict[str, tuple[str, str]]:
    """Effective {name: (role, record)} with the overlay applied."""
    from app import auth as auth_mod
    from app import config as config_mod

    users = auth_mod.parse_users(config_mod.DEMO_USERS or "")
    for rec in store.state.get("registered_users", []):
        if not isinstance(rec, dict) or rec.get("disabled"):
            continue
        name = rec.get("username", "")
        if (name and rec.get("record", "").startswith("pbkdf2$")
                and rec.get("role") in auth_mod.ROLES):
            users[name] = (rec["role"], rec["record"])
    return users


def contact_taken(store, email: str, phone: str) -> bool:
    """True when a registered contact already claims email or phone."""
    for rec in store.state.get("registered_users", []):
        if not isinstance(rec, dict):
            continue
        if email and rec.get("email") == email:
            return True
        if phone and rec.get("phone") == phone:
            return True
    return False


def build_record(username: str, role: str, record: str,
                 email: str = "", phone: str = "",
                 origin: str = "admin") -> dict[str, Any]:
    """Assemble one registered-user record (hash already made)."""
    return {"username": username, "role": role, "record": record,
            "email": email, "phone": phone, "email_verified": False,
            "phone_verified": False, "disabled": False, "origin": origin,
            "created_at": _now()}


def public_user(rec: dict[str, Any]) -> dict[str, Any]:
    """API-safe projection (password record never leaves the server)."""
    return {key: rec.get(key) for key in
            ("username", "role", "email", "phone", "email_verified",
             "phone_verified", "disabled", "origin", "created_at")}
