"""L13 Part 8.4: unknown-location login-risk scoring (D-028).

Scores each successful password login as low/elevated/high from
privacy-preserving fingerprints of the network identity, the
user-agent class, and the hour-of-day bucket. The first login for a
user learns a baseline and scores low; later logins compare against
it. No GeoIP or vendor lookups, no raw IPs or user-agent strings
are stored -- only SHA-256 digests and hour buckets.

Scoring weights (deterministic, additive over the novel components):
  new network identity ........... 2
  new user-agent class ........... 2
  unusual hour-of-day ............ 1
Level: 0-1 low, 2-3 elevated, 4+ high. An exact repeat of a known
(ip, user-agent, hour) context short-circuits to low.
"""
from __future__ import annotations

import hashlib

RISK_VERSION = 1
WEIGHT_NEW_IP = 2
WEIGHT_NEW_DEVICE = 2
WEIGHT_NEW_HOUR = 1
BASELINE_CAP = 8  # fingerprints / network tags / UA classes retained


def _digest(*parts: str) -> str:
    blob = "\x00".join(parts).encode("utf-8", "replace")
    return hashlib.sha256(blob).hexdigest()


def classify_ua(user_agent: str) -> str:
    """Bucket a User-Agent header into a coarse device class.

    Order matters: mobile/tablet tokens are checked before desktop
    OS tokens because mobile agents embed desktop-OS substrings
    (e.g. "like Mac OS X"). Empty or missing headers map to
    "unknown" rather than failing closed on the login itself.
    """
    text = (user_agent or "").lower()
    if not text.strip():
        return "unknown"
    if ("bot" in text or "crawl" in text or "spider" in text
            or "curl" in text or "wget" in text or "python-" in text
            or "http-client" in text or "httpclient" in text):
        return "bot"
    if "ipad" in text or "tablet" in text:
        return "tablet"
    if ("mobi" in text or "android" in text or "iphone" in text
            or "ipod" in text):
        return "mobile"
    if "windows" in text:
        return "desktop-windows"
    if "mac os" in text or "macintosh" in text:
        return "desktop-macos"
    if "linux" in text or "x11" in text:
        return "desktop-linux"
    return "other"


def session_fingerprint(ip_key: str,
                        user_agent: str) -> tuple[str, str]:
    """Coarse device class + network digest for the session registry."""
    ua_class = classify_ua(user_agent)
    return ua_class, _digest("net", ip_key or "", ua_class)


def hour_bucket(now: float) -> int:
    """UTC hour-of-day bucket for a POSIX timestamp."""
    return int(now // 3600) % 24


def _bounded(items: list, value, cap: int = BASELINE_CAP) -> list:
    ordered = [v for v in items if v != value]
    ordered.append(value)
    return ordered[-cap:]


def assess(baseline: dict, ip_key: str, user_agent: str,
           now: float) -> tuple[str, list[str], dict]:
    """Score one successful login; return (level, signals, baseline).

    `ip_key` is the rate-limit client identity ("xff:<ip>" or
    "peer:<host>"); only its digest is retained. `signals` names the
    novel components ("new_ip", "new_device", "unusual_hour") so the
    client can explain an elevated/high level. The baseline is
    learned on every call, including first-seen users (who score
    low). Unknown users must never reach this function -- callers
    assess only after the password verifies.
    """
    ua_class = classify_ua(user_agent)
    hour = hour_bucket(now)
    fp = _digest("fp", ip_key, ua_class, str(hour))
    ip_tag = _digest("ip", ip_key)

    stored = baseline if isinstance(baseline, dict) else {}
    fps = list(stored.get("fingerprints", []))
    ips = list(stored.get("networks", []))
    uas = list(stored.get("ua_classes", []))
    hours = list(stored.get("hours", []))
    logins = int(stored.get("logins", 0) or 0)

    signals: list[str] = []
    if logins and fp in fps:
        level = "low"  # exact known context: nothing novel
    elif not logins:
        level = "low"  # first login learns the baseline
    else:
        if ip_tag not in ips:
            signals.append("new_ip")
        if ua_class not in uas:
            signals.append("new_device")
        if hour not in hours:
            signals.append("unusual_hour")
        score = (WEIGHT_NEW_IP * ("new_ip" in signals)
                 + WEIGHT_NEW_DEVICE * ("new_device" in signals)
                 + WEIGHT_NEW_HOUR * ("unusual_hour" in signals))
        level = "low" if score <= 1 else (
            "elevated" if score <= 3 else "high")

    updated = {
        "version": RISK_VERSION,
        "logins": logins + 1,
        "fingerprints": _bounded(fps, fp),
        "networks": _bounded(ips, ip_tag),
        "ua_classes": _bounded(uas, ua_class),
        "hours": sorted(set(hours) | {hour}),
        "last_level": level,
        "last_signals": signals,
    }
    return level, signals, updated
