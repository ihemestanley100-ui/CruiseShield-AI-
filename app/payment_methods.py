"""Canonical payment-method taxonomy + traceability registry (UFI payment core).

Every method carries its family (A-I per directive section 05), instrument
type, known networks, channel hints, and an honest traceability record.
Classification never invents a method: provider-reported ids must exist in
the registry, channel hints are labelled inferred-from-channel, and anything
else stays UNKNOWN.
"""
from __future__ import annotations

from typing import Any

FAMILIES = {
    "A": "Bank and account payments",
    "B": "Cards",
    "C": "Digital wallets",
    "D": "Cryptocurrency and digital assets",
    "E": "Gift cards and vouchers",
    "F": "International money transfer",
    "G": "Mobile money",
    "H": "Merchant and alternative payments",
    "I": "Cash and physical-value transactions",
}

LIFECYCLE = (
    "INITIATED", "AUTHORIZED", "DECLINED", "PENDING", "PROCESSED",
    "CLEARED", "SETTLED", "FAILED", "REVERSED", "REFUNDED",
    "CANCELLED", "DISPUTED", "CHARGEBACK", "PAYOUT_COMPLETED",
)


def _method(ident: str, name: str, family: str, instrument: str,
            networks: tuple[str, ...] = (),
            channels: tuple[str, ...] = (),
            sender: str = "provider-dependent",
            recipient: str = "provider-dependent",
            history: str = "provider-dependent",
            reversal: str = "provider-dependent",
            limitations: tuple[str, ...] = ()) -> dict[str, Any]:
    return {
        "method_id": ident, "name": name, "family": family,
        "family_label": FAMILIES[family], "instrument_type": instrument,
        "networks": list(networks), "channel_hints": list(channels),
        "traceability": {
            "sender_information": sender,
            "recipient_information": recipient,
            "transaction_history": history,
            "reversal_refund_support": reversal,
            "limitations": list(limitations) or [
                "Tracing capability depends on the authorizing provider; "
                "unavailable fields stay null.",
            ],
        },
    }


METHODS: tuple[dict[str, Any], ...] = (
    _method("bank_transfer", "Bank transfer", "A", "account",
            channels=("TRANSFER", "NIP"),
            history="bank-statement/rail records where authorized",
            reversal="recall rules vary by rail; confirmation required"),
    _method("nip_instant", "NIP instant payment", "A", "account",
            networks=("NIP",), channels=("NIP",),
            reversal="limited; requires receiving-institution confirmation"),
    _method("wire_swift", "Wire / SWIFT-message payment", "A", "account",
            networks=("SWIFT",),
            history="message copies where the institution participates",
            limitations=("No live SWIFT integration; message data only from "
                          "authorized supplied records.",)),
    _method("card_present", "Card-present payment", "B", "card",
            networks=("VISA", "MASTERCARD", "VERVE"),
            channels=("POS", "ATM"),
            reversal="chargeback process via acquirer/issuer"),
    _method("card_not_present", "Card-not-present payment", "B", "card",
            networks=("VISA", "MASTERCARD", "VERVE"), channels=("WEB",),
            reversal="chargeback process via acquirer/issuer"),
    _method("mobile_wallet", "Mobile wallet transfer", "C", "wallet",
            channels=("MOBILE_APP", "USSD", "AGENT"),
            history="wallet-provider ledger where authorized"),
    _method("crypto_onchain", "On-chain crypto transfer", "D", "crypto",
            networks=("BTC", "ETH"),
            sender="pseudonymous address unless provider attribution exists",
            recipient="pseudonymous address unless provider attribution exists",
            history="public chain data for supported networks",
            reversal="generally irreversible on-chain",
            limitations=("Address ownership is UNKNOWN without provider "
                          "attribution or verified customer identity.",)),
    _method("stablecoin", "Stablecoin transfer", "D", "crypto",
            networks=("USDT", "USDC"),
            sender="pseudonymous address unless provider attribution exists",
            recipient="pseudonymous address unless provider attribution exists",
            history="public chain data for supported networks",
            reversal="generally irreversible on-chain"),
    _method("gift_card", "Gift card / voucher event", "E", "voucher",
            sender="purchaser record where issuer participates",
            recipient="redemption record; final holder often unknown",
            history="issuer ledger where authorized",
            reversal="issuer policy; codes never exposed",
            limitations=("Purchase records do not reveal the final "
                          "recipient.",)),
    _method("remittance", "Money-transfer payout", "F", "remittance",
            channels=("AGENT",),
            sender="provider-supplied sender record",
            recipient="provider-supplied recipient record",
            history="provider transfer reference trail",
            reversal="cancellation rules vary by provider and payout state",
            limitations=("No live remittance provider; records only from "
                          "authorized supplied data.",)),
    _method("mobile_money", "Mobile-money transfer", "G", "wallet",
            channels=("USSD", "MOBILE_APP", "AGENT"),
            history="operator ledger where authorized"),
    _method("qr_checkout", "QR / payment-link checkout", "H", "merchant",
            channels=("POS", "WEB", "QR"),
            history="gateway/merchant records where authorized"),
    _method("cash", "Cash event", "I", "cash",
            channels=("ATM", "AGENT"),
            sender="rarely recorded", recipient="rarely recorded",
            history="terminal/agent journal where available",
            reversal="not applicable once handed over",
            limitations=("Cash legs break deterministic tracing; links "
                          "beyond cash stay UNVERIFIED.",)),
)

