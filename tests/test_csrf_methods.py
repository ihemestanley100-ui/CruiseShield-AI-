"""F-D1: CSRF header required for every unsafe method (POST/PUT/PATCH/DELETE).

Drives session_guard directly with crafted ASGI scopes (no sockets):
armed session cookie + parametrized method/header presence.
"""
import json

import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse

import app.auth as auth_mod
import app.config as config_mod
import app.main as main_mod

SECRET = "test-secret-csrfguard-032-chars-ok"
RECORD = auth_mod.hash_password("demo-pass-1")


def _arm(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(
        config_mod, "DEMO_USERS", "csrfjudge:investigator:%s" % RECORD)


def _drive(method, headers):
    """Run session_guard with a stub downstream.

    Returns (status_code, error_code_or_None, downstream_reached).
    """
    reached = []

    async def downstream(request):
        reached.append(True)
        return JSONResponse({"ok": True})

    raw = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    scope = {"type": "http", "http_version": "1.1", "method": method,
             "path": "/api/v1/cases", "headers": raw,
             "query_string": b"", "server": ("test", 80),
             "scheme": "http", "client": ("127.0.0.1", 5000)}

    async def receive():
        return {"type": "http.request", "body": b"{}", "more_body": False}

    coro = main_mod.session_guard(Request(scope, receive), downstream)
    try:
        coro.send(None)
    except StopIteration as exc:
        response = exc.value
    else:
        raise AssertionError("guard suspended on real I/O")
    code = None
    if response.status_code != 200 or not reached:
        try:
            code = json.loads(response.body)["error"]["code"]
        except (ValueError, KeyError, TypeError):
            code = None
    return response.status_code, code, bool(reached)


def _session_cookie():
    token = auth_mod.create_session("csrfjudge", "investigator", SECRET)
    return "%s=%s" % (auth_mod.SESSION_COOKIE, token)


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_unsafe_method_without_header_rejected(monkeypatch, method):
    _arm(monkeypatch)
    status, code, reached = _drive(
        method, {"cookie": _session_cookie()})
    assert status == 403
    assert code == "CSRF_HEADER_REQUIRED"
    assert not reached


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_unsafe_method_with_header_passes(monkeypatch, method):
    _arm(monkeypatch)
    status, _, reached = _drive(
        method, {"cookie": _session_cookie(),
                 "x-requested-with": "XMLHttpRequest"})
    assert status == 200
    assert reached


def test_safe_method_without_header_passes(monkeypatch):
    _arm(monkeypatch)
    status, _, reached = _drive(
        "GET", {"cookie": _session_cookie()})
    assert status == 200
    assert reached


def test_token_credential_exempt_from_header(monkeypatch):
    _arm(monkeypatch)
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "csrf-probe-token")
    status, _, reached = _drive(
        "POST", {"authorization": "Bearer csrf-probe-token"})
    assert status == 200
    assert reached


def test_anonymous_post_still_requires_login(monkeypatch):
    _arm(monkeypatch)
    status, code, reached = _drive("POST", {})
    assert status == 401
    assert code == "LOGIN_REQUIRED"
    assert not reached
