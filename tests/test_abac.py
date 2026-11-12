"""D-025: central ABAC policy + policy-check endpoint. Socket-free."""
import pytest
from starlette.requests import Request

import app.main as main
from app import abac as abac_mod
from app import auth as auth_mod
from app import config as config_mod
from app import tenancy as tenancy_mod

SECRET = "test-secret-not-a-real-credential"
RECORD = auth_mod.hash_password("demo-pass-1")


def _users(monkeypatch, token=""):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", token)
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:investigator:%s,boss:admin:%s,viewer:demo_viewer:%s"
        % (RECORD, RECORD, RECORD))


def _scope(path, method="GET", cookie=None, token=None, xrw=False):
    headers = [(b"host", b"t")]
    if cookie is not None:
        headers.append((b"cookie", ("csai_session=%s" % cookie).encode()))
    if token is not None:
        headers.append((b"authorization", ("Bearer %s" % token).encode()))
    if xrw:
        headers.append((b"x-requested-with", b"XMLHttpRequest"))
    return {"type": "http", "method": method, "scheme": "http",
            "server": ("t", 80), "client": ("9.9.9.9", 1234),
            "path": path, "query_string": b"", "headers": headers}


def _sess(user, role, pending=False):
    return auth_mod.create_session(user, role, SECRET, mfa_pending=pending)


def _subject(user="judge", role="investigator", kind="session",
             tenant=None, full=True):
    if tenant is None:
        tenant = tenancy_mod.DEFAULT_TENANT
    return {"user": user, "role": role, "tenant": tenant, "kind": kind,
            "mfa_full": full}


def test_allow_matrix_happy_paths():
    assert abac_mod.decide(_subject(), "read", {"kind": "case"})[0]
    assert abac_mod.decide(
        _subject(), "write",
        {"kind": "case", "tenant": tenancy_mod.DEFAULT_TENANT})[0]
    assert abac_mod.decide(_subject(role="admin"), "approve",
                           {"kind": "agent-plan"})[0]
    assert abac_mod.decide(_subject(role="auditor"), "audit_read",
                           {"kind": "audit"})[0]


def test_deny_anonymous_unknown_action_unknown_kind():
    allowed, reason = abac_mod.decide(abac_mod.blank_subject(), "read",
                                      {"kind": "case"})
    assert not allowed and "authentication" in reason
    assert not abac_mod.decide(_subject(), "teleport",
                               {"kind": "case"})[0]
    assert not abac_mod.decide(_subject(kind="carrier-pigeon"), "read",
                               {"kind": "case"})[0]
    assert not abac_mod.decide({}, "read", {})[0]
    assert abac_mod.decide(_subject(), "read", None)[0] is True


def test_deny_cross_tenant_even_for_admin():
    allowed, reason = abac_mod.decide(
        _subject(role="admin"), "read",
        {"kind": "case", "tenant": "other"})
    assert not allowed and "cross-tenant" in reason


def test_deny_role_without_permission():
    allowed, reason = abac_mod.decide(
        _subject(role="demo_viewer"), "write", {"kind": "case"})
    assert not allowed and "lacks" in reason
    assert not abac_mod.decide(_subject(), "approve",
                               {"kind": "agent-plan"})[0]


def test_sensitive_needs_full_session():
    token = {"user": "platform-token", "role": "",
             "tenant": tenancy_mod.DEFAULT_TENANT, "kind": "token",
             "mfa_full": False}
    assert not abac_mod.decide(token, "read", {"kind": "audit"})[0]
    assert not abac_mod.decide(_subject(full=False), "read",
                               {"kind": "sar"})[0]
    assert abac_mod.decide(_subject(), "read", {"kind": "audit"})[0]
    # Token keeps normal read/write (existing gate semantics preserved).
    assert abac_mod.decide(token, "read", {"kind": "case"})[0]
    assert abac_mod.decide(token, "write", {"kind": "case"})[0]
    assert not abac_mod.decide(token, "approve",
                               {"kind": "agent-plan"})[0]


def test_hold_blocks_close_and_delete_only():
    held = {"kind": "case", "hold": True}
    assert not abac_mod.decide(_subject(), "close", held)[0]
    assert not abac_mod.decide(_subject(role="admin"), "delete",
                               held)[0]
    assert abac_mod.decide(_subject(), "read", held)[0]
    assert abac_mod.decide(_subject(), "write", held)[0]


def test_subject_from_request_shapes(monkeypatch, tmp_store):
    _users(monkeypatch, token="tok-1")
    full = Request(_scope("/x", cookie=_sess("judge", "investigator")))
    assert abac_mod.subject_from_request(full) == {
        "user": "judge", "role": "investigator",
        "tenant": tenancy_mod.DEFAULT_TENANT,
        "kind": "session", "mfa_full": True}
    pending = Request(_scope("/x", cookie=_sess("boss", "admin",
                                               pending=True)))
    assert abac_mod.subject_from_request(pending)["mfa_full"] is False
    tok = Request(_scope("/x", token="tok-1"))
    assert abac_mod.subject_from_request(tok)["kind"] == "token"
    bad = Request(_scope("/x", token="wrong"))
    assert abac_mod.subject_from_request(bad)["kind"] == "none"
    anon = Request(_scope("/x"))
    assert abac_mod.subject_from_request(anon)["kind"] == "none"


def test_subject_resolves_tenant_via_d014(monkeypatch, tmp_store):
    # F-C: a mapped foreign-tenant session must not present a
    # default-tenant subject (previously pinned, fail open).
    _users(monkeypatch)
    monkeypatch.setattr(config_mod, "USER_TENANTS", "judge:org_beta")
    tenancy_mod.register_tenant("org_beta")
    full = Request(_scope("/x", cookie=_sess("judge", "investigator")))
    subject = abac_mod.subject_from_request(full)
    assert subject["tenant"] == "org_beta"
    assert not abac_mod.decide(
        subject, "read",
        {"kind": "case",
         "tenant": tenancy_mod.DEFAULT_TENANT})[0]
    assert abac_mod.decide(
        subject, "read", {"kind": "case", "tenant": "org_beta"})[0]
    # Unmapped users keep default-tenant subjects (single-org unchanged).
    monkeypatch.setattr(config_mod, "USER_TENANTS", "")
    assert abac_mod.subject_from_request(full)["tenant"] == (
        tenancy_mod.DEFAULT_TENANT)


def test_policy_check_endpoint(monkeypatch, tmp_store):
    _users(monkeypatch, token="tok-1")
    with pytest.raises(main.AppError) as exc:
        main.policy_check({"action": "read"},
                          Request(_scope("/api/v1/auth/policy-check",
                                         method="POST")))
    assert exc.value.code == "LOGIN_REQUIRED"
    cookie = _sess("viewer", "demo_viewer")
    req = Request(_scope("/api/v1/auth/policy-check", method="POST",
                         cookie=cookie, xrw=True))
    denied = main.policy_check({"action": "write",
                                "resource": {"kind": "case"}}, req)
    assert denied["allowed"] is False
    assert denied["subject"] == {"user": "viewer",
                                 "role": "demo_viewer",
                                 "kind": "session"}
    allowed = main.policy_check({"action": "read",
                                 "resource": {"kind": "case"}}, req)
    assert allowed["allowed"] is True
    treq = Request(_scope("/api/v1/auth/policy-check", method="POST",
                          token="tok-1"))
    sensitive = main.policy_check({"action": "read",
                                   "resource": {"kind": "audit"}},
                                  treq)
    assert sensitive["allowed"] is False
