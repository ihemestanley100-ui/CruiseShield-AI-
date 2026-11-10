"""CruiseShield AI hackathon vertical slice: pages + JSON API."""
from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (HTMLResponse, JSONResponse,
                                Response)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import abac as abac_mod
from app import accounts as accounts_mod
from app import agents as agents_mod
from app import ai_adapter, auth as auth_mod
from app import ai_gateway as ai_gateway_mod
from app import billing as billing_mod
from app import capabilities as cap_mod
from app import cases as cases_mod, evidence as evidence_mod
from app import connectors as conn_mod
from app import device_intel as device_mod
from app import geo_intel as geo_mod
from app import governance as gov_mod
from app import graph as graph_mod, graph_intel as gintel_mod
from app import industries as ind_mod
from app import intel_evidence as iev_mod
from app import intel_link as link_mod
from app import ip_intel as ip_mod
from app import login_risk as risk_mod
from app import mfa as mfa_mod
from app import notify as notify_mod
from app import orgs as orgs_mod
from app import passkeys as passkeys_mod
from app import payments as payments_mod
from app import pilot as pilot_mod
from app import ratelimit as ratelimit_mod
from app import replay as replay_mod, risk_intel as rintel_mod
from app import rules as rules_mod
from app import seed as seed_mod, simulate as simulate_mod
from app import telecom_providers as telecom_prov_mod
from app import telecom_registry as telecom_reg_mod
from app import telecom_verify as telecom_mod
from app import address_verify as address_mod
from app import identity_verify as identity_mod
from app import intel_auth as intelauth_mod
from app import intel_common as intelcommon_mod
from app import intel_providers as intelprov_mod
from app import investigation_map as invmap_mod
from app import location_obs as locobs_mod
from app import trusted_devices as trustdev_mod
from app import tenancy as tenancy_mod
from app import verify as verify_mod
from app import web3 as web3_mod
from app import detection as det_mod
from app import channels as chan_mod
from app import config as config_mod
from app.config import META_MODEL_ID, ROOT, cors_options
from app.models import EvidencePackage, RuleResult
from app.store import Store, storage_backend

AUTH_LOGIN_PATH = "/api/v1/auth/login"
MFA_CHALLENGE_PATH = "/api/v1/auth/mfa/challenge"

APP_VERSION = "1.0.0-p0"

app = FastAPI(title="CruiseShield AI", version=APP_VERSION)

# Render staging (SEC-009): transport-level body cap. SEC-001 caps fields
# AFTER JSON parsing; a giant body would be fully read first. Legitimate
# payloads are KBs (decision/sim/AI bodies ≤ ~50 KB worst case).
# Limitation: only enforced when Content-Length is present (chunked bodies
# without it rely on the hosting proxy's own limits).
MAX_BODY_BYTES = 1_000_000


@app.middleware("http")
async def body_size_guard(request: Request, call_next):
    length = request.headers.get("content-length", "")
    if length.isdigit() and int(length) > MAX_BODY_BYTES:
        return JSONResponse(status_code=413, content={
            "error": {"code": "BODY_TOO_LARGE",
                      "message": f"content-length {length} exceeds "
                                 f"{MAX_BODY_BYTES} bytes",
                      "trace_id": _trace(request)}})
    response = await call_next(request)
    # SEC-010: baseline secure headers (mirrors frontend next.config).
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = \
        "camera=(), microphone=(), geolocation=()"
    # R09-F4: HSTS only when the request arrived over TLS — direct
    # https or first X-Forwarded-Proto hop (TLS-terminating proxy,
    # same rule as the Secure cookie flag). Local plain-HTTP dev
    # gets no header. No includeSubDomains: the app shares parent
    # domains on managed hosting; no preload (one-way decision).
    first_proto = request.headers.get(
        "x-forwarded-proto", "").split(",")[0].strip().lower()
    if request.url.scheme == "https" or first_proto == "https":
        response.headers["Strict-Transport-Security"] = \
            "max-age=31536000"
    return response


# Paths the rate limiter never throttles (orchestrator + smoke checks).
RATE_LIMIT_EXEMPT = frozenset({"/api/v1/health", "/api/v1/ready",
                               "/system-health"})


# Paths reachable without login when auth is armed. Health/ready
# for orchestrators; login to obtain a session; legacy index + static so a
# logged-out visitor sees branding (all DATA endpoints stay gated).
AUTH_MODE_PATH = "/api/v1/auth/mode"
AUTH_OPEN_PATHS = frozenset({"/", "/api/v1/health", "/api/v1/ready",
                              "/system-health", AUTH_LOGIN_PATH,
                              AUTH_MODE_PATH, MFA_CHALLENGE_PATH})
# Canonical + deprecated alias (alias removal needs owner confirm).
AUTH_ADMIN_PREFIXES = ("/api/v1/platform/", "/api/v1/demo/")
# D-022: pending (mfa_pending) sessions may only reach these paths;
# everything else returns 403 MFA_REQUIRED until enrollment confirms.
# F-D1: methods that mutate state. The CSRF header check and the
# permission layer share this set (DELETE has no routes yet).
_UNSAFE_METHODS = ("POST", "PUT", "PATCH", "DELETE")


MFA_SESSION_PATHS = frozenset({
    "/api/v1/auth/mfa/enroll", "/api/v1/auth/mfa/confirm",
    "/api/v1/auth/mfa/status", "/api/v1/auth/mfa/disable",
    "/api/v1/auth/mfa/codes", "/api/v1/auth/logout",
    "/api/v1/auth/logout-all", "/api/v1/auth/me"})


@app.middleware("http")
async def session_guard(request: Request, call_next):
    """Phase 5: login enforcement (SEC-013). Inert when unconfigured."""
    if config_mod.session_secret_misconfigured():
        # R09-F2: weak secret fails closed — guarded paths refuse to
        # serve; only the always-open paths (health/ready/branding)
        # stay reachable. No session can be minted or validated.
        path = request.url.path
        if path not in AUTH_OPEN_PATHS and not path.startswith("/static/"):
            return JSONResponse(
                status_code=503,
                content={"error": {
                    "code": "AUTH_MISCONFIGURED",
                    "message": "session secret too weak to arm auth",
                    "trace_id": _trace(request)}})
        return await call_next(request)
    if config_mod.session_auth_armed():
        path = request.url.path
        if path not in AUTH_OPEN_PATHS and not path.startswith("/static/"):
            kind, role = _credential(request)
            if kind == "none":
                return JSONResponse(
                    status_code=401,
                    content={"error": {
                        "code": "LOGIN_REQUIRED",
                        "message": "login required",
                        "trace_id": _trace(request)}})
            # R1: admin prefixes need a genuine admin SESSION. The
            # shared write token (kind "token") must never satisfy an
            # admin gate — it previously skipped this check entirely
            # (F-PRIV-1: anonymous browsers outranked non-admin logins
            # on /api/v1/platform/* (and the deprecated /api/v1/demo/* alias).
            if path.startswith(AUTH_ADMIN_PREFIXES) and not (
                    kind == "session" and role == "admin"):
                return JSONResponse(
                    status_code=403,
                    content={"error": {
                        "code": "ADMIN_REQUIRED",
                        "message": "admin role required",
                        "trace_id": _trace(request)}})
            # D-022: a pending session (required role, MFA not yet
            # confirmed) cannot reach product paths — only the MFA
            # self-service paths that complete enrollment.
            if kind == "session" and path not in MFA_SESSION_PATHS:
                claims = _session_claims(request)
                if claims is not None and claims.get("mfa_pending"):
                    return JSONResponse(
                        status_code=403,
                        content={"error": {
                            "code": "MFA_REQUIRED",
                            "message": "complete MFA enrollment",
                            "trace_id": _trace(request)}})
            if kind == "session":
                if request.method in _UNSAFE_METHODS and not request.headers.get(
                        "x-requested-with"):
                    return JSONResponse(
                        status_code=403,
                        content={"error": {
                            "code": "CSRF_HEADER_REQUIRED",
                            "message": "X-Requested-With header required",
                            "trace_id": _trace(request)}})
                need = _required_perm(request.method, path)
                if not auth_mod.can(role, need):
                    return JSONResponse(
                        status_code=403,
                        content={"error": {
                            "code": "PERMISSION_DENIED",
                            "message": "role '%s' lacks '%s'" % (role, need),
                            "trace_id": _trace(request)}})
            request.state.auth_kind = kind
            request.state.auth_role = role
    return await call_next(request)


@app.middleware("http")
async def rate_limit_guard(request: Request, call_next):
    """D-001: per-IP fixed-window throttle (SEC-011)."""
    if request.url.path not in RATE_LIMIT_EXEMPT:
        peer = request.client.host if request.client else None
        key = ratelimit_mod.client_key(
            request.headers.get("x-forwarded-for"), peer)
        allowed, retry_after = ratelimit_mod.check_and_consume(key)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"error": {
                    "code": "RATE_LIMITED",
                    "message": f"limit {ratelimit_mod.LIMIT_PER_MINUTE} "
                               f"requests per {ratelimit_mod.WINDOW_SECONDS}s "
                               "exceeded",
                    "trace_id": _trace(request)}},
                headers={"Retry-After": str(retry_after)})
    return await call_next(request)


# CORS is registered LAST so it runs FIRST (outermost): guard
# short-circuits (401/403/429/413) must carry ACAO headers or browsers
# hide them as network failures, and preflights must be answered before
# the session guard. Registered earlier, armed-mode login was
# unreachable from any browser.
app.add_middleware(CORSMiddleware, **cors_options())
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "templates")
templates.env.globals["naira"] = evidence_mod.kobo_to_naira

store = Store()


class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


def _trace(request: Request) -> str:
    return request.headers.get("x-request-id", uuid.uuid4().hex[:12])


def _session_of(request: Request | None) -> tuple[str, str] | None:
    """Live session cookie -> (username, role), else None.

    J4: full live validation (signature, expiry, revocation, epoch,
    provisioning, role). Open when auth is unconfigured.
    """
    if not config_mod.session_auth_armed() or request is None:
        return None
    secret = config_mod.SESSION_SECRET or ""
    ring = [secret, config_mod.SESSION_SECRET_PREVIOUS or ""]
    users = accounts_mod.resolve_users(store)
    claims = auth_mod.verify_session_live(
        request.cookies.get(auth_mod.SESSION_COOKIE, ""), secret,
        store, users, secrets=ring)
    if claims is None:
        return None
    return claims["user"], claims["role"]


def _session_claims(request: Request | None) -> dict | None:
    """Live session claims (incl. nonce/iat) or None. J4 logout path."""
    if not config_mod.session_auth_armed() or request is None:
        return None
    secret = config_mod.SESSION_SECRET or ""
    ring = [secret, config_mod.SESSION_SECRET_PREVIOUS or ""]
    users = accounts_mod.resolve_users(store)
    return auth_mod.verify_session_live(
        request.cookies.get(auth_mod.SESSION_COOKIE, ""), secret,
        store, users, secrets=ring)


def _maybe_record_founder(username: str, request) -> None:
    """D-040: record the founder entitlement on first founder login."""
    founder = (config_mod.FOUNDER_USER or "").strip()
    if not founder or username != founder:
        return
    if store.founder_record() is not None:
        return
    billing_mod.ensure_founder(store, username)
    store.append_audit("user", username, "founder.active", "user",
                       username, "", "founder",
                       "founder entitlement recorded",
                       store.state["trace_id"], _trace(request))


def _device_allowed(request, username: str) -> None:
    """SEC-DEV: deny login/step-up from a revoked device (audited)."""
    peer = request.client.host if request.client else None
    ua_class, net_digest = risk_mod.session_fingerprint(
        ratelimit_mod.client_key(request.headers.get("x-forwarded-for"),
                                 peer),
        request.headers.get("user-agent", "") or "")
    if trustdev_mod.revoked(store, username, ua_class, net_digest):
        store.append_audit("user", username, "auth.login.device_revoked",
                           "session", username, "", "", ua_class,
                           store.state["trace_id"], _trace(request))
        raise AppError("DEVICE_REVOKED",
                       "device revoked for this user", 403)


def _track_session(request, token: str, username: str) -> None:
    """D-039: record an issued session for the sessions registry."""
    claims = auth_mod.parse_session(token,
                                    config_mod.SESSION_SECRET or "")
    if claims is None or request is None:
        return
    peer = request.client.host if request.client else None
    ua_class, net_digest = risk_mod.session_fingerprint(
        ratelimit_mod.client_key(request.headers.get("x-forwarded-for"),
                                 peer),
        request.headers.get("user-agent", "") or "")
    store.register_session(claims["nonce"], username, claims["exp"],
                           ua_class, net_digest)
    trustdev_mod.touch(store, username, ua_class, net_digest)


def _request_ctx(request: Request | None) -> tenancy_mod.TenantContext:
    """Tenant context for a request. D-014: the user resolves through
    USER_TENANTS; an empty map means single-org (all default);
    with a non-empty map, authed-but-unmapped users get 403.
    Single seam: tests monkeypatch this to drive cross-tenant paths.
    Refusals emit tenant.default_fallback audit first."""
    claims = _session_claims(request)
    mapping = tenancy_mod.parse_user_tenants(
        config_mod.USER_TENANTS or "")
    user = claims["user"] if claims else ""
    if claims and mapping and user not in mapping:
        store.append_audit(
            tenancy_mod.DEFAULT_TENANT, user,
            "tenant.default_fallback", "tenant",
            tenancy_mod.DEFAULT_TENANT, "",
            tenancy_mod.DEFAULT_TENANT,
            "authenticated user absent from USER_TENANTS",
            store.state["trace_id"], _trace(request))
        raise AppError(
            "AUTHORIZATION_REQUIRED",
            "authenticated user %s is not mapped to a tenant" % user,
            403)
    return tenancy_mod.context_for_user(user, mapping)


def _required_perm(method: str, path: str) -> str:
    """J4: permission a guarded request needs (token creds exempt)."""
    if path in ("/api/v1/auth/logout", "/api/v1/auth/logout-all",
                "/api/v1/auth/me", "/api/v1/auth/policy-check"):
        return "read"
    # D-022: MFA self-service mutates only the caller's own MFA record
    # (cross-user disable additionally requires the admin role inside
    # the handler), so read-only roles can complete enrollment.
    if path in MFA_SESSION_PATHS:
        return "read"
    if path.endswith("/audit") or "/ai-runs/" in path:
        return "audit_read" if method == "GET" else "write"
    if path.endswith("/ai-analysis") or path.endswith("/ai-followup"):
        return "ai_run"
    if method in _UNSAFE_METHODS:
        return "write"
    return "read"


def _token_ok(request: Request | None) -> bool:
    import hmac

    expected = config_mod.DEMO_WRITE_TOKEN or ""
    if not expected or request is None:
        return False
    presented = (request.headers.get("authorization", "") or "")
    if presented.startswith("Bearer "):
        presented = presented[len("Bearer "):]
    return bool(presented) and hmac.compare_digest(presented, expected)


def _require_write_token(request: Request | None) -> None:
    """D-002: shared write-token gate (SEC-012). Open when unconfigured.

    A valid login session with the write permission also satisfies the
    gate (J4: read-only roles cannot pass even when logged in)."""
    # BATCH-1: single live validation (was _session_of + _session_claims).
    claims = _session_claims(request)
    if claims is not None:
        # D-022: pending sessions cannot satisfy write gates even when
        # called past the middleware (direct handler invocation).
        if claims.get("mfa_pending"):
            raise AppError("MFA_REQUIRED", "complete MFA enrollment", 403)
        if not auth_mod.can(claims["role"], "write"):
            raise AppError("PERMISSION_DENIED",
                           "role '%s' cannot modify data" % claims["role"],
                           403)
        return
    client = _client_of(request)
    if client is not None:
        if "write" not in client["scopes"]:
            raise AppError("PERMISSION_DENIED",
                           "client scope lacks 'write'", 403)
        return
    expected = config_mod.DEMO_WRITE_TOKEN or ""
    if not expected:
        return
    if request is None or not _token_ok(request):
        raise AppError("WRITE_TOKEN_REQUIRED",
                       "valid write credential required", 401)


def _credential(request: Request) -> tuple[str, str | None]:
    """Return ("session", role) | ("token", None) | ("none", None).

    D-034: intentionally distinct from abac.subject_from_request,
    which is armed-mode-only; this honors tokens even unarmed so
    R2 attribution ("platform-token") never weakens.
    """
    session = _session_of(request)
    if session is not None:
        return "session", session[1]
    client = _client_of(request)
    if client is not None:
        return "client", client["client_id"]
    if _token_ok(request):
        return "token", None
    return "none", None


def _client_of(request: Request | None) -> dict | None:
    """SEC-CRED: verified per-client credential or None."""
    from app import api_credentials as cred_mod

    if request is None:
        return None
    presented = (request.headers.get("authorization", "") or "")
    if presented.startswith("Bearer "):
        presented = presented[len("Bearer "):]
    if not presented.startswith("csc_"):
        return None
    return cred_mod.verify(store, presented)


def _decision_actor(request: Request | None, claimed: str) -> str:
    """R2: token creds cannot self-assert an audit identity (F-AUDIT-1).

    Token-authenticated decisions are attributed to "platform-token";
    anything else is taken from the (authenticated or local) caller.
    """
    kind, ident = _credential(request)  # type: ignore[arg-type]
    if kind == "token":
        return "platform-token"
    if kind == "client":
        return "client:%s" % (ident or "unknown")
    return claimed


def _decision_actor_role(request):
    """GAP-017: session role for decision attribution (server-side only).

    Token/anonymous callers keep the legacy INVESTIGATOR default; a live
    session contributes its validated role, uppercased to the audit
    vocabulary. Client input never reaches this value.
    """
    kind, role = _credential(request)  # type: ignore[arg-type]
    if kind == "session" and role in auth_mod.ROLES:
        return role.upper()
    return cases_mod.DEFAULT_ACTOR_ROLE


def _require_login(request: Request | None) -> None:
    """R3: AI endpoints need an authenticated login session (F-QUOTA-1).

    Armed mode only — the unarmed local mode has no sessions and
    keeps working unchanged.
    """
    if config_mod.session_auth_armed() and _session_of(request) is None:
        raise AppError("AI_LOGIN_REQUIRED",
                       "authenticated login required for AI operations",
                       403)


@app.exception_handler(AppError)
async def _app_error(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status, content={
        "error": {"code": exc.code, "message": str(exc),
                  "trace_id": _trace(request)}})


def _domain_error(exc: ValueError, default_status: int = 400) -> AppError:
    text = str(exc)
    code, _, message = text.partition(":")
    code = code.strip() or "DOMAIN_ERROR"
    status = default_status
    if code in ("CASE_NOT_FOUND", "UNKNOWN_SCENARIO", "UNKNOWN_TRANSACTION",
                "UNKNOWN_EDGE", "INVESTIGATION_NOT_FOUND"):
        status = 404
    if code in ("TENANT_DENIED", "AUTHORIZATION_REQUIRED",
                "PRODUCTION_REFUSED"):
        status = 403
    if code == "CONSENT_REQUIRED":
        status = 409
    return AppError(code, message.strip() or text, status)


def _ensure_assessment(txn_id: str,
                       ctx: tenancy_mod.TenantContext | None = None
                       ) -> tuple[dict, dict, list[dict]]:
    if txn_id in store.state["risk"]:
        risk = store.state["risk"][txn_id]
        return (risk["transaction"], risk["network"],
                store.state["rule_results"][txn_id])
    txn = store.get_transaction(txn_id)
    if txn is None:
        raise AppError("UNKNOWN_TRANSACTION", txn_id, 404)
    if ctx is None:
        txns, edges = store.state["transactions"], store.state["edges"]
    else:
        if tenancy_mod.enforce_read(txn, ctx) is None:
            raise AppError("UNKNOWN_TRANSACTION", txn_id, 404)
        txns, _, edges = tenancy_mod.visible_graph(store.state, ctx)
    trace_id = store.state["trace_id"]
    results = rules_mod.evaluate(txn_id, txns, edges, trace_id)
    as_txn = rules_mod.assess(txn_id, "transaction", txns, edges,
                              results, trace_id)
    as_net = rules_mod.assess(txn_id, "network", txns, edges,
                              results, trace_id)
    return as_txn, as_net, [r.model_dump() for r in results]


# -- pages ---------------------------------------------------------------
def _page_context(request: Request) -> dict[str, Any]:
    return {"request": request, "app_version": APP_VERSION,
            "scenario_id": store.state["scenario_id"],
            "manifest": store.state["manifest"],
            "model_configured": ai_adapter.configured(),
            "model_id": META_MODEL_ID}


@app.get("/", response_class=HTMLResponse)
def command_center(request: Request):
    primary = store.state["primary_transaction_id"]
    txn = store.get_transaction(primary)
    risk_txn, risk_net, _ = _ensure_assessment(primary)
    ctx = _page_context(request)
    ctx.update({"txn": txn, "risk_txn": risk_txn, "risk_net": risk_net,
                "counts": store.state["manifest"]["expected_graph_counts"],
                "investigations": store.state["investigations"],
                "scenarios": seed_mod.available_scenarios()})
    return templates.TemplateResponse(request, "command.html", ctx)


@app.get("/investigations/{inv_id}", response_class=HTMLResponse)
def investigation_page(request: Request, inv_id: str):
    inv = tenancy_mod.enforce_read(store.get_investigation(inv_id), _request_ctx(request))
    if inv is None:
        raise AppError("UNKNOWN_INVESTIGATION", inv_id, 404)
    tctx = _request_ctx(request)
    txn = tenancy_mod.enforce_read(
        store.get_transaction(inv["transaction_id"]), tctx)
    if txn is None:
        raise AppError("UNKNOWN_INVESTIGATION", inv_id, 404)
    risk_txn, risk_net, rule_results = _ensure_assessment(
        inv["transaction_id"], tctx)
    case = tenancy_mod.enforce_read(next((c for c in store.state["cases"]
                 if c["investigation_id"] == inv_id), None), _request_ctx(request))
    package = store.state["evidence_packages"][inv_id]
    audits = [a for a in store.state["audits"]
              if a["target_id"] in (inv_id, case["case_id"] if case else "",
                                    inv["alert_id"])][:50]
    ctx = _page_context(request)
    ctx.update({"inv": inv, "txn": txn, "risk_txn": risk_txn,
                "risk_net": risk_net, "rule_results": rule_results,
                "case": case, "package": package,
                "allowed": cases_mod.allowed_transitions(case["status"]) if case else [],
                "decisions": cases_mod.DECISION_LABELS,
                "audits": audits,
                "ai_runs": [r for r in store.state["ai_runs"]
                            if r["evidence_package_id"] == package["package_id"]
                            and tenancy_mod.enforce_read(r, tctx) is not None],
                "simulations": [s for s in store.state["simulations"]
                                if tenancy_mod.enforce_read(s, tctx)
                                is not None],
                "nodes": store.state["nodes"], "edges": store.state["edges"]})
    return templates.TemplateResponse(request, "investigation.html", ctx)


@app.get("/system-health", response_class=HTMLResponse)
def system_health_page(request: Request):
    ctx = _page_context(request)
    ctx.update({"health": health()})
    return templates.TemplateResponse(request, "system_health.html", ctx)


# -- health / platform --------------------------------------------------------
def _counts_now() -> dict[str, int]:
    by_type: dict[str, int] = {}
    for node in store.state["nodes"]:
        by_type[node["node_type"]] = by_type.get(node["node_type"], 0) + 1
    return {"nodes": len(store.state["nodes"]), "edges": len(store.state["edges"]),
            "accounts": by_type.get("account", 0),
            "devices": by_type.get("device", 0),
            "phones": by_type.get("phone", 0),
            "merchants": by_type.get("merchant", 0),
            "beneficiaries": by_type.get("beneficiary", 0),
            "transactions": len(store.state["transactions"]),
            "events": len(store.state["events"])}


@app.get("/api/v1/health")
def health() -> dict[str, Any]:
    expected = store.state["manifest"]["expected_graph_counts"]
    actual = _counts_now()
    provenance_bad = graph_mod.validate_provenance(store.state["edges"])
    selected = storage_backend()
    checks = {
        "store": "PASS" if store.state.get("scenario_id") else "FAIL",
        "seed_integrity": ("PASS" if actual == expected
                           else f"FAIL expected={expected} actual={actual}"),
        "graph_provenance": ("PASS" if not provenance_bad
                             else f"FAIL edges={provenance_bad}"),
        "model_configured": ("PASS" if ai_adapter.configured()
                             else "NOT_CONFIGURED"),
        "storage_backend": f"PASS active={store.backend} selected={selected}",
        "pg": _pg_check(selected),
        "audit_chain": _audit_chain_check(),
    }
    exempt = {"model_configured", "audit_chain"} | ({"pg"} if selected != "pg" else set())
    blocking = [k for k in checks if k not in exempt]
    status = ("healthy" if all(str(checks[k]).startswith("PASS")
                               for k in blocking) else "degraded")
    return {"status": status, "version": APP_VERSION,
            "scenario_id": store.state["scenario_id"],
            "run_id": store.state["run_id"], "checks": checks}


def _pg_check(selected: str) -> str:
    """Phase 5.1 PostgreSQL check (additive; never leaks connection info)."""
    if selected != "pg":
        return "NOT_CONFIGURED"
    try:
        from app import db as db_mod
    except ImportError:
        return "FAIL driver unavailable"
    probe = db_mod.database_health()
    if not probe.get("reachable"):
        return f"FAIL {probe.get('reason', 'unreachable')}"
    if not probe.get("schema_version"):
        return "FAIL schema not initialized"
    counts = probe.get("counts", {})
    total = sum(counts.values()) if counts else 0
    return f"PASS schema={probe['schema_version']} rows={total}"


def _audit_chain_check() -> str:
    """AUD-04: presence-only audit-chain status for /health.

    Counts sealed vs legacy entries without creating keys, loading
    a keyring, or verifying signatures (verification needs the D-018
    ceremony keyring, unavailable here). No digests or key material
    leave this function -- counts only. Informational: health()
    exempts it from the blocking set.
    """
    audits = store.state["audits"]
    sealed = sum(1 for entry in audits if "audit_digest" in entry)
    if sealed:
        return f"PASS sealed={sealed} total={len(audits)}"
    if audits:
        return f"NOT_CONFIGURED legacy={len(audits)}"
    return "NOT_CONFIGURED no audit events"


