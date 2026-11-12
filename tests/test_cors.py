"""CORS: exact local origins allowed, everything else denied, preflight works.

Behavioral tests drive the real CORSMiddleware as pure ASGI with synchronous
mocks (no sockets, no event loop). The transport assertion is socket-gated.
"""
import pytest
from fastapi.middleware.cors import CORSMiddleware

import app.main as main
import app.config as config_mod
from app.config import FRONTEND_ORIGINS, cors_options
from env_probe import CAN_SOCKETS


def _drive(coro):
    """Run to completion a coroutine that never blocks on real I/O."""
    try:
        coro.send(None)
    except StopIteration as exc:
        return exc.value
    raise AssertionError("coroutine suspended on real I/O")


async def _downstream_ok(scope, receive, send):
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"ok"})


def _run(method, origin, extra_headers=None):
    middleware = CORSMiddleware(_downstream_ok, **cors_options())
    headers = [(b"origin", origin.encode())] + list(extra_headers or [])
    scope = {"type": "http", "http_version": "1.1", "method": method,
             "path": "/api/v1/health", "headers": headers}
    sent = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    _drive(middleware(scope, receive, send))
    start = next(m for m in sent if m["type"] == "http.response.start")
    return start["status"], {k.decode(): v.decode()
                             for k, v in start["headers"]}


def test_config_has_no_wildcard_but_allows_credentials():
    # UGLS-02: allow_credentials must be True even in open-demo mode —
    # the frontend always fetches with credentials:"include", and
    # browsers reject a credentialed response without ACA-C, so False
    # broke every open-demo browser fetch (BACKEND_UNREACHABLE in Edge).
    # Explicit origins (never "*") keep this safe.
    assert FRONTEND_ORIGINS == ["http://localhost:3000", "http://127.0.0.1:3000"]
    options = cors_options()
    assert "*" not in options["allow_origins"]
    assert options["allow_credentials"] is True
    assert set(options["allow_methods"]) <= {"GET", "POST", "PUT", "PATCH",
                                             "OPTIONS"}
    assert set(options["allow_headers"]) <= {"Content-Type", "X-Request-ID",
                                             "X-Requested-With"}


def test_staging_arms_credentialed_cors_without_wildcard(monkeypatch):
    """SESSION_SECRET set (login armed): cookies + XRW allowed, no '*'."""
    monkeypatch.setattr(config_mod, "SESSION_SECRET",
                        "staging-secret-not-a-real-credential")
    options = cors_options()
    assert options["allow_credentials"] is True
    assert "*" not in options["allow_origins"]
    assert "X-Requested-With" in options["allow_headers"]
    assert set(options["allow_methods"]) <= {"GET", "POST", "PUT", "PATCH",
                                             "OPTIONS"}


