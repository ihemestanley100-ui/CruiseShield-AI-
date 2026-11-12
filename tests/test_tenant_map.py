"""D-014 user->tenant map: parsing, resolution, request wiring.

Socket-free: direct function calls plus real _request_ctx with a
signed cookie (no monkeypatched seam for the wiring test).
"""
import pytest
from starlette.requests import Request

import app.main as main
from app import auth as auth_mod
from app import config as config_mod
from app.tenancy import (DEFAULT_TENANT, context_for_user,
                         known_tenants, parse_user_tenants,
                         tenant_for_user)

SECRET = "s" * 40


def _cookie_req(token):
    return Request({"type": "http", "method": "GET", "headers": [
        (b"cookie", ("csai_session=" + token).encode())], "path": "/"})


def test_parse_basic_and_spaces():
    assert parse_user_tenants("alice:org_acme, bob : org_beta ") == {
        "alice": "org_acme", "bob": "org_beta"}


def test_parse_skips_bad_entries():
    assert parse_user_tenants("nope,:, :x,y:,ok:org_ok") == {"ok": "org_ok"}
    assert parse_user_tenants("") == {}
    assert parse_user_tenants(None) == {}


def test_tenant_for_user_mapped_and_registered():
    assert tenant_for_user("alice", {"alice": "org_acme"}) == "org_acme"
    assert "org_acme" in known_tenants()


def test_tenant_for_user_unknown_defaults():
    assert tenant_for_user("ghost", {"alice": "org_acme"}) == DEFAULT_TENANT
    assert tenant_for_user("alice", {}) == DEFAULT_TENANT
    assert tenant_for_user("alice", None) == DEFAULT_TENANT
    assert tenant_for_user("", {"alice": "org_acme"}) == DEFAULT_TENANT


def test_tenant_for_user_invalid_slug_defaults():
    assert tenant_for_user("mallory", {"mallory": "NOT A SLUG!!!"}) == (
        DEFAULT_TENANT)


def test_context_for_user_actor():
    ctx = context_for_user("alice", {"alice": "org_acme"})
    assert (ctx.tenant_id, ctx.actor) == ("org_acme", "alice")
    assert context_for_user("", {}).actor == "anonymous"


def test_request_ctx_resolves_map(tmp_store, monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(config_mod, "USER_TENANTS", "bob:org_beta")
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "bob:investigator:%s" % auth_mod.hash_password("pw"))
    token = auth_mod.create_session("bob", "investigator", SECRET)
    ctx = main._request_ctx(_cookie_req(token))
    assert (ctx.tenant_id, ctx.actor) == ("org_beta", "bob")


def test_request_ctx_unknown_user_denied(tmp_store, monkeypatch):
    """Strict multi-tenant mode: authed-but-unmapped with a non-empty
    map is refused (403), never silently defaulted (CS-VFEP-001 S8)."""
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(config_mod, "USER_TENANTS", "bob:org_beta")
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "amy:investigator:%s" % auth_mod.hash_password("pw"))
    token = auth_mod.create_session("amy", "investigator", SECRET)
    with pytest.raises(main.AppError) as caught:
        main._request_ctx(_cookie_req(token))
    assert (caught.value.code, caught.value.status) == (
        "AUTHORIZATION_REQUIRED", 403)


def test_request_ctx_empty_map_defaults(tmp_store, monkeypatch):
    """Single-org mode (empty map): everyone belongs to the default
    tenant — the only mode where defaulting is allowed."""
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(config_mod, "USER_TENANTS", "")
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "amy:investigator:%s" % auth_mod.hash_password("pw"))
    token = auth_mod.create_session("amy", "investigator", SECRET)
    ctx = main._request_ctx(_cookie_req(token))
    assert (ctx.tenant_id, ctx.actor) == (DEFAULT_TENANT, "amy")


def test_request_ctx_bad_cookie_anonymous(tmp_store, monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(config_mod, "USER_TENANTS", "bob:org_beta")
    ctx = main._request_ctx(_cookie_req("tampered.payload"))
    assert (ctx.tenant_id, ctx.actor) == (DEFAULT_TENANT, "anonymous")


def test_request_ctx_unarmed_default():
    ctx = main._request_ctx(None)
    assert (ctx.tenant_id, ctx.actor) == (DEFAULT_TENANT, "anonymous")


def _authed_req(monkeypatch, user, tenants):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(config_mod, "USER_TENANTS", tenants)
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "%s:investigator:%s" % (user, auth_mod.hash_password("pw")))
    return _cookie_req(auth_mod.create_session(user, "investigator", SECRET))


def _fallback_actions(tmp_store):
    return [a.get("action") for a in tmp_store.state.get("audits", [])]


def test_unmapped_authed_user_audited(tmp_store, monkeypatch):
    req = _authed_req(monkeypatch, "amy", "bob:org_beta")
    with pytest.raises(main.AppError):
        main._request_ctx(req)
    hits = [a for a in tmp_store.state.get("audits", [])
            if a.get("action") == "tenant.default_fallback"]
    assert len(hits) == 1
    assert (hits[0]["actor_id"], hits[0]["target_id"]) == ("amy", DEFAULT_TENANT)


def test_mapped_user_not_audited(tmp_store, monkeypatch):
    req = _authed_req(monkeypatch, "bob", "bob:org_beta")
    main._request_ctx(req)
    assert "tenant.default_fallback" not in _fallback_actions(tmp_store)


def test_empty_map_no_audit(tmp_store, monkeypatch):
    req = _authed_req(monkeypatch, "amy", "")
    main._request_ctx(req)
    assert "tenant.default_fallback" not in _fallback_actions(tmp_store)