@app.get("/api/v1/ready")
def ready() -> JSONResponse:
    """Readiness: JSON store loaded, plus PG reachable when selected."""
    selected = storage_backend()
    store_ok = bool(store.state.get("scenario_id"))
    pg_ok = True
    detail: dict[str, Any] = {"backend": store.backend,
                              "selected": selected, "store": store_ok}
    if selected == "pg":
        pg_check = _pg_check(selected)
        pg_ok = pg_check.startswith("PASS")
        detail["pg"] = pg_check
    ok = store_ok and pg_ok
    detail["ready"] = ok
    return JSONResponse(status_code=200 if ok else 503, content=detail)


def _session_cookie_attrs(request: Request) -> dict[str, Any]:
    """X-ORIGIN: cookie transport attributes shared by set + delete sites.

    Cross-site Netlify -> Render fetch withholds SameSite=Lax cookies, so
    use None whenever the channel is Secure; on plain-HTTP local dev
    browsers reject SameSite=None without Secure, so keep Lax there.
    Secure detection is the existing J3-P2 rule (Render terminates TLS).
    """
    forwarded = request.headers.get("x-forwarded-proto", "")
    first_hop = forwarded.split(",")[0].strip().lower()
    secure = request.url.scheme == "https" or first_hop == "https"
    return {"secure": secure, "samesite": "none" if secure else "lax"}


@app.post(AUTH_LOGIN_PATH)
def auth_login(body: dict[str, Any], request: Request) -> JSONResponse:
    """Phase 5: login. 503 when auth is not configured."""
    if config_mod.session_secret_misconfigured():
        raise AppError("AUTH_MISCONFIGURED",
                       "session secret too weak to arm auth", 503)
    secret = config_mod.SESSION_SECRET or ""
    if not secret:
        raise AppError("AUTH_DISABLED", "login is not configured", 503)
    peer = request.client.host if request.client else None
    login_key = "login:" + ratelimit_mod.client_key(
        request.headers.get("x-forwarded-for"), peer)
    allowed, retry_after = ratelimit_mod.check_and_consume(
        login_key, limit=auth_mod.LOGIN_LIMIT_PER_MINUTE)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"error": {"code": "LOGIN_RATE_LIMITED",
                               "message": "too many login attempts",
                               "trace_id": _trace(request)}},
            headers={"Retry-After": str(retry_after)})
    username = str((body or {}).get("username", "")).strip()
    password = str((body or {}).get("password", ""))
    users = accounts_mod.resolve_users(store)
    role, record = users.get(username, ("", "pbkdf2$210000$" + "0" * 32 +
                                        "$" + "0" * 64))
    if username not in users or not auth_mod.verify_password(password,
                                                             record):
        # R09-F3: audit rejected logins for brute-force forensics.
        # Actor/target carry the presented username only — never the
        # password, and no token/secret material exists on this path.
        store.append_audit("user", username or "unknown",
                           "auth.login.failed", "session",
                           username or "unknown", "", "",
                           "invalid username or password",
                           store.state["trace_id"], _trace(request))
        raise AppError("INVALID_CREDENTIALS",
                       "invalid username or password", 401)
    _device_allowed(request, username)
    # D-028: login-risk baseline (unknown-location detection).
    # Runs only after the password verifies: unknown users
    # and rate-limited attempts never learn a baseline.
    risk_level, risk_signals, risk_baseline = \
        risk_mod.assess(store.login_risk_for(username),
                        ratelimit_mod.client_key(
                            request.headers.get(
                                "x-forwarded-for"), peer),
                        request.headers.get("user-agent", "")
                        or "", time.time())
    store.save_login_risk(username, risk_baseline)
    if risk_level != "low":
        store.notify_user(
            username, "risk.login", "Unusual sign-in activity",
            "Sign-in scored %s: %s." % (risk_level,
                                        ", ".join(risk_signals)),
            level="warn")
        notify_mod.dispatch(store, "suspicious_login", username,
                            {"level": risk_level,
                             "signals": ", ".join(risk_signals)})
    mfa_state = store.mfa_state(username)
    # D-022: enrolled users step up via a single-use ticket (no session
    # cookie until the second factor verifies). Required-but-unenrolled
    # roles get a pending session that can only reach MFA self-service.
    if mfa_state["status"] == mfa_mod.STATUS_ACTIVE:
        ticket = mfa_mod.create_ticket(secret, username)
        store.append_audit("user", username, "auth.login.mfa_required",
                           "session", username, "", "", "step-up ticket",
                           store.state["trace_id"], _trace(request))
        return JSONResponse({"mfa_required": True, "ticket": ticket})
    pending = (role in config_mod.mfa_required_roles()
               and mfa_state["status"] != mfa_mod.STATUS_ACTIVE)
    token = auth_mod.create_session(username, role, secret,
                                    mfa_pending=pending)
    _track_session(request, token, username)
    store.append_audit("user", username, "auth.login", "session", username,
                       "", role, "login",
                       store.state["trace_id"], _trace(request))
    _maybe_record_founder(username, request)
    # The pending flag is additive-only: non-required logins keep the
    # exact historical body (test_login_success_sets_cookie).
    login_body: dict[str, Any] = {"user": username, "role": role}
    if pending:
        login_body["mfa_pending"] = True
    if risk_level != "low":
        login_body["risk"] = {"level": risk_level,
                                  "signals": risk_signals}
    response = JSONResponse(login_body)
    attrs = _session_cookie_attrs(request)
    response.set_cookie(auth_mod.SESSION_COOKIE, token,
                        max_age=auth_mod.SESSION_TTL_SECONDS,
                        httponly=True, secure=attrs["secure"],
                        samesite=attrs["samesite"], path="/")
    return response


@app.post("/api/v1/auth/logout")
def auth_logout(request: Request) -> JSONResponse:
    """J4: logout revokes this session server-side (not just the cookie)."""
    claims = _session_claims(request)
    if claims is not None:
        store.revoke_session(claims["nonce"], claims["exp"])
        store.drop_session(claims["nonce"])
        store.append_audit("user", claims["user"], "auth.logout",
                           "session", claims["user"], claims["role"], "",
                           "logout", store.state["trace_id"],
                           _trace(request))
    response = JSONResponse({"ok": True})
    attrs = _session_cookie_attrs(request)
    response.delete_cookie(auth_mod.SESSION_COOKIE, path="/",
                           secure=attrs["secure"],
                           samesite=attrs["samesite"])
    return response


@app.post("/api/v1/auth/logout-all")
def auth_logout_all(request: Request) -> JSONResponse:
    """J4: invalidate every session for the calling user.

    Nonce revocation kills tracked sessions deterministically (the
    second-resolution epoch alone misses same-second tokens); the
    epoch bump stays as the backstop for untracked tokens.
    """
    claims = _session_claims(request)
    if claims is None:
        raise AppError("LOGIN_REQUIRED", "login required", 401)
    store.bump_epoch(claims["user"])
    for entry in store.sessions_for(claims["user"]):
        store.revoke_session(entry["nonce"], entry["exp"])
        store.drop_session(entry["nonce"])
    store.append_audit("user", claims["user"], "auth.logout_all",
                       "session", claims["user"], claims["role"], "",
                       "logout-all", store.state["trace_id"],
                       _trace(request))
    response = JSONResponse({"ok": True})
    attrs = _session_cookie_attrs(request)
    response.delete_cookie(auth_mod.SESSION_COOKIE, path="/",
                           secure=attrs["secure"],
                           samesite=attrs["samesite"])
    return response


def _require_admin(request: Request) -> dict:
    """Full admin session or 403 (shared by admin endpoints)."""
    claims = _session_claims(request)
    if claims is None or claims["role"] != "admin":
        raise AppError("ADMIN_REQUIRED", "admin role required", 403)
    if claims.get("mfa_pending"):
        raise AppError("MFA_REQUIRED", "complete MFA enrollment", 403)
    return claims


@app.post("/api/v1/admin/users")
def admin_create_user(body: dict[str, Any], request: Request) -> dict[str, Any]:
    """D-037: runtime user provisioning (full admin session only)."""
    claims = _require_admin(request)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    try:
        username = accounts_mod.validate_username(body.get("username", ""))
        password = accounts_mod.validate_password(body.get("password", ""))
        role = body.get("role", "")
        if role not in auth_mod.ROLES:
            raise ValueError("ROLE_UNKNOWN: %s" % (role,))
        email = accounts_mod.validate_email(body.get("email", ""))
        phone = accounts_mod.validate_phone(body.get("phone", ""))
        if username in accounts_mod.resolve_users(store):
            raise ValueError("USERNAME_TAKEN: %s" % username)
        if accounts_mod.contact_taken(store, email, phone):
            raise ValueError("CONTACT_TAKEN: email or phone in use")
        rec = accounts_mod.build_record(
            username, role, auth_mod.hash_password(password),
            email, phone, origin="admin")
        store.upsert_registered_user(rec)
    except ValueError as exc:
        raise _domain_error(exc)
    audit = store.append_audit(
        "user", claims["user"], "user.provision", "user", username,
        "", role, "provisioned (origin admin)",
        store.state["trace_id"], _trace(request))
    return {"user": accounts_mod.public_user(rec), "audit": audit}


@app.post("/api/v1/auth/register")
def auth_register(body: dict[str, Any], request: Request):
    """D-037: self-registration (disabled unless explicitly enabled)."""
    if not config_mod.public_registration_enabled():
        raise AppError("REGISTRATION_DISABLED",
                       "self-registration is not enabled", 403)
    peer = request.client.host if request.client else None
    reg_key = "register:" + ratelimit_mod.client_key(
        request.headers.get("x-forwarded-for"), peer)
    allowed, retry_after = ratelimit_mod.check_and_consume(
        reg_key, limit=auth_mod.LOGIN_LIMIT_PER_MINUTE)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"error": {"code": "REGISTER_RATE_LIMITED",
                               "message": "too many registration attempts",
                               "trace_id": _trace(request)}},
            headers={"Retry-After": str(retry_after)})
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    try:
        username = accounts_mod.validate_username(body.get("username", ""))
        password = accounts_mod.validate_password(body.get("password", ""))
        email = accounts_mod.validate_email(body.get("email", ""))
        phone = accounts_mod.validate_phone(body.get("phone", ""))
        if username in accounts_mod.resolve_users(store):
            raise ValueError("USERNAME_TAKEN: %s" % username)
        if accounts_mod.contact_taken(store, email, phone):
            raise ValueError("CONTACT_TAKEN: email or phone in use")
        rec = accounts_mod.build_record(
            username, "investigator", auth_mod.hash_password(password),
            email, phone, origin="self")
        store.upsert_registered_user(rec)
        trial = billing_mod.ensure_trial(store, username)
    except ValueError as exc:
        raise _domain_error(exc)
    audit = store.append_audit(
        "user", username, "user.register", "user", username,
        "", "investigator", "self-registered (trial opened)",
        store.state["trace_id"], _trace(request))
    return {"user": accounts_mod.public_user(rec),
            "trial": {"status": trial["status"],
                      "ends_at": trial["ends_at"],
                      "credits": trial["credits"]},
            "audit": audit}


@app.post("/api/v1/auth/verify/request")
def verify_request(body: dict[str, Any], request: Request):
    """D-038: issue a verification token (delivery BLOCKED_EXTERNAL)."""
    secret = _mfa_armed()
    claims = _session_claims(request)
    if claims is None:
        raise AppError("LOGIN_REQUIRED", "login required", 401)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    purpose = body.get("purpose", "")
    if purpose not in verify_mod.PURPOSES:
        raise AppError("PURPOSE_UNKNOWN",
                       "purpose must be email|phone", 400)
    rec = store.registered_user(claims["user"])
    stored = ""
    if rec is not None:
        stored = rec.get("email") if purpose == "email" else rec.get("phone")
    if not stored:
        raise AppError("CONTACT_NOT_FOUND",
                       "no %s on record" % purpose, 404)
    target = body.get("target", "") or stored
    if target != stored:
        raise AppError("CONTACT_MISMATCH",
                       "target does not match the record", 400)
    peer = request.client.host if request.client else None
    key = "verify:" + ratelimit_mod.client_key(
        request.headers.get("x-forwarded-for"), peer)
    allowed, retry_after = ratelimit_mod.check_and_consume(
        key, limit=auth_mod.LOGIN_LIMIT_PER_MINUTE)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"error": {"code": "VERIFY_RATE_LIMITED",
                               "message": "too many verify requests",
                               "trace_id": _trace(request)}},
            headers={"Retry-After": str(retry_after)})
    verify_mod.issue_token(secret, claims["user"], purpose, stored)
    store.append_audit(
        "user", claims["user"], "verify.requested", "user",
        claims["user"], "", purpose, "token issued (delivery blocked)",
        store.state["trace_id"], _trace(request))
    return {"purpose": purpose,
            "target_masked": verify_mod.mask_contact(stored),
            "delivery": "BLOCKED_EXTERNAL",
            "expires_in": verify_mod.VERIFY_TTL_SECONDS}


@app.post("/api/v1/auth/verify/confirm")
def verify_confirm(body: dict[str, Any], request: Request) -> dict[str, Any]:
    """D-038: redeem a verification token for the caller's own contact."""
    secret = _mfa_armed()
    claims = _session_claims(request)
    if claims is None:
        raise AppError("LOGIN_REQUIRED", "login required", 401)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    parsed = verify_mod.parse_token(body.get("token", ""), secret)
    if parsed is None:
        raise AppError("VERIFY_INVALID", "invalid or expired token", 400)
    if parsed["user"] != claims["user"]:
        raise AppError("VERIFY_FOREIGN",
                       "token belongs to another user", 403)
    if not verify_mod.spend_token(store, parsed["purpose"],
                                  parsed["nonce"],
                                  float(parsed["exp"])):
        raise AppError("VERIFY_SPENT", "token already used", 410)
    rec = store.registered_user(claims["user"])
    key = "email" if parsed["purpose"] == "email" else "phone"
    if rec is None or rec.get(key) != parsed["target"]:
        raise AppError("CONTACT_MISMATCH",
                       "contact changed since issue", 400)
    rec[key + "_verified"] = True
    store.upsert_registered_user(rec)
    store.append_audit(
        "user", claims["user"], "verify.confirmed", "user",
        claims["user"], "", purpose_key(parsed["purpose"]),
        "contact verified", store.state["trace_id"], _trace(request))
    notify_mod.dispatch(store, "contact_verified", claims["user"],
                        {"purpose": parsed["purpose"]})
    return {"purpose": parsed["purpose"], "verified": True}


def purpose_key(purpose: str) -> str:
    """Audit detail key for a verification purpose."""
    return "email_verified" if purpose == "email" else "phone_verified"


@app.post("/api/v1/auth/password")
def auth_change_password(body: dict[str, Any],
                         request: Request) -> dict[str, Any]:
    """D-039: rotate the caller's password (all sessions die)."""
    claims = _session_claims(request)
    if claims is None:
        raise AppError("LOGIN_REQUIRED", "login required", 401)
    if claims.get("mfa_pending"):
        raise AppError("MFA_REQUIRED", "complete MFA enrollment", 403)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    entry = accounts_mod.resolve_users(store).get(claims["user"])
    if entry is None or not auth_mod.verify_password(
            str(body.get("current_password", "")), entry[1]):
        store.append_audit("user", claims["user"], "auth.password.failed",
                           "session", claims["user"], "", "",
                           "wrong current password",
                           store.state["trace_id"], _trace(request))
        raise AppError("INVALID_CREDENTIALS",
                       "current password is wrong", 401)
    try:
        new = accounts_mod.validate_password(body.get("new_password", ""))
    except ValueError as exc:
        raise _domain_error(exc)
    new_hash = auth_mod.hash_password(new)
    rec = store.registered_user(claims["user"])
    if rec is None:
        rec = accounts_mod.build_record(
            claims["user"], claims["role"], new_hash,
            origin="password-change")
    rec["record"] = new_hash
    store.upsert_registered_user(rec)
    store.bump_epoch(claims["user"])
    for entry in store.sessions_for(claims["user"]):
        store.revoke_session(entry["nonce"], entry["exp"])
        store.drop_session(entry["nonce"])
    store.append_audit("user", claims["user"], "auth.password.change",
                       "session", claims["user"], "", "",
                       "password rotated; sessions revoked",
                       store.state["trace_id"], _trace(request))
    notify_mod.dispatch(store, "password_changed", claims["user"], {})
    return {"ok": True, "reauthenticate": True}


@app.get("/api/v1/auth/sessions")
def list_sessions(request: Request) -> dict[str, Any]:
    """D-039: the caller's live sessions (digests only, no secrets)."""
    claims = _session_claims(request)
    if claims is None:
        raise AppError("LOGIN_REQUIRED", "login required", 401)
    return {"sessions": store.sessions_for(claims["user"])}


@app.post("/api/v1/auth/sessions/revoke")
def revoke_session(body: dict[str, Any],
                   request: Request) -> dict[str, Any]:
    """D-039: revoke one of the caller's own sessions by nonce."""
    claims = _session_claims(request)
    if claims is None:
        raise AppError("LOGIN_REQUIRED", "login required", 401)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    mine = [s for s in store.sessions_for(claims["user"])
            if s.get("nonce") == body.get("nonce")]
    if not mine:
        raise AppError("SESSION_UNKNOWN", "no such live session", 404)
    store.revoke_session(mine[0]["nonce"], mine[0]["exp"])
    store.drop_session(mine[0]["nonce"])
    store.append_audit("user", claims["user"], "session.revoke",
                       "session", claims["user"], "", "",
                       "session revoked by owner",
                       store.state["trace_id"], _trace(request))
    return {"ok": True, "dropped": True}


@app.get("/api/v1/account/notifications/preferences")
def get_notif_prefs(request: Request) -> dict[str, Any]:
    """D-039: the caller's notification preferences."""
    claims = _session_claims(request)
    if claims is None:
        raise AppError("LOGIN_REQUIRED", "login required", 401)
    return {"preferences": store.notif_prefs_for(claims["user"])}


@app.put("/api/v1/account/notifications/preferences")
def put_notif_prefs(body: dict[str, Any],
                    request: Request) -> dict[str, Any]:
    """D-039: update preferences (security notices stay always-on).

    No audit event: preference flips are not security-relevant
    (mirrors the deliberate mark-read quietness)."""
    claims = _session_claims(request)
    if claims is None:
        raise AppError("LOGIN_REQUIRED", "login required", 401)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    picked = {}
    for key in ("product", "marketing"):
        if key in body:
            if not isinstance(body[key], bool):
                raise AppError("PREF_INVALID",
                               "preference '%s' must be boolean" % key,
                               400)
            picked[key] = body[key]
    saved = store.save_notif_prefs(claims["user"], picked)
    return {"preferences": saved}


@app.get("/api/v1/account/entitlements")
def get_entitlements(request: Request) -> dict[str, Any]:
    """D-040: the caller's trial/subscription/founder status."""
    claims = _session_claims(request)
    if claims is None:
        raise AppError("LOGIN_REQUIRED", "login required", 401)
    founder = None
    if billing_mod.founder_active(store, claims["user"],
                                  config_mod.FOUNDER_USER or ""):
        founder = store.founder_record()
    return {"trial": store.trial_for(claims["user"]),
            "subscription": store.subscription_for(claims["user"]),
            "founder": founder,
            "enforcement": config_mod.trial_enforcement_enabled()}


@app.post("/api/v1/admin/subscriptions")
def admin_start_subscription(body: dict[str, Any],
                             request: Request) -> dict[str, Any]:
    """D-040: activate a plan (full admin session; references only)."""
    claims = _require_admin(request)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    try:
        rec = billing_mod.start_subscription(
            store, body.get("username", ""), body.get("plan", ""),
            body.get("evidence", ""))
    except ValueError as exc:
        raise _domain_error(exc)
    store.append_audit("user", claims["user"], "subscription.start",
                       "user", body.get("username", ""), "",
                       body.get("plan", ""), "plan activated",
                       store.state["trace_id"], _trace(request))
    return {"subscription": rec}


@app.post("/api/v1/admin/subscriptions/cancel")
def admin_cancel_subscription(body: dict[str, Any],
                              request: Request) -> dict[str, Any]:
    """D-040: cancel a plan (full admin session)."""
    claims = _require_admin(request)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    try:
        rec = billing_mod.cancel_subscription(store,
                                              body.get("username", ""))
    except ValueError as exc:
        raise _domain_error(exc)
    store.append_audit("user", claims["user"], "subscription.cancel",
                       "user", body.get("username", ""), "",
                       "cancelled", "plan cancelled",
                       store.state["trace_id"], _trace(request))
    return {"subscription": rec}


@app.post("/api/v1/billing/intents")
def create_intent(body: dict[str, Any],
                  request: Request) -> dict[str, Any]:
    """D-041: record a payment intent (manual reconciliation; no charge)."""
    claims = _session_claims(request)
    if claims is None:
        raise AppError("LOGIN_REQUIRED", "login required", 401)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    try:
        rec = payments_mod.create_intent(
            store, claims["user"], body.get("amount"),
            body.get("currency", ""), body.get("provider", ""),
            body.get("reference", ""))
    except ValueError as exc:
        raise _domain_error(exc)
    store.append_audit("user", claims["user"], "billing.intent",
                       "payment", rec["payment_id"], "",
                       rec["status"], "intent recorded (no charge)",
                       store.state["trace_id"], _trace(request))
    return {"payment": rec}


@app.get("/api/v1/billing/intents")
def list_intents(request: Request) -> dict[str, Any]:
    """D-041: the caller's own payment records."""
    claims = _session_claims(request)
    if claims is None:
        raise AppError("LOGIN_REQUIRED", "login required", 401)
    return {"payments": store.payments_for(claims["user"])}


@app.post("/api/v1/billing/intents/{payment_id}/cancel")
def cancel_intent(payment_id: str, request: Request) -> dict[str, Any]:
    """D-041: cancel one of the caller's own pending intents."""
    claims = _session_claims(request)
    if claims is None:
        raise AppError("LOGIN_REQUIRED", "login required", 401)
    rec = store.payment(payment_id)
    if rec is None or rec.get("user") != claims["user"]:
        raise AppError("PAYMENT_NOT_FOUND", "no such payment", 404)
    try:
        updated = payments_mod.transition(store, payment_id, "cancelled")
    except ValueError as exc:
        raise _domain_error(exc)
    store.append_audit("user", claims["user"], "billing.cancel",
                       "payment", payment_id, rec["status"], "cancelled",
                       "intent cancelled",
                       store.state["trace_id"], _trace(request))
    return {"payment": updated}


@app.post("/api/v1/admin/payments/refund")
def admin_refund(body: dict[str, Any],
                 request: Request) -> dict[str, Any]:
    """D-041: mark a succeeded payment refunded (full admin session)."""
    claims = _require_admin(request)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    if not (body.get("evidence") or "").strip():
        raise AppError("REFUND_EVIDENCE_REQUIRED",
                       "cite the refund artifact", 400)
    rec = store.payment(body.get("payment_id", ""))
    if rec is None:
        raise AppError("PAYMENT_NOT_FOUND", "no such payment", 404)
    try:
        updated = payments_mod.transition(store, body["payment_id"],
                                          "refunded")
    except ValueError as exc:
        raise _domain_error(exc)
    store.append_audit("user", claims["user"], "billing.refund",
                       "payment", body["payment_id"], "succeeded",
                       "refunded", "refund recorded (manual)",
                       store.state["trace_id"], _trace(request))
    return {"payment": updated}


@app.post("/api/v1/billing/web3/prepare")
def web3_prepare(body: dict[str, Any],
                 request: Request) -> dict[str, Any]:
    """D-041: record a stablecoin intent (nothing broadcasts)."""
    claims = _session_claims(request)
    if claims is None:
        raise AppError("LOGIN_REQUIRED", "login required", 401)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    try:
        rec = web3_mod.prepare_transfer(
            store, claims["user"], body.get("asset", ""),
            body.get("chain", ""), body.get("amount"),
            body.get("address", ""))
    except ValueError as exc:
        raise _domain_error(exc)
    store.append_audit("user", claims["user"], "billing.web3.prepare",
                       "payment", rec["payment_id"], "", "awaiting_tx",
                       "web3 intent recorded",
                       store.state["trace_id"], _trace(request))
    return {"payment": rec}


@app.post("/api/v1/billing/web3/tx")
def web3_record_tx(body: dict[str, Any],
                   request: Request) -> dict[str, Any]:
    """D-041: attach an operator tx hash (stays unverified)."""
    claims = _session_claims(request)
    if claims is None:
        raise AppError("LOGIN_REQUIRED", "login required", 401)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    rec = store.payment(body.get("payment_id", ""))
    if rec is None or rec.get("user") != claims["user"]:
        raise AppError("PAYMENT_NOT_FOUND", "no such payment", 404)
    try:
        updated = web3_mod.record_tx(store, body["payment_id"],
                                     body.get("tx_hash", ""))
    except ValueError as exc:
        raise _domain_error(exc)
    store.append_audit("user", claims["user"], "billing.web3.tx",
                       "payment", body["payment_id"], "awaiting_tx",
                       "awaiting_confirmations", "tx hash recorded",
                       store.state["trace_id"], _trace(request))
    return {"payment": updated}


@app.get("/api/v1/admin/org")
def get_org(request: Request) -> dict[str, Any]:
    """D-042: organization profile (admin only)."""
    _require_admin(request)
    return {"profile": store.org_profile()}


@app.put("/api/v1/admin/org")
def put_org(body: dict[str, Any],
            request: Request) -> dict[str, Any]:
    """D-042: update the organization profile (admin only)."""
    claims = _require_admin(request)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    current = store.org_profile()
    try:
        name = current["name"]
        if "name" in body:
            name = orgs_mod.validate_org_name(body.get("name", ""))
        contact = accounts_mod.validate_email(
            body.get("contact_email", current["contact_email"]))
    except ValueError as exc:
        raise _domain_error(exc)
    profile = store.save_org_profile(name, contact)
    store.append_audit("user", claims["user"], "org.update", "org",
                       "org", "", name, "profile updated",
                       store.state["trace_id"], _trace(request))
    return {"profile": profile}


