"""Threshold recovery shares (Phase 5.4F/P1, CEREMONY USE ONLY).

SLIP-39 Shamir sharing via the maintained Trezor `shamir-mnemonic`
reference library. Single-group configuration only (plain 2-of-N).
This module must NEVER be imported by producer/restore automation:
shares exist on paper, in sealed envelopes, handled by humans.
(A test enforces that no automation module imports this one.)

Secrets in = secrets out. Errors never echo share or secret material.
"""
from __future__ import annotations

from shamir_mnemonic import shamir as _shamir

MAX_SHARES = 16


class ShareError(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code


def split_secret(master_secret: bytes, *, threshold: int,
                 share_count: int) -> list[str]:
    """Split a secret into mnemonic shares (single 2-of-N group).

    Returns share_count SLIP-39 mnemonics; any `threshold` of them
    recombine. Use ONLY in the witnessed key ceremony with TEST secrets
    here; production ceremony needs its own authorization.
    """
    if not 1 <= threshold <= share_count <= MAX_SHARES:
        raise ShareError("BAD_THRESHOLD",
                         f"need 1<=t<=n<={MAX_SHARES}")
    if not 16 <= len(master_secret) <= 64:
        raise ShareError("BAD_SECRET_LEN", f"len={len(master_secret)}")
    try:
        groups = _shamir.generate_mnemonics(
            1, [(threshold, share_count)], master_secret)
    except Exception as exc:
        raise ShareError("SPLIT_FAILED", type(exc).__name__) from None
    return list(groups[0])


def combine_shares(mnemonics: list[str]) -> bytes:
    """Recombine mnemonic shares into the master secret. Fails closed."""
    if len(mnemonics) < 1:
        raise ShareError("NO_SHARES", "at least one mnemonic required")
    try:
        return bytes(_shamir.combine_mnemonics(mnemonics))
    except Exception as exc:
        raise ShareError("COMBINE_FAILED", type(exc).__name__) from None