def test_open_demo_allows_csrf_header_preflight(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", "")
    options = cors_options()
    # AI-REPAIR: this previously asserted X-Requested-With ABSENT here,
    # which made open-demo preflights fail and browsers report every
    # POST as BACKEND_UNREACHABLE. Allowlisting the header for
    # preflight is not validation (server still requires it).
    assert options["allow_credentials"] is True
    assert "X-Requested-With" in options["allow_headers"]


def test_open_demo_post_preflight_with_csrf_header_succeeds(monkeypatch):
    """End-to-end preflight: browser POST headers accepted in open mode."""
    monkeypatch.setattr(config_mod, "SESSION_SECRET", "")
    status, headers = _run("OPTIONS", "http://127.0.0.1:3000", [
        (b"access-control-request-method", b"POST"),
        (b"access-control-request-headers",
         b"x-requested-with,content-type"),
    ])
    assert status == 200
    assert headers.get("access-control-allow-origin") == \
        "http://127.0.0.1:3000"


def test_middleware_registered_on_app():
    middlewares = [m for m in main.app.user_middleware
                   if getattr(m, "cls", None) is CORSMiddleware]
    assert len(middlewares) == 1


@pytest.mark.parametrize("origin", ["http://localhost:3000",
                                    "http://127.0.0.1:3000"])
def test_allowed_origin_gets_header(origin):
    status, headers = _run("GET", origin)
    assert status == 200
    assert headers["access-control-allow-origin"] == origin
    # UGLS-02 regression: without ACA-C the browser rejects the
    # frontend's credentials:"include" fetch as BACKEND_UNREACHABLE.
    assert headers["access-control-allow-credentials"] == "true"


def test_rejected_origin_gets_no_header():
    status, headers = _run("GET", "https://evil.example")
    assert status == 200
    assert "access-control-allow-origin" not in headers


def test_preflight_allows_post_with_json():
    status, headers = _run("OPTIONS", "http://localhost:3000", [
        (b"access-control-request-method", b"POST"),
        (b"access-control-request-headers", b"content-type"),
    ])
    assert status == 200
    assert "POST" in headers["access-control-allow-methods"]
    assert "access-control-allow-origin" in headers


def test_staging_preflight_allows_xrw_header(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET",
                        "staging-secret-not-a-real-credential")
    status, headers = _run("OPTIONS", "http://localhost:3000", [
        (b"access-control-request-method", b"POST"),
        (b"access-control-request-headers", b"x-requested-with"),
    ])
    assert status == 200
    assert "x-requested-with" in headers[
        "access-control-allow-headers"].lower()


@pytest.mark.parametrize("method", ["PUT", "PATCH"])
def test_preflight_allows_put_and_patch(method):
    """F-D2: split-origin PUT/PATCH preflights succeed (guard validates)."""
    status, headers = _run("OPTIONS", "http://localhost:3000", [
        (b"access-control-request-method", method.encode()),
        (b"access-control-request-headers",
         b"x-requested-with,content-type"),
    ])
    assert status == 200
    assert method in headers["access-control-allow-methods"]
    assert "access-control-allow-origin" in headers


def test_preflight_rejects_disallowed_method():
    status, _ = _run("OPTIONS", "http://localhost:3000", [
        (b"access-control-request-method", b"DELETE"),
    ])
    assert status == 400


def test_armed_guard_401_carries_cors_headers(client, monkeypatch):
    """Armed-mode 401s must be browser-readable (ACAO + credentials).

    Socket-free: TestClient is in-process ASGI. Regression: CORSMiddleware
    sat inside session_guard, so guard short-circuits bypassed it and the
    browser reported BACKEND_UNREACHABLE instead of a login gate.
    """
    monkeypatch.setattr(config_mod, "SESSION_SECRET",
                        "staging-secret-not-a-real-credential")
    monkeypatch.setattr(config_mod, "DEMO_USERS", "")
    response = client.get("/api/v1/alerts",
                          headers={"Origin": "http://127.0.0.1:3000"})
    assert response.status_code == 401
    assert (response.headers["access-control-allow-origin"]
            == "http://127.0.0.1:3000")
    assert response.headers["access-control-allow-credentials"] == "true"


def test_armed_preflight_answered_before_guard(client, monkeypatch):
    """Preflight to a guarded path must reach CORS, not the 401 guard.

    Socket-free (see above). Request headers stay within the open-demo
    allowlist: the app's middleware is built at import, so XRW admission
    under staging options is covered by
    test_staging_preflight_allows_xrw_header.
    """
    monkeypatch.setattr(config_mod, "SESSION_SECRET",
                        "staging-secret-not-a-real-credential")
    monkeypatch.setattr(config_mod, "DEMO_USERS", "")
    response = client.options(
        "/api/v1/cases/case_84721/decision",
        headers={"Origin": "http://127.0.0.1:3000",
                 "Access-Control-Request-Method": "POST",
                 "Access-Control-Request-Headers": "content-type"})
    assert response.status_code == 200
    assert (response.headers["access-control-allow-origin"]
            == "http://127.0.0.1:3000")


@pytest.mark.skipif(
    not CAN_SOCKETS,
    reason="socket creation forbidden in this sandbox; runs in CI/user envs")
def test_health_sends_allow_origin_header(client):
    response = client.get("/api/v1/health",
                          headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert (response.headers["access-control-allow-origin"]
            == "http://localhost:3000")