@app.get("/api/v1/admin/members")
def list_members(request: Request) -> dict[str, Any]:
    """D-042: membership view (admin only; hashes never included)."""
    _require_admin(request)
    return {"members": orgs_mod.members(store)}


# SEC-REV: audit actions that change who can access what. Everything
# else (logins, ingests, decisions, runs) is out of review scope.
ACCESS_REVIEW_ACTIONS = frozenset({
    "user.provision", "user.register", "user.disable", "user.enable",
    "invitation.issue", "invitation.redeem",
    "mfa.confirm", "mfa.disable",
})


@app.get("/api/v1/admin/access-review")
def access_review(request: Request) -> dict[str, Any]:
    """SEC-REV: access-grant deltas + current snapshot (admin only).

    Read-only aggregate over the audit trail: every grant, revoke,
    invitation, and MFA-enrollment change in audit order, plus the
    current membership view. Hashes and secrets never included
    (members() excludes them; audit reasons carry none).
    """
    _require_admin(request)
    events = [
        {"at": entry.get("timestamp", ""),
         "action": entry["action"],
         "actor": entry.get("actor_id", ""),
         "target": entry.get("target_id", ""),
         "detail": entry.get("reason", "")}
        for entry in store.state["audits"]
        if isinstance(entry, dict)
        and entry.get("action") in ACCESS_REVIEW_ACTIONS
    ]
    return {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                          time.gmtime()),
            "events": events,
            "current": orgs_mod.members(store)}


@app.post("/api/v1/admin/users/disable")
def admin_disable_user(body: dict[str, Any],
                       request: Request) -> dict[str, Any]:
    """D-042: disable a user (self and founder protected)."""
    claims = _require_admin(request)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    try:
        username = accounts_mod.validate_username(body.get("username", ""))
        result = orgs_mod.set_disabled(store, username, True,
                                       claims["user"],
                                       config_mod.FOUNDER_USER or "")
    except ValueError as exc:
        raise _domain_error(exc)
    store.append_audit("user", claims["user"], "user.disable", "user",
                       username, "", "disabled", "access revoked",
                       store.state["trace_id"], _trace(request))
    return result


@app.post("/api/v1/admin/users/enable")
def admin_enable_user(body: dict[str, Any],
                      request: Request) -> dict[str, Any]:
    """D-042: re-enable a user."""
    claims = _require_admin(request)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    try:
        username = accounts_mod.validate_username(body.get("username", ""))
        result = orgs_mod.set_disabled(store, username, False,
                                       claims["user"],
                                       config_mod.FOUNDER_USER or "")
    except ValueError as exc:
        raise _domain_error(exc)
    store.append_audit("user", claims["user"], "user.enable", "user",
                       username, "", "enabled", "access restored",
                       store.state["trace_id"], _trace(request))
    return result


@app.post("/api/v1/admin/invitations")
def admin_invite(body: dict[str, Any],
                 request: Request) -> dict[str, Any]:
    """D-042: invite a user (token relayed manually until delivery)."""
    claims = _require_admin(request)
    secret = _mfa_armed()
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    try:
        issued = orgs_mod.issue_invitation(
            store, body.get("email", ""), body.get("role", ""),
            claims["user"], secret)
    except ValueError as exc:
        raise _domain_error(exc)
    store.append_audit("user", claims["user"], "invitation.issue",
                       "invitation", issued["invitation"]["nonce"], "",
                       issued["invitation"]["role"], "invitation issued",
                       store.state["trace_id"], _trace(request))
    return {"email": issued["invitation"]["email"],
            "role": issued["invitation"]["role"],
            "exp": issued["invitation"]["exp"],
            "token": issued["token"]}


@app.post("/api/v1/auth/invitations/redeem")
def redeem_invitation(body: dict[str, Any], request: Request):
    """D-042: redeem an invitation (authorization in itself)."""
    secret = _mfa_armed()
    peer = request.client.host if request.client else None
    key = "redeem:" + ratelimit_mod.client_key(
        request.headers.get("x-forwarded-for"), peer)
    allowed, retry_after = ratelimit_mod.check_and_consume(
        key, limit=auth_mod.LOGIN_LIMIT_PER_MINUTE)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"error": {"code": "REDEEM_RATE_LIMITED",
                               "message": "too many redeem attempts",
                               "trace_id": _trace(request)}},
            headers={"Retry-After": str(retry_after)})
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    try:
        result = orgs_mod.redeem_invitation(
            store, body.get("token", ""), body.get("username", ""),
            body.get("password", ""), secret)
    except ValueError as exc:
        raise _domain_error(exc)
    user = result["user"]["username"]
    store.append_audit("user", user, "invitation.redeem", "user", user,
                       "", result["user"]["role"], "invitation redeemed",
                       store.state["trace_id"], _trace(request))
    return {"user": result["user"],
            "trial": {"status": result["trial"]["status"],
                      "ends_at": result["trial"]["ends_at"],
                      "credits": result["trial"]["credits"]}}


def _passkeys_ready() -> None:
    """Flag + RP configuration gate for the passkey endpoints."""
    if not config_mod.passkeys_enabled():
        raise AppError("PASSKEYS_DISABLED", "passkeys are not enabled", 403)
    if not (config_mod.RP_ID or "").strip() or \
            not (config_mod.RP_ORIGIN or "").strip():
        raise AppError("PASSKEYS_MISCONFIGURED",
                       "RP identity not configured", 503)


@app.post("/api/v1/auth/passkey/register/options")
def passkey_register_options(body: dict[str, Any] | None,
                             request: Request) -> dict[str, Any]:
    """D-045: begin passkey enrollment (session)."""
    _passkeys_ready()
    claims = _session_claims(request)
    if claims is None:
        raise AppError("LOGIN_REQUIRED", "login required", 401)
    display = str((body or {}).get("display_name", "")) or claims["user"]
    return passkeys_mod.registration_options(
        store, claims["user"], display, config_mod.RP_ID)


@app.post("/api/v1/auth/passkey/register/verify")
def passkey_register_verify(body: dict[str, Any],
                            request: Request) -> dict[str, Any]:
    """D-045: finish passkey enrollment (session)."""
    _passkeys_ready()
    claims = _session_claims(request)
    if claims is None:
        raise AppError("LOGIN_REQUIRED", "login required", 401)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    try:
        credential = passkeys_mod.verify_registration(
            store, claims["user"], body.get("response", {}),
            config_mod.RP_ID, config_mod.RP_ORIGIN,
            body.get("challenge_id", ""))
    except ValueError as exc:
        raise _domain_error(exc)
    store.append_audit("user", claims["user"], "passkey.register",
                       "passkey", credential["credential_id"], "",
                       "active", "passkey enrolled",
                       store.state["trace_id"], _trace(request))
    return {"credential_id": credential["credential_id"]}


@app.post("/api/v1/auth/passkey/authenticate/options")
def passkey_auth_options(body: dict[str, Any], request: Request):
    """D-045: begin passkey login (throttled; 404 hides nothing extra)."""
    _passkeys_ready()
    peer = request.client.host if request.client else None
    key = "passkey-options:" + ratelimit_mod.client_key(
        request.headers.get("x-forwarded-for"), peer)
    allowed, retry_after = ratelimit_mod.check_and_consume(
        key, limit=auth_mod.LOGIN_LIMIT_PER_MINUTE)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"error": {"code": "PASSKEY_RATE_LIMITED",
                               "message": "too many passkey attempts",
                               "trace_id": _trace(request)}},
            headers={"Retry-After": str(retry_after)})
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    try:
        return passkeys_mod.authentication_options(
            store, str(body.get("username", "")))
    except ValueError as exc:
        if str(exc).startswith("CREDENTIALS_NONE"):
            raise AppError("CREDENTIALS_NONE",
                           "no passkeys for this user", 404)
        raise _domain_error(exc)


@app.post("/api/v1/auth/passkey/authenticate/verify")
def passkey_auth_verify(body: dict[str, Any], request: Request):
    """D-045: passkey login (replaces the password, not MFA policy)."""
    _passkeys_ready()
    peer = request.client.host if request.client else None
    key = "passkey-verify:" + ratelimit_mod.client_key(
        request.headers.get("x-forwarded-for"), peer)
    allowed, retry_after = ratelimit_mod.check_and_consume(
        key, limit=auth_mod.LOGIN_LIMIT_PER_MINUTE)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"error": {"code": "PASSKEY_RATE_LIMITED",
                               "message": "too many passkey attempts",
                               "trace_id": _trace(request)}},
            headers={"Retry-After": str(retry_after)})
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    username = str(body.get("username", ""))
    try:
        passkeys_mod.verify_assertion(
            store, username, body.get("response", {}),
            config_mod.RP_ID, config_mod.RP_ORIGIN,
            body.get("challenge_id", ""))
    except ValueError as exc:
        raise _domain_error(exc)
    entry = accounts_mod.resolve_users(store).get(username)
    if entry is None:
        raise AppError("INVALID_CREDENTIALS", "unknown user", 401)
    role = entry[0]
    pending = (role in config_mod.mfa_required_roles()
               and store.mfa_state(username).get("status")
               != mfa_mod.STATUS_ACTIVE)
    _device_allowed(request, username)
    token = auth_mod.create_session(
        username, role, config_mod.SESSION_SECRET or "",
        mfa_pending=pending)
    _track_session(request, token, username)
    _maybe_record_founder(username, request)
    store.append_audit("user", username, "auth.login.passkey", "session",
                       username, "", role, "passkey login",
                       store.state["trace_id"], _trace(request))
    login_body: dict[str, Any] = {"user": username, "role": role}
    if pending:
        login_body["mfa_pending"] = True
    response = JSONResponse(login_body)
    attrs = _session_cookie_attrs(request)
    response.set_cookie(auth_mod.SESSION_COOKIE, token,
                        max_age=auth_mod.SESSION_TTL_SECONDS,
                        httponly=True, secure=attrs["secure"],
                        samesite=attrs["samesite"], path="/")
    return response


@app.get("/api/v1/auth/passkey/credentials")
def list_passkeys(request: Request) -> dict[str, Any]:
    """D-045: the caller's passkeys (key material excluded)."""
    _passkeys_ready()
    claims = _session_claims(request)
    if claims is None:
        raise AppError("LOGIN_REQUIRED", "login required", 401)
    return {"credentials": [
        {"credential_id": c["credential_id"],
         "created_at": c.get("created_at", 0),
         "sign_count": c.get("sign_count", 0)}
        for c in store.passkeys_for(claims["user"])]}


@app.post("/api/v1/auth/passkey/credentials/remove")
def remove_passkey(body: dict[str, Any],
                   request: Request) -> dict[str, Any]:
    """D-045: remove one of the caller's passkeys."""
    _passkeys_ready()
    claims = _session_claims(request)
    if claims is None:
        raise AppError("LOGIN_REQUIRED", "login required", 401)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    cid = str(body.get("credential_id", ""))
    if not store.delete_passkey_credential(cid, claims["user"]):
        raise AppError("CREDENTIAL_UNKNOWN", "no such passkey", 404)
    store.append_audit("user", claims["user"], "passkey.remove",
                       "passkey", cid, "", "removed", "passkey removed",
                       store.state["trace_id"], _trace(request))
    return {"ok": True, "removed": True}


def _mfa_armed() -> str:
    """D-022: MFA needs armed session auth; return the signing secret."""
    if config_mod.session_secret_misconfigured():
        raise AppError("AUTH_MISCONFIGURED",
                       "session secret too weak to arm auth", 503)
    secret = config_mod.SESSION_SECRET or ""
    if not secret:
        raise AppError("AUTH_DISABLED", "login is not configured", 503)
    return secret


def _mfa_claims(request: Request) -> dict:
    """Live session claims (pending or full) or 401 LOGIN_REQUIRED."""
    claims = _session_claims(request)
    if claims is None:
        raise AppError("LOGIN_REQUIRED", "login required", 401)
    return claims


def _mfa_set_cookie(response: JSONResponse, request: Request,
                    username: str, role: str) -> None:
    """Issue a full (non-pending) session cookie after step-up."""
    _device_allowed(request, username)
    token = auth_mod.create_session(username, role,
                                    config_mod.SESSION_SECRET or "")
    _track_session(request, token, username)
    _maybe_record_founder(username, request)
    attrs = _session_cookie_attrs(request)
    response.set_cookie(auth_mod.SESSION_COOKIE, token,
                        max_age=auth_mod.SESSION_TTL_SECONDS,
                        httponly=True, secure=attrs["secure"],
                        samesite=attrs["samesite"], path="/")


def _mfa_fail(state: dict, username: str, action: str,
              request: Request, now: float) -> None:
    """Record a failed MFA attempt; lock the account at the ceiling.

    Audit detail carries counts only — never codes, tickets, or secrets.
    """
    state["failed"] = int(state.get("failed", 0)) + 1
    detail = "invalid second factor"
    if state["failed"] >= mfa_mod.MFA_MAX_FAILED:
        state["locked_until"] = now + mfa_mod.MFA_LOCKOUT_SECONDS
        detail = "account locked after %d failures" % state["failed"]
    store.save_mfa_state(username, state)
    store.append_audit("user", username, action, "session", username,
                       "", "", detail,
                       store.state["trace_id"], _trace(request))


@app.post("/api/v1/auth/mfa/enroll")
def mfa_enroll(request: Request) -> JSONResponse:
    """D-022: start TOTP enrollment. Returns the secret + recovery codes
    (shown once); the enrollment activates only after /confirm proves
    the code. Re-enrolling bumps the counter, retiring the old secret."""
    secret = _mfa_armed()
    claims = _mfa_claims(request)
    username = claims["user"]
    state = store.mfa_state(username)
    if state["status"] == mfa_mod.STATUS_ACTIVE:
        raise AppError("MFA_ALREADY_ACTIVE",
                       "MFA already active; disable it first", 409)
    counter = int(state.get("counter", 0)) + 1
    codes = mfa_mod.new_recovery_codes()
    state.update({"status": mfa_mod.STATUS_PENDING, "counter": counter,
                  "last_counter": -1,
                  "recovery_hashes": [mfa_mod.hash_recovery_code(c)
                                      for c in codes],
                  "failed": 0, "locked_until": 0.0,
                  "enrolled_at": time.time(), "confirmed_at": 0.0})
    store.save_mfa_state(username, state)
    store.append_audit("user", username, "mfa.enroll", "session", username,
                       "", "", "enrollment pending confirmation",
                       store.state["trace_id"], _trace(request))
    derived = mfa_mod.derive_secret(secret, username, counter)
    return JSONResponse({"secret": mfa_mod.secret_b32(derived),
                         "uri": mfa_mod.provisioning_uri(username,
                                                         derived),
                         "recovery_codes": codes})


@app.post("/api/v1/auth/mfa/confirm")
def mfa_confirm(body: dict[str, Any],
                request: Request) -> JSONResponse:
    """D-022: activate a pending enrollment by proving the TOTP code.
    Issues a full session cookie (clears the pending state)."""
    secret = _mfa_armed()
    claims = _mfa_claims(request)
    username = claims["user"]
    state = store.mfa_state(username)
    if state["status"] == mfa_mod.STATUS_ACTIVE:
        raise AppError("MFA_ALREADY_ACTIVE", "MFA already active", 409)
    if state["status"] != mfa_mod.STATUS_PENDING:
        raise AppError("MFA_NOT_PENDING", "call /mfa/enroll first", 409)
    now = time.time()
    if mfa_mod.locked(state, now):
        raise AppError("MFA_LOCKED", "too many failures; retry later", 423)
    derived = mfa_mod.derive_secret(secret, username,
                                    int(state.get("counter", 0)))
    matched = mfa_mod.verify_totp(
        derived, (body or {}).get("code", ""), now,
        int(state.get("last_counter", -1)))
    if matched is None:
        _mfa_fail(state, username, "mfa.confirm.failed", request, now)
        raise AppError("INVALID_MFA_CODE", "invalid code", 401)
    state.update({"status": mfa_mod.STATUS_ACTIVE,
                  "last_counter": matched, "failed": 0,
                  "locked_until": 0.0, "confirmed_at": now})
    store.save_mfa_state(username, state)
    store.append_audit("user", username, "mfa.confirm", "session", username,
                       "", "", "enrollment confirmed",
                       store.state["trace_id"], _trace(request))
    store.notify_user(
        username, "mfa.enabled",
        "Two-factor authentication enabled",
        "TOTP enrollment confirmed for your account.")
    notify_mod.dispatch(store, "mfa_enabled", username, {})
    response = JSONResponse(
        {"ok": True,
         "recovery_remaining": len(state.get("recovery_hashes", []))})
    _mfa_set_cookie(response, request, username, claims["role"])
    return response


@app.get("/api/v1/auth/mfa/status")
def mfa_status(request: Request) -> dict[str, Any]:
    """D-022: caller's enrollment status + requirement + codes left."""
    _mfa_armed()
    claims = _mfa_claims(request)
    state = store.mfa_state(claims["user"])
    return {"status": state["status"],
            "required": claims["role"] in config_mod.mfa_required_roles(),
            "recovery_remaining": len(state.get("recovery_hashes", []))}


@app.post(MFA_CHALLENGE_PATH)
def mfa_challenge(body: dict[str, Any],
                  request: Request) -> JSONResponse:
    """D-022: second-factor step-up. Open path: the single-use ticket in
    the body is the credential (unpredictable + single-use, so no CSRF
    exposure); rate-limited like login. Accepts a TOTP code or a
    one-time recovery code."""
    secret = _mfa_armed()
    peer = request.client.host if request.client else None
    challenge_key = "mfa:" + ratelimit_mod.client_key(
        request.headers.get("x-forwarded-for"), peer)
    allowed, retry_after = ratelimit_mod.check_and_consume(
        challenge_key, limit=auth_mod.LOGIN_LIMIT_PER_MINUTE)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"error": {"code": "LOGIN_RATE_LIMITED",
                               "message": "too many MFA attempts",
                               "trace_id": _trace(request)}},
            headers={"Retry-After": str(retry_after)})
    ticket = mfa_mod.parse_ticket((body or {}).get("ticket", ""), secret)
    if ticket is None:
        raise AppError("INVALID_MFA_TICKET",
                       "invalid or expired ticket", 401)
    username = ticket["user"]
    users = accounts_mod.resolve_users(store)
    if username not in users:
        raise AppError("INVALID_MFA_TICKET", "unknown user", 401)
    role = users[username][0]
    state = store.mfa_state(username)
    now = time.time()
    if mfa_mod.locked(state, now):
        raise AppError("MFA_LOCKED", "too many failures; retry later", 423)
    # Single-use BEFORE verification: a spent ticket never verifies
    # twice (one attempt per login; a mistype means logging in again).
    if not store.spend_mfa_ticket(ticket["nonce"], float(ticket["exp"])):
        raise AppError("MFA_TICKET_SPENT", "ticket already used", 401)
    recovery = (body or {}).get("recovery_code", "")
    if recovery:
        digest = mfa_mod.hash_recovery_code(recovery)
        hashes = list(state.get("recovery_hashes", []))
        if digest not in hashes:
            _mfa_fail(state, username, "mfa.challenge.failed",
                      request, now)
            raise AppError("INVALID_MFA_CODE",
                           "invalid recovery code", 401)
        hashes.remove(digest)
        state.update({"recovery_hashes": hashes, "failed": 0,
                      "locked_until": 0.0})
        store.save_mfa_state(username, state)
        store.append_audit("user", username, "mfa.challenge", "session",
                           username, "", "", "recovery code accepted",
                           store.state["trace_id"], _trace(request))
        store.notify_user(
            username, "mfa.recovery_used", "Recovery code used",
            "A recovery code signed in to your account; %d"
            " remaining." % len(hashes),
            level="warn")
        notify_mod.dispatch(store, "recovery_used", username,
                            {"remaining": str(len(hashes))})
        response = JSONResponse({"user": username, "role": role,
                                 "recovery_remaining": len(hashes)})
        _mfa_set_cookie(response, request, username, role)
        return response
    if state["status"] != mfa_mod.STATUS_ACTIVE:
        raise AppError("MFA_NOT_ACTIVE", "no active enrollment", 409)
    derived = mfa_mod.derive_secret(secret, username,
                                    int(state.get("counter", 0)))
    matched = mfa_mod.verify_totp(
        derived, (body or {}).get("code", ""), now,
        int(state.get("last_counter", -1)))
    if matched is None:
        _mfa_fail(state, username, "mfa.challenge.failed", request, now)
        raise AppError("INVALID_MFA_CODE", "invalid code", 401)
    state.update({"last_counter": matched, "failed": 0,
                  "locked_until": 0.0})
    store.save_mfa_state(username, state)
    store.append_audit("user", username, "mfa.challenge", "session",
                       username, "", "", "totp accepted",
                       store.state["trace_id"], _trace(request))
    response = JSONResponse({"user": username, "role": role})
    _mfa_set_cookie(response, request, username, role)
    return response


@app.post("/api/v1/auth/mfa/disable")
def mfa_disable(body: dict[str, Any],
                request: Request) -> JSONResponse:
    """D-022: remove an enrollment. Self-disable proves the current TOTP
    code (or aborts an unconfirmed enrollment); admins with a full
    session may disable another user (audited, no code needed)."""
    secret = _mfa_armed()
    claims = _mfa_claims(request)
    target = str((body or {}).get("username", "") or claims["user"])
    users = accounts_mod.resolve_users(store)
    if target not in users:
        raise AppError("UNKNOWN_USER", "unknown user", 404)
    if target != claims["user"] and (
            claims["role"] != "admin" or claims.get("mfa_pending")):
        raise AppError("ADMIN_REQUIRED", "admin role required", 403)
    state = store.mfa_state(target)
    if state["status"] == mfa_mod.STATUS_NONE:
        raise AppError("MFA_NOT_ACTIVE", "no enrollment to disable", 409)
    now = time.time()
    if target == claims["user"]:
        if state["status"] == mfa_mod.STATUS_PENDING:
            pass  # aborting your own unconfirmed enrollment: no proof
        else:
            if mfa_mod.locked(state, now):
                raise AppError("MFA_LOCKED",
                               "too many failures; retry later", 423)
            derived = mfa_mod.derive_secret(
                secret, target, int(state.get("counter", 0)))
            matched = mfa_mod.verify_totp(
                derived, (body or {}).get("code", ""), now,
                int(state.get("last_counter", -1)))
            if matched is None:
                _mfa_fail(state, target, "mfa.disable.failed",
                          request, now)
                raise AppError("INVALID_MFA_CODE", "invalid code", 401)
    fresh = mfa_mod.blank_state()
    fresh["counter"] = int(state.get("counter", 0))
    store.save_mfa_state(target, fresh)
    store.append_audit("user", claims["user"], "mfa.disable", "session",
                       target, "", "", "enrollment removed",
                       store.state["trace_id"], _trace(request))
    store.notify_user(
        target, "mfa.disabled",
        "Two-factor authentication disabled",
        "Enrollment removed%s." % (
            "" if target == claims["user"]
            else " by %s" % claims["user"]),
        level="warn")
    notify_mod.dispatch(store, "mfa_disabled", target,
                        {"actor": claims["user"]})
    return JSONResponse({"ok": True})


@app.post("/api/v1/auth/mfa/codes")
def mfa_codes(body: dict[str, Any],
              request: Request) -> JSONResponse:
    """D-022: rotate recovery codes (proves the current TOTP code).
    The old set is invalidated immediately."""
    secret = _mfa_armed()
    claims = _mfa_claims(request)
    username = claims["user"]
    state = store.mfa_state(username)
    if state["status"] != mfa_mod.STATUS_ACTIVE:
        raise AppError("MFA_NOT_ACTIVE", "no active enrollment", 409)
    now = time.time()
    if mfa_mod.locked(state, now):
        raise AppError("MFA_LOCKED", "too many failures; retry later", 423)
    derived = mfa_mod.derive_secret(secret, username,
                                    int(state.get("counter", 0)))
    matched = mfa_mod.verify_totp(
        derived, (body or {}).get("code", ""), now,
        int(state.get("last_counter", -1)))
    if matched is None:
        _mfa_fail(state, username, "mfa.codes.failed", request, now)
        raise AppError("INVALID_MFA_CODE", "invalid code", 401)
    codes = mfa_mod.new_recovery_codes()
    state.update({"recovery_hashes": [mfa_mod.hash_recovery_code(c)
                                      for c in codes],
                  "last_counter": matched})
    store.save_mfa_state(username, state)
    store.append_audit("user", username, "mfa.codes", "session", username,
                       "", "", "recovery codes rotated",
                       store.state["trace_id"], _trace(request))
    return JSONResponse({"recovery_codes": codes})


@app.get("/api/v1/auth/me")
def auth_me(request: Request) -> dict[str, Any]:
    session = _session_of(request)
    if session is None:
        raise AppError("LOGIN_REQUIRED", "login required", 401)
    username, role = session
    return {"user": username, "role": role,
            "permissions": sorted(auth_mod.PERMISSIONS.get(role, ()))}


@app.post("/api/v1/auth/policy-check")
def policy_check(body: dict[str, Any] | None,
                 request: Request) -> dict[str, Any]:
    """D-025: evaluate the ABAC policy for the CALLER (session/token).

    Powers permission-aware views. Never evaluates other subjects and
    never leaks policy internals beyond allow/deny + reason."""
    subject = abac_mod.subject_from_request(request)
    if subject["kind"] == "none":
        raise AppError("LOGIN_REQUIRED", "login required", 401)
    action = str((body or {}).get("action", ""))
    resource = (body or {}).get("resource") or {}
    if not isinstance(resource, dict):
        resource = {}
    allowed, reason = abac_mod.decide(subject, action, resource)
    return {"allowed": allowed, "reason": reason,
            "subject": {"user": subject["user"], "role": subject["role"],
                        "kind": subject["kind"]},
            "action": action}


