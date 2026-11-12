"""Financial institution / payment-network registry (UFI section 07).

The registry seeds payment NETWORKS/RAILS (public-knowledge entities), not
specific banks: no subscriber or institutional account data exists in this
repository, so per-bank records would be fabrication. Integration status is
resolved against the live connector registry; anything without a connector
is NOT_INTEGRATED.
"""
from __future__ import annotations

from typing import Any

try:
    from app import connectors as _connectors
except Exception:  # pragma: no cover - registry stays usable standalone
    _connectors = None  # type: ignore


def _network(ident: str, name: str, kind: str, countries: tuple[str, ...],
             methods: tuple[str, ...], connector: str | None = None,
             note: str = "") -> dict[str, Any]:
    return {
        "institution_id": ident, "name": name, "institution_type": kind,
        "countries": list(countries), "payment_methods": list(methods),
        "connector_id": connector, "provenance": "public-knowledge",
        "note": note,
    }


NETWORKS: tuple[dict[str, Any], ...] = (
    _network("net_nip", "NIP (Nigeria Instant Payments)", "rail",
             ("NG",), ("nip_instant",)),
    _network("net_visa", "Visa", "card-network", ("GLOBAL",),
             ("card_present", "card_not_present")),
    _network("net_mastercard", "Mastercard", "card-network", ("GLOBAL",),
             ("card_present", "card_not_present")),
    _network("net_verve", "Verve", "card-network", ("NG",),
             ("card_present", "card_not_present")),
    _network("net_swift", "SWIFT messaging", "messaging", ("GLOBAL",),
             ("wire_swift",),
             note="Message layer only; no live integration."),
    _network("net_btc", "Bitcoin network", "chain", ("GLOBAL",),
             ("crypto_onchain",)),
    _network("net_eth", "Ethereum network", "chain", ("GLOBAL",),
             ("crypto_onchain", "stablecoin")),
    _network("net_ussd", "USSD / mobile-money rails", "rail", ("NG",),
             ("mobile_money", "mobile_wallet")),
)

_BY_ID = {n["institution_id"]: n for n in NETWORKS}


def _integration_status(connector_id: str | None) -> str:
    if not connector_id or _connectors is None:
        return "NOT_INTEGRATED"
    try:
        available = {c.get("id") for c in _connectors.registry()}
    except Exception:
        return "NOT_INTEGRATED"
    return "REGISTERED" if connector_id in available else "NOT_INTEGRATED"


def list_networks() -> list[dict[str, Any]]:
    rows = []
    for entry in NETWORKS:
        row = dict(entry)
        row["integration_status"] = _integration_status(
            entry["connector_id"])
        row["verification_status"] = "UNVERIFIED"
        rows.append(row)
    return rows


def get_network(institution_id: str) -> dict[str, Any] | None:
    found = _BY_ID.get(institution_id)
    if not found:
        return None
    row = dict(found)
    row["integration_status"] = _integration_status(found["connector_id"])
    row["verification_status"] = "UNVERIFIED"
    return row


def identify(txn: dict[str, Any]) -> dict[str, Any]:
    """Identify the processing network for a transaction, if evidenced."""
    reported = txn.get("network")
    if isinstance(reported, str) and reported:
        match = next(
            (n for n in NETWORKS
             if n["name"].lower() == reported.strip().lower()
             or n["institution_id"] == reported.strip().lower()),
            None,
        )
        if match:
            return {"institution_id": match["institution_id"],
                    "confidence": "provider-reported",
                    "explanation": "Network supplied by the source record."}
        return {"institution_id": "UNKNOWN", "confidence": "unclassified",
                "explanation": "Reported network '%s' is not in the "
                               "registry; left UNKNOWN." % reported}
    return {"institution_id": "UNKNOWN", "confidence": "unclassified",
            "explanation": "No network evidence on the record."}
