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

# Gap-closure (D-002): shared write token for hosted staging. When UNSET
# (local default) all endpoints stay open. When SET, state-changing
# POST endpoints require `Authorization: Bearer <token>`. This is a
# low-assurance shared credential (also baked into the public frontend
# bundle), appropriate for staging — NOT user authentication.
DEMO_WRITE_TOKEN = os.environ.get("DEMO_WRITE_TOKEN", "")

# Zero-cost staging auth (Phase 5). SESSION_SECRET unset = auth DISABLED
# (open local mode, byte-identical behavior). Set = login enforcement on.
# DEMO_USERS format: "name:role:pbkdf2$iter$salt$hex,..." (generate records
# with `python -m app.auth hash`; roles: investigator, admin, auditor,
# demo_viewer).
SESSION_SECRET = os.environ.get("SESSION_SECRET", "")
SESSION_SECRET_PREVIOUS = os.environ.get(
    "SESSION_SECRET_PREVIOUS", "")
DEMO_USERS = os.environ.get("DEMO_USERS", "")
# D-014 user→tenant map: "alice:org_acme,bob:org_beta,...". Users
# absent from the map (or an empty map) resolve to DEFAULT_TENANT,
# preserving single-org behavior. Tenant slugs must match
# register_tenant(); invalid entries are skipped fail-safe.
USER_TENANTS = os.environ.get("USER_TENANTS", "")

# R09-F2: minimum HMAC signing-secret strength. A set-but-short secret
# is a misconfiguration: auth fails closed (503 AUTH_MISCONFIGURED)
# rather than signing sessions with weak key material. Unset/empty
# keeps the documented open local default.
MIN_SESSION_SECRET_LENGTH = 32


# CS_ENV: development (default) | staging | production. Only
# production changes behavior: the JSON store refuses synthetic
# seeding/reset there (fail-closed). Staging behaves like
# development. Set CS_ENV=production on the production service
# only, with a persistent DATA_DIR or database provisioned.
CS_ENV = os.environ.get("CS_ENV", "development")


def is_production() -> bool:
    """True only when CS_ENV selects the production environment."""
    return (CS_ENV or "").strip().lower() == "production"


def session_auth_armed() -> bool:
    """True only when a strong signing secret is configured."""
    return len(SESSION_SECRET or "") >= MIN_SESSION_SECRET_LENGTH




# MFA (D-022): roles that must complete TOTP enrollment before
# their sessions leave the pending state. Comma-separated
# allowlist; unknown roles are ignored. Empty disables it.
MFA_REQUIRED_ROLES = os.environ.get("MFA_REQUIRED_ROLES", "")


def mfa_required_roles() -> frozenset:
    """Roles requiring MFA (parsed from MFA_REQUIRED_ROLES)."""
    from app.auth import ROLES
    return frozenset(r.strip() for r in
                        (MFA_REQUIRED_ROLES or "").split(",")
                        if r.strip() in ROLES)
def session_secret_misconfigured() -> bool:
    """True when a secret is set but too weak to arm auth."""
    return bool(SESSION_SECRET) and not session_auth_armed()


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

# Gateway routing (D-047): per-provider daily call ceiling. 0
# disables the per-provider check; the global AI_DAILY_CALL_LIMIT
# still governs every call. Negative values clamp to 0.
AI_PROVIDER_DAILY_LIMIT = _safe_int(
    os.environ.get("AI_PROVIDER_DAILY_LIMIT"), 0)
if AI_PROVIDER_DAILY_LIMIT < 0:
    AI_PROVIDER_DAILY_LIMIT = 0
AI_TIMEOUT_SECONDS = _safe_int(
    os.environ.get("AI_TIMEOUT_SECONDS"), 30)
if AI_TIMEOUT_SECONDS <= 0:
    AI_TIMEOUT_SECONDS = 30

# Cost control: per-call ceiling on model output length, sent as
# `max_tokens` on every analysis and follow-up request. Garbage, zero,
# and negative values fall back to the default — a missing or hostile
# env value must never uncap spend or crash boot.
DEFAULT_AI_MAX_OUTPUT_TOKENS = 4096
AI_MAX_OUTPUT_TOKENS = _safe_int(
    os.environ.get("AI_MAX_OUTPUT_TOKENS"), DEFAULT_AI_MAX_OUTPUT_TOKENS)
if AI_MAX_OUTPUT_TOKENS <= 0:
    AI_MAX_OUTPUT_TOKENS = DEFAULT_AI_MAX_OUTPUT_TOKENS


