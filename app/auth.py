"""Protected-demo authentication (stdlib only, no new dependencies).

Design (zero-cost staging):
- Stateless signed-cookie sessions (HMAC-SHA256, 12 h expiry). No server
  storage, so Render Free (no disk) and Neon-backed deployments all work.
- Demo users from env: DEMO_USERS="name:role:hash,name:role:hash" with
  PBKDF2-HMAC-SHA256 password records. Roles: investigator, admin.
- When SESSION_SECRET is UNSET (local demo default) auth is DISABLED and
  every endpoint behaves exactly as before (open). Setting the secret
  arms login enforcement. The write token (SEC-012) remains as a
  non-browser fallback credential when both are configured.
- CSRF: cookie-authed POSTs must carry an X-Requested-With header
  (SameSite=Lax + explicit header; token-authed calls are exempt since
  browsers never attach that header cross-origin by themselves).

Generate a password record (owner runs locally, never commits values):
    python -m app.auth hash
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time

SESSION_COOKIE = "csai_session"
SESSION_TTL_SECONDS = 12 * 3600
PBKDF2_ITERATIONS = 210_000
ROLES = ("investigator", "admin")
LOGIN_LIMIT_PER_MINUTE = 10


def hash_password(password: str, salt: bytes | None = None) -> str:
    if not password:
        raise ValueError("empty password")
    raw_salt = salt if salt is not None else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), raw_salt, PBKDF2_ITERATIONS)
    return "pbkdf2$%d$%s$%s" % (
        PBKDF2_ITERATIONS, raw_salt.hex(), digest.hex())


def verify_password(password: str, record: str) -> bool:
    try:
        scheme, iters, salt_hex, digest_hex = record.split("$", 3)
        if scheme != "pbkdf2":
            return False
        expect = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex),
            int(iters)).hex()
        return hmac.compare_digest(expect, digest_hex)
    except (ValueError, TypeError):
        return False


def parse_users(env_value: str) -> dict[str, tuple[str, str]]:
    """Parse DEMO_USERS into {name: (role, hash)}. Skips bad entries."""
    users: dict[str, tuple[str, str]] = {}
    for entry in (env_value or "").split(","):
        parts = entry.strip().split(":", 2)
        if len(parts) != 3:
            continue
        name, role, record = (p.strip() for p in parts)
        if not name or role not in ROLES or not record.startswith("pbkdf2$"):
            continue
        users[name] = (role, record)
    return users


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def create_session(username: str, role: str, secret: str,
                   now: float | None = None) -> str:
    moment = time.time() if now is None else now
    payload = _b64e(json.dumps(
        {"u": username, "r": role, "exp": int(moment) + SESSION_TTL_SECONDS,
         "n": secrets.token_hex(8)}, separators=(",", ":")).encode())
    sig = _b64e(hmac.new(secret.encode(), payload.encode(),
                         hashlib.sha256).digest())
    return payload + "." + sig


def verify_session(token: str, secret: str,
                   now: float | None = None) -> tuple[str, str] | None:
    """Return (username, role) or None. Never raises on bad input."""
    try:
        payload, sig = token.split(".", 1)
        expect = _b64e(hmac.new(secret.encode(), payload.encode(),
                               hashlib.sha256).digest())
        if not hmac.compare_digest(expect, sig):
            return None
        data = json.loads(_b64d(payload).decode())
        moment = time.time() if now is None else now
        if int(data.get("exp", 0)) < int(moment):
            return None
        user, role = str(data.get("u", "")), str(data.get("r", ""))
        if not user or role not in ROLES:
            return None
        return user, role
    except (ValueError, TypeError, KeyError):
        return None


if __name__ == "__main__":  # pragma: no cover - owner tooling
    import getpass
    import sys

    if len(sys.argv) != 2 or sys.argv[1] != "hash":
        print("usage: python -m app.auth hash")
        raise SystemExit(2)
    secret_in = getpass.getpass("password: ")
    print(hash_password(secret_in))
