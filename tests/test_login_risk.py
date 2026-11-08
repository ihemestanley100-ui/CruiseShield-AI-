"""D-028 / L13 Part 8.4: unknown-location login-risk scoring. Socket-free."""
import json
import time

import pytest
from starlette.requests import Request

import app.main as main
from app import auth as auth_mod
from app import config as config_mod
from app import login_risk as risk_mod
from app import mfa as mfa_mod
from app import ratelimit as rl

SECRET = "test-secret-not-a-real-credential"
RECORD = auth_mod.hash_password("demo-pass-1")
UA_DESK = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
           "Chrome/126.0 Safari/537.36")
UA_MOB = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
          "AppleWebKit/605.1.15 Mobile/15E148")


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
    clk = _Clock(1_700_000_000.0)
    monkeypatch.setattr(time, "time", clk)
    return clk


def _users(monkeypatch, roles=""):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(config_mod, "MFA_REQUIRED_ROLES", roles)
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:investigator:%s,boss:admin:%s" % (RECORD, RECORD))


def _scope(path, method="GET", cookie=None, xrw=False, xff=None,
           ua=None):
    headers = [(b"host", b"t")]
    if cookie is not None:
        headers.append((b"cookie", ("csai_session=%s" % cookie).encode()))
    if xrw:
        headers.append((b"x-requested-with", b"XMLHttpRequest"))
    if xff is not None:
        headers.append((b"x-forwarded-for", xff.encode()))
    if ua is not None:
        headers.append((b"user-agent", ua.encode()))
    return {"type": "http", "method": method, "scheme": "http",
            "server": ("t", 80), "client": ("9.9.9.9", 1234),
            "path": path, "query_string": b"", "headers": headers}


def _login(user, password="demo-pass-1", xff=None, ua=None):
    req = Request(_scope("/api/v1/auth/login", method="POST",
                         xff=xff, ua=ua))
    return main.auth_login({"username": user, "password": password},
                           req)


def _cookie(resp):
    raw = resp.headers["set-cookie"]
    part = [p for p in raw.split(";") if "csai_session=" in p][0]
    return part.split("csai_session=", 1)[1]


def _code(user, counter=1):
    return mfa_mod.totp(mfa_mod.derive_secret(SECRET, user, counter))


# --- learning + levels -------------------------------------------------


def test_first_login_learns_baseline_and_scores_low(monkeypatch,
                                                    tmp_store):
    _users(monkeypatch)
    body = json.loads(_login("judge", xff="10.1.0.1",
                             ua=UA_DESK).body.decode())
    assert body == {"user": "judge", "role": "investigator"}
    baseline = tmp_store.login_risk_for("judge")
    assert baseline["logins"] == 1
    assert baseline["last_level"] == "low"
    assert len(baseline["fingerprints"]) == 1


def test_repeat_login_same_context_stays_low(monkeypatch, tmp_store):
    _users(monkeypatch)
    _login("judge", xff="10.1.0.2", ua=UA_DESK)
    body = json.loads(_login("judge", xff="10.1.0.2",
                             ua=UA_DESK).body.decode())
    assert "risk" not in body
    assert tmp_store.login_risk_for("judge")["last_level"] == "low"


def test_unknown_user_never_learns_baseline(monkeypatch, tmp_store):
    _users(monkeypatch)
    with pytest.raises(main.AppError) as exc:
        _login("ghost", xff="10.1.0.3", ua=UA_DESK)
    assert exc.value.code == "INVALID_CREDENTIALS"
    assert tmp_store.login_risk_for("ghost") == {}
    with pytest.raises(main.AppError):
        _login("judge", password="wrong", xff="10.1.0.3", ua=UA_DESK)
    assert tmp_store.login_risk_for("judge") == {}


def test_new_ip_scores_elevated_with_signal(monkeypatch, tmp_store):
    _users(monkeypatch)
    _login("judge", xff="10.1.0.4", ua=UA_DESK)
    body = json.loads(_login("judge", xff="10.2.9.9",
                             ua=UA_DESK).body.decode())
    assert body["risk"]["level"] == "elevated"
    assert "new_ip" in body["risk"]["signals"]


def test_new_device_scores_elevated_with_signal(monkeypatch,
                                                tmp_store):
    _users(monkeypatch)
    _login("judge", xff="10.1.0.5", ua=UA_DESK)
    body = json.loads(_login("judge", xff="10.1.0.5",
                             ua=UA_MOB).body.decode())
    assert body["risk"]["level"] == "elevated"
    assert "new_device" in body["risk"]["signals"]