def _agent_subject(request: Request) -> dict[str, Any]:
    """Agents are an interactive-only surface: a login session (full
    or pending-MFA) is required; the shared service token is denied.
    The tenant comes from the request seam so agent reads stay scoped."""
    subject = abac_mod.subject_from_request(request)
    subject["tenant"] = _request_ctx(request).tenant_id
    if subject["kind"] != "session":
        raise AppError("AGENT_SESSION_REQUIRED",
                       "login session required for agents", 403)
    return subject


def _agent_error(exc: ValueError) -> AppError:
    code = str(exc).partition(":")[0].strip()
    if code in ("AGENT_UNKNOWN", "AGENT_PLAN_UNKNOWN"):
        status = 404
    elif code in ("AGENT_TOOL_DENIED", "AGENT_FORBIDDEN"):
        status = 403
    elif code in ("AGENT_PLAN_STATE", "AGENT_PLAN_EXPIRED"):
        status = 409
    else:
        status = 400
    return _domain_error(exc, default_status=status)


@app.get("/api/v1/agents")
def agents_registry() -> dict[str, Any]:
    """Governed agent manifests + tool catalogue (§11)."""
    return {"agents": agents_mod.manifests(),
            "tools": agents_mod.tools()}


@app.post("/api/v1/agents/{agent_id}/propose")
def agent_propose(agent_id: str, body: dict[str, Any] | None,
                  request: Request) -> JSONResponse:
    """Propose a tool call; auto-approved agents run immediately."""
    _require_login(request)
    subject = _agent_subject(request)
    try:
        plan, run = agents_mod.propose(
            store, agent_id, (body or {}).get("tool", ""),
            (body or {}).get("args", {}), subject)
    except ValueError as exc:
        raise _agent_error(exc)
    store.append_audit("user", subject["user"], "agent.propose",
                       "agent-plan", plan["plan_id"], "",
                       plan["status"], "%s/%s" % (agent_id,
                                                 plan["tool"]),
                       store.state["trace_id"], _trace(request))
    if run is not None:
        store.append_audit("user", subject["user"], "agent.run",
                           "agent-run", run["run_id"], plan["plan_id"],
                           run["status"], plan["tool"],
                           store.state["trace_id"], _trace(request))
    return JSONResponse({"plan": plan, "run": run})


@app.post("/api/v1/agents/plans/{plan_id}/approve")
def agent_approve(plan_id: str, request: Request) -> JSONResponse:
    """Human approval executes a PENDING plan (admin/manage only)."""
    _require_login(request)
    subject = _agent_subject(request)
    try:
        run = agents_mod.approve(store, plan_id, subject)
    except ValueError as exc:
        raise _agent_error(exc)
    store.append_audit("user", subject["user"], "agent.approve",
                       "agent-run", run["run_id"], plan_id,
                       run["status"], run["tool"],
                       store.state["trace_id"], _trace(request))
    return JSONResponse({"run": run})


@app.get("/api/v1/agents/runs")
def agent_runs(request: Request, limit: int = 50) -> dict[str, Any]:
    """Recorded agent runs, newest last (session-only, tenant-scoped)."""
    _require_login(request)
    _agent_subject(request)
    if limit < 1 or limit > 200:
        raise AppError("FILTER_INVALID", "limit must be 1..200", 400)
    runs = tenancy_mod.filter_visible(store.agent_run_list(),
                                      _request_ctx(request))
    return {"runs": runs[-limit:], "count": len(runs)}


@app.get("/api/v1/capabilities")
def capabilities_registry() -> dict[str, Any]:
    """§14 A–O product-intelligence map with live verification."""
    return {"capabilities": cap_mod.registry(),
            "verification": cap_mod.verify()}


def _gov_subject(request: Request, action: str,
                 kind: str) -> dict[str, Any]:
    """ABAC-enforce a governance action (sensitive: full session)."""
    subject = abac_mod.subject_from_request(request)
    subject["tenant"] = _request_ctx(request).tenant_id
    allowed, reason = abac_mod.decide(subject, action, {"kind": kind})
    if not allowed:
        if subject["kind"] == "none":
            raise AppError("LOGIN_REQUIRED", "login required", 401)
        raise AppError("GOV_FORBIDDEN", reason, 403)
    return subject


def _gov_error(exc: ValueError) -> AppError:
    code = str(exc).partition(":")[0].strip()
    if code == "GOV_TRANSITION":
        status = 409
    elif code in ("GOV_APPROVER", "GOV_SEPARATION"):
        status = 403
    else:
        status = 400
    return _domain_error(exc, default_status=status)


def _gov_audit(subject: dict, action: str, target_type: str,
               target_id: str, previous: str, new: str,
               request: Request) -> None:
    store.append_audit("user", subject["user"], action, target_type,
                       target_id, previous, new, new,
                       store.state["trace_id"], _trace(request))


@app.post("/api/v1/governance/sar")
def sar_create(body: dict[str, Any] | None,
               request: Request) -> JSONResponse:
    """Draft a SAR handoff package (sensitive, audited, tenant-scoped)."""
    subject = _gov_subject(request, "write", "sar")
    ctx = _request_ctx(request)
    case_id = str((body or {}).get("case_id", ""))
    if tenancy_mod.enforce_read(store.get_case(case_id), ctx) is None:
        raise AppError("CASE_NOT_FOUND", case_id, 404)
    try:
        sar = gov_mod.create_sar(case_id, (body or {}).get("summary",
                                                           ""),
                                 subject["user"])
    except ValueError as exc:
        raise _gov_error(exc)
    tenancy_mod.stamp(sar, ctx)
    store.sar_save(sar)
    _gov_audit(subject, "gov.sar.create", "sar", sar["sar_id"], "",
               "DRAFT", request)
    return JSONResponse(sar)


@app.get("/api/v1/governance/sar")
def sar_list(request: Request) -> dict[str, Any]:
    """List SAR drafts (sensitive read, tenant-scoped)."""
    _gov_subject(request, "read", "sar")
    items = tenancy_mod.filter_visible(store.sar_list(),
                                       _request_ctx(request))
    return {"sars": items, "count": len(items)}


@app.post("/api/v1/governance/sar/{sar_id}/transition")
def sar_transition(sar_id: str, body: dict[str, Any] | None,
                   request: Request) -> JSONResponse:
    """Move a SAR along its flow (READY/FILED need admin)."""
    to = str((body or {}).get("to", ""))
    action = "approve" if to in ("READY", "FILED") else "write"
    subject = _gov_subject(request, action, "sar")
    sar = tenancy_mod.enforce_read(store.sar_get(sar_id),
                                   _request_ctx(request))
    if sar is None:
        raise AppError("SAR_NOT_FOUND", sar_id, 404)
    before = sar["status"]
    try:
        gov_mod.transition_sar(sar, to, subject["user"],
                               str((body or {}).get("note", "")),
                               subject["role"])
    except ValueError as exc:
        raise _gov_error(exc)
    store.sar_save(sar)
    _gov_audit(subject, "gov.sar.transition", "sar", sar_id, before,
               sar["status"], request)
    return JSONResponse(sar)


@app.post("/api/v1/governance/dsr")
def dsr_create(body: dict[str, Any] | None,
               request: Request) -> JSONResponse:
    """Open a data-subject request (sensitive, audited, tenant-scoped)."""
    subject = _gov_subject(request, "write", "dsr")
    try:
        dsr = gov_mod.create_dsr((body or {}).get("subject_ref", ""),
                                 (body or {}).get("kind", ""),
                                 (body or {}).get("details", ""),
                                 subject["user"])
    except ValueError as exc:
        raise _gov_error(exc)
    tenancy_mod.stamp(dsr, _request_ctx(request))
    store.dsr_save(dsr)
    _gov_audit(subject, "gov.dsr.create", "dsr", dsr["dsr_id"], "",
               "RECEIVED", request)
    return JSONResponse(dsr)


@app.get("/api/v1/governance/dsr")
def dsr_list(request: Request) -> dict[str, Any]:
    """List data-subject requests (sensitive read, tenant-scoped)."""
    _gov_subject(request, "read", "dsr")
    items = tenancy_mod.filter_visible(store.dsr_list(),
                                       _request_ctx(request))
    return {"dsrs": items, "count": len(items)}


@app.post("/api/v1/governance/dsr/{dsr_id}/transition")
def dsr_transition(dsr_id: str, body: dict[str, Any] | None,
                   request: Request) -> JSONResponse:
    """Move a DSR along its flow (FULFILLED/REJECTED need admin)."""
    to = str((body or {}).get("to", ""))
    action = "approve" if to in ("FULFILLED", "REJECTED") else "write"
    subject = _gov_subject(request, action, "dsr")
    dsr = tenancy_mod.enforce_read(store.dsr_get(dsr_id),
                                   _request_ctx(request))
    if dsr is None:
        raise AppError("DSR_NOT_FOUND", dsr_id, 404)
    before = dsr["status"]
    try:
        gov_mod.transition_dsr(dsr, to, subject["user"],
                               str((body or {}).get("note", "")),
                               subject["role"])
    except ValueError as exc:
        raise _gov_error(exc)
    store.dsr_save(dsr)
    _gov_audit(subject, "gov.dsr.transition", "dsr", dsr_id, before,
               dsr["status"], request)
    return JSONResponse(dsr)


@app.post("/api/v1/governance/holds")
def hold_place(body: dict[str, Any] | None,
               request: Request) -> JSONResponse:
    """Place a legal hold (admin only, audited, tenant-scoped)."""
    subject = _gov_subject(request, "approve", "hold")
    try:
        hold = gov_mod.place_hold((body or {}).get("resource_kind", ""),
                                  (body or {}).get("resource_id", ""),
                                  (body or {}).get("reason", ""),
                                  subject["user"])
    except ValueError as exc:
        raise _gov_error(exc)
    tenancy_mod.stamp(hold, _request_ctx(request))
    store.hold_save(hold)
    _gov_audit(subject, "gov.hold.place", "hold", hold["hold_id"], "",
               "ACTIVE", request)
    return JSONResponse(hold)


@app.get("/api/v1/governance/holds")
def hold_list(request: Request) -> dict[str, Any]:
    """List legal holds (sensitive read, tenant-scoped)."""
    _gov_subject(request, "read", "hold")
    items = tenancy_mod.filter_visible(store.hold_list(),
                                       _request_ctx(request))
    return {"holds": items, "count": len(items)}


@app.post("/api/v1/governance/holds/{hold_id}/release")
def hold_release(hold_id: str, body: dict[str, Any] | None,
                 request: Request) -> JSONResponse:
    """Release a legal hold (admin only, reason required)."""
    subject = _gov_subject(request, "approve", "hold")
    hold = tenancy_mod.enforce_read(store.hold_get(hold_id),
                                    _request_ctx(request))
    if hold is None:
        raise AppError("HOLD_NOT_FOUND", hold_id, 404)
    try:
        gov_mod.release_hold(hold, (body or {}).get("reason", ""),
                             subject["user"])
    except ValueError as exc:
        raise _gov_error(exc)
    store.hold_save(hold)
    _gov_audit(subject, "gov.hold.release", "hold", hold_id, "ACTIVE",
               "RELEASED", request)
    return JSONResponse(hold)


@app.get(AUTH_MODE_PATH)
def auth_mode() -> dict[str, Any]:
    return {"auth_enabled": config_mod.session_auth_armed()}


# Deprecated compat alias (D-019: removal needs owner confirm).
@app.get("/api/v1/demo/scenarios", deprecated=True)
@app.get("/api/v1/platform/scenarios")
def platform_scenarios() -> dict[str, Any]:
    return {"scenarios": seed_mod.available_scenarios(),
            "active_scenario_id": store.state["scenario_id"]}


# Deprecated compat alias (D-019: removal needs owner confirm).
@app.post("/api/v1/demo/reset", deprecated=True)
@app.post("/api/v1/platform/reset")
def platform_reset(request: Request,
               body: dict[str, Any] | None = None) -> dict[str, Any]:
    _require_write_token(request)
    scenario_id = (body or {}).get("scenario_id", "scn_primary")
    try:
        return store.reset(scenario_id)
    except ValueError as exc:
        raise _domain_error(exc)


# Deprecated compat alias (D-019: removal needs owner confirm).
@app.post("/api/v1/demo/scenarios/{scenario_id}/start", deprecated=True)
@app.post("/api/v1/platform/scenarios/{scenario_id}/start")
def platform_start(scenario_id: str, request: Request) -> dict[str, Any]:
    _require_write_token(request)
    try:
        result = store.reset(scenario_id)
    except ValueError as exc:
        raise _domain_error(exc)
    inv = store.state["investigations"][0]
    result["investigation_id"] = inv["investigation_id"]
    result["url"] = f"/investigations/{inv['investigation_id']}"
    return result


# Deprecated compat alias (D-019: removal needs owner confirm).
@app.post("/api/v1/demo/judge-start", deprecated=True)
@app.post("/api/v1/platform/judge-start")
def judge_start(request: Request) -> dict[str, Any]:
    _require_write_token(request)
    result = store.reset("scn_primary")
    inv = store.state["investigations"][0]
    result["investigation_id"] = inv["investigation_id"]
    result["url"] = f"/investigations/{inv['investigation_id']}"
    return result


@app.get("/api/v1/industries")
def industries_catalog() -> dict[str, Any]:
    """Public industry-module catalogue (Level 14 §6 registry)."""
    items = ind_mod.registry()
    return {"industries": items, "count": len(items)}


@app.get("/api/v1/industries/pilot-readiness")
def industries_pilot_readiness() -> dict[str, Any]:
    """Pilot-readiness evaluation for all 45 modules (PHASE H)."""
    reports = pilot_mod.evaluate_all()
    ready = sorted(r["id"] for r in reports if r["ready"])
    return {"modules": reports, "ready_ids": ready,
            "ready_count": len(ready), "total": len(reports)}


@app.post("/api/v1/industries/{ident}/promote")
def industry_promote(ident: str, body: dict[str, Any] | None,
                     request: Request) -> JSONResponse:
    """Promote a TESTING module to PILOT (write-gated, audited)."""
    _require_write_token(request)
    try:
        pilot_mod.promote(ident, (body or {}).get("evidence", ""))
    except ValueError as exc:
        code = str(exc).partition(":")[0].strip()
        status = 404 if code == "INDUSTRY_UNKNOWN" else (
            409 if code in ("PILOT_STATUS", "PILOT_NOT_READY") else 400)
        raise _domain_error(exc, default_status=status)
    session = _session_of(request)
    if session is not None:
        actor = session[0]
    elif _token_ok(request):
        actor = "platform-token"
    else:
        actor = "anonymous"
    store.append_audit("user", actor, "industry.promote", "industry",
                       ident, "TESTING", "PILOT",
                       str((body or {}).get("evidence", "")).strip()[:200],
                       store.state["trace_id"], _trace(request))
    return JSONResponse({"id": ident, "status": "PILOT"})


def _connection_or_404(conn_id: str,
                         request: Request | None = None) -> dict[str, Any]:
    record = tenancy_mod.enforce_read(store.connection_get(conn_id),
                                      _request_ctx(request))
    if record is None:
        raise AppError("CONNECTION_NOT_FOUND", "unknown connection",
                       404)
    return record


def _connector_actor(request: Request | None) -> str:
    session = _session_of(request)
    if session is not None:
        return session[0]
    return "platform-token" if _token_ok(request) else "anonymous"


def _connector_audit(actor: str, action: str, conn_id: str,
                     previous: str, new: str, reason: str,
                     request: Request) -> None:
    # Reasons carry adapter names and presence notes only — secret
    # VALUES never reach a connection record, so none can leak here.
    store.append_audit("user", actor, action, "connection", conn_id,
                       previous, new, reason[:200],
                       store.state["trace_id"], _trace(request))


def _connector_error(exc: ValueError) -> AppError:
    code = str(exc).partition(":")[0].strip()
    status = 409 if code == "CONNECTOR_STATUS" else 400
    return _domain_error(exc, default_status=status)


@app.get("/api/v1/connectors")
def connectors_registry() -> dict[str, Any]:
    """Adapter catalogue: provider adapters + loopback harness."""
    specs = conn_mod.registry()
    return {"connectors": specs, "count": len(specs)}


@app.get("/api/v1/connections")
def connections_list(request: Request = None) -> dict[str, Any]:
    """Visible connections (redacted: ref names + presence bools only)."""
    items = [conn_mod.redact(r) for r in tenancy_mod.filter_visible(
        store.connection_list(), _request_ctx(request))]
    return {"connections": items, "count": len(items)}


@app.post("/api/v1/connections")
def connection_create(body: dict[str, Any] | None,
                      request: Request) -> JSONResponse:
    """Create a DRAFT connection (write-gated, audited, tenant-scoped)."""
    _require_write_token(request)
    try:
        record = conn_mod.create_connection(
            (body or {}).get("adapter", ""),
            (body or {}).get("name", ""),
            _request_ctx(request).tenant_id)
    except ValueError as exc:
        raise _connector_error(exc)
    store.connection_save(record)
    _connector_audit(_connector_actor(request), "connector.create",
                     record["id"], "", "DRAFT", record["adapter"],
                     request)
    return JSONResponse(conn_mod.redact(record))


@app.get("/api/v1/connections/{conn_id}")
def connection_detail(conn_id: str,
                      request: Request = None) -> dict[str, Any]:
    """One visible connection (redacted)."""
    return conn_mod.redact(_connection_or_404(conn_id, request))


@app.post("/api/v1/connections/{conn_id}/configure")
def connection_configure(conn_id: str, body: dict[str, Any] | None,
                         request: Request) -> JSONResponse:
    """Store non-secret params (write-gated, audited)."""
    _require_write_token(request)
    record = _connection_or_404(conn_id, request)
    before = record["status"]
    try:
        conn_mod.configure(record, (body or {}).get("params", {}))
    except ValueError as exc:
        raise _connector_error(exc)
    store.connection_save(record)
    _connector_audit(_connector_actor(request), "connector.configure",
                     conn_id, before, record["status"],
                     "%d params stored" % len(record["params"]), request)
    return JSONResponse(conn_mod.redact(record))


@app.post("/api/v1/connections/{conn_id}/verify")
def connection_verify(conn_id: str, request: Request) -> JSONResponse:
    """Run verification (write-gated, audited). A FAILED outcome is a
    200 result — the attempt ran; only illegal transitions are 409."""
    _require_write_token(request)
    record = _connection_or_404(conn_id, request)
    before = record["status"]
    try:
        conn_mod.begin_verify(record)
        record, ok = conn_mod.complete_verify(record)
    except ValueError as exc:
        raise _connector_error(exc)
    store.connection_save(record)
    _connector_audit(_connector_actor(request), "connector.verify",
                     conn_id, before, record["status"],
                     record.get("status_reason", ""), request)
    return JSONResponse({"id": conn_id, "ok": ok,
                         "status": record["status"],
                         "reason": record.get("status_reason", "")})


@app.post("/api/v1/connections/{conn_id}/health")
def connection_health(conn_id: str, request: Request) -> JSONResponse:
    """Probe a CONNECTED connection (write-gated, audited). Three
    consecutive failures auto-suspend."""
    _require_write_token(request)
    record = _connection_or_404(conn_id, request)
    before = record["status"]
    try:
        ok, detail, latency = conn_mod.probe_connection(record)
    except ValueError as exc:
        raise _connector_error(exc)
    auto = conn_mod.record_health(record, ok, latency, detail)
    store.connection_save(record)
    _connector_audit(_connector_actor(request), "connector.health",
                     conn_id, before, record["status"], detail, request)
    return JSONResponse({"id": conn_id, "ok": ok,
                         "latency_ms": latency, "detail": detail,
                         "status": record["status"],
                         "auto_suspended": auto,
                         "consecutive_failures": record[
                             "consecutive_failures"]})


@app.post("/api/v1/connections/{conn_id}/suspend")
def connection_suspend(conn_id: str, body: dict[str, Any] | None,
                       request: Request) -> JSONResponse:
    """Operator suspension (write-gated, reason required, audited)."""
    _require_write_token(request)
    record = _connection_or_404(conn_id, request)
    before = record["status"]
    try:
        conn_mod.suspend(record, (body or {}).get("reason", ""))
    except ValueError as exc:
        raise _connector_error(exc)
    store.connection_save(record)
    _connector_audit(_connector_actor(request), "connector.suspend",
                     conn_id, before, record["status"],
                     record.get("status_reason", ""), request)
    return JSONResponse(conn_mod.redact(record))


@app.post("/api/v1/connections/{conn_id}/revoke")
def connection_revoke(conn_id: str, body: dict[str, Any] | None,
                      request: Request) -> JSONResponse:
    """Terminal revocation (write-gated, reason required, audited)."""
    _require_write_token(request)
    record = _connection_or_404(conn_id, request)
    before = record["status"]
    try:
        conn_mod.revoke(record, (body or {}).get("reason", ""))
    except ValueError as exc:
        raise _connector_error(exc)
    store.connection_save(record)
    _connector_audit(_connector_actor(request), "connector.revoke",
                     conn_id, before, record["status"],
                     record.get("status_reason", ""), request)
    return JSONResponse(conn_mod.redact(record))


# -- geointelligence os --------------------------------------------------
INTEL_SENSITIVE_ROLES = ("admin", "investigator")


def _intel_reader(request: Request | None) -> bool:
    """Sensitive intel reads. Returns masked (auditor reads masked).

    Unarmed local mode passes through unmasked, matching
    existing read behavior; once armed, sessions with admin/
    investigator read full, auditor reads masked, everyone else is
    denied. Raw identifiers are never stored, so masking drops
    coordinates and full addresses only.
    """
    if not config_mod.SESSION_SECRET and not config_mod.DEMO_WRITE_TOKEN:
        return False
    claims = _session_claims(request)
    if claims is None:
        raise AppError("AUTH_REQUIRED", "login required", 401)
    role = claims.get("role")
    if role in INTEL_SENSITIVE_ROLES:
        return False
    if role == "auditor":
        return True
    raise AppError("PERMISSION_DENIED",
                   "role '%s' may not read intelligence" % role, 403)


def _intel_writer(request: Request | None) -> tuple[str, str]:
    """Write gate + role gate for intel mutations; returns (org, user)."""
    _require_write_token(request)
    _telecom_role_gate(request)
    return _telecom_actor(request)


def _intel_quota(org: str, user: str, subject_key: str) -> None:
    allowed, retry = ratelimit_mod.check_and_consume(
        "geo:actor:%s:%s" % (org, user),
        limit=config_mod.GEO_ACTOR_PER_MIN, window=60)
    if not allowed:
        raise AppError("GEO_RATE_LIMITED", "retry in %ds" % retry, 429)
    allowed, _ = ratelimit_mod.check_and_consume(
        "geo:subj:%s" % subject_key,
        limit=config_mod.GEO_SUBJECT_PER_DAY, window=86400)
    if not allowed:
        raise AppError("GEO_RATE_LIMITED", "subject quota exhausted",
                       429)


def _intel_audit(user: str, action: str, target_type: str,
                 target_id: str, previous: str, new: str,
                 reason: str, request: Request | None) -> None:
    store.append_audit("user", user, action, target_type, target_id,
                       previous, new, reason, store.state["trace_id"],
                       _trace(request))


def _intel_investigation_or_404(investigation_id: str) -> dict[str, Any]:
    for inv in store.state.get("investigations", []) or []:
        if isinstance(inv, dict) and inv.get("investigation_id") \
                == investigation_id:
            return inv
    raise AppError("UNKNOWN_INVESTIGATION", investigation_id, 404)


@app.post("/api/v1/identity/verifications")
def identity_verify_create(body: dict[str, Any] | None,
                           request: Request) -> dict[str, Any]:
    """Run one identity verification (gated, quota-bound, audited)."""
    org, user = _intel_writer(request)
    payload = body or {}
    subject = str(payload.get("subject_ref", "") or "")
    _intel_quota(org, user, intelcommon_mod.subject_hash(subject or "?"))
    ctx = _request_ctx(request)
    try:
        record = identity_mod.run_verification(
            store, str(payload.get("verify_type", "")), subject,
            payload.get("attributes") or {},
            str(payload.get("country", "")),
            str(payload.get("purpose", "")), org, user, ctx.tenant_id,
            investigation_id=str(
                payload.get("investigation_id", "") or ""))
    except ValueError as exc:
        raise _domain_error(exc)
    _intel_audit(user, "intel.identity.verify", "identity_verification",
                 record["verification_id"], "",
                 record["verification_status"],
                 "%s %s" % (record["verify_type"],
                            record["subject_masked"]), request)
    return record


@app.get("/api/v1/identity/verifications/{verification_id}")
def identity_verify_get(verification_id: str,
                        request: Request = None) -> dict[str, Any]:
    masked = _intel_reader(request)
    record = tenancy_mod.enforce_read(
        store.state.get("identity_verifications", {}).get(
            verification_id), _request_ctx(request))
    if not isinstance(record, dict):
        raise AppError("UNKNOWN_VERIFICATION", verification_id, 404)
    view = dict(record)
    view["integrity"] = ("ok" if intelcommon_mod.check_integrity(record)
                         else "MISMATCH")
    if identity_mod.is_expired(record):
        view["previous_status"] = record["verification_status"]
        view["verification_status"] = identity_mod.EXPIRED_EVIDENCE
    view["masked_view"] = masked
    return view


@app.get("/api/v1/identity/verifications")
def identity_verify_list(subject_hash: str = "",
                         request: Request = None) -> dict[str, Any]:
    """List by subject hash only (no bulk harvest)."""
    masked = _intel_reader(request)
    if not (subject_hash or "").strip():
        raise AppError("SUBJECT_REQUIRED", "subject_hash required",
                       400)
    ctx = _request_ctx(request)
    rows = [r for r in
            store.state.get("identity_verifications", {}).values()
            if isinstance(r, dict)
            and r.get("subject_hash") == subject_hash.strip()]
    return {"verifications": tenancy_mod.filter_visible(rows, ctx),
            "masked_view": masked}


