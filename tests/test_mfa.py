"""D-022: TOTP MFA enrollment, step-up, recovery, lockout. Socket-free."""
import json
import time

import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse

import app.main as main
from app import auth as auth_mod
from app import config as config_mod
from app import mfa as mfa_mod
from app import ratelimit as rl

SECRET = "test-secret-not-a-real-credential"
RECORD = auth_mod.hash_password("demo-pass-1")
RFC_SECRET = b"12345678901234567890"


def _drive(coro):
    try:
        coro.send(None)
    except StopIteration as exc:
        return exc.value
    raise AssertionError("coroutine suspended on real I/O")


async def _downstream_ok(request):
    return JSONResponse({"ok": True})


@pytest.fixture(autouse=True)
def _buckets():
    rl.reset()
    yield
    rl.reset()


class _Clock:
    def __init__(self, start):
        self.now = start

    def __call__(self):
        return self.now


@pytest.fixture()
def clock(monkeypatch):
    """Deterministic wall clock (TOTP windows, ticket/session expiry)."""
    clk = _Clock(1_700_000_000.0)
    monkeypatch.setattr(time, "time", clk)
    return clk


def _users(monkeypatch, roles="admin"):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(config_mod, "MFA_REQUIRED_ROLES", roles)
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


def _cookie(resp):
    raw = resp.headers["set-cookie"]
    part = [p for p in raw.split(";") if "csai_session=" in p][0]
    return part.split("csai_session=", 1)[1]


def _login(user):
    req = Request(_scope("/api/v1/auth/login", method="POST"))
    return main.auth_login({"username": user, "password": "demo-pass-1"},
                           req)


def _enroll(cookie, xff="10.0.0.1"):
    req = Request(_scope("/api/v1/auth/mfa/enroll", method="POST",
                         cookie=cookie, xrw=True, xff=xff))
    return main.mfa_enroll(req)


def _code(user, counter):
    derived = mfa_mod.derive_secret(SECRET, user, counter)
    return mfa_mod.totp(derived)


# --- TOTP primitives -------------------------------------------------

def test_totp_matches_rfc6238_vectors():
    # RFC 6238 Appendix B, truncated to 6 digits.
    assert mfa_mod.totp(RFC_SECRET, now=59) == "287082"
    assert mfa_mod.totp(RFC_SECRET, now=1111111109) == "081804"
    assert mfa_mod.totp(RFC_SECRET, now=2000000000) == "279037"