_BY_ID = {m["method_id"]: m for m in METHODS}

_CHANNEL_DEFAULT = {
    "POS": "card_present", "ATM": "card_present", "NIP": "nip_instant",
    "TRANSFER": "bank_transfer", "WEB": "card_not_present",
    "MOBILE_APP": "mobile_wallet", "USSD": "mobile_money",
    "QR": "qr_checkout",
    "AGENT": "mobile_money",
}

# Provider status -> canonical lifecycle. Unknown providers pass through with
# the original value preserved; nothing is forced into the canonical set.
_PROVIDER_STATUS = {
    ("nip", "successful"): "SETTLED",
    ("nip", "failed"): "FAILED",
    ("nip", "pending"): "PENDING",
    ("card", "approved"): "AUTHORIZED",
    ("card", "declined"): "DECLINED",
    ("card", "settled"): "SETTLED",
    ("card", "chargeback"): "CHARGEBACK",
    ("chain", "confirmed"): "SETTLED",
    ("chain", "pending"): "PENDING",
    ("chain", "dropped"): "FAILED",
}


def list_methods() -> list[dict[str, Any]]:
    return [dict(m) for m in METHODS]


def get_method(method_id: str) -> dict[str, Any] | None:
    found = _BY_ID.get(method_id)
    return dict(found) if found else None


def classify(txn: dict[str, Any]) -> dict[str, Any]:
    """Classify a transaction's payment method. Honest by construction."""
    reported = txn.get("payment_method")
    if isinstance(reported, str) and reported in _BY_ID:
        return {"method_id": reported, "confidence": "provider-reported",
                "explanation": "Method id supplied by the source record."}
    if isinstance(reported, str) and reported:
        return {"method_id": "UNKNOWN", "confidence": "unclassified",
                "explanation": "Reported method '%s' is not in the canonical "
                               "registry; left UNKNOWN." % reported}
    channel = txn.get("channel")
    if isinstance(channel, str) and channel in _CHANNEL_DEFAULT:
        return {"method_id": _CHANNEL_DEFAULT[channel],
                "confidence": "inferred-from-channel",
                "explanation": "Channel %s maps to a default method; treat "
                               "as a hint, not proof of rail." % channel}
    return {"method_id": "UNKNOWN", "confidence": "unclassified",
            "explanation": "No usable method or channel evidence."}


def map_lifecycle(provider: str | None, status: str | None) -> dict[str, Any]:
    """Map a provider status to canonical lifecycle, preserving originals."""
    key = ((provider or "").strip().lower(), (status or "").strip().lower())
    canonical = _PROVIDER_STATUS.get(key)
    if canonical:
        return {"canonical": canonical, "provider": provider,
                "provider_status": status, "mapped": True}
    return {"canonical": "UNKNOWN", "provider": provider,
            "provider_status": status, "mapped": False,
            "note": "Status preserved verbatim; no canonical mapping."}