@app.get("/api/v1/devices/{device_id}/relationships")
def device_relationships(device_id: str,
                         request: Request = None) -> dict[str, Any]:
    """Derived device relationships (accounts, transactions)."""
    try:
        device_mod.validate_device_id(device_id)
    except ValueError:
        raise AppError("INVALID_DEVICE_ID", device_id, 400) from None
    ctx = _request_ctx(request)
    view = tenancy_mod.visible_state(store.state, ctx)
    observations = [o for o in device_mod.build_observations(view)
                    if o.device_id == device_id]
    if not observations and device_mod.get_profile(view, device_id) \
            is None:
        raise AppError("UNKNOWN_DEVICE", device_id, 404)
    edges = []
    for obs in observations:
        if obs.account_id:
            edges.append({"source": device_id,
                          "target": obs.account_id,
                          "relationship_type": "PERSON_TO_DEVICE",
                          "strength": "OBSERVED",
                          "evidence_reference": obs.obs_id})
        if obs.txn_id:
            edges.append({"source": device_id,
                          "target": obs.txn_id,
                          "relationship_type": "DEVICE_TO_TRANSACTION",
                          "strength": "OBSERVED",
                          "evidence_reference": obs.obs_id})
    return {"device_id": device_id, "relationships": edges}


@app.get("/api/v1/devices/{device_id}/observations")
def device_observations(device_id: str,
                        request: Request = None) -> dict[str, Any]:
    """Derived device observations (tenant view, no writes)."""
    try:
        device_mod.validate_device_id(device_id)
    except ValueError:
        raise AppError("INVALID_DEVICE_ID", device_id, 400) from None
    ctx = _request_ctx(request)
    view = tenancy_mod.visible_state(store.state, ctx)
    observations = [o for o in device_mod.build_observations(view)
                    if o.device_id == device_id]
    if not observations and device_mod.get_profile(view, device_id) \
            is None:
        raise AppError("UNKNOWN_DEVICE", device_id, 404)
    return {"device_id": device_id,
            "observations": [obs.model_dump() for obs in observations]}


@app.post("/api/v1/geolocation/ip/lookup")
def ip_lookup_create(body: dict[str, Any] | None,
                     request: Request) -> dict[str, Any]:
    """ESTIMATED-only IP lookup (persisted masked, audited)."""
    org, user = _intel_writer(request)
    payload = body or {}
    ip = str(payload.get("ip_address", "") or "")
    purpose = str(payload.get("purpose", "") or "")
    investigation_id = str(
        payload.get("investigation_id", "") or "")
    if investigation_id:
        _intel_investigation_or_404(investigation_id)
    try:
        purpose = intelcommon_mod.check_purpose(purpose)
    except ValueError as exc:
        raise _domain_error(exc)
    _intel_quota(org, user, intelcommon_mod.subject_hash("ip:" + ip))
    result = ip_mod.lookup_geolocation(ip, investigation_id, purpose)
    record = ip_mod.record_network_observation(
        store, ip, result, _request_ctx(request).tenant_id,
        investigation_id, purpose, org, user,
        retention_days=config_mod.GEO_RETENTION_DAYS)
    _intel_audit(user, "intel.ip.lookup", "network_geo_observation",
                 record["observation_id"], "", result["status"],
                 "%s %s" % (ip_mod.mask_ip(ip),
                            result["status"]), request)
    return {**result, "observation_id": record["observation_id"]}


@app.post("/api/v1/geolocation/observations")
def location_observation_create(body: dict[str, Any] | None,
                                request: Request) -> dict[str, Any]:
    """Record an authorized location observation (gated + audited)."""
    org, user = _intel_writer(request)
    payload = body or {}
    subject = str(payload.get("subject_ref", "") or "")
    _intel_quota(org, user, intelcommon_mod.subject_hash(subject or "?"))
    try:
        record = locobs_mod.record_observation(
            store, payload.get("observation") or {}, subject,
            str(payload.get("purpose", "") or ""), org, user,
            _request_ctx(request).tenant_id,
            investigation_id=str(
                payload.get("investigation_id", "") or ""),
            device_ref=str(payload.get("device_ref", "") or ""))
    except ValueError as exc:
        raise _domain_error(exc)
    _intel_audit(user, "intel.location.record", "location_observation",
                 record["observation_id"], "", "recorded",
                 "%s %s" % (record["source_type"],
                            record["subject_masked"]), request)
    return record


@app.get("/api/v1/geolocation/observations/{observation_id}")
def location_observation_get(observation_id: str,
                             request: Request = None) -> dict[str, Any]:
    masked = _intel_reader(request)
    record = tenancy_mod.enforce_read(
        store.state.get("location_observations", {}).get(
            observation_id), _request_ctx(request))
    if not isinstance(record, dict):
        raise AppError("UNKNOWN_OBSERVATION", observation_id, 404)
    view = dict(record)
    view["integrity"] = ("ok" if intelcommon_mod.check_integrity(record)
                         else "MISMATCH")
    if masked:
        view.pop("latitude", None)
        view.pop("longitude", None)
        view["coordinates"] = "MASKED"
    view["masked_view"] = masked
    return view


@app.get("/api/v1/geolocation/observations")
def location_observation_list(investigation_id: str = "",
                              request: Request = None
                              ) -> dict[str, Any]:
    masked = _intel_reader(request)
    ctx = _request_ctx(request)
    rows = [r for r in
            store.state.get("location_observations", {}).values()
            if isinstance(r, dict) and (not investigation_id or
                                        r.get("investigation_id")
                                        == investigation_id)]
    views = []
    for row in tenancy_mod.filter_visible(rows, ctx):
        view = dict(row)
        if masked:
            view.pop("latitude", None)
            view.pop("longitude", None)
            view["coordinates"] = "MASKED"
        views.append(view)
    return {"observations": views, "masked_view": masked}


@app.post("/api/v1/addresses/verify")
def address_verify_create(body: dict[str, Any] | None,
                          request: Request) -> dict[str, Any]:
    """Verify a supplied address (gated, quota-bound, audited)."""
    org, user = _intel_writer(request)
    payload = body or {}
    subject = str(payload.get("subject_ref", "") or "")
    _intel_quota(org, user, intelcommon_mod.subject_hash(subject or "?"))
    ctx = _request_ctx(request)
    try:
        record = address_mod.run_verification(
            store, payload.get("address") or {}, subject,
            str(payload.get("method", "") or ""),
            str(payload.get("purpose", "") or ""), org, user,
            ctx.tenant_id,
            investigation_id=str(
                payload.get("investigation_id", "") or ""),
            geocoded_only=bool(payload.get("geocoded_only", False)))
    except ValueError as exc:
        raise _domain_error(exc)
    _intel_audit(user, "intel.address.verify", "address_verification",
                 record["verification_id"], "",
                 record["verification_status"],
                 "%s %s" % (record["verification_method"],
                            record["subject_masked"]), request)
    view = dict(record)
    claims = _session_claims(request)
    masked = claims is not None and claims.get("role") == "auditor"
    if masked:
        view.pop("address", None)
    view["masked_view"] = masked
    return view


@app.get("/api/v1/addresses/verifications/{verification_id}")
def address_verify_get(verification_id: str,
                       request: Request = None) -> dict[str, Any]:
    masked = _intel_reader(request)
    record = tenancy_mod.enforce_read(
        store.state.get("address_verifications", {}).get(
            verification_id), _request_ctx(request))
    if not isinstance(record, dict):
        raise AppError("UNKNOWN_VERIFICATION", verification_id, 404)
    view = dict(record)
    view["integrity"] = ("ok" if intelcommon_mod.check_integrity(record)
                         else "MISMATCH")
    if address_mod.is_expired(record):
        view["previous_status"] = record["verification_status"]
        view["verification_status"] = address_mod.EXPIRED
    if masked:
        view.pop("address", None)
    view["masked_view"] = masked
    return view


@app.get("/api/v1/investigations/{investigation_id}/map")
def investigation_map(investigation_id: str,
                      request: Request = None) -> dict[str, Any]:
    masked = _intel_reader(request)
    _intel_investigation_or_404(investigation_id)
    ctx = _request_ctx(request)
    view = tenancy_mod.visible_state(store.state, ctx)
    body = invmap_mod.investigation_map(view, investigation_id, masked)
    body["masked_view"] = masked
    return body


@app.get("/api/v1/investigations/{investigation_id}/locations")
def investigation_locations(investigation_id: str, status: str = "",
                            provider: str = "",
                            request: Request = None) -> dict[str, Any]:
    masked = _intel_reader(request)
    _intel_investigation_or_404(investigation_id)
    ctx = _request_ctx(request)
    view = tenancy_mod.visible_state(store.state, ctx)
    return {"investigation_id": investigation_id,
            "locations": invmap_mod.investigation_locations(
                view, investigation_id, masked, status, provider),
            "masked_view": masked}


@app.get("/api/v1/investigations/{investigation_id}/relationships")
def investigation_relationships(investigation_id: str,
                                request: Request = None
                                ) -> dict[str, Any]:
    _intel_investigation_or_404(investigation_id)
    ctx = _request_ctx(request)
    view = tenancy_mod.visible_state(store.state, ctx)
    return {"investigation_id": investigation_id,
            "relationships": invmap_mod.investigation_relationships(
                view, investigation_id)}


@app.get("/api/v1/providers")
def intel_providers(request: Request = None) -> dict[str, Any]:
    rows = intelprov_mod.unified_registry(
        store, _request_ctx(request).tenant_id)
    return {"providers": rows, "count": len(rows)}


@app.get("/api/v1/providers/{provider_id}")
def intel_provider_get(provider_id: str,
                       request: Request = None) -> dict[str, Any]:
    rows = intelprov_mod.unified_registry(
        store, _request_ctx(request).tenant_id)
    for row in rows:
        if row["provider_id"] == provider_id:
            return row
    raise AppError("UNKNOWN_PROVIDER", provider_id, 404)


@app.get("/api/v1/providers/{provider_id}/health")
def intel_provider_health(provider_id: str,
                          request: Request = None) -> dict[str, Any]:
    body = intelprov_mod.provider_health(
        store, _request_ctx(request).tenant_id, provider_id)
    if body is None:
        raise AppError("UNKNOWN_PROVIDER", provider_id, 404)
    return body


@app.get("/api/v1/geointel/coverage")
def intel_coverage(request: Request = None) -> dict[str, Any]:
    _ = request
    rows = intelprov_mod.country_coverage()
    return {"countries": rows, "count": len(rows),
            "map_provider": intelprov_mod.map_provider()}


@app.get("/api/v1/geointel/metrics")
def intel_metrics(request: Request) -> dict[str, Any]:
    claims = _require_admin(request)
    body = invmap_mod.metrics(store.state,
                              _request_ctx(request).tenant_id)
    _intel_audit(claims["user"], "intel.metrics.read",
                 "intel_metrics", "metrics", "", "read",
                 "admin metrics viewed", request)
    return body


@app.get("/api/v1/evidence/{evidence_id}")
def intel_evidence_get(evidence_id: str,
                       request: Request = None) -> dict[str, Any]:
    """Read-only cross-store evidence resolver (no creation endpoint).

    Evidence is created only by verification flows (immutability);
    this resolves an ID to its record for investigators.
    """
    masked = _intel_reader(request)
    ctx = _request_ctx(request)
    for key, kind in (("telecom_verifications", "telecom"),
                      ("identity_verifications", "identity"),
                      ("address_verifications", "address"),
                      ("location_observations", "location"),
                      ("network_geo_observations", "network_geo")):
        record = tenancy_mod.enforce_read(
            store.state.get(key, {}).get(evidence_id), ctx)
        if isinstance(record, dict):
            view = dict(record)
            view["evidence_kind"] = kind
            if masked:
                view.pop("address", None)
                view.pop("latitude", None)
                view.pop("longitude", None)
            view["masked_view"] = masked
            return view
    raise AppError("UNKNOWN_EVIDENCE", evidence_id, 404)


@app.post("/api/v1/intel/authorizations")
def intel_authorization_create(body: dict[str, Any] | None,
                               request: Request) -> dict[str, Any]:
    org, user = _intel_writer(request)
    payload = body or {}
    claims = _session_claims(request)
    if claims is not None and claims.get("role") not in (
            "admin", "investigator"):
        raise AppError("PERMISSION_DENIED",
                       "auditors may not request authorization", 403)
    try:
        record = intelauth_mod.create_authorization(
            store, _request_ctx(request).tenant_id,
            str(payload.get("investigation_id", "") or ""), user,
            str(payload.get("subject_ref", "") or ""),
            str(payload.get("purpose", "") or ""),
            str(payload.get("legal_basis", "") or ""),
            str(payload.get("country", "") or ""),
            str(payload.get("scope", "") or ""))
    except ValueError as exc:
        raise _domain_error(exc)
    _intel_audit(user, "intel.authz.request", "intel_authorization",
                 record["authorization_id"], "", "PENDING",
                 "%s %s" % (record["purpose"],
                            record["subject_masked"]), request)
    return record


@app.post("/api/v1/intel/authorizations/{authorization_id}/decide")
def intel_authorization_decide(authorization_id: str,
                               body: dict[str, Any] | None,
                               request: Request) -> dict[str, Any]:
    claims = _require_admin(request)
    payload = body or {}
    try:
        record = intelauth_mod.decide_authorization(
            store, authorization_id, claims["user"],
            bool(payload.get("approve", False)),
            str(payload.get("reference", "") or ""))
    except ValueError as exc:
        raise _domain_error(exc)
    if record is None:
        raise AppError("UNKNOWN_AUTHORIZATION", authorization_id, 404)
    _intel_audit(claims["user"], "intel.authz.decide",
                 "intel_authorization", authorization_id, "PENDING",
                 record["authorization_status"], "decided", request)
    return record


@app.get("/api/v1/intel/authorizations/{authorization_id}")
def intel_authorization_get(authorization_id: str,
                            request: Request = None) -> dict[str, Any]:
    _intel_reader(request)
    record = tenancy_mod.enforce_read(
        store.state.get("intel_authorizations", {}).get(
            authorization_id), _request_ctx(request))
    if not isinstance(record, dict):
        raise AppError("UNKNOWN_AUTHORIZATION", authorization_id, 404)
    return record


@app.post("/api/v1/intel/consents")
def intel_consent_create(body: dict[str, Any] | None,
                         request: Request) -> dict[str, Any]:
    org, user = _intel_writer(request)
    payload = body or {}
    try:
        record = intelauth_mod.record_consent(
            store, _request_ctx(request).tenant_id,
            str(payload.get("subject_ref", "") or ""),
            str(payload.get("purpose", "") or ""),
            str(payload.get("consent_method", "") or ""), user, org)
    except ValueError as exc:
        raise _domain_error(exc)
    _intel_audit(user, "intel.consent.record", "telecom_consent",
                 record["consent_id"], "", "granted",
                 "%s %s" % (record["purpose"],
                            record["subject_masked"]), request)
    return record


@app.post("/api/v1/intel/consents/withdraw")
def intel_consent_withdraw(body: dict[str, Any] | None,
                           request: Request) -> dict[str, Any]:
    org, user = _intel_writer(request)
    _ = org
    payload = body or {}
    try:
        purpose = intelcommon_mod.check_purpose(
            str(payload.get("purpose", "") or ""))
    except ValueError as exc:
        raise _domain_error(exc)
    digest = intelcommon_mod.subject_hash(
        str(payload.get("subject_ref", "") or ""))
    record = intelauth_mod.withdraw_consent(store, digest, purpose)
    if record is None:
        raise AppError("UNKNOWN_CONSENT", "no live consent", 404)
    _intel_audit(user, "intel.consent.withdraw", "telecom_consent",
                 record["consent_id"], "granted", "withdrawn",
                 "%s %s" % (purpose, record["subject_masked"]),
                 request)
    return {"consent_id": record["consent_id"], "revoked": True}



# -- telecom identity ------------------------------------------------------
TELECOM_VERIFY_ROLES = ("admin", "investigator", "auditor")


def _telecom_actor(request: Request | None) -> tuple[str, str]:
    """Server-derived (org, user): tenant org + session/token identity."""
    ctx = _request_ctx(request)
    return ctx.tenant_id, _connector_actor(request)


def _telecom_role_gate(request: Request | None) -> None:
    """Least privilege: authed sessions need a telecom-capable role."""
    claims = _session_claims(request)
    if claims is not None and claims.get("role") not in TELECOM_VERIFY_ROLES:
        raise AppError("PERMISSION_DENIED",
                       "role '%s' may not use telecom verification"
                       % claims.get("role"), 403)


def _telecom_audit(user: str, action: str, target_id: str,
                   previous: str, new: str, reason: str,
                   request: Request | None) -> None:
    store.append_audit("user", user, action, "telecom_verification",
                       target_id, previous, new, reason,
                       store.state["trace_id"], _trace(request))


@app.get("/api/v1/telecom/operators")
def telecom_operators(country: str = "",
                      request: Request = None) -> dict[str, Any]:
    """Versioned operator registry (public allocation data, no PII)."""
    _ = request
    ops = telecom_reg_mod.list_operators(country or None)
    return {"operators": ops, "count": len(ops),
            "registry": telecom_reg_mod.registry_version()}


@app.get("/api/v1/telecom/operators/{operator_id}")
def telecom_operator(operator_id: str,
                     request: Request = None) -> dict[str, Any]:
    _ = request
    op = telecom_reg_mod.get_operator(operator_id)
    if op is None:
        raise AppError("UNKNOWN_OPERATOR", operator_id, 404)
    return op


@app.get("/api/v1/telecom/numbers/parse")
def telecom_parse(e164: str = "",
                  request: Request = None) -> dict[str, Any]:
    """Parse + allocation lookup (derived, never persisted)."""
    _ = request
    try:
        normalized = telecom_reg_mod.normalize_e164(e164)
    except ValueError:
        raise AppError("INVALID_E164", "unparseable number", 400)
    alloc = telecom_reg_mod.allocation_lookup(normalized)
    return {"e164_masked": telecom_mod.mask_e164(normalized),
            "country": alloc["country"],
            "operator_id": alloc["operator_id"], "basis": alloc["basis"],
            "limitation": alloc["limitation"]}


@app.post("/api/v1/telecom/verifications")
def telecom_verify_create(body: dict[str, Any] | None,
                          request: Request) -> dict[str, Any]:
    """Run one verification (write-gated, rate-limited, audited).

    Persists masked subject + hash only. Raw E.164 and raw provider
    payloads are never stored or returned.
    """
    _require_write_token(request)
    _telecom_role_gate(request)
    org, user = _telecom_actor(request)
    payload = body or {}
    allowed, retry = ratelimit_mod.check_and_consume(
        "telecom:actor:%s:%s" % (org, user),
        limit=config_mod.TELECOM_ACTOR_PER_MIN, window=60)
    if not allowed:
        raise AppError("TELECOM_RATE_LIMITED",
                       "retry in %ds" % retry, 429)
    try:
        normalized = telecom_reg_mod.normalize_e164(
            payload.get("e164", ""))
    except ValueError:
        raise AppError("INVALID_E164", "unparseable number", 400)
    allowed, retry = ratelimit_mod.check_and_consume(
        "telecom:subj:%s" % telecom_mod.hash_subject(normalized),
        limit=config_mod.TELECOM_SUBJECT_PER_DAY, window=86400)
    if not allowed:
        raise AppError("TELECOM_RATE_LIMITED",
                       "subject quota exhausted", 429)
    ctx = _request_ctx(request)
    view = tenancy_mod.visible_state(store.state, ctx)
    try:
        record = telecom_mod.run_verification(
            store, view, str(payload.get("verify_type", "")),
            normalized, str(payload.get("purpose", "")), org, user,
            ctx.tenant_id,
            context=payload.get("context") or {})
    except ValueError as exc:
        raise _domain_error(exc)
    _telecom_audit(user, "telecom.verify", record["verification_id"],
                   "", record["state"],
                   "%s %s" % (record["verify_type"],
                              record["subject_masked"]), request)
    return record


@app.get("/api/v1/telecom/verifications/{verification_id}")
def telecom_verify_get(verification_id: str,
                       request: Request = None) -> dict[str, Any]:
    """One evidence record (tenant-scoped; stale + integrity evaluated)."""
    record = tenancy_mod.enforce_read(
        store.telecom_get(verification_id), _request_ctx(request))
    if record is None:
        raise AppError("UNKNOWN_VERIFICATION", verification_id, 404)
    view = dict(record)
    view["integrity"] = ("ok" if telecom_mod.check_integrity(record)
                         else "MISMATCH")
    if telecom_mod.is_stale(record):
        view["previous_state"] = record["state"]
        view["state"] = telecom_mod.STALE_RESULT
    return view


@app.get("/api/v1/telecom/summary")
def telecom_summary(subject: str = "", phone_label: str = "",
                    request: Request = None) -> dict[str, Any]:
    """Allocation + verification history + co-signals (no verdicts)."""
    ctx = _request_ctx(request)
    view = tenancy_mod.visible_state(store.state, ctx)
    history: list[dict[str, Any]] = []
    alloc: dict[str, Any] = {"operator_id": None, "country": None,
                             "basis": "no-subject",
                             "limitation": "no subject supplied"}
    masked = ""
    if (subject or "").strip():
        try:
            normalized = telecom_reg_mod.normalize_e164(subject)
        except ValueError:
            raise AppError("INVALID_E164", "unparseable number", 400)
        masked = telecom_mod.mask_e164(normalized)
        alloc = telecom_reg_mod.allocation_lookup(normalized)
        digest = telecom_mod.hash_subject(normalized)
        history = tenancy_mod.filter_visible(
            store.telecom_for_subject(digest), ctx)
    label = (phone_label or "").strip()
    summary = telecom_mod.summarize(view, history, label)
    summary["subject_masked"] = masked
    summary["allocation"] = alloc
    summary["phone_label"] = label
    return summary


@app.post("/api/v1/telecom/consents")
def telecom_consent_create(body: dict[str, Any] | None,
                           request: Request) -> dict[str, Any]:
    """Record explicit subject consent (write-gated, audited)."""
    _require_write_token(request)
    _telecom_role_gate(request)
    org, user = _telecom_actor(request)
    payload = body or {}
    try:
        normalized = telecom_reg_mod.normalize_e164(
            payload.get("e164", ""))
    except ValueError:
        raise AppError("INVALID_E164", "unparseable number", 400)
    purpose = str(payload.get("purpose", "") or "").strip()
    if not purpose or len(purpose) > 200:
        raise AppError("PURPOSE_REQUIRED",
                       "lawful purpose 1..200 chars", 400)
    import time as _time

    try:
        days = int(payload.get("expires_days", 30))
    except (TypeError, ValueError):
        days = 30
    days = min(max(days, 1), 90)
    now = _time.time()
    record = {"consent_id": "tcon_%06d" % store.telecom_next_seq(),
              "subject_hash": telecom_mod.hash_subject(normalized),
              "subject_masked": telecom_mod.mask_e164(normalized),
              "purpose": purpose, "org": org, "granted_by": user,
              "granted_at": now, "expires_ts": now + days * 86400,
              "revoked": False,
              "tenant_id": _request_ctx(request).tenant_id}
    store.telecom_consent_save(record)
    _telecom_audit(user, "telecom.consent", record["consent_id"], "",
                   "granted", "%s %s" % (purpose,
                                         record["subject_masked"]),
                   request)
    return record


@app.get("/api/v1/admin/telecom-config")
def telecom_config(request: Request) -> dict[str, Any]:
    """Availability matrix + provider statuses + thresholds (admin)."""
    claims = _require_admin(request)
    ctx = _request_ctx(request)
    body = {
        "registry": telecom_reg_mod.registry_version(),
        "tracked_apis": list(telecom_reg_mod.TRACKED_APIS),
        "verify_types": list(telecom_mod.TYPES),
        "consent_required_all": config_mod.telecom_consent_required(),
        "always_consent_types": list(telecom_mod.ALWAYS_CONSENT),
        "retention_days": config_mod.TELECOM_RETENTION_DAYS,
        "actor_per_min": config_mod.TELECOM_ACTOR_PER_MIN,
        "subject_per_day": config_mod.TELECOM_SUBJECT_PER_DAY,
        "providers": telecom_prov_mod.provider_status(store,
                                                      ctx.tenant_id),
        "live_integrations": [],
    }
    _telecom_audit(claims["user"], "telecom.config.read", "config",
                   "", "read", "admin telecom config viewed", request)
    return body


# -- investigation data ---------------------------------------------------
@app.get("/api/v1/transactions/{txn_id}")
def get_transaction(txn_id: str,
                    request: Request = None) -> dict[str, Any]:
    ctx = _request_ctx(request)
    txn = tenancy_mod.enforce_read(store.get_transaction(txn_id), ctx)
    if txn is None:
        raise AppError("UNKNOWN_TRANSACTION", txn_id, 404)
    risk_txn, risk_net, _ = _ensure_assessment(txn_id, ctx)
    return {"transaction": txn, "risk_transaction": risk_txn,
            "risk_network": risk_net}


@app.get("/api/v1/devices/{device_id}")
def get_device(device_id: str,
               request: Request = None) -> dict[str, Any]:
    """DI-03 read-only device profile (derived, never persisted)."""
    try:
        device_mod.validate_device_id(device_id)
    except ValueError:
        raise AppError("INVALID_DEVICE_ID", device_id, 400) from None
    view = tenancy_mod.visible_state(store.state,
                                          _request_ctx(request))
    profile = device_mod.get_profile(view, device_id)
    if profile is None:
        raise AppError("UNKNOWN_DEVICE", device_id, 404)
    return profile.model_dump()


@app.get("/api/v1/ip-observations/{label}")
def get_ip_observations(label: str,
                        request: Request = None) -> dict[str, Any]:
    """DI-04 read-only IP-label observations (derived, never persisted)."""
    try:
        ip_mod.validate_label(label)
    except ValueError:
        raise AppError("INVALID_IP_LABEL", label, 400) from None
    view = tenancy_mod.visible_state(store.state,
                                          _request_ctx(request))
    mine = [o.model_dump() for o in ip_mod.build_observations(view)
            if o.ip_label == label]
    if not mine:
        raise AppError("UNKNOWN_IP_LABEL", label, 404)
    return {"ip_label": label, "address_status": ip_mod.UNKNOWN,
            "observations": mine}


