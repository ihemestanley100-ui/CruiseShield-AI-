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


def test_login_success_sets_cookie(monkeypatch, tmp_store):
    req = _login_req(monkeypatch)
    resp = main.auth_login({"username": "judge", "password": "demo-pass-1"},
                           req)
    assert resp.status_code == 200
    body = json.loads(bytes(resp.body).decode())
    assert body == {"user": "judge", "role": "investigator"}
    cookie = resp.headers["set-cookie"]
    assert "csai_session=" in cookie and "HttpOnly" in cookie


def _login_req_scheme(monkeypatch, scheme, extra_headers=()):
    _users(monkeypatch)
    rl.reset()
    scope = _scope("/api/v1/auth/login", method="POST", xff="11.0.0.9")
    scope["scheme"] = scheme
    scope["headers"] = list(scope["headers"]) + list(extra_headers)
    return Request(scope)


def _login_cookie(monkeypatch, scheme, extra_headers=()):
    req = _login_req_scheme(monkeypatch, scheme, extra_headers)
    resp = main.auth_login({"username": "judge", "password": "demo-pass-1"},
                           req)
    assert resp.status_code == 200
    return resp.headers["set-cookie"]


def test_cookie_secure_on_direct_https(monkeypatch, tmp_store):
    assert "Secure" in _login_cookie(monkeypatch, "https")


def test_cookie_secure_behind_tls_proxy(monkeypatch, tmp_store):
    """J3-P2: X-Forwarded-Proto:https keeps Secure behind Render-style TLS."""
    cookie = _login_cookie(monkeypatch, "http",
                           [(b"x-forwarded-proto", b"https")])
    assert "Secure" in cookie


def test_cookie_not_secure_on_plain_local_http(monkeypatch, tmp_store):
    assert "Secure" not in _login_cookie(monkeypatch, "http")


def test_cookie_samesite_none_on_direct_https(monkeypatch, tmp_store):
    """X-ORIGIN: cross-site Netlify->Render fetch needs SameSite=None."""
    assert "samesite=none" in _login_cookie(monkeypatch, "https").lower()


def test_cookie_samesite_none_behind_tls_proxy(monkeypatch, tmp_store):
    cookie = _login_cookie(monkeypatch, "http",
                           [(b"x-forwarded-proto", b"https")])
    assert "samesite=none" in cookie.lower()


def test_cookie_samesite_lax_on_plain_local_http(monkeypatch, tmp_store):
    """X-ORIGIN: browsers reject SameSite=None without Secure; keep Lax."""
    cookie = _login_cookie(monkeypatch, "http").lower()
    assert "samesite=lax" in cookie and "samesite=none" not in cookie


def test_logout_clears_cookie_with_matching_attrs(monkeypatch, tmp_store):
    """X-ORIGIN: deletion must mirror set attrs or Chrome keeps the cookie."""
    _users(monkeypatch)
    token = auth_mod.create_session("judge", "investigator", SECRET)
    scope = _scope("/api/v1/auth/logout", method="POST", cookie=token,
                   xrw=True)
    scope["scheme"] = "https"
    resp = main.auth_logout(Request(scope))
    assert resp.status_code == 200
    cleared = resp.headers["set-cookie"].lower()
    assert "samesite=none" in cleared and "secure" in cleared


def test_logout_all_clears_cookie_with_matching_attrs(monkeypatch, tmp_store):
    """X-ORIGIN: logout-all deletion must mirror set attrs (all sessions)."""
    _users(monkeypatch)
    token = auth_mod.create_session("judge", "investigator", SECRET)
    scope = _scope("/api/v1/auth/logout-all", method="POST", cookie=token,
                   xrw=True)
    scope["scheme"] = "https"
    resp = main.auth_logout_all(Request(scope))
    assert resp.status_code == 200
    cleared = resp.headers["set-cookie"].lower()
    assert "samesite=none" in cleared and "secure" in cleared


def test_login_rejects_bad_password_no_enumeration(monkeypatch, tmp_store):
    req = _login_req(monkeypatch, xff="11.0.0.78")
    with pytest.raises(main.AppError) as exc:
        main.auth_login({"username": "judge", "password": "wrong"}, req)
    assert exc.value.status == 401
    with pytest.raises(main.AppError) as exc2:
        main.auth_login({"username": "ghost", "password": "wrong"}, req)
    assert (exc2.value.status, exc2.value.code) == (
        exc.value.status, exc.value.code)


