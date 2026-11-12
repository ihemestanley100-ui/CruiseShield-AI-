"""Attribute-based authorization policy (master directive §4).

Central server-side policy, deny-by-default. Every decision returns
(allowed, reason) so denials are explainable and auditable. Layers:

1. Authentication required (anonymous is denied everything).
2. Tenant match (fail closed; session subjects resolve through
   the D-014 user→tenant map, defaulting to the default tenant
   only when unmapped, per tenancy.tenant_for_user).
3. Role permission (reuses the canonical auth.PERMISSIONS matrix).
4. Session strength: SENSITIVE kinds need a full login session —
   mfa-pending sessions and the shared service token are denied.
5. Legal hold: CLOSE/DELETE on a held resource is denied.

Scope (D-025): enforced on new endpoints (policy-check, agents,
governance). Legacy endpoints keep their existing gates until the
incremental migration; this module never weakens them.
"""
from __future__ import annotations

from typing import Any

ACTION_PERM = {
    "read": "read",
    "write": "write",
    "close": "write",
    "delete": "write",
    "decide": "write",
    "approve": "manage",
    "admin": "manage",
    "audit_read": "audit_read",
    "ai_run": "ai_run",
}

# Kinds whose reads/writes need a full (non-pending) login session.
SENSITIVE_KINDS = frozenset({"audit", "sar", "dsr", "hold", "mfa",
                               "connector"})

# Actions a legal hold blocks on the held resource.
HOLD_BLOCKED_ACTIONS = frozenset({"close", "delete"})


def blank_subject() -> dict[str, Any]:
    """Anonymous subject (denied everything)."""
    return {"user": "", "role": "", "tenant": "", "kind": "none",
            "mfa_full": False}


def subject_from_request(request: Any) -> dict[str, Any]:
    """Build the policy subject from live session/token state."""
    from app import auth as auth_mod
    from app import config as config_mod
    from app import tenancy as tenancy_mod

    subject = blank_subject()
    subject["tenant"] = tenancy_mod.DEFAULT_TENANT
    if request is None or not config_mod.session_auth_armed():
        return subject
    secret = config_mod.SESSION_SECRET or ""
    # NOTE: store-agnostic would be nicer, but revocation/epoch checks
    # need the live store; main passes the app store. Import here to
    # avoid a hard import cycle at module load.
    from app.main import store as live_store
    from app import accounts as accounts_mod

    users = accounts_mod.resolve_users(live_store)

    ring = [secret, config_mod.SESSION_SECRET_PREVIOUS or ""]
    claims = auth_mod.verify_session_live(
        request.cookies.get(auth_mod.SESSION_COOKIE, ""), secret,
        live_store, users, secrets=ring)
    if claims is not None:
        # F-C: resolve the session user's real tenant via D-014.
        # Pinning DEFAULT_TENANT here let a foreign-tenant session
        # satisfy default-tenant resource checks (fail open).
        mapping = tenancy_mod.parse_user_tenants(
            config_mod.USER_TENANTS or "")
        subject.update({"user": claims["user"], "role": claims["role"],
                        "kind": "session",
                        "tenant": tenancy_mod.tenant_for_user(
                            claims["user"], mapping),
                        "mfa_full": not claims.get("mfa_pending",
                                                  False)})
        return subject
    expected = config_mod.DEMO_WRITE_TOKEN or ""
    presented = (request.headers.get("authorization", "") or "")
    if presented.startswith("Bearer "):
        presented = presented[len("Bearer "):]
    if expected and presented:
        import hmac

        if hmac.compare_digest(presented, expected):
            subject.update({"user": "platform-token", "role": "",
                            "kind": "token"})
            return subject
    if presented.startswith("csc_"):
        from app import api_credentials as cred_mod

        record = cred_mod.verify(live_store, presented)
        if record is not None:
            subject.update({"user": "client:" + record["client_id"],
                            "role": "", "kind": "client",
                            "scopes": list(record["scopes"])})
    return subject


def decide(subject: dict[str, Any], action: str,
           resource: dict[str, Any] | None = None) -> tuple[bool, str]:
    """Evaluate the policy. Never raises on bad input (denies)."""
    from app import auth as auth_mod

    try:
        resource = resource or {}
        perm = ACTION_PERM.get(str(action or ""))
        if perm is None:
            return False, "deny: unknown action %r" % (action,)
        kind = subject.get("kind", "none")
        if kind == "none":
            return False, "deny: authentication required"
        want_tenant = str(resource.get("tenant", "") or "")
        have_tenant = str(subject.get("tenant", "") or "")
        if want_tenant and have_tenant and want_tenant != have_tenant:
            return False, "deny: cross-tenant access refused"
        role = str(subject.get("role", "") or "")
        if kind == "session":
            if not auth_mod.can(role, perm):
                return False, "deny: role %r lacks %r" % (role, perm)
        elif kind == "token":
            # The shared service token is a low-assurance non-browser
            # credential: reads/writes on normal resources only, never
            # sensitive kinds, never manage-level actions.
            if perm in ("manage", "audit_read"):
                return False, "deny: token cannot satisfy %r" % (perm,)
        elif kind == "client":
            # SEC-CRED: per-client credential; scopes are explicit and
            # never include manage. Sensitive kinds stay session-only
            # via the check below (kind != "session" denies).
            if perm not in set(subject.get("scopes", ())):
                return False, "deny: client scope lacks %r" % (perm,)
        else:
            return False, "deny: unknown credential kind"
        if str(resource.get("kind", "")) in SENSITIVE_KINDS and not (
                kind == "session" and subject.get("mfa_full")):
            return False, "deny: full login session required"
        if resource.get("hold") and str(action) in HOLD_BLOCKED_ACTIONS:
            return False, "deny: resource under legal hold"
        return True, "allow: %s/%s/%s" % (
            subject.get("user", "?"), action,
            resource.get("kind", "unscoped"))
    except (AttributeError, TypeError, ValueError):
        return False, "deny: malformed policy input"
