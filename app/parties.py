"""Transaction party intelligence (UFI section 06).

Parties are extracted from transaction-record fields only. Identifiers are
masked by default via the shared intel masking helper; full values require
the sensitive-reveal permission enforced at the API layer. Entity resolution
is conservative: exact authorized-identifier matches RESOLVE, shared
device/phone/address signals only SUPPORT, and nothing else matches.
"""
from __future__ import annotations

from typing import Any

from app.intel_common import mask_ref

ROLES = (
    "ORIGINATOR", "SENDER", "PAYER", "BENEFICIARY", "RECIPIENT", "PAYEE",
    "MERCHANT", "ISSUER", "ACQUIRER", "INTERMEDIARY_BANK",
    "CORRESPONDENT_BANK", "PAYMENT_PROCESSOR", "MONEY_TRANSFER_AGENT",
    "EXCHANGE", "WALLET_PROVIDER", "SETTLEMENT_INSTITUTION",
    "OTHER_INTERMEDIARY",
)

# Transaction-record fields that may carry a verified customer/account link.
# Resolution only trusts exact matches on these; names alone never resolve.
AUTHORIZED_ID_FIELDS = ("sender_account_id", "receiver_account_id",
                        "customer_id", "account_id", "wallet_address")

_SUPPORT_FIELDS = ("device_id", "phone_id", "ip_id", "merchant_id",
                    "location_id")


def _party(role: str, ref: str | None, label: str | None,
           source: str) -> dict[str, Any]:
    return {
        "role": role,
        "reference_masked": mask_ref(ref) if ref else None,
        "label": label,
        "source_field": source,
        "verification": "UNVERIFIED",
    }


def extract_parties(txn: dict[str, Any]) -> list[dict[str, Any]]:
    """Build the role list for one transaction record."""
    parties = [
        _party("SENDER", txn.get("sender_account_id"),
               txn.get("sender_name"), "sender_account_id"),
        _party("RECIPIENT", txn.get("receiver_account_id"),
               txn.get("receiver_name"), "receiver_account_id"),
    ]
    if txn.get("merchant_id"):
        parties.append(_party("MERCHANT", txn.get("merchant_id"),
                              txn.get("merchant_name"), "merchant_id"))
    return parties


def reveal(party: dict[str, Any], full_ref: str | None) -> dict[str, Any]:
    """Sensitive view. Callers must enforce the reveal permission + audit."""
    row = dict(party)
    row["reference_full"] = full_ref
    row["disclosure"] = "restricted: authorized reveal, audited"
    return row


def resolve(ref_a: dict[str, Any], ref_b: dict[str, Any]) -> dict[str, Any]:
    """Evidence-based entity resolution between two identifier dicts.

    Each dict maps identifier-field -> value. Returns a decision with the
    method, evidence, confidence, conflicts, and human-review flag.
    """
    evidence: list[str] = []
    conflicts: list[str] = []
    for field in AUTHORIZED_ID_FIELDS:
        val_a, val_b = ref_a.get(field), ref_b.get(field)
        if val_a and val_b:
            if val_a == val_b:
                evidence.append("exact match on %s" % field)
            else:
                conflicts.append("different %s values" % field)
    if evidence and not conflicts:
        return {"decision": "RESOLVED", "method": "exact-authorized-identifier",
                "evidence": evidence, "conflicts": conflicts,
                "confidence": "high: identical authorized identifiers",
                "human_review": False}
    if evidence and conflicts:
        return {"decision": "AMBIGUOUS",
                "method": "exact-authorized-identifier",
                "evidence": evidence, "conflicts": conflicts,
                "confidence": "conflicting authorized identifiers",
                "human_review": True}
    support = [f for f in _SUPPORT_FIELDS
               if ref_a.get(f) and ref_a.get(f) == ref_b.get(f)]
    if support:
        return {"decision": "SUPPORTED_ONLY",
                "method": "shared-signal-support",
                "evidence": ["shared %s" % f for f in support],
                "conflicts": conflicts,
                "confidence": "low: shared signals are not identity proof",
                "human_review": True}
    return {"decision": "NO_MATCH", "method": "no-common-evidence",
            "evidence": [], "conflicts": conflicts,
            "confidence": "no shared identifiers",
            "human_review": False}