def test_verify_window_skew_and_replay():
    now = 1_700_000_000.0
    matched = mfa_mod.verify_totp(RFC_SECRET,
                                  mfa_mod.totp(RFC_SECRET, now - 30),
                                  now, -1)
    assert matched == int(now) // 30 - 1  # previous step accepted
    assert mfa_mod.verify_totp(RFC_SECRET,
                               mfa_mod.totp(RFC_SECRET, now),
                               now, matched) is not None
    # Replay of an accepted-or-older counter is rejected.
    assert mfa_mod.verify_totp(RFC_SECRET,
                               mfa_mod.totp(RFC_SECRET, now),
                               now, int(now) // 30) is None
    assert mfa_mod.verify_totp(RFC_SECRET, "000000", now, -1) is None
    assert mfa_mod.verify_totp(RFC_SECRET, "abcdef", now, -1) is None
    assert mfa_mod.verify_totp(RFC_SECRET, "", now, -1) is None


def test_derive_secret_deterministic_and_scoped():
    first = mfa_mod.derive_secret(SECRET, "boss", 1)
    assert len(first) == mfa_mod.TOTP_SECRET_BYTES
    assert first == mfa_mod.derive_secret(SECRET, "boss", 1)
    assert first != mfa_mod.derive_secret(SECRET, "boss", 2)
    assert first != mfa_mod.derive_secret(SECRET, "judge", 1)
    assert first != mfa_mod.derive_secret(SECRET + "x", "boss", 1)


def test_provisioning_uri_and_b32_shape():
    uri = mfa_mod.provisioning_uri("boss", RFC_SECRET)
    assert uri.startswith("otpauth://totp/")
    assert "secret=" in uri and "issuer=" in uri and "period=30" in uri
    assert "=" not in mfa_mod.secret_b32(RFC_SECRET)


def test_recovery_codes_hash_and_normalize():
    codes = mfa_mod.new_recovery_codes()
    assert len(codes) == mfa_mod.RECOVERY_CODE_COUNT
    assert len(set(codes)) == len(codes)
    sample = codes[0]
    assert mfa_mod.hash_recovery_code(sample) == mfa_mod.hash_recovery_code(
        sample.upper().replace("-", ""))
    assert mfa_mod.hash_recovery_code("nope") != \
        mfa_mod.hash_recovery_code(sample)


def test_ticket_roundtrip_expiry_tamper():
    ticket = mfa_mod.create_ticket(SECRET, "boss", now=5000.0)
    claims = mfa_mod.parse_ticket(ticket, SECRET, now=5000.0)
    assert claims["user"] == "boss" and claims["nonce"]
    assert mfa_mod.parse_ticket(
        ticket, SECRET, now=5000.0 + mfa_mod.MFA_TICKET_TTL_SECONDS + 1
    ) is None
    assert mfa_mod.parse_ticket(ticket[:-2] + "xx", SECRET,
                                now=5000.0) is None
    assert mfa_mod.parse_ticket("junk", SECRET, now=5000.0) is None


def test_lockout_boundaries():
    state = mfa_mod.blank_state()
    assert not mfa_mod.locked(state, 100.0)
    state["locked_until"] = 200.0
    assert mfa_mod.locked(state, 100.0)
    assert not mfa_mod.locked(state, 200.0)
    assert not mfa_mod.locked({}, 100.0)


def test_required_roles_parsing(monkeypatch):
    monkeypatch.setattr(config_mod, "MFA_REQUIRED_ROLES",
                        "admin, superuser,,investigator")
    assert config_mod.mfa_required_roles() == frozenset(
        {"admin", "investigator"})
    monkeypatch.setattr(config_mod, "MFA_REQUIRED_ROLES", "")
    assert config_mod.mfa_required_roles() == frozenset()


# --- enrollment + step-up flow ---------------------------------------

def test_login_pending_enroll_confirm_flow(monkeypatch, tmp_store):
    _users(monkeypatch)
    resp = _login("boss")
    assert resp.status_code == 200
    body = json.loads(resp.body.decode())
    assert body["mfa_pending"] is True
    pending = _cookie(resp)
    assert main.auth_me(Request(_scope("/x", cookie=pending)))["user"] \
        == "boss"

    enroll = _enroll(pending)
    assert enroll.status_code == 200
    data = json.loads(enroll.body.decode())
    assert data["secret"] and data["uri"].startswith("otpauth://")
    assert len(data["recovery_codes"]) == mfa_mod.RECOVERY_CODE_COUNT

    req = Request(_scope("/api/v1/auth/mfa/confirm", method="POST",
                         cookie=pending, xrw=True))
    confirmed = main.mfa_confirm({"code": _code("boss", 1)}, req)
    assert confirmed.status_code == 200
    full = _cookie(confirmed)
    claims = auth_mod.parse_session(full, SECRET)
    assert claims["mfa_pending"] is False

    status = main.mfa_status(Request(_scope("/x", cookie=full)))
    assert status == {"status": "ACTIVE", "required": True,
                      "recovery_remaining": mfa_mod.RECOVERY_CODE_COUNT}


def test_non_required_role_gets_full_session(monkeypatch, tmp_store):
    _users(monkeypatch)
    resp = _login("judge")
    body = json.loads(resp.body.decode())
    assert body == {"user": "judge", "role": "investigator"}


def test_active_user_logins_via_ticket_challenge(monkeypatch, tmp_store,
                                                   clock):
    _users(monkeypatch)
    pending = _cookie(_login("boss"))
    _enroll(pending)
    req = Request(_scope("/api/v1/auth/mfa/confirm", method="POST",
                         cookie=pending, xrw=True))
    main.mfa_confirm({"code": _code("boss", 1)}, req)

    second = _login("boss")
    ticket_body = json.loads(second.body.decode())
    assert ticket_body["mfa_required"] is True
    assert "set-cookie" not in second.headers  # no session before step-up

    clock.now += 31  # consumed codes never verify twice (replay guard)
    challenge_req = Request(_scope("/api/v1/auth/mfa/challenge",
                                   method="POST", xff="10.9.9.9"))
    done = main.mfa_challenge({"ticket": ticket_body["ticket"],
                               "code": _code("boss", 1)},
                              challenge_req)
    assert done.status_code == 200
    full = _cookie(done)
    guarded = _drive(main.session_guard(
        Request(_scope("/api/v1/transactions", cookie=full)),
        _downstream_ok))
    assert guarded.status_code == 200


def test_challenge_recovery_code_single_use(monkeypatch, tmp_store):
    _users(monkeypatch)
    pending = _cookie(_login("boss"))
    codes = json.loads(_enroll(pending).body.decode())["recovery_codes"]
    req = Request(_scope("/api/v1/auth/mfa/confirm", method="POST",
                         cookie=pending, xrw=True))
    main.mfa_confirm({"code": _code("boss", 1)}, req)

    ticket = json.loads(_login("boss").body.decode())["ticket"]
    first = main.mfa_challenge(
        {"ticket": ticket, "recovery_code": codes[0]},
        Request(_scope("/api/v1/auth/mfa/challenge", method="POST",
                       xff="10.9.9.1")))
    assert first.status_code == 200
    assert json.loads(first.body.decode())["recovery_remaining"] == \
        mfa_mod.RECOVERY_CODE_COUNT - 1

    ticket2 = json.loads(_login("boss").body.decode())["ticket"]
    with pytest.raises(main.AppError) as exc:
        main.mfa_challenge(
            {"ticket": ticket2, "recovery_code": codes[0]},
            Request(_scope("/api/v1/auth/mfa/challenge", method="POST",
                           xff="10.9.9.2")))
    assert exc.value.code == "INVALID_MFA_CODE"


def test_ticket_single_use(monkeypatch, tmp_store, clock):
    _users(monkeypatch)
    pending = _cookie(_login("boss"))
    _enroll(pending)
    req = Request(_scope("/api/v1/auth/mfa/confirm", method="POST",
                         cookie=pending, xrw=True))
    main.mfa_confirm({"code": _code("boss", 1)}, req)
    ticket = json.loads(_login("boss").body.decode())["ticket"]
    clock.now += 31
    scope = _scope("/api/v1/auth/mfa/challenge", method="POST",
                   xff="10.9.8.1")
    main.mfa_challenge({"ticket": ticket, "code": _code("boss", 1)},
                       Request(scope))
    with pytest.raises(main.AppError) as exc:
        main.mfa_challenge({"ticket": ticket, "code": _code("boss", 1)},
                           Request(_scope(
                               "/api/v1/auth/mfa/challenge", method="POST",
                               xff="10.9.8.2")))
    assert exc.value.code == "MFA_TICKET_SPENT"


def test_totp_replay_rejected_across_tickets(monkeypatch, tmp_store,
                                               clock):
    _users(monkeypatch)
    pending = _cookie(_login("boss"))
    _enroll(pending)
    req = Request(_scope("/api/v1/auth/mfa/confirm", method="POST",
                         cookie=pending, xrw=True))
    code = _code("boss", 1)
    main.mfa_confirm({"code": code}, req)
    ticket = json.loads(_login("boss").body.decode())["ticket"]
    with pytest.raises(main.AppError) as exc:
        main.mfa_challenge(
            {"ticket": ticket, "code": code},
            Request(_scope("/api/v1/auth/mfa/challenge", method="POST",
                           xff="10.9.7.1")))
    assert exc.value.code == "INVALID_MFA_CODE"


def test_pending_session_gated_everywhere_but_mfa(monkeypatch, tmp_store):
    _users(monkeypatch)
    pending = _cookie(_login("boss"))
    blocked = _drive(main.session_guard(
        Request(_scope("/api/v1/transactions", cookie=pending)),
        _downstream_ok))
    assert blocked.status_code == 403
    assert json.loads(blocked.body.decode())["error"]["code"] == \
        "MFA_REQUIRED"
    allowed = _drive(main.session_guard(
        Request(_scope("/api/v1/auth/mfa/status", cookie=pending)),
        _downstream_ok))
    assert allowed.status_code == 200
    with pytest.raises(main.AppError) as exc:
        main._require_write_token(
            Request(_scope("/x", method="POST", cookie=pending)))
    assert exc.value.code == "MFA_REQUIRED"


def test_lockout_after_five_failures(monkeypatch, tmp_store):
    _users(monkeypatch)
    pending = _cookie(_login("boss"))
    _enroll(pending)
    scope = _scope("/api/v1/auth/mfa/confirm", method="POST",
                   cookie=pending, xrw=True)
    for _ in range(mfa_mod.MFA_MAX_FAILED):
        with pytest.raises(main.AppError) as exc:
            main.mfa_confirm({"code": "000000"}, Request(scope))
        assert exc.value.code == "INVALID_MFA_CODE"
    with pytest.raises(main.AppError) as exc:
        main.mfa_confirm({"code": _code("boss", 1)}, Request(scope))
    assert exc.value.code == "MFA_LOCKED"


def test_admin_disables_other_user_but_not_reverse(monkeypatch,
                                                   tmp_store):
    _users(monkeypatch, roles="admin,investigator")
    judge_pending = _cookie(_login("judge"))
    _enroll(judge_pending)
    confirm_req = Request(_scope("/api/v1/auth/mfa/confirm",
                                 method="POST", cookie=judge_pending,
                                 xrw=True))
    judge_full = _cookie(
        main.mfa_confirm({"code": _code("judge", 1)}, confirm_req))
    boss_pending = _cookie(_login("boss"))
    _enroll(boss_pending, xff="10.0.0.2")
    boss_full = _cookie(main.mfa_confirm(
        {"code": _code("boss", 1)},
        Request(_scope("/api/v1/auth/mfa/confirm", method="POST",
                       cookie=boss_pending, xrw=True))))

    denied = Request(_scope("/api/v1/auth/mfa/disable", method="POST",
                            cookie=judge_full, xrw=True, xff="10.0.0.3"))
    with pytest.raises(main.AppError) as exc:
        main.mfa_disable({"username": "boss"}, denied)
    assert exc.value.code == "ADMIN_REQUIRED"

    allowed = Request(_scope("/api/v1/auth/mfa/disable", method="POST",
                             cookie=boss_full, xrw=True, xff="10.0.0.4"))
    assert main.mfa_disable({"username": "judge"}, allowed).status_code \
        == 200
    assert main.mfa_status(
        Request(_scope("/x", cookie=judge_full)))["status"] == "NONE"


def test_self_disable_requires_current_code(monkeypatch, tmp_store,
                                              clock):
    _users(monkeypatch)
    pending = _cookie(_login("boss"))
    _enroll(pending)
    full = _cookie(main.mfa_confirm(
        {"code": _code("boss", 1)},
        Request(_scope("/api/v1/auth/mfa/confirm", method="POST",
                       cookie=pending, xrw=True))))
    clock.now += 31
    scope = _scope("/api/v1/auth/mfa/disable", method="POST",
                   cookie=full, xrw=True)
    with pytest.raises(main.AppError) as exc:
        main.mfa_disable({"code": "000000"}, Request(scope))
    assert exc.value.code == "INVALID_MFA_CODE"
    assert main.mfa_disable(
        {"code": _code("boss", 1)}, Request(scope)).status_code == 200
    assert main.mfa_status(
        Request(_scope("/x", cookie=full)))["status"] == "NONE"


def test_enroll_confirm_state_machine_guards(monkeypatch, tmp_store):
    _users(monkeypatch)
    pending = _cookie(_login("boss"))
    confirm_scope = _scope("/api/v1/auth/mfa/confirm", method="POST",
                           cookie=pending, xrw=True)
    with pytest.raises(main.AppError) as exc:
        main.mfa_confirm({"code": _code("boss", 1)},
                         Request(confirm_scope))
    assert exc.value.code == "MFA_NOT_PENDING"
    _enroll(pending)
    main.mfa_confirm({"code": _code("boss", 1)}, Request(confirm_scope))
    with pytest.raises(main.AppError) as exc:
        main.mfa_confirm({"code": "000000"}, Request(confirm_scope))
    assert exc.value.code == "MFA_ALREADY_ACTIVE"
    with pytest.raises(main.AppError) as exc:
        main.mfa_enroll(Request(_scope("/api/v1/auth/mfa/enroll",
                                       method="POST", cookie=pending,
                                       xrw=True)))
    assert exc.value.code == "MFA_ALREADY_ACTIVE"


def test_recovery_rotation_invalidates_old_set(monkeypatch, tmp_store,
                                                 clock):
    _users(monkeypatch)
    pending = _cookie(_login("boss"))
    old = json.loads(_enroll(pending).body.decode())["recovery_codes"]
    full = _cookie(main.mfa_confirm(
        {"code": _code("boss", 1)},
        Request(_scope("/api/v1/auth/mfa/confirm", method="POST",
                       cookie=pending, xrw=True))))
    clock.now += 31
    rotated = main.mfa_codes(
        {"code": _code("boss", 1)},
        Request(_scope("/api/v1/auth/mfa/codes", method="POST",
                       cookie=full, xrw=True)))
    new = json.loads(rotated.body.decode())["recovery_codes"]
    assert new != old
    ticket = json.loads(_login("boss").body.decode())["ticket"]
    with pytest.raises(main.AppError) as exc:
        main.mfa_challenge(
            {"ticket": ticket, "recovery_code": old[0]},
            Request(_scope("/api/v1/auth/mfa/challenge", method="POST",
                           xff="10.9.6.1")))
    assert exc.value.code == "INVALID_MFA_CODE"


def test_challenge_rejects_deprovisioned_user(monkeypatch, tmp_store):
    _users(monkeypatch)
    ticket = mfa_mod.create_ticket(SECRET, "ghost")
    with pytest.raises(main.AppError) as exc:
        main.mfa_challenge(
            {"ticket": ticket, "code": "000000"},
            Request(_scope("/api/v1/auth/mfa/challenge", method="POST",
                           xff="10.9.5.1")))
    assert exc.value.code == "INVALID_MFA_TICKET"


def test_mfa_503_when_auth_unarmed(monkeypatch, tmp_store):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", "")
    with pytest.raises(main.AppError) as exc:
        main.mfa_enroll(Request(_scope("/api/v1/auth/mfa/enroll",
                                       method="POST")))
    assert exc.value.code == "AUTH_DISABLED"
    with pytest.raises(main.AppError) as exc:
        main.mfa_status(Request(_scope("/api/v1/auth/mfa/status")))
    assert exc.value.code == "AUTH_DISABLED"


def test_audit_trail_records_mfa_without_secrets(monkeypatch, tmp_store):
    _users(monkeypatch)
    pending = _cookie(_login("boss"))
    codes = json.loads(_enroll(pending).body.decode())["recovery_codes"]
    main.mfa_confirm(
        {"code": _code("boss", 1)},
        Request(_scope("/api/v1/auth/mfa/confirm", method="POST",
                       cookie=pending, xrw=True)))
    actions = [event.get("action")
               for event in tmp_store.state.get("audits", [])]
    assert "mfa.enroll" in actions
    assert "mfa.confirm" in actions
    blob = json.dumps(tmp_store.state.get("audits", []))
    for secret in codes:
        assert secret not in blob
        assert secret.replace("-", "") not in blob
