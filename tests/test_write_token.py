"""SEC-012 (D-002): shared write-token gate. Socket-free."""
import pytest
from starlette.requests import Request

import app.main as main
from app import auth as auth_mod
from app import config as config_mod


def _req(auth=None, cookie=None):
    headers = [(b"host", b"t")]
    if auth is not None:
        headers.append((b"authorization", auth.encode()))
    if cookie is not None:
        headers.append((b"cookie", ("%s=%s" % (
            auth_mod.SESSION_COOKIE, cookie)).encode()))
    return Request({"type": "http", "method": "POST", "path": "/x",
                    "headers": headers})


def test_open_when_unconfigured(monkeypatch):
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "")
    main._require_write_token(_req(None))  # no header
    main._require_write_token(None)  # direct call, no request


def test_correct_token_passes(monkeypatch):
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "s3cret-demo")
    main._require_write_token(_req("Bearer s3cret-demo"))


def test_wrong_token_rejected(monkeypatch):
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "s3cret-demo")
    with pytest.raises(main.AppError) as exc:
        main._require_write_token(_req("Bearer wrong"))
    assert exc.value.status == 401
    assert exc.value.code == "WRITE_TOKEN_REQUIRED"


def test_missing_token_rejected(monkeypatch):
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "s3cret-demo")
    with pytest.raises(main.AppError):
        main._require_write_token(_req(None))


def test_no_request_fails_closed(monkeypatch):
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "s3cret-demo")
    with pytest.raises(main.AppError):
        main._require_write_token(None)


def test_wrong_scheme_rejected(monkeypatch):
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "s3cret-demo")
    with pytest.raises(main.AppError):
        main._require_write_token(_req("Token s3cret-demo"))


def test_valid_session_satisfies_gate_without_token(monkeypatch):
    # J3 closeout (backend EV14): either credential satisfies the gate.
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "s3cret-demo")
    monkeypatch.setattr(config_mod, "SESSION_SECRET",
                        "test-secret-not-a-real-credential")
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:investigator:%s" % auth_mod.hash_password("pw"))
    session = auth_mod.create_session("judge", "investigator",
                                      "test-secret-not-a-real-credential")
    main._require_write_token(_req("Bearer wrong", cookie=session))
    main._require_write_token(_req(None, cookie=session))
