"""Project configuration. Reads environment + local .env (names only, never logged)."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("DATA_DIR", ROOT / "data"))


def load_dotenv() -> list[str]:
    """Load KEY=VALUE lines from ROOT/.env without overriding real env vars.

    Returns the loaded key names only (never values).
    """
    loaded: list[str] = []
    path = ROOT / ".env"
    if not path.exists():
        return loaded
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")
            loaded.append(key)
    return loaded


load_dotenv()

MODEL_API_KEY = os.environ.get("MODEL_API_KEY", "")
META_MODEL_ID = os.environ.get("META_MODEL_ID", "muse-spark-1.3")
META_BASE_URL = os.environ.get("META_BASE_URL", "https://api.meta.ai/v1")

# Gap-closure (D-002): shared write token for hosted demos. When UNSET
# (local demo default) all endpoints stay open. When SET, state-changing
# POST endpoints require `Authorization: Bearer <token>`. This is a
# low-assurance shared credential (also baked into the demo frontend
# bundle), appropriate for staging demos — NOT user authentication.
DEMO_WRITE_TOKEN = os.environ.get("DEMO_WRITE_TOKEN", "")

# Zero-cost staging auth (Phase 5). SESSION_SECRET unset = auth DISABLED
# (open local demo, byte-identical behavior). Set = login enforcement on.
# DEMO_USERS format: "name:role:pbkdf2$iter$salt$hex,..." (generate records
# with `python -m app.auth hash`; roles: investigator, admin).
SESSION_SECRET = os.environ.get("SESSION_SECRET", "")
DEMO_USERS = os.environ.get("DEMO_USERS", "")


def _safe_int(raw: str | None, default: int) -> int:
    try:
        return int((raw or "").strip())
    except (ValueError, TypeError):
        return default


# Phase 6: AI cost controls. The daily cap counts persisted run ATTEMPTS
# (ai_runs started today, UTC) so restarts cannot reset it; 0 disables.
# The timeout bounds one model call — keep below the frontend's 35 s
# abort. Garbage values fall back to defaults (fail-safe, never crash).
AI_DAILY_CALL_LIMIT = _safe_int(
    os.environ.get("AI_DAILY_CALL_LIMIT"), 100)
AI_TIMEOUT_SECONDS = _safe_int(
    os.environ.get("AI_TIMEOUT_SECONDS"), 30)
if AI_TIMEOUT_SECONDS <= 0:
    AI_TIMEOUT_SECONDS = 30


def _frontend_origins() -> list[str]:
    raw = os.environ.get(
        "FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


FRONTEND_ORIGINS = _frontend_origins()


def cors_options() -> dict:
    """Single source of truth for CORSMiddleware wiring (also used by tests).

    Open local demo (SESSION_SECRET unset): byte-identical legacy policy.
    Staging (secret set, login armed): credentialed CORS so the HttpOnly
    session cookie flows Vercel -> Render, plus X-Requested-With through
    preflight (required CSRF header for cookie-authed POSTs). Origins stay
    an explicit allowlist in both modes — never "*".
    """
    armed = bool(SESSION_SECRET)
    headers = ["Content-Type", "X-Request-ID"]
    if armed:
        headers = headers + ["X-Requested-With"]
    return {
        "allow_origins": list(FRONTEND_ORIGINS),
        "allow_credentials": armed,
        "allow_methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": headers,
        "max_age": 600,
    }

STATE_PATH = DATA_DIR / "state.json"

# -- Phase 5.1 storage backend selection ------------------------------------
# STORE_BACKEND is validated and defaults to "json". JSON remains the active
# backend; "pg" enables the PostgreSQL adapter for scratch migration
# verification only. DATABASE_URL is never logged or returned by any API.
VALID_STORAGE_BACKENDS = ("json", "pg")


def validate_backend(value: str) -> str:
    """Normalize and validate a storage backend name (fail-fast)."""
    normalized = (value or "").strip().lower()
    if normalized not in VALID_STORAGE_BACKENDS:
        raise ValueError(
            f"UNKNOWN_STORAGE_BACKEND: {value!r} "
            f"(expected one of {list(VALID_STORAGE_BACKENDS)})"
        )
    return normalized


STORE_BACKEND = validate_backend(os.environ.get("STORE_BACKEND", "json"))
DATABASE_URL = os.environ.get("DATABASE_URL", "")
PG_CONNECT_TIMEOUT = int(os.environ.get("PG_CONNECT_TIMEOUT", "5"))
