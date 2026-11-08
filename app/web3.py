"""Isolated Web3 payment adapter (Phase 5, D-041).

No chain client, no custody. Records stablecoin-transfer intents and
operator-supplied tx hashes. Nothing here derives keys, signs,
broadcasts, or polls a chain: on-chain confirmation needs a provider
decision and stays explicitly unverified.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

SUPPORTED_ASSETS = ("USDC", "USDT")
SUPPORTED_CHAINS = ("ethereum", "base", "polygon")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _is_hex(text: str, length: int) -> bool:
    clean = text[2:] if text.startswith("0x") else None
    if clean is None or len(clean) != length:
        return False
    try:
        int(clean, 16)
        return True
    except (ValueError, TypeError):
        return False


def validate_address(chain: str, address: str) -> str:
    """EVM address shape check (no chain lookup is performed)."""
    if chain not in SUPPORTED_CHAINS:
        raise ValueError("WEB3_CHAIN_UNSUPPORTED: %s" % (chain,))
    clean = (address or "").strip()
    if not _is_hex(clean, 40):
        raise ValueError("WEB3_ADDRESS_INVALID: 0x + 40 hex chars")
    return clean


def validate_tx_hash(tx_hash: str) -> str:
    """Tx-hash shape check (inclusion is never verified here)."""
    clean = (tx_hash or "").strip()
    if not _is_hex(clean, 64):
        raise ValueError("WEB3_TX_INVALID: 0x + 64 hex chars")
    return clean


def prepare_transfer(store, username: str, asset: str, chain: str,
                     amount: int, address: str) -> dict[str, Any]:
    """Record a stablecoin intent (minor units; nothing broadcasts)."""
    if asset not in SUPPORTED_ASSETS:
        raise ValueError("WEB3_ASSET_UNSUPPORTED: %s" % (asset,))
    clean_address = validate_address(chain, address)
    if not isinstance(amount, int) or isinstance(amount, bool) \
            or amount <= 0:
        raise ValueError("AMOUNT_INVALID: positive integer minor units")
    store.state["web3_seq"] = int(store.state.get("web3_seq", 0)) + 1
    rec = {"payment_id": "w3_%04d" % store.state["web3_seq"],
           "kind": "web3", "user": username, "asset": asset,
           "chain": chain, "amount": amount, "address": clean_address,
           "status": "awaiting_tx", "tx_hash": "", "confirmations": 0,
           "created_at": _now()}
    store.save_payment(rec)
    return rec


def record_tx(store, payment_id: str, tx_hash: str) -> dict[str, Any]:
    """Attach an operator-supplied tx hash (stays unverified)."""
    rec = store.payment(payment_id)
    if rec is None or rec.get("kind") != "web3":
        raise ValueError("PAYMENT_NOT_FOUND: %s" % payment_id)
    if rec.get("status") != "awaiting_tx":
        raise ValueError("WEB3_TX_LATE: intent is %s"
                         % rec.get("status"))
    rec["tx_hash"] = validate_tx_hash(tx_hash)
    rec["status"] = "awaiting_confirmations"
    store._save()
    return rec


def refund_policy() -> dict[str, str]:
    """Operator-only refunds; the platform never holds keys or funds."""
    return {"refunds": "manual-operator-only",
            "custody": "none — platform never holds keys or funds"}