@app.get("/api/v1/geo-observations/{identifier}")
def get_geo_observations(identifier: str,
                         request: Request = None) -> dict[str, Any]:
    """DI-05 read-only geo lookup (derived; NullProvider default).

    Fixture labels (e.g. loc_01) return their label observations;
    IP literals are validated and resolved (unavailable unless a
    provider supplies data); anything else is a structured error.
    """
    try:
        geo_mod.validate_label(identifier)
    except ValueError:
        raise AppError("INVALID_GEO_LABEL", identifier, 400) from None
    view = tenancy_mod.visible_state(store.state,
                                          _request_ctx(request))
    mine = [o for o in geo_mod.build_label_observations(view)
            if o["location_label"] == identifier]
    if mine:
        return {"identifier": identifier, "kind": "fixture_label",
                "observations": mine}
    if ip_mod.parse_ip(identifier) is not None:
        return {"identifier": identifier, "kind": "ip_literal",
                "lookup": geo_mod.resolve_ip(identifier).model_dump()}
    raise AppError("UNKNOWN_GEO_IDENTIFIER", identifier, 404)


@app.get("/api/v1/transactions/{txn_id}/intel")
def get_transaction_intel(txn_id: str,
                          request: Request = None) -> dict[str, Any]:
    """DI-06 read-only transaction intel summary (derived)."""
    view = tenancy_mod.visible_state(store.state,
                                          _request_ctx(request))
    summary = link_mod.transaction_intel(view, txn_id)
    if summary is None:
        raise AppError("UNKNOWN_TRANSACTION", txn_id, 404)
    return summary


@app.get("/api/v1/accounts/{account_id}/intel")
def get_account_intel(account_id: str,
                      request: Request = None) -> dict[str, Any]:
    """DI-06 read-only account intel summary (derived)."""
    view = tenancy_mod.visible_state(store.state,
                                          _request_ctx(request))
    summary = link_mod.account_intel(view, account_id)
    if summary is None:
        raise AppError("UNKNOWN_ACCOUNT", account_id, 404)
    return summary


@app.get("/api/v1/investigations/{inv_id}/intel")
def get_investigation_intel(inv_id: str,
                            request: Request = None) -> dict[str, Any]:
    """DI-06 read-only investigation intel summary (derived)."""
    view = tenancy_mod.visible_state(store.state,
                                          _request_ctx(request))
    summary = link_mod.investigation_intel(view, inv_id)
    if summary is None:
        raise AppError("UNKNOWN_INVESTIGATION", inv_id, 404)
    return summary


@app.get("/api/v1/graph/{txn_id}/overlay")
def get_graph_overlay(txn_id: str,
                      request: Request = None) -> dict[str, Any]:
    """DI-07 derived intel overlay (in-memory, never persisted)."""
    view = tenancy_mod.visible_state(store.state,
                                          _request_ctx(request))
    overlay = gintel_mod.build_overlay(view, txn_id)
    if overlay is None:
        raise AppError("UNKNOWN_TRANSACTION", txn_id, 404)
    return overlay


@app.get("/api/v1/risk-intelligence/{identifier}")
def get_risk_intelligence(identifier: str,
                          request: Request = None) -> dict[str, Any]:
    """DI-08 candidate findings (flag-gated; v1 never affected)."""
    if not rintel_mod.enabled():
        return rintel_mod.disabled_response()
    if identifier.startswith("txn_"):
        subject_type = "transaction"
    elif identifier.startswith("acct_"):
        subject_type = "account"
    elif identifier.startswith("inv_"):
        subject_type = "investigation"
    else:
        raise AppError("INVALID_RISK_INTEL_ID", identifier, 400)
    view = tenancy_mod.visible_state(store.state,
                                          _request_ctx(request))
    result = rintel_mod.assess(view, subject_type, identifier)
    if result is None:
        raise AppError("UNKNOWN_RISK_INTEL_SUBJECT", identifier, 404)
    return result


@app.get("/api/v1/investigations/{inv_id}/intel-evidence")
def get_intel_evidence(inv_id: str,
                       request: Request = None) -> dict[str, Any]:
    """DI-09 read-only intelligence findings + trace (derived).

    Flag-gated like /risk-intelligence: candidate findings stay hidden
    until RISK_INTELLIGENCE_V2_ENABLED=true.
    """
    if not rintel_mod.enabled():
        body = rintel_mod.disabled_response()
        body["investigation_id"] = inv_id
        return body
    view = tenancy_mod.visible_state(store.state,
                                          _request_ctx(request))
    findings = iev_mod.build_findings(view, "investigation", inv_id)
    if findings is None:
        raise AppError("UNKNOWN_INVESTIGATION", inv_id, 404)
    return {"investigation_id": inv_id, "findings": findings,
            "trace": iev_mod.trace_chain(view, inv_id),
            "synthetic": True}


@app.get("/api/v1/graph/{txn_id}")
def get_graph(txn_id: str,
              request: Request = None) -> dict[str, Any]:
    ctx = _request_ctx(request)
    if tenancy_mod.enforce_read(store.get_transaction(txn_id),
                                ctx) is None:
        raise AppError("UNKNOWN_TRANSACTION", txn_id, 404)
    # Tenant-visible subgraph; for the default tenant this is the full
    # seeded network (22 nodes / 30 edges) matching the seed manifest.
    _, nodes, edges = tenancy_mod.visible_graph(store.state, ctx)
    return {"transaction_id": txn_id, "nodes": nodes, "edges": edges,
            "provenance_errors": graph_mod.validate_provenance(edges),
            "counts": {"nodes": len(nodes), "edges": len(edges)}}


@app.get("/api/v1/risk/{txn_id}")
def get_risk(txn_id: str, scope: str = "network",
             request: Request = None) -> dict[str, Any]:
    if scope not in ("transaction", "network"):
        raise AppError("UNKNOWN_SCOPE", scope, 400)
    ctx = _request_ctx(request)
    if tenancy_mod.enforce_read(store.get_transaction(txn_id),
                                ctx) is None:
        raise AppError("UNKNOWN_TRANSACTION", txn_id, 404)
    risk_txn, risk_net, rule_results = _ensure_assessment(txn_id, ctx)
    return {"assessment": risk_txn if scope == "transaction" else risk_net,
            "rule_results": rule_results}


def _visible_alerts(request: Request | None) -> list[dict[str, Any]]:
    """Alerts whose transaction is visible to the request tenant."""
    ctx = _request_ctx(request)
    visible = {t.get("transaction_id")
               for t in tenancy_mod.filter_visible(
                   store.state.get("transactions", []), ctx)}
    return [a for a in store.state.get("alerts", [])
            if a.get("transaction_id") in visible]


@app.get("/api/v1/alerts")
def list_alerts(request: Request = None) -> dict[str, Any]:
    return {"alerts": _visible_alerts(request)}


@app.get("/api/v1/detectors")
def list_detectors() -> dict[str, Any]:
    """Detector registry with honest operational status."""
    return {"detectors": [
        {"family": fam, "version": det_mod.VERSION,
         "status": ("NOT_IMPLEMENTED" if fam == "ML_ANOMALY"
                    else "OPERATIONAL"),
         "description": det_mod.DESCRIPTIONS[fam],
         "rules": list(det_mod.RULE_MAPPED.get(fam, ()))}
        for fam in det_mod.FAMILIES]}


def _tenant_signals(request: Request | None) -> tuple[list[dict], dict]:
    ctx = _request_ctx(request)
    txns = tenancy_mod.filter_visible(store.state["transactions"], ctx)
    result = det_mod.evaluate_all(txns, store.state["edges"])
    return txns, result


@app.get("/api/v1/signals/summary")
def signals_summary(request: Request = None) -> dict[str, Any]:
    """Measured signal frequency over tenant-visible transactions."""
    txns, result = _tenant_signals(request)
    signals = result["signals"]
    by_family: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for sig in signals:
        by_family[sig["detector_family"]] = by_family.get(
            sig["detector_family"], 0) + 1
        by_severity[sig["severity"]] = by_severity.get(
            sig["severity"], 0) + 1
    stamps = sorted(t.get("occurred_at", "") for t in txns if t.get(
        "occurred_at"))
    flagged = {s["transaction_id"] for s in signals}
    ctx = _request_ctx(request)
    inv_ids = {i["investigation_id"]
               for i in tenancy_mod.filter_visible(
                   store.state["investigations"], ctx)
               if i.get("transaction_id") in flagged}
    reviewed = dismissed = 0
    for sig in signals:
        current = (store.signal_outcome(sig["signal_id"]) or {}).get(
            "current")
        if current == "CONFIRMED_SUSPICIOUS":
            reviewed += 1
        elif current == "DISMISSED":
            reviewed += 1
            dismissed += 1
    fp_rate = round(dismissed / reviewed, 4) if reviewed else None
    return {
        "total_signals": len(signals),
        "unique_transactions_flagged": len(flagged),
        "unique_entities_flagged": len(
            {e for s in signals for e in s["entities"].values() if e}),
        "unique_investigations_created": len(inv_ids),
        "false_positive_rate": fp_rate,
        "false_positive_basis": (
            f"{dismissed} dismissed of {reviewed} reviewed"
            if reviewed else "no reviewed outcomes recorded"),
        "by_family": by_family, "by_severity": by_severity,
        "measurement_period": {"start": stamps[0] if stamps else "",
                               "end": stamps[-1] if stamps else ""},
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                      time.gmtime()),
        "tenant_scope": _request_ctx(request).tenant_id,
        "evaluation": result["meta"],
        "note": ("Zero means no qualifying events recorded, not "
                 "missing instrumentation.")}


@app.get("/api/v1/channels/summary")
def channels_summary(request: Request = None) -> dict[str, Any]:
    """Per-channel volume + signal counts with mapping alerts."""
    txns, result = _tenant_signals(request)
    summary = chan_mod.summarize(txns, result["signals"])
    summary["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                            time.gmtime())
    summary["tenant_scope"] = _request_ctx(request).tenant_id
    return summary


@app.get("/api/v1/detection/matrix")
def detection_matrix(request: Request = None) -> dict[str, Any]:
    """Detector × channel support matrix with per-cell evidence."""
    txns, result = _tenant_signals(request)
    signals = result["signals"]
    txn_channels = {t.get("transaction_id"): chan_mod.classify(
        t.get("channel")) for t in txns}
    chan_txn_count: dict[str, int] = {}
    for txn_id, canonical in txn_channels.items():
        if canonical in chan_mod.CANONICAL:
            chan_txn_count[canonical] = chan_txn_count.get(
                canonical, 0) + 1
    cells = []
    for fam in det_mod.FAMILIES:
        fam_sigs = [s for s in signals if s["detector_family"] == fam]
        for channel in chan_mod.CANONICAL:
            cell_sigs = [s for s in fam_sigs
                         if txn_channels.get(s["transaction_id"]) ==
                         channel]
            if fam == "ML_ANOMALY":
                status = "NOT_YET_IMPLEMENTED"
            elif chan_txn_count.get(channel, 0) == 0:
                status = "AWAITING_DATA_SOURCE"
            else:
                status = "SUPPORTED_AND_ACTIVE"
            cells.append({
                "family": fam, "channel": channel, "status": status,
                "signals": len(cell_sigs),
                "transactions": chan_txn_count.get(channel, 0),
                "evidence_signal_id": (cell_sigs[0]["signal_id"]
                                       if cell_sigs else "")})
    return {"cells": cells,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                          time.gmtime()),
            "tenant_scope": _request_ctx(request).tenant_id}


@app.get("/api/v1/signals/by-transaction/{txn_id}")
def signals_by_transaction(txn_id: str,
                           request: Request = None) -> dict[str, Any]:
    """Signal-to-investigation drill-down for one transaction.

    Derived signals plus the linked investigation, case, and case
    audits (provenance chain). Tenant-gated at every hop; foreign or
    missing records read as NOT FOUND.
    """
    ctx = _request_ctx(request)
    txn = tenancy_mod.enforce_read(store.get_transaction(txn_id), ctx)
    if txn is None:
        raise AppError("UNKNOWN_TRANSACTION", txn_id, 404)
    txns = tenancy_mod.filter_visible(store.state["transactions"], ctx)
    result = det_mod.evaluate_all(txns, store.state["edges"])
    txn_signals = [s for s in result["signals"]
                   if s["transaction_id"] == txn_id]
    inv = tenancy_mod.enforce_read(next(
        (i for i in store.state["investigations"]
         if i.get("transaction_id") == txn_id), None), ctx)
    case = None
    audits: list[dict] = []
    if inv is not None:
        case = tenancy_mod.enforce_read(next(
            (c for c in store.state["cases"]
             if c.get("investigation_id") == inv["investigation_id"]),
            None), ctx)
        if case is not None:
            audits = [a for a in store.state["audits"]
                      if a.get("target_id") == case["case_id"]]
    return {"transaction_id": txn_id, "signals": txn_signals,
            "signal_count": len(txn_signals),
            "investigation": inv, "case": case, "audits": audits,
            "tenant_scope": ctx.tenant_id}


SIGNAL_OUTCOMES = ("CONFIRMED_SUSPICIOUS", "DISMISSED", "PENDING_REVIEW")


def _filtered_signals(request: Request | None, q: str = "",
                      family: str = "", channel: str = "",
                      severity: str = "", start: str = "",
                      end: str = "") -> list[dict]:
    """Tenant-visible signals filtered by range/family/channel/severity/q."""
    _, result = _tenant_signals(request)
    try:
        signals = det_mod.filter_signals(
            result["signals"], start=start, end=end, family=family,
            channel=channel, severity=severity)
    except ValueError as exc:
        raise AppError("FILTER_INVALID", str(exc), 400)
    if q:
        needle = q.lower()
        signals = [s for s in signals
                   if needle in s["signal_id"].lower()
                   or needle in s["transaction_id"].lower()
                   or needle in s["reason"].lower()]
    return signals


def _visible_signal(signal_id: str, request: Request | None) -> dict:
    _, result = _tenant_signals(request)
    sig = next((s for s in result["signals"]
                if s["signal_id"] == signal_id), None)
    if sig is None:
        raise AppError("UNKNOWN_SIGNAL", signal_id, 404)
    return sig


@app.get("/api/v1/signals/search")
def signals_search(q: str = "", family: str = "", channel: str = "",
                   severity: str = "", start: str = "", end: str = "",
                   limit: int = 50, offset: int = 0,
                   request: Request = None) -> dict[str, Any]:
    """Paged signal search over tenant-visible derived signals."""
    if limit < 1 or limit > 200:
        raise AppError("FILTER_INVALID", "limit must be 1..200", 400)
    if offset < 0:
        raise AppError("FILTER_INVALID", "offset must be >= 0", 400)
    signals = _filtered_signals(request, q, family, channel, severity,
                                start, end)
    page = []
    for sig in signals[offset:offset + limit]:
        row = dict(sig)
        outcome = store.signal_outcome(sig["signal_id"])
        row["outcome"] = outcome["current"] if outcome else None
        link = store.signal_link(sig["signal_id"])
        row["linked_investigations"] = (
            [h["investigation_id"] for h in link["history"]]
            if link else [])
        page.append(row)
    return {"signals": page, "total": len(signals), "limit": limit,
            "offset": offset,
            "tenant_scope": _request_ctx(request).tenant_id}


@app.get("/api/v1/signals/time-series")
def signals_time_series(granularity: str = "day", family: str = "",
                        channel: str = "", severity: str = "",
                        start: str = "", end: str = "",
                        request: Request = None) -> dict[str, Any]:
    """UTC-bucketed signal counts (hour/day/week/month)."""
    if granularity not in ("hour", "day", "week", "month"):
        raise AppError("FILTER_INVALID",
                       "granularity must be hour|day|week|month", 400)
    signals = _filtered_signals(request, "", family, channel, severity,
                                start, end)
    try:
        buckets = det_mod.bucketize(signals, granularity)
    except ValueError as exc:
        raise AppError("FILTER_INVALID", str(exc), 400)
    stamps = sorted(s.get("occurred_at", "") for s in signals)
    return {"granularity": granularity, "buckets": buckets,
            "total_signals": len(signals),
            "measurement_period": {
                "start": stamps[0] if stamps else "",
                "end": stamps[-1] if stamps else ""},
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                          time.gmtime()),
            "tenant_scope": _request_ctx(request).tenant_id}


@app.get("/api/v1/signals/{signal_id}")
def signal_detail(signal_id: str,
                  request: Request = None) -> dict[str, Any]:
    """One derived signal with outcome, link, and provenance."""
    sig = _visible_signal(signal_id, request)
    detail = dict(sig)
    detail["outcome"] = store.signal_outcome(signal_id)
    detail["link"] = store.signal_link(signal_id)
    detail["tenant_scope"] = _request_ctx(request).tenant_id
    return detail


@app.post("/api/v1/signals/{signal_id}/outcome")
def set_signal_outcome(signal_id: str, body: dict,
                       request: Request) -> dict[str, Any]:
    """Reviewer outcome for a signal (write-gated, audited)."""
    _require_write_token(request)
    _visible_signal(signal_id, request)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    outcome = body.get("outcome", "")
    if outcome not in SIGNAL_OUTCOMES:
        raise AppError("OUTCOME_INVALID",
                       "outcome must be one of " +
                       "|".join(SIGNAL_OUTCOMES), 400)
    note = str(body.get("note", "") or "")[:500]
    actor = _decision_actor(request, body.get("actor_id", "investigator"))
    previous = store.signal_outcome(signal_id)
    entry = store.set_signal_outcome(signal_id, outcome, actor, note)
    store.append_audit(
        "human", actor, "signal.outcome", "signal", signal_id,
        previous["current"] if previous else "NONE", outcome,
        note or outcome, store.state["trace_id"], _trace(request))
    return {"signal_id": signal_id, "outcome": outcome,
            "recorded_at": entry["recorded_at"]}


@app.post("/api/v1/signals/{signal_id}/link")
def link_signal(signal_id: str, body: dict,
                request: Request) -> dict[str, Any]:
    """Link a signal to an investigation (write-gated, audited)."""
    _require_write_token(request)
    _visible_signal(signal_id, request)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    inv_id = body.get("investigation_id", "")
    inv = tenancy_mod.enforce_read(store.get_investigation(inv_id),
                                   _request_ctx(request))
    if inv is None:
        raise AppError("UNKNOWN_INVESTIGATION", inv_id, 404)
    actor = _decision_actor(request, body.get("actor_id", "investigator"))
    entry = store.link_signal(signal_id, inv_id, actor)
    store.append_audit(
        "human", actor, "signal.link", "signal", signal_id,
        "NONE", inv_id, f"linked to {inv_id}",
        store.state["trace_id"], _trace(request))
    return {"signal_id": signal_id, "investigation_id": inv_id,
            "linked_at": entry["linked_at"]}


def _caller_identity(request: Request | None) -> str:
    """Stable per-caller key for notification read state.

    Session username when armed, "platform-token" for token creds,
    "local-default" for the unarmed local default. One caller's
    reads are never visible to another identity.
    """
    session = _session_of(request)
    if session is not None:
        return "user:" + session[0]
    if _token_ok(request):
        return "platform-token"
    return "local-default"


@app.get("/api/v1/notifications")
def list_notifications(request: Request) -> dict[str, Any]:
    reads = store.notification_reads_for(_caller_identity(request))
    items = [{
        "notification_id": a.get("alert_id"),
        "title": a.get("title", ""),
        "status": a.get("status", ""),
        "transaction_id": a.get("transaction_id"),
        "created_at": a.get("created_at", ""),
        "read": a.get("alert_id") in reads,
    } for a in _visible_alerts(request)]
    ident = _caller_identity(request)
    if ident.startswith("user:"):
        for entry in store.user_notifications_for(
                ident[len("user:"):]):
            items.append({
                "notification_id": entry.get("notification_id"),
                "title": entry.get("title", ""),
                "status": "OPEN",
                "transaction_id": None,
                "created_at": entry.get("created_at", ""),
                "read": entry.get("notification_id") in reads,
                "kind": "security",
                "detail": entry.get("detail", ""),
                "level": entry.get("level", "info"),
            })
    items.sort(key=lambda n: n["created_at"] or "", reverse=True)
    items = items[:200]
    unread = sum(1 for n in items
                 if not n["read"] and n["status"] == "OPEN")
    return {"notifications": items, "unread_count": unread,
            "synthetic_notice": "Synthetic data."}


@app.post("/api/v1/notifications/read")
def mark_notifications_read(body: dict[str, Any],
                            request: Request) -> dict[str, Any]:
    # Read-state writes use the standard write gate; per-identity
    # isolation is enforced via _caller_identity. Mark-read is not
    # security-relevant, so no audit event (auth failures elsewhere
    # are audited centrally).
    _require_write_token(request)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    if body.get("all", False):
        ids = [a.get("alert_id") for a in _visible_alerts(request)]
        _mark_ident = _caller_identity(request)
        if _mark_ident.startswith("user:"):
            ids += [e.get("notification_id") for e in
                    store.user_notifications_for(
                        _mark_ident[len("user:"):])]
    else:
        ids = body.get("notification_ids", [])
    if not isinstance(ids, list) or len(ids) > 500:
        raise AppError("INVALID_NOTIFICATION_IDS",
                       "notification_ids must be a list of at most 500",
                       400)
    clean: list[str] = []
    for nid in ids:
        if not isinstance(nid, str) or not nid or len(nid) > 128:
            raise AppError("INVALID_NOTIFICATION_ID",
                           "each id must be a 1..128 char string", 400)
        clean.append(nid)
    identity = _caller_identity(request)
    marked = store.mark_notifications_read(identity, clean)
    reads = store.notification_reads_for(identity)
    unread = sum(1 for a in _visible_alerts(request)
                 if a.get("alert_id") not in reads
                 and a.get("status") == "OPEN")
    return {"marked": marked, "unread_count": unread}


@app.get("/api/v1/investigations/{inv_id}")
def get_investigation(inv_id: str, request: Request = None) -> dict[str, Any]:
    inv = tenancy_mod.enforce_read(store.get_investigation(inv_id), _request_ctx(request))
    if inv is None:
        raise AppError("UNKNOWN_INVESTIGATION", inv_id, 404)
    alert = next(a for a in store.state["alerts"]
                 if a["alert_id"] == inv["alert_id"])
    case = tenancy_mod.enforce_read(next((c for c in store.state["cases"]
                 if c["investigation_id"] == inv_id), None), _request_ctx(request))
    ctx = _request_ctx(request)
    txn = tenancy_mod.enforce_read(
        store.get_transaction(inv["transaction_id"]), ctx)
    if txn is None:
        raise AppError("UNKNOWN_INVESTIGATION", inv_id, 404)
    risk_txn, risk_net, rule_results = _ensure_assessment(
        inv["transaction_id"], ctx)
    package = store.state["evidence_packages"][inv_id]
    return {"investigation": inv, "alert": alert,
            "transaction": txn,
            "risk_transaction": risk_txn, "risk_network": risk_net,
            "rule_results": rule_results, "case": case,
            "evidence_package_id": package["package_id"],
            "evidence_count": len(package["items"])}


@app.post("/api/v1/investigations/{inv_id}/evidence-package")
def build_evidence_package(inv_id: str,
                           request: Request) -> dict[str, Any]:
    # R4: same write gate as every other state-changing POST
    # (F-CONSIST-1; the handler stays a read-only alias of GET).
    _require_write_token(request)
    return _evidence_package(inv_id)


def _evidence_package(inv_id: str) -> dict[str, Any]:
    inv = store.get_investigation(inv_id)
    if inv is None:
        raise AppError("UNKNOWN_INVESTIGATION", inv_id, 404)
    return store.state["evidence_packages"][inv_id]


@app.get("/api/v1/investigations/{inv_id}/evidence-package")
def read_evidence_package(inv_id: str) -> dict[str, Any]:
    return _evidence_package(inv_id)


@app.get("/api/v1/investigations/{inv_id}/evidence-package/export")
def export_evidence_package(inv_id: str) -> Response:
    """EVID-01: deterministic export bytes + sha256 fingerprint.

    Read-only mirror of read_evidence_package (same visibility, no
    new auth surface). The body is canonical JSON so two exports of
    the same package are byte-identical; X-Export-SHA256
    fingerprints the exact bytes served.
    """
    package = _evidence_package(inv_id)
    blob = evidence_mod.canonical_export_bytes(package)
    return Response(content=blob, media_type="application/json",
                    headers={"X-Export-SHA256":
                             evidence_mod.export_fingerprint(blob)})


async def _run_ai(package: EvidencePackage, summary: str, run_id: str,
                  trace_id: str, question: str = "",
                  prior_context: str = "",
                  ctx: tenancy_mod.TenantContext | None = None) -> dict[str, Any]:
    """Run one model analysis (or follow-up) and persist run + audit.

    Shared by ai-analysis and ai-followup so validation, persistence,
    and audit behavior cannot drift between them.

    Phase 6: the daily live-call cap is enforced before any provider
    request; rejections are audited but persist no run (no call made).
    """
    limit = config_mod.AI_DAILY_CALL_LIMIT
    # J3-P7: quota visibility — name used/limit + reset time, not just the cap.
    used = ai_adapter.attempts_today(store.state.get("ai_runs", []))
    if limit > 0 and used >= limit:
        quota_msg = (f"daily live-model call limit reached "
                     f"({used}/{limit} used today; resets 00:00 UTC)")
        store.append_audit(
            "service", "ai-adapter", "ai.run.rejected", "agent_run", run_id,
            "PENDING", "REJECTED", quota_msg,
            store.state["trace_id"], trace_id)
        raise AppError("AI_DAILY_LIMIT_EXCEEDED", quota_msg, 429)
    t0 = time.monotonic()
    task = "followup" if (question or "").strip() else "analysis"
    try:
        run = await ai_gateway_mod.run(
            task, package, summary, store.state["trace_id"], run_id,
            store.state.get("ai_runs", []),
            timeout=config_mod.AI_TIMEOUT_SECONDS,
            question=question, prior_context=prior_context)
    except ai_adapter.AIError as exc:
        partial = getattr(exc, "run", None)
        detail = getattr(exc, "detail", None) or {}
        route = detail.get("route", {}) or {}
        first = (route.get("candidates") or [{}])[0]
        if partial is None:
            partial = {
                "agent_run_id": run_id,
                "provider": first.get("provider", "meta"),
                "model_id": first.get("model", META_MODEL_ID),
                "prompt_version": ai_adapter.PROMPT_VERSION,
                "request_id": "", "trace_id": store.state["trace_id"],
                "evidence_package_id": package.package_id,
                "evidence_ids_sent": sorted(i.evidence_id for i in package.items),
                "status": "FAILED", "response_reference": "",
                "schema_validation_status": "NOT_VALIDATED",
                "evidence_reference_validation_status": "NOT_VALIDATED",
                "error_code": exc.code, "synthetic_data_flag": True,
                "latency_ms": 0, "result": {},
                "route": route,
            }
        failed = dict(partial)
        if not failed.get("latency_ms"):
            failed["latency_ms"] = int((time.monotonic() - t0) * 1000)
        if ctx is not None:
            tenancy_mod.stamp(failed, ctx)
        store.save_ai_run(failed)
        store.append_audit("service", "ai-adapter", "ai.run.failed",
                           "agent_run", run_id, "PENDING", "FAILED",
                           f"{exc.code}: {exc}", store.state["trace_id"], trace_id)
        raise AppError(exc.code, str(exc), 503)
    if ctx is not None:
        tenancy_mod.stamp(run, ctx)
    store.save_ai_run(run)
    store.append_audit("service", "ai-adapter", "ai.run.succeeded",
                       "agent_run", run_id, "PENDING", run["status"],
                       f"Model {run['model_id']} validation "
                       f"{run['schema_validation_status']}/"
                       f"{run['evidence_reference_validation_status']}",
                       store.state["trace_id"], trace_id)
    return run


