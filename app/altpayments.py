"""Crypto / gift-card / remittance adapters (UFI sections 11-13).

Provider-neutral and honest: format validation reuses the existing web3
validators; every provider operation reports PROVIDER_UNAVAILABLE until a
connector is configured. Wallet/entity attribution distinguishes
PUBLIC_ON_CHAIN_DATA (structure only, no chain access here),
PROVIDER_ATTRIBUTED_ENTITY, VERIFIED_CUSTOMER_IDENTITY, INFERRED_ENTITY
(never emitted by this module), and UNKNOWN_ENTITY.
"""
from __future__ import annotations

from typing import Any

from app import web3 as _web3

ATTRIBUTION = (
    "PUBLIC_ON_CHAIN_DATA", "PROVIDER_ATTRIBUTED_ENTITY",
    "VERIFIED_CUSTOMER_IDENTITY", "INFERRED_ENTITY", "UNKNOWN_ENTITY",
)


def capabilities() -> dict[str, Any]:
    """Honest capability document for the three alternative rails."""
    return {
        "crypto": {
            "address_validation": "AVAILABLE",
            "hash_validation": "AVAILABLE",
            "chain_data": "PROVIDER_UNAVAILABLE",
            "attribution": "UNKNOWN_ENTITY unless provider evidence supplied",
        },
        "gift_card": {
            "record_ingest": "AVAILABLE",
            "issuer_lookup": "PROVIDER_UNAVAILABLE",
            "code_handling": "codes never stored or displayed",
        },
        "remittance": {
            "record_ingest": "AVAILABLE",
            "provider_lookup": "PROVIDER_UNAVAILABLE",
        },
    }


def validate_crypto_transfer(chain: str, address: str,
                             tx_hash: str | None = None) -> dict[str, Any]:
    """Validate formats only; returns UNKNOWN_ENTITY attribution."""
    chain_result = _web3.validate_address(chain, address)
    result: dict[str, Any] = {
        "chain": chain, "address": address,
        "address_validation": chain_result,
        "attribution": "UNKNOWN_ENTITY",
        "attribution_note": "An address alone never identifies its owner.",
    }
    if tx_hash is not None:
        result["hash_validation"] = _web3.validate_tx_hash(tx_hash)
    return result


def gift_card_event(issuer: str, event_type: str, reference: str,
                    value_minor: int | None = None,
                    currency: str | None = None) -> dict[str, Any]:
    """Build an issuer-record event. Redemption secrets are rejected."""
    if event_type not in ("PURCHASE", "REDEMPTION", "RESALE", "BALANCE_EVENT"):
        raise ValueError("GIFT_EVENT_UNKNOWN: %s" % event_type)
    lowered = reference.lower()
    if any(token in lowered for token in ("code:", "pin:", "secret")):
        raise ValueError("GIFT_SECRET_REJECTED")
    return {
        "issuer": issuer, "event_type": event_type, "reference": reference,
        "value_minor": value_minor, "currency": currency,
        "final_recipient": "UNKNOWN",
        "note": "Purchase records do not reveal the final recipient.",
    }


def remittance_event(provider: str, transfer_reference: str,
                     status: str, amount_minor: int | None = None,
                     currency: str | None = None) -> dict[str, Any]:
    """Build a provider-supplied remittance record."""
    if status not in ("SENT", "IN_TRANSIT", "AVAILABLE_FOR_PICKUP",
                      "PAYOUT_COMPLETED", "CANCELLED", "REVERSED"):
        raise ValueError("REMITTANCE_STATUS_UNKNOWN: %s" % status)
    return {
        "provider": provider, "transfer_reference": transfer_reference,
        "status": status, "amount_minor": amount_minor,
        "currency": currency,
        "provenance": "provider-supplied record; no live lookup",
    }
