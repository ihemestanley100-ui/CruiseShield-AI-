"""Authenticated multi-recipient backup encryption (Phase 5.4F/P1).

CRYPTOGRAPHIC SPECIFICATION (P1.2, accepted wording pending user sign-off):
- Algorithms: X25519 key agreement + XSalsa20-Poly1305 AEAD, exactly as
  implemented by libsodium's crypto_box via PyNaCl. No custom algorithms,
  no custom modes, no hand-rolled KDF (NaCl internals: HSalsa20 key
  derivation; Box.encrypt draws a fresh random nonce per call).
- Envelope: custom versioned format CSBK1: b"CSBK1" + version(1B, =1) +
  nrecipients(1B, 1..16) + per-recipient stanzas of eph_pubkey(32B) +
  sealed_len(4B big-endian) + sealed(nonce24 + ciphertext+tag). Each
  stanza uses a FRESH ephemeral X25519 keypair, so every recipient of
  every backup gets a unique DEK. Multi-recipient = full ciphertext per
  recipient (simple; ~2x bytes at backup scale, acceptable by design).
- Explicit NON-CLAIMS: no age CLI interoperability; no age-format
  compatibility. This module was specified against age v1 (5.4E.2), but
  the only pip-installable Python age ("age" 0.5.1/pyage) declares itself
  experimental and not secure (verified on PyPI 2026-10-30), so NaCl was
  substituted with equivalent security properties and a different wire
  format. This substitution requires explicit user acceptance (P1.1).
- Future age migration path: the version byte reserves it. A future
  envelope version may carry age-format stanzas; decryptors then try
  CSBK1 stanzas first and age stanzas second (dual-decrypt), with
  re-encryption of the newest verified generation at cutover. Not
  implemented; no code here anticipates it beyond the version byte.
- Security assumptions: OS CSPRNG sound; libsodium/PyNaCl sound;
  recipients' private keys confidential; at most MAX_RECIPIENTS-1
  recipients malicious (a malicious recipient learns the plaintext they
  were legitimately given - no cross-recipient leakage by construction).
- Limitations: no forward secrecy across backups sharing one KEK (KEK
  rotation bounds exposure); no deniability analysis performed (not
  required); interop limited to NaCl implementations + this layout doc.
- Errors never include key material or plaintext.
"""
from __future__ import annotations

import hashlib
import struct

from nacl.bindings import crypto_box_PUBLICKEYBYTES as PUB_LEN
from nacl.exceptions import CryptoError as _NaclCryptoError
from nacl.public import Box, PrivateKey, PublicKey

MAGIC = b"CSBK1"
VERSION = 1
MAX_RECIPIENTS = 16


class CryptoError(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code


def generate_keypair() -> tuple[bytes, bytes]:
    """Fresh X25519 (private32, public32) from the OS CSPRNG."""
    private = PrivateKey.generate()
    return bytes(private), bytes(private.public_key)


def fingerprint(public_key: bytes) -> str:
    """Non-secret key fingerprint: sha256(pubkey) hex, first 32 chars."""
    if len(public_key) != PUB_LEN:
        raise CryptoError("BAD_PUBLIC_KEY", f"len={len(public_key)}")
    return hashlib.sha256(public_key).hexdigest()[:32]


def encrypt_bytes(plaintext: bytes,
                  recipient_pubkeys: list[bytes]) -> bytes:
    """Seal plaintext to 1..16 recipients (fresh ephemeral DEK each)."""
    if not 1 <= len(recipient_pubkeys) <= MAX_RECIPIENTS:
        raise CryptoError("BAD_RECIPIENT_COUNT",
                          f"n={len(recipient_pubkeys)}")
    for pub in recipient_pubkeys:
        if len(pub) != PUB_LEN:
            raise CryptoError("BAD_PUBLIC_KEY", f"len={len(pub)}")
    out = bytearray(MAGIC + bytes([VERSION, len(recipient_pubkeys)]))
    for pub in recipient_pubkeys:
        ephemeral = PrivateKey.generate()
        sealed = Box(ephemeral, PublicKey(pub)).encrypt(plaintext)
        stanza = bytes(ephemeral.public_key) + struct.pack(">I", len(sealed))
        out += stanza + sealed
    return bytes(out)


def decrypt_bytes(envelope: bytes, private_key: bytes) -> bytes:
    """Open an envelope with one X25519 private key. Fails closed."""
    if len(private_key) != 32:
        raise CryptoError("BAD_PRIVATE_KEY", f"len={len(private_key)}")
    stanzas = _parse(envelope)
    identity = PrivateKey(private_key)
    for eph_pub, sealed in stanzas:
        try:
            return Box(identity, PublicKey(eph_pub)).decrypt(sealed)
        except _NaclCryptoError:
            continue
    raise CryptoError("DECRYPT_FAILED", "no stanza opened with this key")


def _parse(envelope: bytes) -> list[tuple[bytes, bytes]]:
    if len(envelope) < 7 or envelope[:5] != MAGIC:
        raise CryptoError("BAD_ENVELOPE", "bad magic")
    if envelope[5] != VERSION:
        raise CryptoError("BAD_ENVELOPE_VERSION", f"v={envelope[5]}")
    count = envelope[6]
    if not 1 <= count <= MAX_RECIPIENTS:
        raise CryptoError("BAD_ENVELOPE", f"nrecipients={count}")
    stanzas: list[tuple[bytes, bytes]] = []
    offset = 7
    for _ in range(count):
        if len(envelope) < offset + 36:
            raise CryptoError("BAD_ENVELOPE", "truncated stanza header")
        eph_pub = envelope[offset:offset + 32]
        (sealed_len,) = struct.unpack(">I", envelope[offset + 32:offset + 36])
        offset += 36
        if len(envelope) < offset + sealed_len:
            raise CryptoError("BAD_ENVELOPE", "truncated stanza body")
        stanzas.append((eph_pub, envelope[offset:offset + sealed_len]))
        offset += sealed_len
    if offset != len(envelope):
        raise CryptoError("BAD_ENVELOPE", "trailing bytes")
    return stanzas
