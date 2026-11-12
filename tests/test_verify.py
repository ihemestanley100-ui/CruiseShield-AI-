"""D-038 verification tokens: crypto + endpoints. Socket-free."""
import pytest
from starlette.requests import Request

import app.config as config_mod
import app.main as main
from app import accounts as accounts_mod
from app import auth as auth_mod
from app import ratelimit as rl
from app import verify as verify_mod

SECRET = "test-secret-verify-032-chars-ok!!"
RECORD = auth_mod.hash_password("demo-pass-1")


@pytest.fixture(autouse=True)
def _buckets():
    rl.reset()
    yield
    rl.reset()


@pytest.fixture()
def armed(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(
        config_mod, "DEMO_USERS", "boss:admin:%s" % RECORD)
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "")
    return monkeypatch


def _req(cookie=None):
    hdrs = [(b"host", b"t")]
    if cookie is not None:
        hdrs.append((b"cookie", ("csai_session=%s" % cookie).encode()))
    return Request({"type": "http", "method": "POST", "scheme": "http",
                    "server": ("t", 80), "client": ("9.9.9.9", 1234),
                    "path": "/x", "query_string": b"", "headers": hdrs})


def _login(user, password="demo-pass-1"):
    resp = main.auth_login({"username": user, "password": password},
                           _req())
    raw = resp.headers["set-cookie"]
    part = [p for p in raw.split(";") if "csai_session=" in p][0]
    return part.split("csai_session=", 1)[1]


def _provision(store, cookie, **over):
    body = {"username": "ann", "password": "long-password-1",
            "role": "investigator", "email": "ann@example.com",
            "phone": "+15551234567"}
    body.update(over)
    return main.admin_create_user(body, _req(cookie))


def test_token_roundtrip_expiry_tamper():
    token = verify_mod.issue_token(SECRET, "ann", "email",
                                   "ann@example.com", now=1000.0)
    claims = verify_mod.parse_token(token, SECRET, now=1000.0)
    assert (claims["user"], claims["purpose"],
            claims["target"]) == ("ann", "email", "ann@example.com")
    assert verify_mod.parse_token(
        token, SECRET, now=1000.0 + 24 * 3600 + 1) is None
    assert verify_mod.parse_token(token[:-2] + "xx", SECRET,
                                  now=1000.0) is None
    assert verify_mod.parse_token(token, "other-secret",
                                  now=1000.0) is None
    assert verify_mod.parse_token("junk", SECRET) is None


def test_spend_single_use(tmp_store):
    assert verify_mod.spend_token(tmp_store, "email", "n1", 9999999999.0)
    assert not verify_mod.spend_token(tmp_store, "email", "n1",
                                      9999999999.0)
    assert verify_mod.spend_token(tmp_store, "phone", "n1", 9999999999.0)


def test_mask_contact_hides_middle():
    assert verify_mod.mask_contact("ann@example.com") == "a***@ple.com"
    assert verify_mod.mask_contact("+15551234567") == "+155***67"
    assert "ann" not in verify_mod.mask_contact("ann@example.com")


def test_request_success_shape(tmp_store, armed):
    boss = _login("boss")
    _provision(tmp_store, boss)
    body = main.verify_request({"purpose": "email"}, _req(_login("ann", "long-password-1")))
    assert body["delivery"] == "BLOCKED_EXTERNAL"
    assert body["expires_in"] == 24 * 3600
    assert "token" not in body
    assert "ann@example.com" not in str(body)
    assert any(a["action"] == "verify.requested"
               for a in tmp_store.state["audits"])


def test_request_rejects(tmp_store, armed):
    boss = _login("boss")
    _provision(tmp_store, boss)
    cookie = _login("ann", "long-password-1")
    with pytest.raises(main.AppError) as exc:
        main.verify_request({"purpose": "email"}, _req())
    assert exc.value.code == "LOGIN_REQUIRED"
    with pytest.raises(main.AppError) as exc:
        main.verify_request({"purpose": "pager"}, _req(cookie))
    assert exc.value.code == "PURPOSE_UNKNOWN"
    with pytest.raises(main.AppError) as exc:
        main.verify_request({"purpose": "email",
                             "target": "other@example.com"}, _req(cookie))
    assert exc.value.code == "CONTACT_MISMATCH"
    with pytest.raises(main.AppError) as exc:
        main.verify_request({"purpose": "email"}, _req(boss))
    assert exc.value.code == "CONTACT_NOT_FOUND"


def test_request_rate_limited(tmp_store, armed):
    boss = _login("boss")
    _provision(tmp_store, boss)
    cookie = _login("ann", "long-password-1")
    for _ in range(10):
        main.verify_request({"purpose": "email"}, _req(cookie))
    resp = main.verify_request({"purpose": "email"}, _req(cookie))
    assert resp.status_code == 429


def test_confirm_success_marks_verified(tmp_store, armed):
    boss = _login("boss")
    _provision(tmp_store, boss)
    cookie = _login("ann", "long-password-1")
    token = verify_mod.issue_token(SECRET, "ann", "email",
                                   "ann@example.com")
    body = main.verify_confirm({"token": token}, _req(cookie))
    assert body == {"purpose": "email", "verified": True}
    assert tmp_store.registered_user("ann")["email_verified"] is True
    assert any(a["action"] == "verify.confirmed"
               for a in tmp_store.state["audits"])


def test_confirm_rejects(tmp_store, armed):
    boss = _login("boss")
    _provision(tmp_store, boss)
    cookie = _login("ann", "long-password-1")
    with pytest.raises(main.AppError) as exc:
        main.verify_confirm({"token": "junk"}, _req(cookie))
    assert exc.value.code == "VERIFY_INVALID"
    foreign = verify_mod.issue_token(SECRET, "boss", "email",
                                     "boss@example.com")
    with pytest.raises(main.AppError) as exc:
        main.verify_confirm({"token": foreign}, _req(cookie))
    assert exc.value.code == "VERIFY_FOREIGN"


def test_confirm_single_use(tmp_store, armed):
    boss = _login("boss")
    _provision(tmp_store, boss)
    cookie = _login("ann", "long-password-1")
    token = verify_mod.issue_token(SECRET, "ann", "phone",
                                   "+15551234567")
    main.verify_confirm({"token": token}, _req(cookie))
    with pytest.raises(main.AppError) as exc:
        main.verify_confirm({"token": token}, _req(cookie))
    assert (exc.value.code, exc.value.status) == ("VERIFY_SPENT", 410)


def test_endpoints_need_armed_secret(tmp_store, armed):
    armed.setattr(config_mod, "SESSION_SECRET", "")
    with pytest.raises(main.AppError) as exc:
        main.verify_request({"purpose": "email"}, _req())
    assert exc.value.code == "AUTH_DISABLED"
    with pytest.raises(main.AppError) as exc:
        main.verify_confirm({"token": "x"}, _req())
    assert exc.value.code == "AUTH_DISABLED"