def test_failed_login_audited_without_secrets(monkeypatch, tmp_store):
    """R09-F3: rejected logins audit the username, never the password."""
    req = _login_req(monkeypatch, xff="11.0.0.79")
    with pytest.raises(main.AppError):
        main.auth_login({"username": "judge", "password": "wrong-pw-9"},
                        req)
    with pytest.raises(main.AppError):
        main.auth_login({"username": "ghost", "password": "wrong-pw-9"},
                        req)
    failed = [a for a in tmp_store.state["audits"]
              if a["action"] == "auth.login.failed"]
    assert len(failed) == 2
    assert {a["actor_id"] for a in failed} == {"judge", "ghost"}
    blob = json.dumps(failed)
    assert "wrong-pw-9" not in blob
    assert SECRET not in blob
    assert RECORD not in blob


def test_login_rate_limited(monkeypatch, tmp_store):
    req = _login_req(monkeypatch, xff="11.0.0.77")
    for _ in range(auth_mod.LOGIN_LIMIT_PER_MINUTE):
        with pytest.raises(main.AppError):
            main.auth_login({"username": "judge", "password": "wrong"},
                            req)
    resp = main.auth_login({"username": "judge", "password": "wrong"}, req)
    assert resp.status_code == 429
    # R09-F3: credential rejections audit; the 429 itself adds none.
    failed = [a for a in tmp_store.state["audits"]
              if a["action"] == "auth.login.failed"]
    assert len(failed) == auth_mod.LOGIN_LIMIT_PER_MINUTE


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


def _weak_users(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", "short-secret")
    monkeypatch.setattr(
        config_mod, "DEMO_USERS", "judge:investigator:%s" % RECORD)


def test_weak_secret_guard_fails_closed(monkeypatch):
    """R09-F2: weak signing secret refuses guarded paths (503)."""
    _weak_users(monkeypatch)
    resp = _guard(Request(_scope("/api/v1/alerts")))
    assert resp.status_code == 503
    assert _code(resp) == "AUTH_MISCONFIGURED"
    assert _guard(Request(_scope("/api/v1/health"))).status_code == 200


def test_weak_secret_login_refused(monkeypatch):
    """R09-F2: no session can be minted with a weak secret."""
    _weak_users(monkeypatch)
    rl.reset()
    with pytest.raises(main.AppError) as exc:
        main.auth_login({"username": "judge", "password": "demo-pass-1"},
                        Request(_scope("/api/v1/auth/login", method="POST")))
    assert (exc.value.status, exc.value.code) == (503, "AUTH_MISCONFIGURED")


def test_weak_secret_sessions_invalid_and_mode_off(monkeypatch):
    """R09-F2: weak-secret cookies validate nothing; mode reports off."""
    _weak_users(monkeypatch)
    cookie = auth_mod.create_session("judge", "investigator", "short-secret")
    assert main._session_of(Request(_scope("/x", cookie=cookie))) is None
    assert main.auth_mode() == {"auth_enabled": False}


def test_auth_routes_wired_to_handlers():
    """Socket-free: every auth URL maps to its handler (no typos)."""
    table = {(r.path, m) for r in main.app.routes
             for m in getattr(r, "methods", set()) or set()}
    assert ("/api/v1/auth/login", "POST") in table
    assert ("/api/v1/auth/logout", "POST") in table
    assert ("/api/v1/auth/logout-all", "POST") in table
    assert ("/api/v1/auth/me", "GET") in table
    assert ("/api/v1/auth/mode", "GET") in table
    by_path = {r.path: r for r in main.app.routes}
    assert by_path["/api/v1/auth/login"].endpoint is main.auth_login
    assert by_path["/api/v1/auth/logout"].endpoint is main.auth_logout
    assert by_path["/api/v1/auth/logout-all"].endpoint is main.auth_logout_all
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
    # J4: /me now also reports the role's permission set.
    assert me.json() == {"user": "judge", "role": "investigator",
                         "permissions": ["ai_run", "audit_read", "read",
                                         "write"]}
    assert client.get("/api/v1/alerts").status_code == 200
    no_xrw = client.post("/api/v1/investigations/inv_84721/ai-analysis")
    assert no_xrw.status_code == 403
    with_xrw = client.post("/api/v1/investigations/inv_84721/ai-analysis",
                           headers={"X-Requested-With": "XMLHttpRequest"})
    # J4: hermetic tests run keyless; 503 proves the perm/CSRF gates
    # passed and only the (absent) provider refused.
    assert with_xrw.status_code == 503
    assert with_xrw.json()["error"]["code"] == "MODEL_NOT_CONFIGURED"
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
        "user": "judge", "role": "investigator",
        "permissions": ["ai_run", "audit_read", "read", "write"]}
    with pytest.raises(main.AppError):
        main.auth_me(Request(_scope("/api/v1/auth/me")))
    resp = main.auth_logout(Request(_scope("/api/v1/auth/logout",
                                           method="POST")))
    assert resp.status_code == 200
    assert "csai_session=" in resp.headers["set-cookie"]


