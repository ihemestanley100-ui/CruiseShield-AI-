"""Phase 5 (SEC-013): sessions, login, roles, CSRF. Socket-free."""
import json

import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse

import app.main as main
from app import auth as auth_mod
from app import config as config_mod
from app import ratelimit as rl
from env_probe import CAN_SOCKETS

SECRET = "test-secret-not-a-real-credential"
RECORD = auth_mod.hash_password("demo-pass-1")


def _drive(coro):
    try:
        coro.send(None)
    except StopIteration as exc:
        return exc.value
    raise AssertionError("coroutine suspended on real I/O")


async def _downstream_ok(request):
    return JSONResponse({"ok": True})


def _users(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:investigator:%s,boss:admin:%s" % (RECORD, RECORD))


def _scope(path, method="GET", cookie=None, xrw=False, xff=None):
    headers = [(b"host", b"t")]
    if cookie is not None:
        headers.append((b"cookie", ("csai_session=%s" % cookie).encode()))
    if xrw:
        headers.append((b"x-requested-with", b"XMLHttpRequest"))
    if xff is not None:
        headers.append((b"x-forwarded-for", xff.encode()))
    return {"type": "http", "method": method, "scheme": "http",
            "server": ("t", 80), "client": ("9.9.9.9", 1234),
            "path": path, "query_string": b"", "headers": headers}


def _guard(request):
    return _drive(main.session_guard(request, _downstream_ok))


# --- password + session primitives -------------------------------------

def test_password_roundtrip_and_wrong():
    assert auth_mod.verify_password("demo-pass-1", RECORD)
    assert not auth_mod.verify_password("nope", RECORD)
    assert not auth_mod.verify_password("demo-pass-1", "garbage")
    with pytest.raises(ValueError):
        auth_mod.hash_password("")


def test_session_roundtrip_expiry_tamper():
    token = auth_mod.create_session("judge", "investigator", SECRET,
                                    now=1000.0)
    assert auth_mod.verify_session(
        token, SECRET, now=1000.0) == ("judge", "investigator")
    assert auth_mod.verify_session(
        token, SECRET,
        now=1000.0 + auth_mod.SESSION_TTL_SECONDS + 1) is None
    assert auth_mod.verify_session(token[:-2] + "xx", SECRET,
                                   now=1000.0) is None
    assert auth_mod.verify_session(token, "other-secret",
                                   now=1000.0) is None
    assert auth_mod.verify_session("junk", SECRET) is None


def test_parse_users_skips_bad_entries():
    parsed = auth_mod.parse_users(
        "ok:investigator:%s,badrole:root:%s,nocolons,nohash:x:" % (RECORD,
                                                                  RECORD))
    assert list(parsed) == ["ok"]
    assert parsed["ok"][0] == "investigator"


# --- middleware ----------------------------------------------------------

def test_disabled_means_open(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", "")
    resp = _guard(Request(_scope("/api/v1/risk/x")))
    assert resp.status_code == 200


def test_gated_api_needs_login(monkeypatch):
    _users(monkeypatch)
    resp = _guard(Request(_scope("/api/v1/risk/x")))
    assert resp.status_code == 401
    assert json.loads(bytes(resp.body).decode())["error"]["code"] == \
        "LOGIN_REQUIRED"


def test_open_paths_bypass(monkeypatch):
    _users(monkeypatch)
    for path in ("/", "/api/v1/health", "/api/v1/ready",
                 "/api/v1/auth/login", "/api/v1/auth/mode"):
        assert _guard(Request(_scope(path))).status_code == 200
    assert _guard(Request(_scope("/static/a.png"))).status_code == 200


def test_session_allows_and_roles_gate_demo(monkeypatch):
    _users(monkeypatch)
    inv = auth_mod.create_session("judge", "investigator", SECRET)
    adm = auth_mod.create_session("boss", "admin", SECRET)
    assert _guard(Request(_scope("/api/v1/risk/x",
                                 cookie=inv))).status_code == 200
    resp = _guard(Request(_scope("/api/v1/demo/reset", method="POST",
                                 cookie=inv, xrw=True)))
    assert resp.status_code == 403
    assert _guard(Request(_scope("/api/v1/demo/reset", method="POST",
                                 cookie=adm, xrw=True))).status_code == 200


def test_csrf_header_required_for_cookie_posts(monkeypatch):
    _users(monkeypatch)
    inv = auth_mod.create_session("judge", "investigator", SECRET)
    resp = _guard(Request(_scope("/api/v1/simulations", method="POST",
                                 cookie=inv)))
    assert resp.status_code == 403
    assert _guard(Request(_scope("/api/v1/simulations", method="POST",
                                 cookie=inv, xrw=True))).status_code == 200


def test_write_token_still_works_when_both_set(monkeypatch):
    _users(monkeypatch)
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "tok-1")
    scope = _scope("/api/v1/simulations", method="POST")
    scope["headers"].append((b"authorization", b"Bearer tok-1"))
    assert _guard(Request(scope)).status_code == 200


# --- login endpoint --------------------------------------------------------

def _login_req(monkeypatch, xff="11.0.0.9"):
    _users(monkeypatch)
    rl.reset()
    return Request(_scope("/api/v1/auth/login", method="POST", xff=xff))


def test_login_success_sets_cookie(monkeypatch):
    req = _login_req(monkeypatch)
    resp = main.auth_login({"username": "judge", "password": "demo-pass-1"},
                           req)
    assert resp.status_code == 200
    body = json.loads(bytes(resp.body).decode())
    assert body == {"user": "judge", "role": "investigator"}
    cookie = resp.headers["set-cookie"]
    assert "csai_session=" in cookie and "HttpOnly" in cookie


def test_login_rejects_bad_password_no_enumeration(monkeypatch):
    req = _login_req(monkeypatch)
    with pytest.raises(main.AppError) as exc:
        main.auth_login({"username": "judge", "password": "wrong"}, req)
    assert exc.value.status == 401
    with pytest.raises(main.AppError) as exc2:
        main.auth_login({"username": "ghost", "password": "wrong"}, req)
    assert (exc2.value.status, exc2.value.code) == (
        exc.value.status, exc.value.code)


def test_login_rate_limited(monkeypatch):
    req = _login_req(monkeypatch, xff="11.0.0.77")
    for _ in range(auth_mod.LOGIN_LIMIT_PER_MINUTE):
        with pytest.raises(main.AppError):
            main.auth_login({"username": "judge", "password": "wrong"},
                            req)
    resp = main.auth_login({"username": "judge", "password": "wrong"}, req)
    assert resp.status_code == 429


def test_login_disabled_without_secret(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", "")
    with pytest.raises(main.AppError) as exc:
        main.auth_login({"username": "x", "password": "y"},
                        Request(_scope("/api/v1/auth/login",
                                       method="POST")))
    assert exc.value.status == 503


def test_auth_mode_reflects_secret(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", "")
    assert main.auth_mode() == {"auth_enabled": False}
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    assert main.auth_mode() == {"auth_enabled": True}


def test_auth_routes_wired_to_handlers():
    """Socket-free: every auth URL maps to its handler (no typos)."""
    table = {(r.path, m) for r in main.app.routes
             for m in getattr(r, "methods", set()) or set()}
    assert ("/api/v1/auth/login", "POST") in table
    assert ("/api/v1/auth/logout", "POST") in table
    assert ("/api/v1/auth/me", "GET") in table
    assert ("/api/v1/auth/mode", "GET") in table
    by_path = {r.path: r for r in main.app.routes}
    assert by_path["/api/v1/auth/login"].endpoint is main.auth_login
    assert by_path["/api/v1/auth/logout"].endpoint is main.auth_logout
    assert by_path["/api/v1/auth/me"].endpoint is main.auth_me
    assert by_path["/api/v1/auth/mode"].endpoint is main.auth_mode


@pytest.mark.skipif(
    not CAN_SOCKETS,
    reason="socket creation forbidden in this sandbox; runs in CI/user envs")
def test_full_stack_login_cookie_csrf_roles(client, monkeypatch):
    """End-to-end over TestClient: guard + routes + cookie jar + roles."""
    _users(monkeypatch)
    rl.reset()
    assert client.get("/api/v1/auth/mode").json() == {"auth_enabled": True}
    denied = client.get("/api/v1/alerts")
    assert denied.status_code == 401
    bad = client.post("/api/v1/auth/login",
                      json={"username": "judge", "password": "wrong"})
    assert bad.status_code == 401
    assert "csai_session" not in bad.cookies
    ok = client.post("/api/v1/auth/login",
                     json={"username": "judge", "password": "demo-pass-1"})
    assert ok.status_code == 200
    assert ok.cookies["csai_session"] != ""
    me = client.get("/api/v1/auth/me")
    assert me.json() == {"user": "judge", "role": "investigator"}
    assert client.get("/api/v1/alerts").status_code == 200
    no_xrw = client.post("/api/v1/investigations/inv_84721/ai-analysis")
    assert no_xrw.status_code == 403
    with_xrw = client.post("/api/v1/investigations/inv_84721/ai-analysis",
                           headers={"X-Requested-With": "XMLHttpRequest"})
    assert with_xrw.status_code == 200
    reset = client.post("/api/v1/demo/reset",
                        json={"scenario_id": "scn_primary"},
                        headers={"X-Requested-With": "XMLHttpRequest"})
    assert reset.status_code == 403
    assert client.post("/api/v1/auth/logout",
                       headers={"X-Requested-With": "XMLHttpRequest"}
                       ).status_code == 200
    client.cookies.clear()
    assert client.get("/api/v1/alerts").status_code == 401


def test_me_and_logout(monkeypatch):
    _users(monkeypatch)
    inv = auth_mod.create_session("judge", "investigator", SECRET)
    assert main.auth_me(Request(_scope("/api/v1/auth/me",
                                       cookie=inv))) == {
        "user": "judge", "role": "investigator"}
    with pytest.raises(main.AppError):
        main.auth_me(Request(_scope("/api/v1/auth/me")))
    resp = main.auth_logout()
    assert resp.status_code == 200
    assert "csai_session=" in resp.headers["set-cookie"]
