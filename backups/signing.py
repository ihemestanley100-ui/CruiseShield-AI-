"""Manifest signing with Ed25519 in minisign layout (Phase 5.4F/P1).

All signatures are libsodium Ed25519 via PyNaCl; this module only encodes
the minisign file layout: untrusted comment, base64 signature packet
(tag + keynum + 64-byte signature), trusted comment, and base64 global
line carrying the bare 64-byte global signature over
message-signature + trusted comment (P2.2C: matches the reference CLI
exactly; pre-P2.2C builds wrongly wrote a 74-byte global packet and are
rejected outright, never reinterpreted).

Our key numbers are deterministic (sha256(vk)[:8]); reference-CLI keys
carry random key numbers, accepted via verify_message's expected_key_id
taken from the trusted .pub. The CLI verifies legacy "Ed" signatures
by default; "ED"-prehashed CLI signatures remain out of scope.

INTEROP VERIFIED (P2.2C, 2026-10-30, minisign CLI 0.12 win64,
synthetic fixtures): Python sign -> CLI -V exits 0 with the trusted
comment; CLI -S -l -> verify_message accepts with the CLI .pub keynum;
tampered bytes, wrong keys, and corrupted signatures are rejected by
both sides. Findings that drove the P2.2C correction (74-byte global
line, CLI-random keynums) are recorded in the phase report.
"""
from __future__ import annotations

import base64
import hashlib

from nacl.exceptions import BadSignatureError as _NaclBadSig
from nacl.signing import SigningKey, VerifyKey

SIGALG = b"Ed"  # minisign Ed25519 algorithm identifier
KEYNUM_LEN = 8


class SignatureError(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code


def generate_signing_keypair() -> tuple[bytes, bytes]:
    """Fresh Ed25519 (seed32, verifykey32) from the OS CSPRNG."""
    signing = SigningKey.generate()
    return bytes(signing), bytes(signing.verify_key)


def key_id(verify_key: bytes) -> bytes:
    """Deterministic 8-byte key id: sha256(verifykey)[:8]."""
    if len(verify_key) != 32:
        raise SignatureError("BAD_VERIFY_KEY", f"len={len(verify_key)}")
    return hashlib.sha256(verify_key).digest()[:KEYNUM_LEN]


def fingerprint(verify_key: bytes) -> str:
    """Non-secret signing-key fingerprint (matches crypto.fingerprint)."""
    if len(verify_key) != 32:
        raise SignatureError("BAD_VERIFY_KEY", f"len={len(verify_key)}")
    return hashlib.sha256(verify_key).hexdigest()[:32]


def sign_message(message: bytes, seed: bytes, trusted_comment: str,
                 untrusted_comment: str = "signature from cruiseshield") -> str:
    """Sign a message; returns the minisign-layout signature document."""
    if len(seed) != 32:
        raise SignatureError("BAD_SEED", f"len={len(seed)}")
    if "\n" in trusted_comment or "\n" in untrusted_comment:
        raise SignatureError("BAD_COMMENT", "comments must be single-line")
    signing = SigningKey(seed)
    verify_key = bytes(signing.verify_key)
    keynum = key_id(verify_key)
    signature = signing.sign(message).signature
    trusted = trusted_comment.encode("utf-8")
    global_sig = signing.sign(signature + trusted).signature
    packet = base64.b64encode(SIGALG + keynum + signature).decode("ascii")
    # The global line is the bare 64-byte signature (no tag/keynum),
    # exactly as the reference CLI encodes and parses it (P2.2C).
    global_line = base64.b64encode(global_sig).decode("ascii")
    return (f"untrusted comment: {untrusted_comment}\n{packet}\n"
            f"trusted comment: {trusted_comment}\n{global_line}\n")


def verify_message(message: bytes, signature_doc: str,
                   verify_key: bytes,
                   expected_key_id: bytes | None = None) -> str:
    """Verify a signature document; returns the trusted comment.

    Raises SignatureError on any tampering, wrong key, or bad format.
    ``verify_key`` is explicitly trusted caller material, never taken
    from the document. ``expected_key_id`` selects the trusted key
    number: ours are deterministic (sha256(vk)[:8], the default), while
    reference-CLI keys carry the random keynum from their trusted .pub,
    which the caller supplies for CLI-issued signatures.
    """
    if len(verify_key) != 32:
        raise SignatureError("BAD_VERIFY_KEY", f"len={len(verify_key)}")
    if expected_key_id is None:
        expected_key_id = key_id(verify_key)
    if len(expected_key_id) != KEYNUM_LEN:
        raise SignatureError("BAD_KEY_ID", f"len={len(expected_key_id)}")
    lines = signature_doc.splitlines()
    if (len(lines) != 4 or not lines[0].startswith("untrusted comment: ")
            or not lines[2].startswith("trusted comment: ")):
        raise SignatureError("BAD_SIGNATURE_DOC", "layout mismatch")
    try:
        packet = base64.b64decode(lines[1], validate=True)
        global_sig = base64.b64decode(lines[3], validate=True)
    except Exception as exc:
        raise SignatureError("BAD_SIGNATURE_DOC", "bad base64") from None
    trusted_comment = lines[2][len("trusted comment: "):]
    trusted = trusted_comment.encode("utf-8")
    if len(packet) != 2 + KEYNUM_LEN + 64 or packet[:2] != SIGALG:
        raise SignatureError("BAD_SIGNATURE_DOC", "bad packet shape")
    if packet[2:10] != expected_key_id:
        raise SignatureError("KEY_MISMATCH", "packet key id mismatch")
    if len(global_sig) != 64:
        raise SignatureError("BAD_SIGNATURE_DOC", "bad global shape")
    verifier = VerifyKey(verify_key)
    try:
        verifier.verify(global_sig + packet[10:] + trusted)
    except _NaclBadSig:
        raise SignatureError("VERIFY_FAILED",
                             "global signature invalid") from None
    try:
        verifier.verify(packet[10:] + message)
    except _NaclBadSig:
        raise SignatureError("VERIFY_FAILED",
                             "message signature invalid") from None
    return trusted_comment


def public_key_document(verify_key: bytes,
                        untrusted_comment: str = "csbk signing key") -> str:
    """Minisign-layout public key document (safe to publish)."""
    if len(verify_key) != 32:
        raise SignatureError("BAD_VERIFY_KEY", f"len={len(verify_key)}")
    packet = base64.b64encode(
        SIGALG + key_id(verify_key) + verify_key).decode("ascii")
    return f"untrusted comment: {untrusted_comment}\n{packet}\n"