def _frontend_origins() -> list[str]:
    raw = os.environ.get(
        "FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


FRONTEND_ORIGINS = _frontend_origins()


def cors_options() -> dict:
    """Single source of truth for CORSMiddleware wiring (also used by tests).

    Credentialed in BOTH modes: the frontend always sends
    credentials:"include" (required for the HttpOnly session cookie in
    armed staging), and browsers reject a credentialed response that
    lacks Access-Control-Allow-Credentials — with allow_credentials off,
    every local-mode browser fetch fails as BACKEND_UNREACHABLE (found by
    UGLS-02 Edge RTL QA). Origins stay an explicit allowlist in both
    modes — never "*" — so ACA-C:true is safe. X-Requested-With is
    allowlisted in BOTH modes (required CSRF header for
    cookie-authed unsafe methods; preflight allow is not validation).
    """
    # AI-REPAIR: X-Requested-With allowlisted in BOTH modes.
    headers = ["Content-Type", "X-Request-ID", "X-Requested-With"]
    # Former armed-only gate removed: local-mode preflights
    # failed without it (browsers: BACKEND_UNREACHABLE). CSRF intact.
    return {
        "allow_origins": list(FRONTEND_ORIGINS),
        # Always True: see docstring. Explicit origins only, never "*".
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "PATCH", "OPTIONS"],
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
# J3-P1: garbage must fall back to 5, never crash the import/boot.
PG_CONNECT_TIMEOUT = _safe_int(os.environ.get("PG_CONNECT_TIMEOUT"), 5)
if PG_CONNECT_TIMEOUT <= 0:
    PG_CONNECT_TIMEOUT = 5

# Phase 5 (D-037/D-040): self-registration (default OFF), trial
# enforcement on metered writes (default OFF), founder username
# (empty = no founder entitlement).
ALLOW_PUBLIC_REGISTRATION = os.environ.get("ALLOW_PUBLIC_REGISTRATION", "0")
TRIAL_ENFORCEMENT = os.environ.get("TRIAL_ENFORCEMENT", "0")
FOUNDER_USER = os.environ.get("FOUNDER_USER", "")


def public_registration_enabled() -> bool:
    """True only when the owner explicitly enables self-registration."""
    return (ALLOW_PUBLIC_REGISTRATION or "").strip() == "1"


def trial_enforcement_enabled() -> bool:
    """True only when the owner arms trial metering."""
    return (TRIAL_ENFORCEMENT or "").strip() == "1"


# Phase 5J (D-045): passkeys default OFF; RP identity for ceremony.
PASSKEYS_ENABLED = os.environ.get("PASSKEYS_ENABLED", "0")
RP_ID = os.environ.get("RP_ID", "")
RP_ORIGIN = os.environ.get("RP_ORIGIN", "")


def passkeys_enabled() -> bool:
    """True only when the owner explicitly enables passkeys."""
    return (PASSKEYS_ENABLED or "").strip() == "1"


# Telecom Identity: consent default OFF (kyc_match/sim_ownership always
# need explicit consent), retention default 90 days, abuse caps.
TELECOM_CONSENT_REQUIRED = os.environ.get("TELECOM_CONSENT_REQUIRED", "0")
TELECOM_RETENTION_DAYS = _safe_int(
    os.environ.get("TELECOM_RETENTION_DAYS"), 90)
TELECOM_ACTOR_PER_MIN = _safe_int(
    os.environ.get("TELECOM_ACTOR_PER_MIN"), 30)
TELECOM_SUBJECT_PER_DAY = _safe_int(
    os.environ.get("TELECOM_SUBJECT_PER_DAY"), 20)
if TELECOM_RETENTION_DAYS <= 0:
    TELECOM_RETENTION_DAYS = 90
if TELECOM_ACTOR_PER_MIN <= 0:
    TELECOM_ACTOR_PER_MIN = 30
if TELECOM_SUBJECT_PER_DAY <= 0:
    TELECOM_SUBJECT_PER_DAY = 20


def telecom_consent_required() -> bool:
    """True only when the owner requires consent for all lookups."""
    return (TELECOM_CONSENT_REQUIRED or "").strip() == "1"


# Geointelligence OS: quotas + retention mirror telecom defaults.
GEO_ACTOR_PER_MIN = _safe_int(
    os.environ.get("GEO_ACTOR_PER_MIN"), 30)
GEO_SUBJECT_PER_DAY = _safe_int(
    os.environ.get("GEO_SUBJECT_PER_DAY"), 20)
GEO_RETENTION_DAYS = _safe_int(
    os.environ.get("GEO_RETENTION_DAYS"), 90)
if GEO_ACTOR_PER_MIN <= 0:
    GEO_ACTOR_PER_MIN = 30
if GEO_SUBJECT_PER_DAY <= 0:
    GEO_SUBJECT_PER_DAY = 20
if GEO_RETENTION_DAYS <= 0:
    GEO_RETENTION_DAYS = 90
