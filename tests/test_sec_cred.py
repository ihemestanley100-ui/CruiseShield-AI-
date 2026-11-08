"""SEC-CRED: per-client credentials + service identities."""
from __future__ import annotations

import pytest
from starlette.requests import Request

import app.main as main
from app import abac as abac_mod
from app import api_credentials as cred_mod
from app import auth as auth_mod
from app import config as config_mod

SECRET = "test-secret-not-a-real-credential"
RECORD = auth_mod.hash_password("demo-pass-1")


def _users(monkeypatch, token=""):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", token)
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:investigator:%s,boss:admin:%s" % (RECORD, RECORD))


def _req(cookie=None, bearer=None):
    headers = [(b"host", b"t")]
    if cookie is not None:
        headers.append((b"cookie", ("csai_session=%s" % cookie).encode()))
    if bearer is not None:
        headers.append((b"authorization", ("Bearer %s" % bearer).encode()))
    return Request({"type": "http", "method": "POST", "scheme": "http",
                    "server": ("t", 80), "client": ("9.9.9.9", 1234),
                    "path": "/x", "query_string": b"", "headers": headers})


def _admin_cookie():
    return auth_mod.create_session("boss", "admin", SECRET)


def test_issue_verify_revoke(tmp_store):
    out = cred_mod.issue(tmp_store, "etl-worker", ["read", "write"],
                         "boss")
    assert out["secret"].startswith("csc_")
    stored = tmp_store.cred_get(out["client_id"])
    assert stored is not None
    assert "secret" not in stored
    assert stored["secret_hash"] != out["secret"]
    assert cred_mod.verify(tmp_store, out["secret"])["client_id"] == \
        out["client_id"]
    assert cred_mod.verify(tmp_store, "csc_" + "0" * 32) is None
    assert cred_mod.verify(tmp_store, "not-a-cred") is None
    assert cred_mod.verify(tmp_store, None) is None
    cred_mod.revoke(tmp_store, out["client_id"], "boss")
    assert cred_mod.verify(tmp_store, out["secret"]) is None
    with pytest.raises(ValueError):
        cred_mod.revoke(tmp_store, "client_nope", "boss")


def test_scopes_validated(tmp_store):
    with pytest.raises(ValueError):
        cred_mod.issue(tmp_store, "x", [], "boss")
    with pytest.raises(ValueError):
        cred_mod.issue(tmp_store, "x", ["manage"], "boss")
    with pytest.raises(ValueError):
        cred_mod.issue(tmp_store, "x", ["read", "bogus"], "boss")
    with pytest.raises(ValueError):
        cred_mod.issue(tmp_store, "  ", ["read"], "boss")
    red = cred_mod.redacted(tmp_store.cred_get(
        cred_mod.issue(tmp_store, "r", ["read"], "boss")["client_id"]))
    assert "secret_hash" not in red


def test_admin_routes(tmp_store, monkeypatch):
    _users(monkeypatch)
    cookie = _admin_cookie()
    out = main.admin_issue_client({"name": "svc", "scopes": ["read"]},
                                  _req(cookie=cookie))
    assert out["secret"].startswith("csc_")
    listed = main.admin_list_clients(_req(cookie=cookie))
    assert listed["clients"]
    assert all("secret_hash" not in r for r in listed["clients"])
    row = main.admin_revoke_client(out["client_id"], _req(cookie=cookie))
    assert row["revoked_at"]
    inv = auth_mod.create_session("judge", "investigator", SECRET)
    with pytest.raises(main.AppError):
        main.admin_issue_client({"name": "x", "scopes": ["read"]},
                                _req(cookie=inv))
    with pytest.raises(main.AppError):
        main.admin_list_clients(_req())


def test_write_gate_client_scopes(tmp_store, monkeypatch):
    _users(monkeypatch, token="shared-token")
    writer = cred_mod.issue(tmp_store, "w", ["write"], "boss")["secret"]
    reader = cred_mod.issue(tmp_store, "r", ["read"], "boss")["secret"]
    main._require_write_token(_req(bearer=writer))
    with pytest.raises(main.AppError):
        main._require_write_token(_req(bearer=reader))
    with pytest.raises(main.AppError):
        main._require_write_token(_req())
    with pytest.raises(main.AppError):
        main._require_write_token(_req(bearer="csc_" + "f" * 32))


def test_credential_and_actor(tmp_store):
    secret = cred_mod.issue(tmp_store, "w", ["write"], "boss")
    kind, ident = main._credential(_req(bearer=secret["secret"]))
    assert (kind, ident) == ("client", secret["client_id"])
    assert main._decision_actor(_req(bearer=secret["secret"]),
                               "claimed") == \
        "client:%s" % secret["client_id"]
    assert main._credential(_req()) == ("none", None)


def test_abac_client_scopes():
    allow, _ = abac_mod.decide(
        {"kind": "client", "user": "client:x", "scopes": ["read"]},
        "read", {"kind": "txn"})
    assert allow is True
    deny, reason = abac_mod.decide(
        {"kind": "client", "user": "client:x", "scopes": ["read"]},
        "write", {"kind": "txn"})
    assert deny is False and "scope" in reason
    deny2, _ = abac_mod.decide(
        {"kind": "client", "user": "client:x", "scopes": ["read"]},
        "read", {"kind": "mfa"})
    assert deny2 is False
    deny3, reason3 = abac_mod.decide(
        {"kind": "client", "user": "client:x", "scopes": ["read"]},
        "approve", {"kind": "txn"})
    assert deny3 is False and "scope" in reason3
