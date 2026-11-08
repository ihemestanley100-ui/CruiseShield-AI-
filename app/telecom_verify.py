"""Telecom verification engine: 11 services, 9 result states.

Honesty rules (non-negotiable):
- VERIFIED only from a live provider response or a synthetic-labeled
  harness script (tests). UNAVAILABLE is never upgraded.
- Allocation ranges identify allocation only (PARTIALLY_VERIFIED at
  best); portability always applies where supported.
- KYC matching needs explicit consent AND a provider; otherwise
  CONSENT_REQUIRED / UNAVAILABLE — client self-reports prove nothing.
- Raw E.164 never persists: masked display + HMAC subject hash only.
- Every record carries a sha256 integrity digest; reads re-verify it.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime, timezone
from typing import Any

from app import telecom_providers as prov_mod
from app import telecom_registry as reg_mod

VERIFIED = "VERIFIED"
NOT_VERIFIED = "NOT_VERIFIED"
PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
UNAVAILABLE = "UNAVAILABLE"
UNSUPPORTED_OPERATOR = "UNSUPPORTED_OPERATOR"
PROVIDER_ERROR = "PROVIDER_ERROR"
CONSENT_REQUIRED = "CONSENT_REQUIRED"
AUTHORIZATION_REQUIRED = "AUTHORIZATION_REQUIRED"
STALE_RESULT = "STALE_RESULT"

STATES = (VERIFIED, NOT_VERIFIED, PARTIALLY_VERIFIED, UNAVAILABLE,
          UNSUPPORTED_OPERATOR, PROVIDER_ERROR, CONSENT_REQUIRED,
          AUTHORIZATION_REQUIRED, STALE_RESULT)

TYPES = (
    "carrier_identification",
    "current_network",
    "number_verification",
    "sim_ownership",
    "sim_swap",
    "number_recycling",
    "device_swap",
    "kyc_match",
    "tenure",
    "roaming",
    "network_type",
)

# Freshness TTL per type (hours). Reads past TTL surface STALE_RESULT.
TTL_HOURS = {
    "carrier_identification": 24 * 30,
    "current_network": 24,
    "number_verification": 1,
    "sim_ownership": 24,
    "sim_swap": 24 * 7,
    "number_recycling": 24 * 7,
    "device_swap": 24 * 7,
    "kyc_match": 24 * 30,
    "tenure": 24 * 7,
    "roaming": 6,
    "network_type": 6,
}

ALWAYS_CONSENT = ("kyc_match", "sim_ownership")
CONSENT_TTL_DAYS = 30

_BOOT_KEY = secrets.token_bytes(32)


def _subject_secret() -> bytes:
    from app import config as config_mod

    raw = (config_mod.SESSION_SECRET or "").encode()
    if len(raw) >= 32:
        return raw
    # Open local mode: boot-random key. Cross-restart correlation is
    # lost, but hashes stay non-reversible. Documented, fail-safe.
    return _BOOT_KEY


def hash_subject(e164: str) -> str:
    return hmac.new(_subject_secret(), e164.encode(),
                    hashlib.sha256).hexdigest()


def mask_e164(e164: str) -> str:
    """Display form: country code + masked middle + last 2 digits."""
    digits = e164.lstrip("+")
    code = ""
    for cand in sorted(reg_mod.CALLING_CODES, key=len, reverse=True):
        if digits.startswith(cand):
            code = cand
            break
    rest = digits[len(code):] if code else digits
    if len(rest) <= 2:
        return "+" + code + "*" * len(rest)
    return "+" + code + "*" * (len(rest) - 2) + rest[-2:]


def _utc(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _digest(record: dict[str, Any]) -> str:
    body = {k: v for k, v in record.items() if k != "record_hash"}
    blob = json.dumps(body, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode()
    return hashlib.sha256(blob).hexdigest()


def check_integrity(record: dict[str, Any]) -> bool:
    return bool(record.get("record_hash")) and hmac.compare_digest(
        str(record.get("record_hash")), _digest(record))


def is_stale(record: dict[str, Any], now: float | None = None) -> bool:
    moment = time.time() if now is None else now
    ttl = TTL_HOURS.get(record.get("verify_type", ""), 24) * 3600
    return (moment - float(record.get("verified_ts", 0.0))) > ttl


def _base(store, verify_type: str, e164: str, purpose: str,
          org: str, user: str, tenant_id: str,
          now: float) -> dict[str, Any]:
    seq = store.telecom_next_seq()
    return {
        "verification_id": "tvrf_%06d" % seq,
        "subject_masked": mask_e164(e164),
        "subject_hash": hash_subject(e164),
        "operator_id": None, "country": None,
        "provider": "none", "provider_ref": "",
        "api": "", "api_version": "",
        "verify_type": verify_type, "state": UNAVAILABLE,
        "previous_state": "", "confidence": "NONE",
        "source": prov_mod.UNAVAILABLE,
        "verified_at": _utc(now), "verified_ts": now,
        "freshness_ttl_hours": TTL_HOURS[verify_type],
        "limitations": [], "consent_id": "",
        "purpose": purpose, "org": org, "user": user,
        "tenant_id": tenant_id, "synthetic": False,
        "evidence": {},
    }


def _seal(store, record: dict[str, Any]) -> dict[str, Any]:
    record["record_hash"] = _digest(record)
    store.telecom_save(record)
    return record


def _need_consent(store, record: dict[str, Any], now: float) -> bool:
    from app import config as config_mod

    if (record["verify_type"] not in ALWAYS_CONSENT
            and not config_mod.telecom_consent_required()):
        return False
    consent = store.telecom_consent_for(record["subject_hash"],
                                        record["purpose"])
    if consent is None:
        return True
    try:
        return float(consent.get("expires_ts", 0.0)) <= now
    except (TypeError, ValueError):
        return True


def _live_adapter(store, record: dict[str, Any]):
    for adapter in prov_mod.TYPE_ADAPTERS.get(record["verify_type"], ()):
        conn = prov_mod.live_connection(store, adapter,
                                        record["tenant_id"])
        if conn is not None:
            return adapter, conn
    return None, None


def _provider_path(store, record, harness, script, now):
    """Live provider first; harness only when explicitly supplied.

    The HTTP handler never supplies a harness, so production traffic
    without a live connection always lands on UNAVAILABLE.
    """
    adapter, _ = _live_adapter(store, record)
    if adapter is not None:
        record["provider"] = adapter
        record["api"] = adapter
        record["api_version"] = "live"
        record["state"] = PROVIDER_ERROR
        record["confidence"] = "NONE"
        record["source"] = prov_mod.UNAVAILABLE
        record["limitations"] = [
            "live connection present but no provider call "
            "implementation; no provider contacted"]
        return record
    if harness is None:
        needed = ", ".join(
            prov_mod.TYPE_ADAPTERS.get(record["verify_type"],
                                       ("none",)))
        record["state"] = UNAVAILABLE
        record["confidence"] = "NONE"
        record["source"] = prov_mod.UNAVAILABLE
        record["limitations"] = [
            "requires live provider (%s); no live connection" % needed]
        return record
    try:
        response = harness.answer(store, record["tenant_id"],
                                  record["verify_type"], script)
    except prov_mod.ProviderOutage as exc:
        record["state"] = PROVIDER_ERROR
        record["confidence"] = "NONE"
        record["source"] = prov_mod.UNAVAILABLE
        record["limitations"] = ["provider failure: %s" % exc]
        return record
    return _apply_harness(record, response)


def _apply_harness(record, response):
    payload = response.get("payload", {}) or {}
    want = str(payload.get("result", "NOT_VERIFIED")).upper()
    record["provider"] = response["provider"]
    record["provider_ref"] = str(response.get("provider_ref", ""))
    record["synthetic"] = True
    record["source"] = prov_mod.HARNESS
    if want not in STATES or want in (AUTHORIZATION_REQUIRED,
                                      CONSENT_REQUIRED, STALE_RESULT):
        record["state"] = PROVIDER_ERROR
        record["confidence"] = "NONE"
        record["limitations"] = ["harness script returned no usable "
                                 "result; treated as provider error"]
        return record
    record["state"] = want
    record["confidence"] = str(payload.get("confidence", "HIGH")).upper()
    if record["confidence"] not in ("HIGH", "MEDIUM", "LOW", "NONE"):
        record["confidence"] = "HIGH"
    record["limitations"] = ["synthetic harness response; no live "
                             "provider contacted"]
    for key in ("operator_id", "country", "api", "api_version"):
        if payload.get(key):
            record[key] = str(payload[key])[:80]
    return record


def _platform_tenure(state, phone_label: str):
    """Observed first/last timestamps for a fixture phone label."""
    stamps = []
    for event in state.get("events", []) or []:
        if not isinstance(event, dict):
            continue
        txn = event.get("transaction") or {}
        if txn.get("phone_id") != phone_label:
            continue
        stamp = str(event.get("occurred_at", ""))
        if stamp:
            stamps.append(stamp)
    if not stamps:
        return None
    return min(stamps), max(stamps)


def run_verification(store, state: dict[str, Any],
                     verify_type: str, e164_raw: str,
                     purpose: str, org: str, user: str,
                     tenant_id: str,
                     context: dict[str, Any] | None = None,
                     harness=None,
                     script: dict[str, Any] | None = None,
                     now: float | None = None) -> dict[str, Any]:
    """Execute one verification; persist and return the evidence record."""
    if verify_type not in TYPES:
        raise ValueError("VERIFY_TYPE_UNKNOWN: %r" % (verify_type,))
    purpose = (purpose or "").strip()
    if not purpose or len(purpose) > 200:
        raise ValueError("PURPOSE_REQUIRED: lawful purpose 1..200 chars")
    if not (user or "").strip() or not (org or "").strip():
        raise ValueError("ACTOR_REQUIRED: org and user are mandatory")
    try:
        e164 = reg_mod.normalize_e164(e164_raw)
    except ValueError:
        raise ValueError("INVALID_E164: %r" % (e164_raw,))
    moment = time.time() if now is None else now
    context = context or {}
    record = _base(store, verify_type, e164, purpose,
                   (org or "").strip()[:80], (user or "").strip()[:80],
                   tenant_id, moment)
    alloc = reg_mod.allocation_lookup(e164)
    record["country"] = alloc["country"]
    if record["country"] is None:
        record["state"] = UNSUPPORTED_OPERATOR
        record["source"] = prov_mod.UNAVAILABLE
        record["limitations"] = [alloc["limitation"]]
        return _seal(store, record)
    if _need_consent(store, record, moment):
        record["state"] = CONSENT_REQUIRED
        record["source"] = prov_mod.UNAVAILABLE
        record["limitations"] = ["explicit consent required before "
                                 "this check; no provider contacted"]
        return _seal(store, record)
    handler = _HANDLERS[verify_type]
    return _seal(store, handler(store, state, record, alloc, context,
                                harness, script, moment))


def _h_carrier(store, state, record, alloc, context, harness,
               script, now):
    _ = (store, state, context, harness, script, now)
    if alloc["operator_id"] is None:
        record["state"] = UNAVAILABLE
        record["source"] = prov_mod.UNAVAILABLE
        record["limitations"] = [alloc["limitation"]]
        return record
    record["operator_id"] = alloc["operator_id"]
    record["state"] = PARTIALLY_VERIFIED
    record["confidence"] = "MEDIUM"
    record["source"] = prov_mod.INFERRED
    record["evidence"] = {"basis": alloc["basis"]}
    record["limitations"] = [alloc["limitation"]]
    return record


def _provider_only(store, state, record, alloc, context, harness,
                   script, now):
    _ = (state, alloc, context)
    return _provider_path(store, record, harness, script, now)


def _h_tenure(store, state, record, alloc, context, harness,
              script, now):
    _ = (store, alloc, harness, script, now)
    label = str(context.get("phone_label", "") or "")
    span = _platform_tenure(state, label) if label else None
    if span is None:
        record["state"] = UNAVAILABLE
        record["source"] = prov_mod.UNAVAILABLE
        record["limitations"] = ["no platform observations linked to "
                                 "this subject; supply phone_label "
                                 "context or a live provider"]
        return record
    record["state"] = PARTIALLY_VERIFIED
    record["confidence"] = "MEDIUM"
    record["source"] = prov_mod.INFERRED
    record["evidence"] = {"observed_first": span[0],
                          "observed_last": span[1],
                          "phone_label": label}
    record["limitations"] = ["observed tenure from platform events "
                             "only; not operator billing tenure"]
    return record


def _client_report(store, record, field, label):
    claim = str(record.get("_ctx_%s" % field, "") or "")
    if not claim:
        return None
    record["state"] = PARTIALLY_VERIFIED
    record["confidence"] = "LOW"
    record["source"] = prov_mod.CLIENT_REPORTED
    record["evidence"] = {field: claim[:80]}
    record["limitations"] = ["unconfirmed %s; no provider contacted"
                             % label]
    return record


def _h_client_or_provider(store, state, record, alloc, context,
                          harness, script, now, field, label):
    _ = (state, alloc, now)
    record["_ctx_%s" % field] = context.get(field, "")
    claimed = _client_report(store, record, field, label)
    if claimed is not None:
        del record["_ctx_%s" % field]
        return record
    record.pop("_ctx_%s" % field, None)
    return _provider_path(store, record, harness, script, now)


def _h_roaming(store, state, record, alloc, context, harness,
               script, now):
    return _h_client_or_provider(store, state, record, alloc, context,
                                 harness, script, now, "roaming",
                                 "client roaming report")


def _h_network_type(store, state, record, alloc, context, harness,
                    script, now):
    return _h_client_or_provider(store, state, record, alloc, context,
                                 harness, script, now, "network_type",
                                 "client network-type report")


def _h_swap(store, state, record, alloc, context, harness,
            script, now):
    return _h_client_or_provider(store, state, record, alloc, context,
                                 harness, script, now, "last_swap_at",
                                 "client swap report")


_HANDLERS = {
    "carrier_identification": _h_carrier,
    "current_network": _provider_only,
    "number_verification": _provider_only,
    "sim_ownership": _provider_only,
    "sim_swap": _h_swap,
    "number_recycling": _provider_only,
    "device_swap": _h_swap,
    "kyc_match": _provider_only,
    "tenure": _h_tenure,
    "roaming": _h_roaming,
    "network_type": _h_network_type,
}


def summarize(state: dict[str, Any], verifications: list[dict],
              phone_label: str = "") -> dict[str, Any]:
    """Correlation summary: allocation + history + co-signals (no verdicts).

    Co-signals reuse platform observations only (devices, accounts,
    beneficiaries, geos, velocity) and cite their sources; they never
    assert telecom facts the evidence does not support.
    """
    history = [{"verification_id": v.get("verification_id", ""),
                "verify_type": v.get("verify_type", ""),
                "state": v.get("state", ""),
                "verified_at": v.get("verified_at", ""),
                "stale": is_stale(v)} for v in verifications
               if isinstance(v, dict)]
    co_signals: dict[str, Any] = {"devices": [], "accounts": [],
                                  "beneficiaries": [],
                                  "geo_labels": [],
                                  "transaction_count": 0}
    if phone_label:
        txns = [t for t in state.get("transactions", []) or []
                if isinstance(t, dict)
                and t.get("phone_id") == phone_label]
        co_signals["devices"] = sorted({str(t.get("device_id")) for t in
                                        txns if t.get("device_id")})
        accounts = set()
        beneficiaries = set()
        geos = set()
        for txn in txns:
            if txn.get("sender_account_id"):
                accounts.add(str(txn["sender_account_id"]))
            if txn.get("receiver_account_id"):
                beneficiaries.add(str(txn["receiver_account_id"]))
            if txn.get("location_id"):
                geos.add(str(txn["location_id"]))
        co_signals["accounts"] = sorted(accounts)
        co_signals["beneficiaries"] = sorted(beneficiaries)
        co_signals["geo_labels"] = sorted(geos)
        co_signals["transaction_count"] = len(txns)
    return {"history": history, "co_signals": co_signals,
            "history_count": len(history)}