def test_new_ip_and_device_scores_high(monkeypatch, tmp_store):
    _users(monkeypatch)
    _login("judge", xff="10.1.0.6", ua=UA_DESK)
    body = json.loads(_login("judge", xff="10.3.8.8",
                             ua=UA_MOB).body.decode())
    assert body["risk"]["level"] == "high"
    assert "new_ip" in body["risk"]["signals"]
    assert "new_device" in body["risk"]["signals"]


def test_rate_limited_attempt_learns_nothing(monkeypatch, tmp_store):
    _users(monkeypatch)
    _login("judge", xff="11.0.0.78", ua=UA_DESK)
    req = Request(_scope("/api/v1/auth/login", method="POST",
                         xff="11.0.0.78", ua=UA_DESK))
    for _ in range(auth_mod.LOGIN_LIMIT_PER_MINUTE - 1):
        with pytest.raises(main.AppError):
            main.auth_login({"username": "judge", "password": "wrong"},
                            req)
    denied = main.auth_login({"username": "judge",
                              "password": "demo-pass-1"}, req)
    assert denied.status_code == 429
    baseline = tmp_store.login_risk_for("judge")
    assert baseline["logins"] == 1
    assert len(baseline["fingerprints"]) == 1


# --- privacy + preserved contracts -------------------------------------


def test_baseline_never_stores_raw_network_or_ua(monkeypatch,
                                                 tmp_store):
    _users(monkeypatch)
    xff, ua = "10.9.8.7", UA_DESK
    _login("judge", xff=xff, ua=ua)
    blob = json.dumps(tmp_store.state.get("login_risk", {}))
    assert xff not in blob
    assert "Windows NT" not in blob and "Chrome/126" not in blob
    assert len(tmp_store.login_risk_for("judge")["fingerprints"][0]) \
        == 64  # hex SHA-256 digest


def test_failed_login_audit_preserved_without_secrets(monkeypatch,
                                                      tmp_store):
    _users(monkeypatch)
    with pytest.raises(main.AppError) as exc:
        _login("judge", password="s3cret-guess", xff="10.1.0.9",
               ua=UA_DESK)
    assert exc.value.code == "INVALID_CREDENTIALS"
    failed = [a for a in tmp_store.state["audits"]
              if a["action"] == "auth.login.failed"]
    assert len(failed) == 1
    blob = json.dumps(tmp_store.state["audits"])
    assert "s3cret-guess" not in blob


def test_mfa_ticket_carries_no_risk_key(monkeypatch, tmp_store,
                                        clock):
    _users(monkeypatch, roles="admin")
    pending = _cookie(_login("boss"))
    enroll = main.mfa_enroll(Request(
        _scope("/api/v1/auth/mfa/enroll", method="POST",
               cookie=pending, xrw=True, xff="10.0.0.1")))
    assert enroll.status_code == 200
    confirmed = main.mfa_confirm(
        {"code": _code("boss")},
        Request(_scope("/api/v1/auth/mfa/confirm", method="POST",
                       cookie=pending, xrw=True, xff="10.0.0.2")))
    assert confirmed.status_code == 200
    clock.now += 31  # consumed TOTP codes never verify twice
    ticket_body = json.loads(_login("boss").body.decode())
    assert ticket_body["mfa_required"] is True
    assert "risk" not in ticket_body
    # Baseline still learned on the password success behind tickets.
    assert tmp_store.login_risk_for("boss")["logins"] == 2


# --- pure-function units ------------------------------------------------


def test_unusual_hour_alone_stays_low():
    baseline = {"logins": 6,
                "fingerprints": ["other"],
                "networks": [risk_mod._digest("ip", "xff:10.0.0.1")],
                "ua_classes": ["desktop-windows"],
                "hours": [9]}
    level, signals, _ = risk_mod.assess(baseline, "xff:10.0.0.1",
                                        UA_DESK, 1_700_000_000.0)
    assert level == "low"  # hour novelty alone never pages


def test_ua_classifier_buckets_clients():
    assert risk_mod.classify_ua(UA_DESK) == "desktop-windows"
    assert risk_mod.classify_ua(UA_MOB) == "mobile"
    assert risk_mod.classify_ua(
        "Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X)") == "tablet"
    assert risk_mod.classify_ua("curl/8.0") == "bot"
    assert risk_mod.classify_ua("") == "unknown"
    assert risk_mod.classify_ua(None) == "unknown"