def _investigation_summary(
        inv_id: str,
        ctx: tenancy_mod.TenantContext | None = None
) -> tuple[dict, EvidencePackage, str]:
    inv = store.get_investigation(inv_id)
    if ctx is not None:
        inv = tenancy_mod.enforce_read(inv, ctx)
    if inv is None:
        raise AppError("UNKNOWN_INVESTIGATION", inv_id, 404)
    package = EvidencePackage.model_validate(
        store.state["evidence_packages"][inv_id])
    txn = store.get_transaction(inv["transaction_id"])
    if ctx is not None:
        txn = tenancy_mod.enforce_read(txn, ctx)
    if txn is None:
        raise AppError("UNKNOWN_INVESTIGATION", inv_id, 404)
    summary = (f"Synthetic investigation {inv_id}: transaction "
               f"{txn['transaction_id']} {txn['sender_account_id']} -> "
               f"{txn['receiver_account_id']} {txn['amount_minor']} kobo.")
    return inv, package, summary


@app.post("/api/v1/investigations/{inv_id}/ai-analysis")
async def ai_analysis(inv_id: str, request: Request) -> dict[str, Any]:
    _require_write_token(request)
    _require_login(request)
    ctx = _request_ctx(request)
    _, package, summary = _investigation_summary(inv_id, ctx)
    run_id = f"agentrun_{len(store.state['ai_runs']) + 1:04d}"
    return await _run_ai(package, summary, run_id, _trace(request),
                         ctx=ctx)


@app.post("/api/v1/investigations/{inv_id}/ai-followup")
async def ai_followup(inv_id: str, body: dict[str, Any],
                      request: Request) -> dict[str, Any]:
    _require_write_token(request)
    _require_login(request)
    ctx = _request_ctx(request)
    _, package, summary = _investigation_summary(inv_id, ctx)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY", "request body must be a JSON object", 400)
    question = (body.get("question", "") or "").strip()
    if not question:
        raise AppError("QUESTION_REQUIRED", "a question is required", 400)
    if len(question) > 2000:
        raise AppError("QUESTION_TOO_LONG",
                       "question exceeds 2000 characters", 400)
    run_id = f"agentrun_{len(store.state['ai_runs']) + 1:04d}"
    prior = ai_adapter.latest_run_context(
        tenancy_mod.filter_visible(
            [r for r in store.state["ai_runs"] if isinstance(r, dict)],
            ctx),
        package.package_id)
    return await _run_ai(package, summary, run_id, _trace(request),
                         question=question, prior_context=prior, ctx=ctx)


@app.get("/api/v1/ai-runs/{run_id}")
def get_ai_run(run_id: str, request: Request = None) -> dict[str, Any]:
    run = next((r for r in store.state["ai_runs"]
                if r["agent_run_id"] == run_id), None)
    run = tenancy_mod.enforce_read(run, _request_ctx(request))
    if run is None:
        raise AppError("UNKNOWN_RUN", run_id, 404)
    return run


# -- replay / simulation / cases ------------------------------------------
@app.get("/api/v1/replay/{scenario_id}")
def get_replay(scenario_id: str, cursor: int = 0,
               request: Request = None) -> dict[str, Any]:
    if scenario_id != store.state["scenario_id"]:
        raise AppError("UNKNOWN_SCENARIO", scenario_id, 404)
    view = tenancy_mod.visible_state(store.state, _request_ctx(request))
    return replay_mod.state_at(view, cursor)


@app.post("/api/v1/simulations")
def post_simulation(body: dict[str, Any], request: Request) -> dict[str, Any]:
    _require_write_token(request)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY", "request body must be a JSON object", 400)
    ignored = body.get("ignored_edge_ids", [])
    if not isinstance(ignored, list) or any(
            not isinstance(e, str) for e in ignored):
        raise AppError("INVALID_EDGE_LIST",
                       "ignored_edge_ids must be a list of strings", 400)
    ctx = _request_ctx(request)
    target = tenancy_mod.enforce_read(
        store.get_transaction(body.get("target_transaction_id", "")), ctx)
    if target is None:
        raise AppError("UNKNOWN_TRANSACTION",
                       body.get("target_transaction_id", ""), 404)
    view = tenancy_mod.visible_state(store.state, ctx)
    try:
        sim = simulate_mod.run(
            view, body.get("target_transaction_id", ""),
            ignored, body.get("assumption", ""),
            store.state["trace_id"])
    except ValueError as exc:
        raise _domain_error(exc)
    tenancy_mod.stamp(sim, ctx)
    store.save_simulation(sim)
    store.append_audit("human", body.get("actor_id", "investigator"),
                       "simulation.run", "simulation", sim["simulation_id"],
                       f"{sim['baseline_score']}", f"{sim['simulated_score']}",
                       sim["assumption"], store.state["trace_id"],
                       _trace(request))
    return sim


@app.get("/api/v1/cases")
def list_cases(request: Request = None) -> dict[str, Any]:
    return {"cases": tenancy_mod.filter_visible(
        store.state["cases"], _request_ctx(request))}


def latest_ai_run_for_case(
        case: dict[str, Any],
        ctx: tenancy_mod.TenantContext | None = None
) -> dict[str, Any] | None:
    """Read-only summary of the latest AI run for a case's evidence package.

    Additive for GET case detail. Returns None when no run exists.
    Never mutates state, scores, or decisions.
    """
    package = store.state["evidence_packages"].get(case["investigation_id"])
    package_id = package["package_id"] if package else None
    runs = store.state["ai_runs"]
    if ctx is not None:
        runs = tenancy_mod.filter_visible(
            [r for r in runs if isinstance(r, dict)], ctx)
    for run in reversed(runs):
        if package_id is not None and run.get("evidence_package_id") != package_id:
            continue
        # J3-P5: a FAILED run (empty result) must never mask the latest
        # SUCCEEDED assessment the case page would otherwise show.
        if run.get("status") != "SUCCEEDED":
            continue
        result = run.get("result") if isinstance(run.get("result"), dict) else {}
        findings = []
        for finding in result.get("key_findings", []) or []:
            if not isinstance(finding, dict):
                continue
            findings.append({
                "finding": finding.get("finding", ""),
                "confidence_label": finding.get("confidence_label", ""),
                "evidence_ids": finding.get("evidence_ids", []) or [],
            })
        return {
            "agent_run_id": run.get("agent_run_id", ""),
            "model_id": run.get("model_id", ""),
            "status": run.get("status", ""),
            "prompt_version": run.get("prompt_version", ""),
            "conclusion": result.get("conclusion", ""),
            "missing_information": result.get("missing_information", []) or [],
            "key_findings": findings,
            "schema_validation_status": run.get("schema_validation_status", ""),
            "evidence_reference_validation_status": run.get(
                "evidence_reference_validation_status", ""),
            "latency_ms": run.get("latency_ms", 0),
            "completed_at": run.get("completed_at", ""),
        }
    return None


@app.post("/api/v1/cases")
def post_case(body: dict[str, Any], request: Request) -> dict[str, Any]:
    """D-036: open a case (was seed-only). Write-gated, audited."""
    _require_write_token(request)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    if config_mod.trial_enforcement_enabled():
        meter_claims = _session_claims(request)
        if meter_claims is not None:
            try:
                billing_mod.metered_action(
                    store, meter_claims["user"],
                    config_mod.FOUNDER_USER or "", True)
            except ValueError as exc:
                raise _domain_error(exc, default_status=402)
    try:
        case, audit = cases_mod.create_case(
            store, body.get("title", ""),
            description=body.get("description", ""),
            priority=body.get("priority", "MEDIUM"),
            assignee=body.get("assignee", ""),
            due_date=body.get("due_date", ""),
            notes=body.get("notes", ""),
            investigation_id=body.get("investigation_id", ""),
            actor_id=_connector_actor(request),
            trace_id=_trace(request),
            tenant=_request_ctx(request))
    except ValueError as exc:
        raise _domain_error(exc)
    return {"case": case, "audit": audit}


@app.get("/api/v1/cases/{case_id}")
def get_case(case_id: str, request: Request = None) -> dict[str, Any]:
    case = tenancy_mod.enforce_read(store.get_case(case_id), _request_ctx(request))
    if case is None:
        raise AppError("CASE_NOT_FOUND", case_id, 404)
    decisions = tenancy_mod.filter_visible(
        [d for d in store.state["decisions"] if d["case_id"] == case_id],
        _request_ctx(request))
    return {"case": case, "decisions": decisions,
            "allowed_transitions": cases_mod.allowed_transitions(case["status"]),
            "latest_ai_run": latest_ai_run_for_case(
                case, _request_ctx(request))}


@app.post("/api/v1/cases/{case_id}/decisions")
def post_decision(case_id: str, body: dict[str, Any],
                  request: Request) -> dict[str, Any]:
    _require_write_token(request)
    try:
        if (body.get("target_status", "") == "CLOSED" and
                gov_mod.is_held(store, "case", case_id,
                                _request_ctx(request).tenant_id)):
            raise AppError("CASE_ON_HOLD",
                           "case under legal hold cannot close", 409)
        record, audit = cases_mod.record_decision(
            store, case_id, body.get("decision", ""),
            body.get("target_status", ""), body.get("reason", ""),
            _decision_actor(request,
                            body.get("actor_id", "investigator")),
            body.get("evidence_viewed", []),
            body.get("recommendation", ""), _trace(request),
            actor_role=_decision_actor_role(request),
            tenant=_request_ctx(request))
    except ValueError as exc:
        raise _domain_error(exc)
    return {"decision": record, "audit": audit,
            "case": store.get_case(case_id)}


@app.get("/api/v1/cases/{case_id}/audit")
def case_audit(case_id: str, request: Request = None) -> dict[str, Any]:
    if tenancy_mod.enforce_read(store.get_case(case_id), _request_ctx(request)) is None:
        raise AppError("CASE_NOT_FOUND", case_id, 404)
    return {"audits": [a for a in store.state["audits"]
                       if a["target_id"] == case_id]}


@app.post("/api/v1/events")
def ingest_event(body: dict[str, Any],
                 request: Request) -> dict[str, Any]:
    """Ingest a signal event (write-gated, audited).

    AUD-03: every validated ingest appends an audit row (accepted
    and idempotent duplicates alike, mirroring the signal-link
    precedent); schema rejections raise before any audit. Actor
    follows the promote-handler contract (session user /
    platform-token / anonymous); the detail carries routing fields
    only, never payload secrets.
    """
    _require_write_token(request)
    try:
        status, event, warnings = store.ingest_event(body)
    except ValueError as exc:
        raise _domain_error(exc, 422)
    session = _session_of(request)
    if session is not None:
        actor = session[0]
    elif _token_ok(request):
        actor = "platform-token"
    else:
        actor = "anonymous"
    txn = event["transaction"]
    store.append_audit(
        "user", actor, "event.ingested", "event", event["event_id"],
        "NONE", status, "%s/%s" % (txn["transaction_id"],
                                  txn["channel"]),
        store.state["trace_id"], _trace(request))
    return {"status": status, "event": event, "warnings": warnings}
# -- universal financial crime intelligence (UFI) -------------------------
from app import alerts as alerts_mod
from app import altpayments as altpay_mod
from app import institutions as inst_mod
from app import parties as uparty_mod
from app import payment_methods as paymethod_mod
from app import reports as reports_mod
from app import tracing as tracing_mod
from app import typologies as typo_mod


@app.get("/api/v1/payment-methods")
def list_payment_methods() -> dict[str, Any]:
    """Canonical payment taxonomy with traceability records."""
    return {"methods": paymethod_mod.list_methods(),
            "families": paymethod_mod.FAMILIES}


@app.get("/api/v1/payment-methods/{method_id}")
def get_payment_method(method_id: str) -> dict[str, Any]:
    """One taxonomy entry or 404."""
    found = paymethod_mod.get_method(method_id)
    if found is None:
        raise AppError("METHOD_UNKNOWN",
                       "unknown payment method: %s" % method_id, 404)
    return found


@app.get("/api/v1/payment-networks")
def list_payment_networks() -> dict[str, Any]:
    """Payment networks/rails with honest integration status."""
    return {"networks": inst_mod.list_networks()}


@app.get("/api/v1/institutions")
def list_institutions() -> dict[str, Any]:
    """Institution registry (networks/rails; no fabricated banks)."""
    return {"institutions": inst_mod.list_networks()}


@app.get("/api/v1/transactions/{txn_id}/parties")
def transaction_parties(txn_id: str, request: Request,
                        reveal: bool = False) -> dict[str, Any]:
    """Masked sender/recipient/merchant roles for one transaction."""
    txns, _ = _tenant_signals(request)
    txn = next((t for t in txns if t.get("transaction_id") == txn_id),
               None)
    if txn is None:
        raise AppError("TRANSACTION_UNKNOWN",
                       "unknown transaction: %s" % txn_id, 404)
    found = uparty_mod.extract_parties(txn)
    if reveal:
        _require_write_token(request)
        actor = _decision_actor(request, "investigator")
        for row in found:
            row.update(uparty_mod.reveal(row, txn.get(row["source_field"])))
        store.append_audit(
            "human", actor, "party.reveal", "transaction", txn_id,
            "MASKED", "REVEALED", "restricted party reveal",
            store.state["trace_id"], _trace(request))
    return {"transaction_id": txn_id, "parties": found,
            "classification": paymethod_mod.classify(txn),
            "network": inst_mod.identify(txn),
            "tenant_scope": _request_ctx(request).tenant_id}


@app.get("/api/v1/fraud/typologies")
def list_typologies(request: Request,
                    industry: str | None = None) -> dict[str, Any]:
    """40-hypothesis typology registry, optionally industry-filtered."""
    return {"typologies": typo_mod.list_typologies(industry)}


@app.get("/api/v1/fraud/typologies/{typology_id}")
def get_typology(typology_id: str,
                 request: Request) -> dict[str, Any]:
    """One typology with real matched-signal evidence."""
    found = typo_mod.get_typology(typology_id)
    if found is None:
        raise AppError("TYPOLOGY_UNKNOWN",
                       "unknown typology: %s" % typology_id, 404)
    _, result = _tenant_signals(request)
    matched = typo_mod.signals_for_typology(typology_id,
                                            result["signals"])
    found["matched_signal_ids"] = [s.get("signal_id") for s in matched]
    found["matched_count"] = len(matched)
    return found


@app.get("/api/v1/industries/{ident}/typologies")
def industry_typologies(ident: str) -> dict[str, Any]:
    """Typologies relevant to one canonical industry."""
    if ind_mod.get_module(ident) is None:
        raise AppError("INDUSTRY_UNKNOWN",
                       "unknown industry: %s" % ident, 404)
    return {"industry_id": ident,
            "typologies": typo_mod.list_typologies(ident)}


@app.get("/api/v1/fraud/alerts")
def list_fraud_alerts(request: Request,
                      status: str | None = None) -> dict[str, Any]:
    """Tenant-scoped fraud alerts, optionally status-filtered."""
    ctx = _request_ctx(request)
    rows = [r for r in alerts_mod.list_alerts(store, status)
            if r.get("tenant_id", tenancy_mod.DEFAULT_TENANT) == ctx.tenant_id]
    return {"alerts": rows, "tenant_scope": ctx.tenant_id}


@app.get("/api/v1/fraud/alerts/metrics")
def fraud_alert_metrics(request: Request) -> dict[str, Any]:
    """Alert metrics computed from stored tenant rows."""
    ctx = _request_ctx(request)
    rows = [r for r in store.fraud_alerts()
            if r.get("tenant_id", tenancy_mod.DEFAULT_TENANT) == ctx.tenant_id]
    by_status: dict[str, int] = {}
    by_family: dict[str, int] = {}
    for row in rows:
        key = row.get("status", "?")
        by_status[key] = by_status.get(key, 0) + 1
        fam = row.get("detector_family") or "?"
        by_family[fam] = by_family.get(fam, 0) + 1
    return {"tenant_scope": ctx.tenant_id, "tenant_total": len(rows),
            "tenant_by_status": by_status,
            "tenant_by_detector_family": by_family,
            "window": "stored fraud alerts for this tenant"}


@app.get("/api/v1/fraud/alerts/{alert_id}")
def get_fraud_alert(alert_id: str,
                    request: Request) -> dict[str, Any]:
    """One tenant-visible fraud alert."""
    ctx = _request_ctx(request)
    found = alerts_mod.get_alert(store, alert_id)
    if found is None or found.get("tenant_id", tenancy_mod.DEFAULT_TENANT) != ctx.tenant_id:
        raise AppError("ALERT_UNKNOWN",
                       "unknown alert: %s" % alert_id, 404)
    return found


@app.post("/api/v1/fraud/alerts")
def open_fraud_alert(body: dict, request: Request) -> dict[str, Any]:
    """Open an alert from a tenant-visible signal (write-gated)."""
    _require_write_token(request)
    if not isinstance(body, dict) or not body.get("signal_id"):
        raise AppError("INVALID_BODY", "signal_id is required", 400)
    _visible_signal(body["signal_id"], request)
    txns, result = _tenant_signals(request)
    sig = next((s for s in result["signals"]
                if s.get("signal_id") == body["signal_id"]), None)
    actor = _decision_actor(request, "investigator")
    try:
        out = alerts_mod.open_from_signal(store, sig, actor)
    except ValueError as exc:
        raise _domain_error(exc, 400)
    if out["status"] == "opened":
        out["alert"]["tenant_id"] = _request_ctx(request).tenant_id
        store.fraud_alert_save(out["alert"])
        store.append_audit(
            "human", actor, "fraud.alert.opened", "signal",
            body["signal_id"], "NONE", out["alert"]["id"],
            out["alert"]["id"], store.state["trace_id"],
            _trace(request))
    return out


@app.patch("/api/v1/fraud/alerts/{alert_id}")
def move_fraud_alert(alert_id: str, body: dict,
                     request: Request) -> dict[str, Any]:
    """Legal alert transition (write-gated, audited)."""
    _require_write_token(request)
    ctx = _request_ctx(request)
    found = alerts_mod.get_alert(store, alert_id)
    if found is None or found.get("tenant_id", tenancy_mod.DEFAULT_TENANT) != ctx.tenant_id:
        raise AppError("ALERT_UNKNOWN",
                       "unknown alert: %s" % alert_id, 404)
    if not isinstance(body, dict) or not body.get("status"):
        raise AppError("INVALID_BODY", "status is required", 400)
    actor = _decision_actor(request, "investigator")
    previous = found["status"]
    try:
        row = alerts_mod.transition(store, alert_id, body["status"], actor)
    except ValueError as exc:
        raise _domain_error(exc, 400)
    store.append_audit(
        "human", actor, "fraud.alert.transition", "fraud_alert",
        alert_id, previous, row["status"], row["status"],
        store.state["trace_id"], _trace(request))
    return row


@app.post("/api/v1/tracing/transactions")
def create_trace(body: dict, request: Request) -> dict[str, Any]:
    """Build and store an evidence-based fund trace (write-gated)."""
    _require_write_token(request)
    if not isinstance(body, dict) or not body.get("transaction_id"):
        raise AppError("INVALID_BODY", "transaction_id is required", 400)
    txns, _ = _tenant_signals(request)
    edges = [e for e in store.state.get("edges", [])
             if isinstance(e, dict)]
    try:
        max_hops = int(body.get("max_hops", 4))
    except (TypeError, ValueError):
        raise AppError("INVALID_BODY", "max_hops must be an integer",
                       400)
    max_hops = min(max(max_hops, 0), 8)
    try:
        trace = tracing_mod.build_trace(txns, edges,
                                        body["transaction_id"], max_hops)
    except ValueError as exc:
        raise _domain_error(exc, 404)
    trace["tenant_id"] = _request_ctx(request).tenant_id
    store.trace_save(trace)
    trace = dict(trace)
    _invs = tenancy_mod.filter_visible(
        [i for i in store.state.get("investigations", [])
         if isinstance(i, dict)], _request_ctx(request))
    trace["related_investigation_ids"] = \
        tracing_mod.related_investigations(trace, _invs)
    actor = _decision_actor(request, "investigator")
    store.append_audit(
        "human", actor, "trace.created", "trace", trace["trace_id"],
        "NONE", body["transaction_id"], trace["trace_id"],
        store.state["trace_id"], _trace(request))
    return trace


@app.get("/api/v1/tracing/{trace_id}")
def get_trace(trace_id: str, request: Request) -> dict[str, Any]:
    """One tenant-visible stored trace."""
    ctx = _request_ctx(request)
    found = next((t for t in store.traces()
                  if t.get("trace_id") == trace_id
                  and t.get("tenant_id", tenancy_mod.DEFAULT_TENANT) == ctx.tenant_id),
                 None)
    if found is None:
        raise AppError("TRACE_UNKNOWN",
                       "unknown trace: %s" % trace_id, 404)
    found = dict(found)
    invs = tenancy_mod.filter_visible(
        [i for i in store.state.get("investigations", [])
         if isinstance(i, dict)], ctx)
    found["related_investigation_ids"] = \
        tracing_mod.related_investigations(found, invs)
    return found


@app.get("/api/v1/tracing/{trace_id}/movements")
def get_trace_movements(trace_id: str,
                        request: Request) -> dict[str, Any]:
    """Movement legs of one tenant-visible trace."""
    trace = get_trace(trace_id, request)
    return {"trace_id": trace_id, "movements": trace.get("movements", []),
            "limitations": trace.get("limitations", [])}


@app.get("/api/v1/altpayments/capabilities")
def altpayment_capabilities() -> dict[str, Any]:
    """Honest crypto/gift/remittance capability document."""
    return altpay_mod.capabilities()


@app.post("/api/v1/reports")
def create_report(body: dict, request: Request) -> dict[str, Any]:
    """Build a deterministic evidence-grounded report (write-gated)."""
    _require_write_token(request)
    if not isinstance(body, dict) or not body.get("report_type"):
        raise AppError("INVALID_BODY", "report_type is required", 400)
    bundle = body.get("bundle")
    inv_id = body.get("investigation_id")
    if bundle is None:
        if not inv_id:
            raise AppError("INVALID_BODY",
                           "bundle or investigation_id is required", 400)
        bundle = _report_bundle_for_investigation(inv_id, request)
    if not isinstance(bundle, dict) or len(bundle) > 40:
        raise AppError("INVALID_BODY",
                       "bundle must be an object of at most 40 keys",
                       400)
    actor = _decision_actor(request, "investigator")
    try:
        report = reports_mod.build(body["report_type"], bundle,
                                   body.get("investigation_id"))
    except ValueError as exc:
        raise _domain_error(exc, 400)
    store.append_audit(
        "human", actor, "report.created", "report",
        report["report_type"], "NONE", report["report_type"],
        ",".join(sorted(bundle)), store.state["trace_id"],
        _trace(request))
    return report
# -- UFI slice 2: transactions, monitoring, industry adapters ------------
from app import industry_adapters as indadapt_mod
from app import monitoring as monitoring_mod


@app.get("/api/v1/transactions")
def list_transactions(request: Request, channel: str | None = None,
                      method: str | None = None, limit: int = 50,
                      offset: int = 0) -> dict[str, Any]:
    """Tenant-visible transactions with classification (+filters)."""
    txns, _ = _tenant_signals(request)
    rows = []
    for txn in txns:
        if channel and txn.get("channel") != channel:
            continue
        classified = paymethod_mod.classify(txn)
        if method and classified["method_id"] != method:
            continue
        rows.append({"transaction": txn, "classification": classified,
                     "network": inst_mod.identify(txn)})
    limit = min(max(int(limit), 1), 200)
    offset = max(int(offset), 0)
    return {"total": len(rows), "limit": limit, "offset": offset,
            "transactions": rows[offset:offset + limit],
            "tenant_scope": _request_ctx(request).tenant_id}


def _visible_txn(txn_id: str, request: Request) -> dict[str, Any]:
    txns, _ = _tenant_signals(request)
    txn = next((t for t in txns if t.get("transaction_id") == txn_id),
               None)
    if txn is None:
        raise AppError("TRANSACTION_UNKNOWN",
                       "unknown transaction: %s" % txn_id, 404)
    return txn


@app.get("/api/v1/transactions/{txn_id}/events")
def transaction_events(txn_id: str,
                       request: Request) -> dict[str, Any]:
    """Lifecycle events for one tenant-visible transaction."""
    _visible_txn(txn_id, request)
    rows = []
    for event in store.state.get("events", []):
        if not isinstance(event, dict):
            continue
        embedded = event.get("transaction", {})
        if embedded.get("transaction_id") != txn_id:
            continue
        rows.append({
            "event_id": event.get("event_id"),
            "event_type": event.get("event_type"),
            "occurred_at": event.get("occurred_at"),
            "source": event.get("source"),
            "lifecycle": paymethod_mod.map_lifecycle(
                event.get("source"), event.get("event_type")),
        })
    return {"transaction_id": txn_id, "events": rows,
            "tenant_scope": _request_ctx(request).tenant_id}