# --- J4 roles, permissions, revocation --------------------------------------

def _users4(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:investigator:%s,boss:admin:%s,ann:auditor:%s,"
        "vie:demo_viewer:%s" % (RECORD, RECORD, RECORD, RECORD))


def _code(resp):
    return json.loads(bytes(resp.body).decode())["error"]["code"]


def test_permission_matrix_least_privilege():
    assert auth_mod.can("admin", "manage")
    assert not auth_mod.can("investigator", "manage")
    assert auth_mod.can("investigator", "write")
    assert not auth_mod.can("auditor", "write")
    assert not auth_mod.can("auditor", "ai_run")
    assert auth_mod.can("auditor", "audit_read")
    assert auth_mod.can("demo_viewer", "read")
    assert not auth_mod.can("demo_viewer", "audit_read")
    assert not auth_mod.can("ghost", "read")
    assert not auth_mod.can("admin", "teleport")


def test_parse_users_accepts_new_roles():
    users = auth_mod.parse_users(
        "a:auditor:%s,v:demo_viewer:%s,x:superuser:%s" % (RECORD, RECORD,
                                                          RECORD))
    assert set(users) == {"a", "v"}
    assert users["a"][0] == "auditor"


def test_logout_revokes_only_that_session(monkeypatch, tmp_store):
    _users4(monkeypatch)
    first = auth_mod.create_session("judge", "investigator", SECRET)
    second = auth_mod.create_session("judge", "investigator", SECRET)
    assert first != second
    main.auth_logout(Request(_scope("/api/v1/auth/logout", method="POST",
                                    cookie=first, xrw=True)))
    assert main._session_of(Request(_scope("/x", cookie=first))) is None
    assert main._session_of(Request(_scope("/x", cookie=second))) is not None


def test_logout_all_invalidates_every_session(monkeypatch, tmp_store):
    import time as _time

    _users4(monkeypatch)
    past = _time.time() - 100
    mine = auth_mod.create_session("judge", "investigator", SECRET,
                                   now=past)
    also_mine = auth_mod.create_session("judge", "investigator", SECRET,
                                        now=past)
    other = auth_mod.create_session("boss", "admin", SECRET)
    resp = main.auth_logout_all(Request(_scope("/api/v1/auth/logout-all",
                                               method="POST", cookie=mine,
                                               xrw=True)))
    assert resp.status_code == 200
    for token in (mine, also_mine):
        assert main._session_of(Request(_scope("/x", cookie=token))) is None
    assert main._session_of(Request(_scope("/x", cookie=other))) is not None
    fresh = auth_mod.create_session("judge", "investigator", SECRET)
    assert main._session_of(Request(_scope("/x", cookie=fresh))) is not None


def test_revocation_survives_restart(monkeypatch, tmp_path):
    from app.store import Store

    _users4(monkeypatch)
    here = tmp_path / "state.json"
    first = Store(here)
    token = auth_mod.create_session("judge", "investigator", SECRET)
    claims = auth_mod.parse_session(token, SECRET)
    first.revoke_session(claims["nonce"], claims["exp"])
    assert Store(here).is_revoked(claims["nonce"])
    assert first.epoch_of("judge") == 0
    stamp = first.bump_epoch("judge", now=5000.0)
    assert stamp == 5000
    assert Store(here).epoch_of("judge") == 5000


def test_deprovision_or_role_change_kills_session(monkeypatch, tmp_store):
    _users4(monkeypatch)
    token = auth_mod.create_session("judge", "investigator", SECRET)
    assert main._session_of(Request(_scope("/x", cookie=token))) is not None
    monkeypatch.setattr(config_mod, "DEMO_USERS",
                        "boss:admin:%s" % RECORD)
    assert main._session_of(Request(_scope("/x", cookie=token))) is None
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:auditor:%s,boss:admin:%s" % (RECORD, RECORD))
    assert main._session_of(Request(_scope("/x", cookie=token))) is None


