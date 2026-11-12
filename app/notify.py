"""Notification delivery: templates, routing, drivers (Phase 5, D-043).

Security events always dispatch; other kinds honor preferences.
Only the "log" test driver exists: provider drivers need a vendor
decision. Templates are versioned; bodies interpolate declared
keys only (extra context never leaks in).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

TEMPLATES = {
    "suspicious_login": {
        "version": 1, "kind": "security",
        "subject": "Suspicious sign-in to CruiseShield AI",
        "body": ("Hi {username}: a sign-in scored {level} risk "
                 "({signals}). If this was you, no action is needed. "
                 "Otherwise review active sessions and revoke "
                 "anything unfamiliar.")},
    "password_changed": {
        "version": 1, "kind": "security",
        "subject": "Your CruiseShield AI password changed",
        "body": ("Hi {username}: your password was changed and all "
                 "sessions were revoked. If this was not you, contact "
                 "your administrator immediately.")},
    "mfa_enabled": {
        "version": 1, "kind": "security",
        "subject": "Two-factor authentication enabled",
        "body": ("Hi {username}: two-factor authentication was "
                 "enabled on your account.")},
    "mfa_disabled": {
        "version": 1, "kind": "security",
        "subject": "Two-factor authentication disabled",
        "body": ("Hi {username}: two-factor authentication was "
                 "disabled on your account by {actor}.")},
    "recovery_used": {
        "version": 1, "kind": "security",
        "subject": "A recovery code was used",
        "body": ("Hi {username}: a recovery code signed in to your "
                 "account; {remaining} remaining.")},
    "contact_verified": {
        "version": 1, "kind": "security",
        "subject": "Contact verified",
        "body": ("Hi {username}: your {purpose} contact was verified.")},
}

SECURITY_KIND = "security"
DRIVERS = ("log",)
RETRY_DELAYS = (60, 300, 900)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def render(event: str, context: dict[str, Any]) -> tuple[str, str, int]:
    """Render subject, body, version or raise a descriptive error."""
    tpl = TEMPLATES.get(event)
    if tpl is None:
        raise ValueError("NOTIF_EVENT_UNKNOWN: %s" % (event,))
    try:
        return (tpl["subject"].format(**context),
                tpl["body"].format(**context), tpl["version"])
    except KeyError as exc:
        raise ValueError("NOTIF_CONTEXT_MISSING: %s" % (exc,))


def next_retry(attempt: int) -> int | None:
    """Backoff seconds for a 0-based attempt, else None (give up)."""
    if 0 <= attempt < len(RETRY_DELAYS):
        return RETRY_DELAYS[attempt]
    return None


def dispatch(store, event: str, username: str,
             context: dict[str, Any],
             channel: str = "email") -> dict[str, Any]:
    """Route one notification to the log driver (recorded, untracked).

    Security events always dispatch; other kinds honor stored
    preferences (suppressions are recorded, not silent).
    """
    if channel not in ("email", "sms"):
        raise ValueError("NOTIF_CHANNEL_UNKNOWN: %s" % (channel,))
    tpl = TEMPLATES.get(event)
    if tpl is None:
        raise ValueError("NOTIF_EVENT_UNKNOWN: %s" % (event,))
    if tpl["kind"] != SECURITY_KIND and not store.notif_prefs_for(
            username).get(tpl["kind"], True):
        entry = {"event": event, "user": username, "channel": channel,
                 "subject": "", "body": "", "template_version": 0,
                 "driver": "log", "status": "suppressed", "attempts": 0,
                 "last_error": "", "at": _now()}
        store.save_outbox(entry)
        return entry
    subject, body, version = render(event, {"username": username,
                                           **context})
    entry = {"event": event, "user": username, "channel": channel,
             "subject": subject, "body": body,
             "template_version": version, "driver": "log",
             "status": "logged", "attempts": 1, "last_error": "",
             "at": _now()}
    store.save_outbox(entry)
    return entry
