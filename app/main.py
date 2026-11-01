"""CruiseShield AI hackathon vertical slice: pages + JSON API."""
from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import ai_adapter, auth as auth_mod
from app import cases as cases_mod, evidence as evidence_mod
from app import device_intel as device_mod
from app import geo_intel as geo_mod
from app import graph as graph_mod, graph_intel as gintel_mod
from app import intel_evidence as iev_mod
from app import intel_link as link_mod
from app import ip_intel as ip_mod
from app import ratelimit as ratelimit_mod
from app import replay as replay_mod, risk_intel as rintel_mod
from app import rules as rules_mod
from app import seed as seed_mod, simulate as simulate_mod
from app import config as config_mod
from app.config import META_MODEL_ID, ROOT, cors_options
from app.models import EvidencePackage, RuleResult
from app.store import Store, storage_backend

AUTH_LOGIN_PATH = "/api/v1/auth/login"

APP_VERSION = "1.0.0-p0"

app = FastAPI(title="CruiseShield AI", version=APP_VERSION)
app.add_middleware(CORSMiddleware, **cors_options())

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
    return response


# Paths the rate limiter never throttles (orchestrator + smoke checks).
RATE_LIMIT_EXEMPT = frozenset({"/api/v1/health", "/api/v1/ready",
                               "/system-health"})


# Paths reachable without login when SESSION_SECRET is set. Health/ready
# for orchestrators; login to obtain a session; legacy index + static so a
# logged-out visitor sees branding (all DATA endpoints stay gated).
AUTH_MODE_PATH = "/api/v1/auth/mode"
AUTH_OPEN_PATHS = frozenset({"/", "/api/v1/health", "/api/v1/ready",
                              "/system-health", AUTH_LOGIN_PATH,
                              AUTH_MODE_PATH})
AUTH_ADMIN_PREFIXES = ("/api/v1/demo/",)


