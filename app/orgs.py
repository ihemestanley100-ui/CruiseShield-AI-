"""Organization administration (Phase 5, D-042). Single-org scope.

Profile, membership derived from the user registry, runtime
disable/enable (self and founder protected), and token invitations
redeemable even when self-registration is off (the invitation is
the authorization). Cross-tenant semantics stay with D-014.
"""
from __future__ import annotations

import time
from typing import Any

INVITE_TTL_SECONDS = 7 * 24 * 3600
MAX_ORG_NAME_CHARS = 120


def validate_org_name(name: str) -> str:
    """Clean org name or raise ORG_NAME_INVALID."""
    clean = (name or "").strip()
    if not clean or len(clean) > MAX_ORG_NAME_CHARS:
        raise ValueError("ORG_NAME_INVALID: 1..120 chars")
    return clean


def members(store) -> list[dict[str, Any]]:
    """Membership view: env seed + overlay (hashes never included)."""
    from app import auth as auth_mod
    from app import config as config_mod

    rows: dict[str, dict[str, Any]] = {}
    for name, (role, _record) in auth_mod.parse_users(
            config_mod.DEMO_USERS or "").items():
        rows[name] = {"username": name, "role": role, "origin": "env",
                      "disabled": False, "email": "", "phone": "",
                      "email_verified": False, "phone_verified": False}
    for rec in store.state.get("registered_users", []):
        if not isinstance(rec, dict) or not rec.get("username"):
            continue
        rows[rec["username"]] = {
            "username": rec["username"],
            "role": rec.get("role", ""),
            "origin": rec.get("origin", "admin"),
            "disabled": bool(rec.get("disabled")),
            "email": rec.get("email", ""),
            "phone": rec.get("phone", ""),
            "email_verified": bool(rec.get("email_verified")),
            "phone_verified": bool(rec.get("phone_verified")),
        }
    return [rows[name] for name in sorted(rows)]


def set_disabled(store, username: str, disabled: bool,
                 actor: str, founder_user: str) -> dict[str, Any]:
    """Disable/enable a user (self and founder are protected)."""
    if username == actor:
        raise ValueError("ORG_SELF_DISABLE: cannot change your own access")
    founder = (founder_user or "").strip()
    if founder and username == founder:
        raise ValueError("ORG_FOUNDER_PROTECTED: founder is protected")
    rec = store.registered_user(username)
    if rec is None:
        rec = {"username": username, "role": "", "record": "",
               "email": "", "phone": "", "email_verified": False,
               "phone_verified": False, "disabled": False,
               "origin": "admin", "created_at": ""}
    rec["disabled"] = bool(disabled)
    store.upsert_registered_user(rec)
    return {"username": username, "disabled": bool(disabled)}


def issue_invitation(store, email: str, role: str, created_by: str,
                     secret: str, now: float | None = None) -> dict[str, Any]:
    """Create an invitation; returns the record plus the token.

    The token goes back to the ADMIN caller for manual relay until
    delivery exists. It never lands in audit records.
    """
    from app import accounts as accounts_mod
    from app import auth as auth_mod
    from app import verify as verify_mod

    clean_email = accounts_mod.validate_email(email)
    if not clean_email:
        raise ValueError("EMAIL_INVALID: invitation needs an address")
    if role not in auth_mod.ROLES:
        raise ValueError("ROLE_UNKNOWN: %s" % (role,))
    moment = time.time() if now is None else now
    token = verify_mod.issue_token(secret, created_by, "invite",
                                   clean_email, now=moment,
                                   ttl_seconds=INVITE_TTL_SECONDS)
    claims = verify_mod.parse_token(token, secret, now=moment)
    assert claims is not None
    record = {"nonce": claims["nonce"], "email": clean_email,
              "role": role, "created_by": created_by,
              "created_at": moment, "exp": float(claims["exp"]),
              "redeemed_at": None, "redeemed_by": ""}
    store.save_invitation(record)
    return {"invitation": record, "token": token}


def redeem_invitation(store, token: str, username: str, password: str,
                      secret: str,
                      now: float | None = None) -> dict[str, Any]:
    """Redeem an invitation into a registered user (trial opened)."""
    from app import accounts as accounts_mod
    from app import auth as auth_mod
    from app import billing as billing_mod
    from app import verify as verify_mod

    moment = time.time() if now is None else now
    claims = verify_mod.parse_token(token, secret, now=moment)
    if claims is None or claims["purpose"] != "invite":
        raise ValueError("INVITE_INVALID: bad or expired token")
    record = store.invitation(claims["nonce"])
    if record is None or record.get("redeemed_at") is not None:
        raise ValueError("INVITE_SPENT: already redeemed")
    if float(record.get("exp", 0)) < moment:
        raise ValueError("INVITE_INVALID: invitation expired")
    if not verify_mod.spend_token(store, "invite", claims["nonce"],
                                  float(claims["exp"])):
        raise ValueError("INVITE_SPENT: already redeemed")
    clean_name = accounts_mod.validate_username(username)
    clean_password = accounts_mod.validate_password(password)
    if clean_name in accounts_mod.resolve_users(store):
        raise ValueError("USERNAME_TAKEN: %s" % clean_name)
    if accounts_mod.contact_taken(store, record["email"], ""):
        raise ValueError("CONTACT_TAKEN: email already registered")
    rec = accounts_mod.build_record(
        clean_name, record["role"],
        auth_mod.hash_password(clean_password),
        record["email"], "", origin="invite")
    store.upsert_registered_user(rec)
    record["redeemed_at"] = moment
    record["redeemed_by"] = clean_name
    store.save_invitation(record)
    trial = billing_mod.ensure_trial(store, clean_name)
    return {"user": accounts_mod.public_user(rec), "trial": trial}