def test_login_mints_fresh_token_fixation_safe(monkeypatch, tmp_store):
    _users4(monkeypatch)
    rl.reset()
    forged = auth_mod.create_session("judge", "investigator", "wrong-secret")
    scope = _scope("/api/v1/auth/login", method="POST", cookie=forged,
                   xff="11.0.0.41")
    first = main.auth_login({"username": "judge",
                             "password": "demo-pass-1"}, Request(scope))
    scope2 = _scope("/api/v1/auth/login", method="POST", cookie=forged,
                    xff="11.0.0.42")
    second = main.auth_login({"username": "judge",
                              "password": "demo-pass-1"}, Request(scope2))
    assert (first.headers["set-cookie"]
            != second.headers["set-cookie"])


def test_read_only_roles_enforced_on_guard(monkeypatch, tmp_store):
    _users4(monkeypatch)
    aud = auth_mod.create_session("ann", "auditor", SECRET)
    vie = auth_mod.create_session("vie", "demo_viewer", SECRET)
    assert _guard(Request(_scope("/api/v1/alerts",
                                 cookie=aud))).status_code == 200
    resp = _guard(Request(_scope("/api/v1/cases/case_84721/audit",
                                 cookie=vie)))
    assert resp.status_code == 403
    assert _code(resp) == "PERMISSION_DENIED"
    assert _guard(Request(_scope("/api/v1/cases/case_84721/audit",
                                 cookie=aud))).status_code == 200
    resp = _guard(Request(_scope("/api/v1/cases/case_84721/decisions",
                                 method="POST", cookie=aud, xrw=True)))
    assert resp.status_code == 403
    assert _code(resp) == "PERMISSION_DENIED"
    resp = _guard(Request(_scope(
        "/api/v1/investigations/inv_84721/ai-analysis", method="POST",
        cookie=vie, xrw=True)))
    assert resp.status_code == 403
    assert _code(resp) == "PERMISSION_DENIED"


def test_write_gate_rejects_read_only_session(monkeypatch, tmp_store):
    _users4(monkeypatch)
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "s3cret-demo")
    aud = auth_mod.create_session("ann", "auditor", SECRET)
    with pytest.raises(main.AppError) as exc:
        main._require_write_token(Request(_scope("/x", method="POST",
                                                 cookie=aud)))
    assert exc.value.code == "PERMISSION_DENIED"


def test_auth_audit_events_recorded(monkeypatch, tmp_store):
    _users4(monkeypatch)
    rl.reset()
    req = Request(_scope("/api/v1/auth/login", method="POST",
                         xff="11.0.0.43"))
    main.auth_login({"username": "judge", "password": "demo-pass-1"}, req)
    token = auth_mod.create_session("judge", "investigator", SECRET)
    main.auth_logout(Request(_scope("/api/v1/auth/logout", method="POST",
                                    cookie=token, xrw=True)))
    token2 = auth_mod.create_session("judge", "investigator", SECRET)
    main.auth_logout_all(Request(_scope("/api/v1/auth/logout-all",
                                        method="POST", cookie=token2,
                                        xrw=True)))
    actions = [a["action"] for a in tmp_store.state["audits"]]
    assert actions[-3:] == ["auth.login", "auth.logout",
                            "auth.logout_all"]


def test_provision_line_roundtrip():
    line = auth_mod.provision_line("vie", "demo_viewer", "s3cret!")
    name, role, record = line.split(":", 2)
    assert (name, role) == ("vie", "demo_viewer")
    assert auth_mod.verify_password("s3cret!", record)
    assert not auth_mod.verify_password("nope", record)
    assert "vie" in auth_mod.parse_users(line)
    with pytest.raises(ValueError):
        auth_mod.provision_line("bad:name", "auditor", "x")
    with pytest.raises(ValueError):
        auth_mod.provision_line("ok", "superuser", "x")
    with pytest.raises(ValueError):
        auth_mod.provision_line("ok", "auditor", "")


def test_reset_preserves_login_state(tmp_path):
    from app.store import Store

    store = Store(tmp_path / "state.json")
    store.revoke_session("n1", 9_999_999_999)
    store.bump_epoch("judge", now=6000.0)
    store.reset("scn_primary")
    assert store.is_revoked("n1")
    assert store.epoch_of("judge") == 6000
