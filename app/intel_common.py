"""Shared evidence helpers for intelligence engines (no duplication).

Identity/address/location/IP engines reuse: the telecom subject-hash
key (ONE pseudonym space), canonical sha256 sealing, UTC helpers, and
the lawful-purpose allowlist. Telecom keeps its own private copies
for backward compatibility; all NEW engines import from here.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any

# §15.3 purpose allowlist for NEW engines (telecom keeps its
# pre-existing free-text purpose for backward compatibility).
PURPOSES = (
    "AUTHORIZED_FRAUD_INVESTIGATION",
    "CUSTOMER_IDENTITY_VERIFICATION",
    "TRANSACTION_RISK_ASSESSMENT",
    "REGULATORY_COMPLIANCE",
    "APPROVED_SECURITY_INVESTIGATION",
)


def check_purpose(purpose: str) -> str:
    value = (purpose or "").strip()
    if value not in PURPOSES:
        raise ValueError("PURPOSE_INVALID: use one of %s"
                         % (", ".join(PURPOSES),))
    return value


def utc(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def digest(record: dict[str, Any]) -> str:
    body = {k: v for k, v in record.items() if k != "record_hash"}
    blob = json.dumps(body, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode()
    return hashlib.sha256(blob).hexdigest()


def seal(record: dict[str, Any]) -> dict[str, Any]:
    record["record_hash"] = digest(record)
    return record


def check_integrity(record: dict[str, Any]) -> bool:
    return bool(record.get("record_hash")) and hmac.compare_digest(
        str(record.get("record_hash")), digest(record))


def subject_hash(ref: str) -> str:
    """Pseudonymous subject key (telecom key = one pseudonym space)."""
    from app import telecom_verify as telecom_mod

    return telecom_mod.hash_subject(ref)


def mask_ref(ref: str, keep: int = 2) -> str:
    """Generic masked display: first 2 + stars + last `keep` chars."""
    text = (ref or "").strip()
    if len(text) <= 4:
        return "*" * len(text)
    suffix = text[-keep:] if keep > 0 else ""
    return text[:2] + "*" * (len(text) - 2 - len(suffix)) + suffix


def actor_name(org: str, user: str) -> tuple[str, str]:
    org = (org or "").strip()[:80]
    user = (user or "").strip()[:80]
    if not org or not user:
        raise ValueError("ACTOR_REQUIRED: org and user are mandatory")
    return org, user