@app.get("/api/v1/transactions/{txn_id}/relationships")
def transaction_relationships(txn_id: str,
                              request: Request) -> dict[str, Any]:
    """Related transactions + graph neighborhood for one transaction."""
    txns, _ = _tenant_signals(request)
    txn = _visible_txn(txn_id, request)
    related = []
    for other in txns:
        other_id = other.get("transaction_id")
        if other_id == txn_id:
            continue
        link = tracing_mod.link_strength(txn, other)
        if link["status"] != "NO_MATCH":
            related.append({"transaction_id": other_id,
                            "status": link["status"],
                            "evidence": link["evidence"]})
    node_ids = {n.get("node_id") for n in store.state.get("nodes", [])
                if isinstance(n, dict)}
    seeds = {v for v in (txn.get("sender_account_id"),
                         txn.get("receiver_account_id")) if v in node_ids}
    neighborhood_nodes: list = []
    neighborhood_edges: list = []
    if seeds:
        neighborhood_nodes, neighborhood_edges = graph_mod.neighborhood(
            store.state.get("nodes", []), store.state.get("edges", []),
            seeds, 1)
    return {"transaction_id": txn_id,
            "related_transactions": related,
            "graph_nodes": neighborhood_nodes,
            "graph_edges": neighborhood_edges,
            "tenant_scope": _request_ctx(request).tenant_id}


@app.get("/api/v1/tracing/{trace_id}/relationships")
def trace_relationships(trace_id: str,
                        request: Request) -> dict[str, Any]:
    """Entities + account edges across a trace's visited transactions."""
    trace = get_trace(trace_id, request)
    txns, _ = _tenant_signals(request)
    by_id = {t.get("transaction_id"): t for t in txns}
    accounts: set = set()
    devices: set = set()
    phones: set = set()
    merchants: set = set()
    for visited in trace.get("visited_transactions", []):
        txn = by_id.get(visited)
        if not txn:
            continue
        for key, bucket in (("sender_account_id", accounts),
                            ("receiver_account_id", accounts),
                            ("device_id", devices),
                            ("phone_id", phones),
                            ("merchant_id", merchants)):
            if txn.get(key):
                bucket.add(txn[key])
    edges = [e for e in store.state.get("edges", [])
             if isinstance(e, dict)
             and e.get("source_node_id") in accounts
             and e.get("target_node_id") in accounts]
    return {"trace_id": trace_id,
            "accounts": sorted(accounts),
            "devices": sorted(devices),
            "phones": sorted(phones),
            "merchants": sorted(merchants),
            "account_edges": edges}


@app.get("/api/v1/monitoring/status")
def monitoring_status(request: Request) -> dict[str, Any]:
    """Monitoring posture from live tenant rows."""
    ctx = _request_ctx(request)
    txns, result = _tenant_signals(request)
    return monitoring_mod.status(store, txns, result["signals"],
                                 ctx.tenant_id)


@app.post("/api/v1/monitoring/evaluate")
def monitoring_evaluate(request: Request) -> dict[str, Any]:
    """Run detection; open alerts for newly-seen signals (write-gated)."""
    _require_write_token(request)
    ctx = _request_ctx(request)
    txns, _ = _tenant_signals(request)
    actor = _decision_actor(request, "investigator")
    out = monitoring_mod.evaluate(
        store, txns, store.state.get("edges", []), ctx.tenant_id,
        actor)
    store.append_audit(
        "human", actor, "monitoring.evaluated", "tenant",
        ctx.tenant_id, "NONE", str(out["signals_evaluated"]),
        "%d opened" % len(out["alerts_opened"]),
        store.state["trace_id"], _trace(request))
    return out


@app.get("/api/v1/industries/{ident}/coverage")
def industry_coverage(ident: str) -> dict[str, Any]:
    """Static adapter coverage for one canonical industry."""
    try:
        return indadapt_mod.coverage(ident)
    except ValueError as exc:
        raise _domain_error(exc, 404)


@app.get("/api/v1/industries/{ident}/readiness")
def industry_readiness(ident: str,
                       request: Request) -> dict[str, Any]:
    """Evidence readiness (never promotes registry status)."""
    if ind_mod.get_module(ident) is None:
        raise AppError("INDUSTRY_UNKNOWN",
                       "unknown industry: %s" % ident, 404)
    _, result = _tenant_signals(request)
    signals = result["signals"]
    matched = {}
    for typo in typo_mod.list_typologies(ident):
        matched[typo["typology_id"]] = len(
            typo_mod.signals_for_typology(typo["typology_id"], signals))
    return indadapt_mod.readiness(ident, matched)
def _report_bundle_for_investigation(inv_id: str,
                                     request: Request) -> dict[str, Any]:
    """Assemble a report bundle from tenant-visible rows (shared with
    the report.build agent tool)."""
    from app import intel_tools as itools_mod

    ctx = _request_ctx(request)
    invs = tenancy_mod.filter_visible(
        [i for i in store.state.get("investigations", [])
         if isinstance(i, dict)], ctx)
    inv = next((i for i in invs
                if i.get("investigation_id") == inv_id), None)
    if inv is None:
        raise AppError("INVESTIGATION_UNKNOWN",
                       "unknown investigation: %s" % inv_id, 404)
    txns, result = _tenant_signals(request)
    try:
        return itools_mod.assemble_bundle(store, txns,
                                          result["signals"],
                                          inv.get("transaction_id"))
    except ValueError as exc:
        raise _domain_error(exc, 400)


@app.get("/api/v1/industries/readiness")
def industries_fleet_readiness(request: Request) -> dict[str, Any]:
    """Measured readiness snapshot across all 45 industries."""
    _, result = _tenant_signals(request)
    signals = result["signals"]
    matched = {}
    for typo in typo_mod.list_typologies():
        matched[typo["typology_id"]] = len(
            typo_mod.signals_for_typology(typo["typology_id"], signals))
    return indadapt_mod.fleet_readiness(matched)
# -- SEC-CRED + SEC-DEV routes ------------------------------------------
from app import api_credentials as apicred_mod


@app.post("/api/v1/auth/clients")
def admin_issue_client(body: dict, request: Request) -> dict[str, Any]:
    """Issue a per-client credential (admin session only).

    The secret returns once; only its hash persists. Audited."""
    claims = _require_admin(request)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    try:
        out = apicred_mod.issue(store, body.get("name", ""),
                                body.get("scopes", []), claims["user"])
    except ValueError as exc:
        raise _domain_error(exc, 400)
    store.append_audit("human", claims["user"], "auth.client.issued",
                       "api_client", out["client_id"], "NONE",
                       out["client_id"], ",".join(out["scopes"]),
                       store.state["trace_id"], _trace(request))
    return out


@app.get("/api/v1/auth/clients")
def admin_list_clients(request: Request) -> dict[str, Any]:
    """Redacted client list (admin session only)."""
    _require_admin(request)
    return {"clients": [apicred_mod.redacted(r)
                        for r in store.api_credentials()]}


@app.post("/api/v1/auth/clients/{client_id}/revoke")
def admin_revoke_client(client_id: str,
                        request: Request) -> dict[str, Any]:
    """Revoke a client credential (admin session only)."""
    claims = _require_admin(request)
    try:
        record = apicred_mod.revoke(store, client_id, claims["user"])
    except ValueError as exc:
        raise _domain_error(exc, 404)
    store.append_audit("human", claims["user"], "auth.client.revoked",
                       "api_client", client_id, "ACTIVE", "REVOKED",
                       client_id, store.state["trace_id"],
                       _trace(request))
    return apicred_mod.redacted(record)


def _self_claims(request: Request) -> dict:
    claims = _session_claims(request)
    if claims is None:
        raise AppError("LOGIN_REQUIRED", "login required", 401)
    return claims


@app.get("/api/v1/account/devices")
def list_my_devices(request: Request) -> dict[str, Any]:
    """The caller's registered devices."""
    claims = _self_claims(request)
    return {"devices": store.user_devices(claims["user"])}


@app.post("/api/v1/account/devices/trust")
def trust_my_device(body: dict, request: Request) -> dict[str, Any]:
    """Trust or untrust one of the caller's devices."""
    claims = _self_claims(request)
    if not isinstance(body, dict) or not body.get("device_key"):
        raise AppError("INVALID_BODY", "device_key is required", 400)
    try:
        record = trustdev_mod.set_trusted(store, claims["user"],
                                          body["device_key"],
                                          bool(body.get("trusted", True)))
    except ValueError as exc:
        raise _domain_error(exc, 404)
    store.append_audit("human", claims["user"], "auth.device.trust",
                       "device", body["device_key"], "NONE",
                       str(record["trusted"]), body["device_key"],
                       store.state["trace_id"], _trace(request))
    return record


@app.post("/api/v1/account/devices/revoke")
def revoke_my_device(body: dict, request: Request) -> dict[str, Any]:
    """Revoke one of the caller's devices (future logins denied)."""
    claims = _self_claims(request)
    if not isinstance(body, dict) or not body.get("device_key"):
        raise AppError("INVALID_BODY", "device_key is required", 400)
    try:
        record = trustdev_mod.revoke(store, claims["user"],
                                     body["device_key"])
    except ValueError as exc:
        raise _domain_error(exc, 404)
    store.append_audit("human", claims["user"], "auth.device.revoked",
                       "device", body["device_key"], "ACTIVE", "REVOKED",
                       body["device_key"], store.state["trace_id"],
                       _trace(request))
    return record
# -- Agent OS routes -----------------------------------------------------
from app import agent_retrieval as agentret_mod
from app import conversations as convos_mod
from app import nl_search as nlsearch_mod
from app import orchestration as orch_mod


def _os_subject(request: Request) -> dict[str, Any]:
    _require_login(request)
    return _agent_subject(request)


@app.post("/api/v1/agent-os/run")
def agent_os_run(body: dict, request: Request) -> dict[str, Any]:
    """Run one orchestrated turn (login session required)."""
    subject = _os_subject(request)
    if not isinstance(body, dict) or not (body.get("text") or ""):
        raise AppError("INVALID_BODY", "text is required", 400)
    record = orch_mod.start(store, body["text"], subject,
                            body.get("args"))
    store.append_audit("user", subject["user"], "agentos.run",
                       "agent-execution", record["execution_id"], "",
                       record["state"], record["execution_id"],
                       store.state["trace_id"], _trace(request))
    return record


@app.post("/api/v1/agent-os/executions/{execution_id}/resume")
def agent_os_resume(execution_id: str,
                    request: Request) -> dict[str, Any]:
    """Resume an APPROVAL_REQUIRED execution after plan approval."""
    subject = _os_subject(request)
    try:
        record = orch_mod.resume(store, execution_id, subject)
    except ValueError as exc:
        raise _domain_error(exc, 400)
    store.append_audit("user", subject["user"], "agentos.resume",
                       "agent-execution", execution_id, "",
                       record["state"], execution_id,
                       store.state["trace_id"], _trace(request))
    return record


@app.get("/api/v1/agent-os/executions")
def agent_os_executions(request: Request) -> dict[str, Any]:
    """Tenant executions (login session required)."""
    subject = _os_subject(request)
    rows = [r for r in store.agent_executions()
            if (r.get("subject") or {}).get("tenant") == subject[
                "tenant"]]
    return {"executions": rows, "tenant_scope": subject["tenant"]}


@app.get("/api/v1/agent-os/metrics")
def agent_os_metrics(request: Request) -> dict[str, Any]:
    """Execution metrics (login session required)."""
    _os_subject(request)
    return orch_mod.metrics(store)


@app.post("/api/v1/agent-os/search")
def agent_os_search(body: dict, request: Request) -> dict[str, Any]:
    """Natural-language transaction search (login required)."""
    subject = _os_subject(request)
    if not isinstance(body, dict) or not (body.get("text") or ""):
        raise AppError("INVALID_BODY", "text is required", 400)
    query = nlsearch_mod.parse(body["text"])
    if query.get("needs_clarification"):
        return {"query": query, "results": None}
    txns, result = _tenant_signals(request)
    return {"query": query,
            "results": nlsearch_mod.execute(store, txns,
                                            result["signals"], query),
            "tenant_scope": subject["tenant"]}


@app.post("/api/v1/agent-os/retrieve")
def agent_os_retrieve(body: dict, request: Request) -> dict[str, Any]:
    """Permission-checked hybrid retrieval (login required)."""
    _os_subject(request)  # enforce login; subject unused beyond the gate
    if not isinstance(body, dict) or not (body.get("query") or ""):
        raise AppError("INVALID_BODY", "query is required", 400)
    ctx = _request_ctx(request)
    return agentret_mod.search(store, ctx, body["query"],
                               body.get("sources"),
                               body.get("limit", 20))


@app.post("/api/v1/conversations")
def create_conversation(body: dict,
                        request: Request) -> dict[str, Any]:
    """Open an assistant thread (login required)."""
    subject = _os_subject(request)
    context = (body or {}).get("context", {})
    if not isinstance(context, dict):
        raise AppError("INVALID_BODY", "context must be an object",
                       400)
    return convos_mod.create(store, subject["tenant"],
                             subject["user"], context)


@app.get("/api/v1/conversations")
def list_conversations(request: Request) -> dict[str, Any]:
    """The caller's threads (login required)."""
    subject = _os_subject(request)
    rows = store.conversations_for(subject["tenant"], subject["user"])
    return {"conversations": [
        {k: v for k, v in r.items() if k != "messages"} for r in rows]}


@app.get("/api/v1/conversations/{conversation_id}")
def get_conversation(conversation_id: str,
                     request: Request) -> dict[str, Any]:
    """One thread with messages (owner + tenant checked)."""
    subject = _os_subject(request)
    found = convos_mod.get_visible(store, conversation_id,
                                   subject["tenant"], subject["user"])
    if found is None:
        raise AppError("CONVERSATION_UNKNOWN", "unknown conversation",
                       404)
    return found


@app.post("/api/v1/conversations/{conversation_id}/messages")
def post_conversation_message(conversation_id: str, body: dict,
                              request: Request) -> dict[str, Any]:
    """Chat turn: stores the user message, runs the orchestrator,
    stores the assistant summary (login required)."""
    subject = _os_subject(request)
    if not isinstance(body, dict) or not (body.get("text") or ""):
        raise AppError("INVALID_BODY", "text is required", 400)
    try:
        user_msg = convos_mod.post_message(
            store, conversation_id, "user", body["text"],
            subject["tenant"], subject["user"])
    except ValueError as exc:
        raise _domain_error(exc, 404)
    record = orch_mod.start(store, body["text"], subject,
                            body.get("args"))
    summary = _os_summarize(record)
    asst_msg = convos_mod.post_message(
        store, conversation_id, "assistant", summary,
        subject["tenant"], subject["user"])
    return {"user_message": user_msg, "assistant_message": asst_msg,
            "execution": record}


def _os_summarize(record: dict[str, Any]) -> str:
    """Deterministic turn summary from the execution record."""
    state = record.get("state", "?")
    intent = (record.get("classification") or {}).get("intent", "?")
    lines = ["state=%s intent=%s" % (state, intent)]
    for step in record.get("steps", []):
        lines.append("%s: %s" % (step.get("tool"),
                                 step.get("status")))
        if step.get("status") == "PENDING_APPROVAL":
            lines.append("approval plan: %s" % step.get("plan_id"))
    if record.get("error"):
        lines.append("note: %s" % record["error"])
    return "\n".join(lines)


@app.get("/api/v1/industries/{ident}/agent-config")
def industry_agent_config(ident: str) -> dict[str, Any]:
    """Agent OS configuration for one industry."""
    try:
        return indadapt_mod.agent_config(ident)
    except ValueError as exc:
        raise _domain_error(exc, 404)
# -- Recovery OS routes ---------------------------------------------------
from app import recovery as recovery_mod
from app import recovery_caps as reccaps_mod
from app import recovery_rules as recrules_mod


@app.get("/api/v1/recovery/rules")
def list_recovery_rules(request: Request) -> dict[str, Any]:
    """Scheme rules with verification states (login required)."""
    _require_login(request)
    return {"rules": recrules_mod.all_rules(store)}


@app.get("/api/v1/recovery/rules/{rule_id}")
def get_recovery_rule(rule_id: str,
                      request: Request) -> dict[str, Any]:
    """One scheme rule (login required)."""
    _require_login(request)
    found = recrules_mod.get_rule(store, rule_id)
    if found is None:
        raise AppError("RULE_UNKNOWN", "unknown rule", 404)
    return found


@app.post("/api/v1/recovery/rules")
def register_recovery_rule(body: dict,
                           request: Request) -> dict[str, Any]:
    """Register a rule version (admin session only)."""
    claims = _require_admin(request)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    try:
        rule = recrules_mod.register(store, body)
    except ValueError as exc:
        raise _domain_error(exc, 400)
    store.append_audit("human", claims["user"], "recovery.rule.registered",
                       "scheme-rule", rule["rule_id"], "NONE",
                       rule["verification_status"], rule["rule_id"],
                       store.state["trace_id"], _trace(request))
    return rule


@app.post("/api/v1/recovery/assess")
def assess_recovery(body: dict, request: Request) -> dict[str, Any]:
    """Eligibility assessment for a tenant-visible transaction."""
    _require_login(request)
    if not isinstance(body, dict) or not body.get("transaction_id") \
            or not body.get("reason"):
        raise AppError("INVALID_BODY",
                       "transaction_id and reason are required", 400)
    txn = _visible_txn(body["transaction_id"], request)
    connector_id = body.get("connector_id", "")
    provider_available = any(
        reccaps_mod.verified(store, connector_id, cap)
        for cap in ("recall", "reversal", "dispute_submission",
                    "refund", "cancellation")) if connector_id else False
    return recovery_mod.assess(store, txn, body["reason"],
                               body.get("evidence", []),
                               provider_available,
                               body.get("funds_record"))


@app.post("/api/v1/recovery/cases")
def open_recovery_case(body: dict,
                       request: Request) -> dict[str, Any]:
    """Open a recovery case (idempotent; write-gated)."""
    _require_write_token(request)
    if not isinstance(body, dict) or not body.get("transaction_id") \
            or not body.get("reason"):
        raise AppError("INVALID_BODY",
                       "transaction_id and reason are required", 400)
    _visible_txn(body["transaction_id"], request)
    ctx = _request_ctx(request)
    actor = _decision_actor(request, "investigator")
    out = recovery_mod.open_case(store, body["transaction_id"],
                                 body["reason"], ctx.tenant_id, actor)
    if out["status"] == "opened":
        store.append_audit(
            "human", actor, "recovery.case.opened", "recovery-case",
            out["case"]["recovery_id"], "NONE",
            out["case"]["recovery_id"], body["transaction_id"],
            store.state["trace_id"], _trace(request))
    return out


@app.get("/api/v1/recovery/cases")
def list_recovery_cases(request: Request) -> dict[str, Any]:
    """Tenant recovery cases (login required)."""
    _require_login(request)
    ctx = _request_ctx(request)
    rows = [r for r in store.recovery_cases()
            if r.get("tenant_id") == ctx.tenant_id]
    return {"cases": rows, "tenant_scope": ctx.tenant_id}


@app.get("/api/v1/recovery/cases/{recovery_id}")
def get_recovery_case(recovery_id: str,
                      request: Request) -> dict[str, Any]:
    """One tenant recovery case (login required)."""
    _require_login(request)
    ctx = _request_ctx(request)
    found = next((r for r in store.recovery_cases()
                  if r.get("recovery_id") == recovery_id
                  and r.get("tenant_id") == ctx.tenant_id), None)
    if found is None:
        raise AppError("RECOVERY_UNKNOWN", "unknown recovery case",
                       404)
    return found


@app.patch("/api/v1/recovery/cases/{recovery_id}")
def move_recovery_case(recovery_id: str, body: dict,
                       request: Request) -> dict[str, Any]:
    """Legal lifecycle transition (audited). APPROVED/REJECTED need
    an admin session; other moves need the write gate."""
    if not isinstance(body, dict) or not body.get("state"):
        raise AppError("INVALID_BODY", "state is required", 400)
    if body["state"] in ("APPROVED", "REJECTED"):
        claims = _require_admin(request)
        actor = claims["user"]
    else:
        _require_write_token(request)
        actor = _decision_actor(request, "investigator")
    ctx = _request_ctx(request)
    found = next((r for r in store.recovery_cases()
                  if r.get("recovery_id") == recovery_id
                  and r.get("tenant_id") == ctx.tenant_id), None)
    if found is None:
        raise AppError("RECOVERY_UNKNOWN", "unknown recovery case",
                       404)
    previous = found["state"]
    try:
        row = recovery_mod.transition(store, recovery_id,
                                      body["state"], actor,
                                      body.get("note", ""))
    except ValueError as exc:
        raise _domain_error(exc, 400)
    store.append_audit("human", actor, "recovery.case.transition",
                       "recovery-case", recovery_id, previous,
                       row["state"], row["state"],
                       store.state["trace_id"], _trace(request))
    return row


@app.post("/api/v1/recovery/cases/{recovery_id}/evidence")
def add_recovery_evidence(recovery_id: str, body: dict,
                          request: Request) -> dict[str, Any]:
    """Attach an evidence reference (write-gated, audited)."""
    _require_write_token(request)
    if not isinstance(body, dict) or not body.get("kind") \
            or not body.get("reference"):
        raise AppError("INVALID_BODY",
                       "kind and reference are required", 400)
    ctx = _request_ctx(request)
    found = next((r for r in store.recovery_cases()
                  if r.get("recovery_id") == recovery_id
                  and r.get("tenant_id") == ctx.tenant_id), None)
    if found is None:
        raise AppError("RECOVERY_UNKNOWN", "unknown recovery case",
                       404)
    found.setdefault("evidence", []).append(
        {"kind": body["kind"], "reference": body["reference"]})
    store.recovery_case_save(found)
    actor = _decision_actor(request, "investigator")
    store.append_audit("human", actor, "recovery.evidence.added",
                       "recovery-case", recovery_id, "NONE",
                       body["kind"], body["reference"],
                       store.state["trace_id"], _trace(request))
    return found


@app.post("/api/v1/recovery/cases/{recovery_id}/submit")
def submit_recovery_case(recovery_id: str, body: dict,
                         request: Request) -> dict[str, Any]:
    """Submit an APPROVED case: live connector (verified capability
    only) or controlled manual workflow (write-gated, audited)."""
    _require_write_token(request)
    if not isinstance(body, dict) or body.get("channel") not in (
            "live", "manual"):
        raise AppError("INVALID_BODY",
                       "channel must be live or manual", 400)
    ctx = _request_ctx(request)
    found = next((r for r in store.recovery_cases()
                  if r.get("recovery_id") == recovery_id
                  and r.get("tenant_id") == ctx.tenant_id), None)
    if found is None:
        raise AppError("RECOVERY_UNKNOWN", "unknown recovery case",
                       404)
    if found["state"] != "APPROVED":
        raise AppError("RECOVERY_STATE",
                       "case must be APPROVED to submit", 409)
    actor = _decision_actor(request, "investigator")
    if body["channel"] == "live":
        connector_id = body.get("connector_id", "")
        ok = any(reccaps_mod.verified(store, connector_id, cap)
                 for cap in ("recall", "reversal",
                             "dispute_submission", "refund",
                             "cancellation"))
        if not ok:
            raise AppError("RECOVERY_CAPABILITY",
                           "no VERIFIED submission capability for "
                           "this connector; use manual", 409)
        found["channel"] = "live"
        found["connector_id"] = connector_id
        store.recovery_case_save(found)
        try:
            row = recovery_mod.transition(
                store, recovery_id, "SUBMITTED_TO_PROVIDER", actor)
        except ValueError as exc:
            raise _domain_error(exc, 400)
    else:
        found["channel"] = "manual"
        if body.get("external_reference"):
            found["external_reference"] = body["external_reference"]
        store.recovery_case_save(found)
        try:
            row = recovery_mod.transition(store, recovery_id,
                                          "UNDER_REVIEW", actor,
                                          "manual workflow packet")
        except ValueError as exc:
            raise _domain_error(exc, 400)
    store.append_audit("human", actor, "recovery.case.submitted",
                       "recovery-case", recovery_id, "APPROVED",
                       row["state"], body["channel"],
                       store.state["trace_id"], _trace(request))
    return row


@app.get("/api/v1/recovery/caps")
def recovery_capability_matrix(request: Request) -> dict[str, Any]:
    """Connector x capability matrix (login required)."""
    _require_login(request)
    return {"matrix": reccaps_mod.matrix(store)}


@app.post("/api/v1/recovery/caps/declare")
def declare_recovery_capability(body: dict,
                                request: Request) -> dict[str, Any]:
    """Declare a VERIFIED capability with evidence (admin only)."""
    claims = _require_admin(request)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY",
                       "request body must be a JSON object", 400)
    try:
        entry = reccaps_mod.declare(store, body.get("connector_id",
                                                    ""),
                                    body.get("capability", ""),
                                    body.get("evidence", ""),
                                    claims["user"])
    except ValueError as exc:
        raise _domain_error(exc, 400)
    store.append_audit("human", claims["user"], "recovery.cap.declared",
                       "connector", body.get("connector_id", ""),
                       "UNSUPPORTED", "VERIFIED",
                       body.get("capability", ""),
                       store.state["trace_id"], _trace(request))
    return entry


@app.get("/api/v1/recovery/metrics")
def recovery_metrics(request: Request) -> dict[str, Any]:
    """Outcome dashboard from stored tenant rows (login required)."""
    _require_login(request)
    return recovery_mod.metrics(store, _request_ctx(request).tenant_id)


@app.get("/api/v1/industries/{ident}/recovery")
def industry_recovery_config(ident: str) -> dict[str, Any]:
    """Recovery compatibility for one industry."""
    try:
        return indadapt_mod.recovery_config(ident)
    except ValueError as exc:
        raise _domain_error(exc, 404)