@app.middleware("http")
async def session_guard(request: Request, call_next):
    """Phase 5: login enforcement (SEC-013). Inert when unconfigured."""
    if config_mod.SESSION_SECRET:
        path = request.url.path
        if path not in AUTH_OPEN_PATHS and not path.startswith("/static/"):
            kind, role = _credential(request)
            if kind == "none":
                return JSONResponse(
                    status_code=401,
                    content={"error": {
                        "code": "LOGIN_REQUIRED",
                        "message": "demo login required",
                        "trace_id": _trace(request)}})
            if kind == "session":
                if path.startswith(AUTH_ADMIN_PREFIXES) and role != "admin":
                    return JSONResponse(
                        status_code=403,
                        content={"error": {
                            "code": "ADMIN_REQUIRED",
                            "message": "admin role required",
                            "trace_id": _trace(request)}})
                if request.method == "POST" and not request.headers.get(
                        "x-requested-with"):
                    return JSONResponse(
                        status_code=403,
                        content={"error": {
                            "code": "CSRF_HEADER_REQUIRED",
                            "message": "X-Requested-With header required",
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
    """Valid session cookie -> (username, role), else None."""
    secret = config_mod.SESSION_SECRET or ""
    if not secret or request is None:
        return None
    return auth_mod.verify_session(
        request.cookies.get(auth_mod.SESSION_COOKIE, ""), secret)


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

    A valid login session also satisfies the gate (either credential)."""
    if _session_of(request) is not None:
        return
    expected = config_mod.DEMO_WRITE_TOKEN or ""
    if not expected:
        return
    if request is None or not _token_ok(request):
        raise AppError("WRITE_TOKEN_REQUIRED",
                       "valid write credential required", 401)


def _credential(request: Request) -> tuple[str, str | None]:
    """Return ("session", role) | ("token", None) | ("none", None)."""
    session = _session_of(request)
    if session is not None:
        return "session", session[1]
    if _token_ok(request):
        return "token", None
    return "none", None


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
                "UNKNOWN_EDGE"):
        status = 404
    return AppError(code, message.strip() or text, status)


def _ensure_assessment(txn_id: str) -> tuple[dict, dict, list[dict]]:
    if txn_id in store.state["risk"]:
        risk = store.state["risk"][txn_id]
        return (risk["transaction"], risk["network"],
                store.state["rule_results"][txn_id])
    txn = store.get_transaction(txn_id)
    if txn is None:
        raise AppError("UNKNOWN_TRANSACTION", txn_id, 404)
    trace_id = store.state["trace_id"]
    results = rules_mod.evaluate(txn_id, store.state["transactions"],
                                 store.state["edges"], trace_id)
    as_txn = rules_mod.assess(txn_id, "transaction",
                              store.state["transactions"], store.state["edges"],
                              results, trace_id)
    as_net = rules_mod.assess(txn_id, "network", store.state["transactions"],
                              store.state["edges"], results, trace_id)
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
    inv = store.get_investigation(inv_id)
    if inv is None:
        raise AppError("UNKNOWN_INVESTIGATION", inv_id, 404)
    txn = store.get_transaction(inv["transaction_id"])
    risk_txn, risk_net, rule_results = _ensure_assessment(inv["transaction_id"])
    case = next((c for c in store.state["cases"]
                 if c["investigation_id"] == inv_id), None)
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
                            if r["evidence_package_id"] == package["package_id"]],
                "simulations": store.state["simulations"],
                "nodes": store.state["nodes"], "edges": store.state["edges"]})
    return templates.TemplateResponse(request, "investigation.html", ctx)


@app.get("/system-health", response_class=HTMLResponse)
def system_health_page(request: Request):
    ctx = _page_context(request)
    ctx.update({"health": health()})
    return templates.TemplateResponse(request, "system_health.html", ctx)


# -- health / demo --------------------------------------------------------
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
    }
    exempt = {"model_configured"} | ({"pg"} if selected != "pg" else set())
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


@app.post(AUTH_LOGIN_PATH)
def auth_login(body: dict[str, Any], request: Request) -> JSONResponse:
    """Phase 5: demo login. 503 when auth is not configured."""
    secret = config_mod.SESSION_SECRET or ""
    if not secret:
        raise AppError("AUTH_DISABLED", "demo login is not configured", 503)
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
    users = auth_mod.parse_users(config_mod.DEMO_USERS or "")
    role, record = users.get(username, ("", "pbkdf2$210000$" + "0" * 32 +
                                        "$" + "0" * 64))
    if username not in users or not auth_mod.verify_password(password,
                                                             record):
        raise AppError("INVALID_CREDENTIALS",
                       "invalid username or password", 401)
    token = auth_mod.create_session(username, role, secret)
    response = JSONResponse({"user": username, "role": role})
    response.set_cookie(auth_mod.SESSION_COOKIE, token,
                        max_age=auth_mod.SESSION_TTL_SECONDS,
                        httponly=True,
                        secure=(request.url.scheme == "https"),
                        samesite="lax", path="/")
    return response


@app.post("/api/v1/auth/logout")
def auth_logout() -> JSONResponse:
    response = JSONResponse({"ok": True})
    response.delete_cookie(auth_mod.SESSION_COOKIE, path="/")
    return response


@app.get("/api/v1/auth/me")
def auth_me(request: Request) -> dict[str, Any]:
    session = _session_of(request)
    if session is None:
        raise AppError("LOGIN_REQUIRED", "demo login required", 401)
    username, role = session
    return {"user": username, "role": role}


@app.get(AUTH_MODE_PATH)
def auth_mode() -> dict[str, Any]:
    return {"auth_enabled": bool(config_mod.SESSION_SECRET or "")}


@app.get("/api/v1/demo/scenarios")
def demo_scenarios() -> dict[str, Any]:
    return {"scenarios": seed_mod.available_scenarios(),
            "active_scenario_id": store.state["scenario_id"]}


@app.post("/api/v1/demo/reset")
def demo_reset(request: Request,
               body: dict[str, Any] | None = None) -> dict[str, Any]:
    _require_write_token(request)
    scenario_id = (body or {}).get("scenario_id", "scn_primary")
    try:
        return store.reset(scenario_id)
    except ValueError as exc:
        raise _domain_error(exc)


@app.post("/api/v1/demo/scenarios/{scenario_id}/start")
def demo_start(scenario_id: str, request: Request) -> dict[str, Any]:
    _require_write_token(request)
    try:
        result = store.reset(scenario_id)
    except ValueError as exc:
        raise _domain_error(exc)
    inv = store.state["investigations"][0]
    result["investigation_id"] = inv["investigation_id"]
    result["url"] = f"/investigations/{inv['investigation_id']}"
    return result


@app.post("/api/v1/demo/judge-start")
def judge_start(request: Request) -> dict[str, Any]:
    _require_write_token(request)
    result = store.reset("scn_primary")
    inv = store.state["investigations"][0]
    result["investigation_id"] = inv["investigation_id"]
    result["url"] = f"/investigations/{inv['investigation_id']}"
    return result


# -- investigation data ---------------------------------------------------
@app.get("/api/v1/transactions/{txn_id}")
def get_transaction(txn_id: str) -> dict[str, Any]:
    txn = store.get_transaction(txn_id)
    if txn is None:
        raise AppError("UNKNOWN_TRANSACTION", txn_id, 404)
    risk_txn, risk_net, _ = _ensure_assessment(txn_id)
    return {"transaction": txn, "risk_transaction": risk_txn,
            "risk_network": risk_net}


@app.get("/api/v1/devices/{device_id}")
def get_device(device_id: str) -> dict[str, Any]:
    """DI-03 read-only device profile (derived, never persisted)."""
    try:
        device_mod.validate_device_id(device_id)
    except ValueError:
        raise AppError("INVALID_DEVICE_ID", device_id, 400) from None
    profile = device_mod.get_profile(store.state, device_id)
    if profile is None:
        raise AppError("UNKNOWN_DEVICE", device_id, 404)
    return profile.model_dump()


@app.get("/api/v1/ip-observations/{label}")
def get_ip_observations(label: str) -> dict[str, Any]:
    """DI-04 read-only IP-label observations (derived, never persisted)."""
    try:
        ip_mod.validate_label(label)
    except ValueError:
        raise AppError("INVALID_IP_LABEL", label, 400) from None
    mine = [o.model_dump() for o in ip_mod.build_observations(store.state)
            if o.ip_label == label]
    if not mine:
        raise AppError("UNKNOWN_IP_LABEL", label, 404)
    return {"ip_label": label, "address_status": ip_mod.UNKNOWN,
            "observations": mine}


@app.get("/api/v1/geo-observations/{identifier}")
def get_geo_observations(identifier: str) -> dict[str, Any]:
    """DI-05 read-only geo lookup (derived; NullProvider default).

    Fixture labels (e.g. loc_01) return their label observations;
    IP literals are validated and resolved (unavailable unless a
    provider supplies data); anything else is a structured error.
    """
    try:
        geo_mod.validate_label(identifier)
    except ValueError:
        raise AppError("INVALID_GEO_LABEL", identifier, 400) from None
    mine = [o for o in geo_mod.build_label_observations(store.state)
            if o["location_label"] == identifier]
    if mine:
        return {"identifier": identifier, "kind": "fixture_label",
                "observations": mine}
    if ip_mod.parse_ip(identifier) is not None:
        return {"identifier": identifier, "kind": "ip_literal",
                "lookup": geo_mod.resolve_ip(identifier).model_dump()}
    raise AppError("UNKNOWN_GEO_IDENTIFIER", identifier, 404)


@app.get("/api/v1/transactions/{txn_id}/intel")
def get_transaction_intel(txn_id: str) -> dict[str, Any]:
    """DI-06 read-only transaction intel summary (derived)."""
    summary = link_mod.transaction_intel(store.state, txn_id)
    if summary is None:
        raise AppError("UNKNOWN_TRANSACTION", txn_id, 404)
    return summary


@app.get("/api/v1/accounts/{account_id}/intel")
def get_account_intel(account_id: str) -> dict[str, Any]:
    """DI-06 read-only account intel summary (derived)."""
    summary = link_mod.account_intel(store.state, account_id)
    if summary is None:
        raise AppError("UNKNOWN_ACCOUNT", account_id, 404)
    return summary


@app.get("/api/v1/investigations/{inv_id}/intel")
def get_investigation_intel(inv_id: str) -> dict[str, Any]:
    """DI-06 read-only investigation intel summary (derived)."""
    summary = link_mod.investigation_intel(store.state, inv_id)
    if summary is None:
        raise AppError("UNKNOWN_INVESTIGATION", inv_id, 404)
    return summary


@app.get("/api/v1/graph/{txn_id}/overlay")
def get_graph_overlay(txn_id: str) -> dict[str, Any]:
    """DI-07 derived intel overlay (in-memory, never persisted)."""
    overlay = gintel_mod.build_overlay(store.state, txn_id)
    if overlay is None:
        raise AppError("UNKNOWN_TRANSACTION", txn_id, 404)
    return overlay


@app.get("/api/v1/risk-intelligence/{identifier}")
def get_risk_intelligence(identifier: str) -> dict[str, Any]:
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
    result = rintel_mod.assess(store.state, subject_type, identifier)
    if result is None:
        raise AppError("UNKNOWN_RISK_INTEL_SUBJECT", identifier, 404)
    return result


@app.get("/api/v1/investigations/{inv_id}/intel-evidence")
def get_intel_evidence(inv_id: str) -> dict[str, Any]:
    """DI-09 read-only intelligence findings + trace (derived).

    Flag-gated like /risk-intelligence: candidate findings stay hidden
    until RISK_INTELLIGENCE_V2_ENABLED=true.
    """
    if not rintel_mod.enabled():
        body = rintel_mod.disabled_response()
        body["investigation_id"] = inv_id
        return body
    findings = iev_mod.build_findings(store.state, "investigation", inv_id)
    if findings is None:
        raise AppError("UNKNOWN_INVESTIGATION", inv_id, 404)
    return {"investigation_id": inv_id, "findings": findings,
            "trace": iev_mod.trace_chain(store.state, inv_id),
            "synthetic": True}


@app.get("/api/v1/graph/{txn_id}")
def get_graph(txn_id: str) -> dict[str, Any]:
    txn = store.get_transaction(txn_id)
    if txn is None:
        raise AppError("UNKNOWN_TRANSACTION", txn_id, 404)
    # The seeded network is small (22 nodes / 30 edges); Reveal Network
    # returns the full real graph so the demo matches the seed manifest.
    nodes, edges = store.state["nodes"], store.state["edges"]
    return {"transaction_id": txn_id, "nodes": nodes, "edges": edges,
            "provenance_errors": graph_mod.validate_provenance(edges),
            "counts": {"nodes": len(nodes), "edges": len(edges)}}


@app.get("/api/v1/risk/{txn_id}")
def get_risk(txn_id: str, scope: str = "network") -> dict[str, Any]:
    if scope not in ("transaction", "network"):
        raise AppError("UNKNOWN_SCOPE", scope, 400)
    if store.get_transaction(txn_id) is None:
        raise AppError("UNKNOWN_TRANSACTION", txn_id, 404)
    risk_txn, risk_net, rule_results = _ensure_assessment(txn_id)
    return {"assessment": risk_txn if scope == "transaction" else risk_net,
            "rule_results": rule_results}


@app.get("/api/v1/alerts")
def list_alerts() -> dict[str, Any]:
    return {"alerts": store.state["alerts"]}


@app.get("/api/v1/investigations/{inv_id}")
def get_investigation(inv_id: str) -> dict[str, Any]:
    inv = store.get_investigation(inv_id)
    if inv is None:
        raise AppError("UNKNOWN_INVESTIGATION", inv_id, 404)
    alert = next(a for a in store.state["alerts"]
                 if a["alert_id"] == inv["alert_id"])
    case = next((c for c in store.state["cases"]
                 if c["investigation_id"] == inv_id), None)
    risk_txn, risk_net, rule_results = _ensure_assessment(inv["transaction_id"])
    package = store.state["evidence_packages"][inv_id]
    return {"investigation": inv, "alert": alert,
            "transaction": store.get_transaction(inv["transaction_id"]),
            "risk_transaction": risk_txn, "risk_network": risk_net,
            "rule_results": rule_results, "case": case,
            "evidence_package_id": package["package_id"],
            "evidence_count": len(package["items"])}


@app.post("/api/v1/investigations/{inv_id}/evidence-package")
def build_evidence_package(inv_id: str) -> dict[str, Any]:
    inv = store.get_investigation(inv_id)
    if inv is None:
        raise AppError("UNKNOWN_INVESTIGATION", inv_id, 404)
    return store.state["evidence_packages"][inv_id]


@app.get("/api/v1/investigations/{inv_id}/evidence-package")
def read_evidence_package(inv_id: str) -> dict[str, Any]:
    return build_evidence_package(inv_id)


async def _run_ai(package: EvidencePackage, summary: str, run_id: str,
                  trace_id: str, question: str = "",
                  prior_context: str = "") -> dict[str, Any]:
    """Run one model analysis (or follow-up) and persist run + audit.

    Shared by ai-analysis and ai-followup so validation, persistence,
    and audit behavior cannot drift between them.

    Phase 6: the daily live-call cap is enforced before any provider
    request; rejections are audited but persist no run (no call made).
    """
    limit = config_mod.AI_DAILY_CALL_LIMIT
    if limit > 0 and ai_adapter.attempts_today(
            store.state.get("ai_runs", [])) >= limit:
        store.append_audit(
            "service", "ai-adapter", "ai.run.rejected", "agent_run", run_id,
            "PENDING", "REJECTED",
            f"daily live-model call limit reached ({limit}/day)",
            store.state["trace_id"], trace_id)
        raise AppError("AI_DAILY_LIMIT_EXCEEDED",
                       f"daily live-model call limit reached ({limit}/day)",
                       429)
    t0 = time.monotonic()
    try:
        run = await ai_adapter.analyze(package, summary,
                                       store.state["trace_id"], run_id,
                                       timeout=config_mod.AI_TIMEOUT_SECONDS,
                                       question=question,
                                       prior_context=prior_context)
    except ai_adapter.AIError as exc:
        partial = getattr(exc, "run", None)
        if partial is None:
            partial = {
                "agent_run_id": run_id, "provider": "meta",
                "model_id": META_MODEL_ID,
                "prompt_version": ai_adapter.PROMPT_VERSION,
                "request_id": "", "trace_id": store.state["trace_id"],
                "evidence_package_id": package.package_id,
                "evidence_ids_sent": sorted(i.evidence_id for i in package.items),
                "status": "FAILED", "response_reference": "",
                "schema_validation_status": "NOT_VALIDATED",
                "evidence_reference_validation_status": "NOT_VALIDATED",
                "error_code": exc.code, "synthetic_data_flag": True,
                "latency_ms": 0, "result": {},
            }
        failed = dict(partial)
        if not failed.get("latency_ms"):
            failed["latency_ms"] = int((time.monotonic() - t0) * 1000)
        store.save_ai_run(failed)
        store.append_audit("service", "ai-adapter", "ai.run.failed",
                           "agent_run", run_id, "PENDING", "FAILED",
                           f"{exc.code}: {exc}", store.state["trace_id"], trace_id)
        raise AppError(exc.code, str(exc), 503)
    store.save_ai_run(run)
    store.append_audit("service", "ai-adapter", "ai.run.succeeded",
                       "agent_run", run_id, "PENDING", run["status"],
                       f"Model {run['model_id']} validation "
                       f"{run['schema_validation_status']}/"
                       f"{run['evidence_reference_validation_status']}",
                       store.state["trace_id"], trace_id)
    return run


def _investigation_summary(inv_id: str) -> tuple[dict, EvidencePackage, str]:
    inv = store.get_investigation(inv_id)
    if inv is None:
        raise AppError("UNKNOWN_INVESTIGATION", inv_id, 404)
    package = EvidencePackage.model_validate(
        store.state["evidence_packages"][inv_id])
    txn = store.get_transaction(inv["transaction_id"])
    summary = (f"Synthetic investigation {inv_id}: transaction "
               f"{txn['transaction_id']} {txn['sender_account_id']} -> "
               f"{txn['receiver_account_id']} {txn['amount_minor']} kobo.")
    return inv, package, summary


@app.post("/api/v1/investigations/{inv_id}/ai-analysis")
async def ai_analysis(inv_id: str, request: Request) -> dict[str, Any]:
    _require_write_token(request)
    _, package, summary = _investigation_summary(inv_id)
    run_id = f"agentrun_{len(store.state['ai_runs']) + 1:04d}"
    return await _run_ai(package, summary, run_id, _trace(request))


@app.post("/api/v1/investigations/{inv_id}/ai-followup")
async def ai_followup(inv_id: str, body: dict[str, Any],
                      request: Request) -> dict[str, Any]:
    _require_write_token(request)
    _, package, summary = _investigation_summary(inv_id)
    if not isinstance(body, dict):
        raise AppError("INVALID_BODY", "request body must be a JSON object", 400)
    question = (body.get("question", "") or "").strip()
    if not question:
        raise AppError("QUESTION_REQUIRED", "a question is required", 400)
    if len(question) > 2000:
        raise AppError("QUESTION_TOO_LONG",
                       "question exceeds 2000 characters", 400)
    run_id = f"agentrun_{len(store.state['ai_runs']) + 1:04d}"
    prior = ai_adapter.latest_run_context(store.state["ai_runs"],
                                          package.package_id)
    return await _run_ai(package, summary, run_id, _trace(request),
                         question=question, prior_context=prior)


@app.get("/api/v1/ai-runs/{run_id}")
def get_ai_run(run_id: str) -> dict[str, Any]:
    run = next((r for r in store.state["ai_runs"]
                if r["agent_run_id"] == run_id), None)
    if run is None:
        raise AppError("UNKNOWN_RUN", run_id, 404)
    return run


# -- replay / simulation / cases ------------------------------------------
@app.get("/api/v1/replay/{scenario_id}")
def get_replay(scenario_id: str, cursor: int = 0) -> dict[str, Any]:
    if scenario_id != store.state["scenario_id"]:
        raise AppError("UNKNOWN_SCENARIO", scenario_id, 404)
    return replay_mod.state_at(store.state, cursor)


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
    try:
        sim = simulate_mod.run(
            store.state, body.get("target_transaction_id", ""),
            ignored, body.get("assumption", ""),
            store.state["trace_id"])
    except ValueError as exc:
        raise _domain_error(exc)
    store.save_simulation(sim)
    store.append_audit("human", body.get("actor_id", "investigator"),
                       "simulation.run", "simulation", sim["simulation_id"],
                       f"{sim['baseline_score']}", f"{sim['simulated_score']}",
                       sim["assumption"], store.state["trace_id"],
                       _trace(request))
    return sim


@app.get("/api/v1/cases")
def list_cases() -> dict[str, Any]:
    return {"cases": store.state["cases"]}


def latest_ai_run_for_case(case: dict[str, Any]) -> dict[str, Any] | None:
    """Read-only summary of the latest AI run for a case's evidence package.

    Additive for GET case detail. Returns None when no run exists.
    Never mutates state, scores, or decisions.
    """
    package = store.state["evidence_packages"].get(case["investigation_id"])
    package_id = package["package_id"] if package else None
    for run in reversed(store.state["ai_runs"]):
        if package_id is not None and run.get("evidence_package_id") != package_id:
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


@app.get("/api/v1/cases/{case_id}")
def get_case(case_id: str) -> dict[str, Any]:
    case = store.get_case(case_id)
    if case is None:
        raise AppError("CASE_NOT_FOUND", case_id, 404)
    decisions = [d for d in store.state["decisions"] if d["case_id"] == case_id]
    return {"case": case, "decisions": decisions,
            "allowed_transitions": cases_mod.allowed_transitions(case["status"]),
            "latest_ai_run": latest_ai_run_for_case(case)}


@app.post("/api/v1/cases/{case_id}/decisions")
def post_decision(case_id: str, body: dict[str, Any],
                  request: Request) -> dict[str, Any]:
    _require_write_token(request)
    try:
        record, audit = cases_mod.record_decision(
            store, case_id, body.get("decision", ""),
            body.get("target_status", ""), body.get("reason", ""),
            body.get("actor_id", "investigator"),
            body.get("evidence_viewed", []),
            body.get("recommendation", ""), _trace(request))
    except ValueError as exc:
        raise _domain_error(exc)
    return {"decision": record, "audit": audit,
            "case": store.get_case(case_id)}


@app.get("/api/v1/cases/{case_id}/audit")
def case_audit(case_id: str) -> dict[str, Any]:
    if store.get_case(case_id) is None:
        raise AppError("CASE_NOT_FOUND", case_id, 404)
    return {"audits": [a for a in store.state["audits"]
                       if a["target_id"] == case_id]}


@app.post("/api/v1/events")
def ingest_event(body: dict[str, Any],
                 request: Request) -> dict[str, Any]:
    _require_write_token(request)
    try:
        status, event, warnings = store.ingest_event(body)
    except ValueError as exc:
        raise _domain_error(exc, 422)
    return {"status": status, "event": event, "warnings": warnings}
