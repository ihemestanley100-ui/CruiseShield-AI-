"""Passkey/WebAuthn ceremonies (Phase 5, D-045). Default OFF.

Registration validates none + packed self-attestation; assertion
verifies ES256/EdDSA signatures with the cryptography package
(fail-closed when unavailable). Third-party attestation trust,
authenticator interop, and lock regen stay review-gated. Passkeys
replace the password, never a pending MFA requirement.
"""
from __future__ import annotations

import hashlib
import json
import secrets
import time
from typing import Any

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec, ed25519, utils
    _CRYPTO = True
except ImportError:  # pragma: no cover - environment lacks the package
    _CRYPTO = False

CHALLENGE_TTL_SECONDS = 300
SUPPORTED_ALGS = (-7, -8)
RP_NAME = "CruiseShield AI"


class PasskeyError(ValueError):
    """Ceremony failure; the message carries a CODE prefix."""


def _b64e(raw: bytes) -> str:
    from app.auth import b64e

    return b64e(raw)


def _b64d(text: str) -> bytes:
    from app.auth import b64d

    try:
        return b64d(str(text or ""))
    except (ValueError, TypeError):
        raise PasskeyError("RESPONSE_MALFORMED: bad base64url")


# -- minimal CBOR (definite lengths; ints/bytes/text/arrays/maps) ---------


def _cbor_uint(data: bytes, pos: int, info: int) -> tuple[int, int]:
    if info < 24:
        return info, pos
    width = {24: 1, 25: 2, 26: 4, 27: 8}.get(info)
    if width is None:
        raise PasskeyError("CBOR_UNSUPPORTED: indefinite/float")
    end = pos + width
    if end > len(data):
        raise PasskeyError("CBOR_TRUNCATED")
    return int.from_bytes(data[pos:end], "big"), end


def _cbor_item(data: bytes, pos: int) -> tuple[Any, int]:
    if pos >= len(data):
        raise PasskeyError("CBOR_TRUNCATED")
    major, info = data[pos] >> 5, data[pos] & 31
    pos += 1
    if major == 0:
        return _cbor_uint(data, pos, info)
    if major == 1:
        value, pos = _cbor_uint(data, pos, info)
        return -1 - value, pos
    if major in (2, 3):
        length, pos = _cbor_uint(data, pos, info)
        end = pos + length
        if end > len(data):
            raise PasskeyError("CBOR_TRUNCATED")
        raw = data[pos:end]
        if major == 3:
            try:
                return raw.decode("utf-8"), end
            except UnicodeDecodeError:
                raise PasskeyError("CBOR_BAD_TEXT")
        return raw, end
    if major == 4:
        length, pos = _cbor_uint(data, pos, info)
        items = []
        for _ in range(length):
            value, pos = _cbor_item(data, pos)
            items.append(value)
        return items, pos
    if major == 5:
        length, pos = _cbor_uint(data, pos, info)
        mapping: dict[Any, Any] = {}
        for _ in range(length):
            key, pos = _cbor_item(data, pos)
            if not isinstance(key, (int, str)):
                raise PasskeyError("CBOR_KEY_UNSUPPORTED")
            value, pos = _cbor_item(data, pos)
            mapping[key] = value
        return mapping, pos
    if major == 7:
        if info < 20:
            return info, pos
        if info in (20, 21):
            return info == 21, pos
        if info == 22:
            return None, pos
        raise PasskeyError("CBOR_UNSUPPORTED: simple/float")
    raise PasskeyError("CBOR_UNSUPPORTED: tag")


def cbor_decode(data: bytes) -> Any:
    """Decode one definite-length item; trailing bytes are rejected."""
    value, pos = _cbor_item(bytes(data), 0)
    if pos != len(data):
        raise PasskeyError("CBOR_TRAILING")
    return value


# -- authenticator data + COSE --------------------------------------------


def parse_auth_data(raw: bytes) -> dict[str, Any]:
    """Split rpIdHash/flags/count (+ attested credential when present)."""
    blob = bytes(raw or b"")
    if len(blob) < 37:
        raise PasskeyError("AUTH_DATA_SHORT")
    flags = blob[32]
    out: dict[str, Any] = {
        "rp_id_hash": blob[:32], "up": bool(flags & 0x01),
        "uv": bool(flags & 0x04), "at": bool(flags & 0x40),
        "sign_count": int.from_bytes(blob[33:37], "big"),
        "credential": None}
    pos = 37
    if out["at"]:
        if len(blob) < pos + 18:
            raise PasskeyError("AUTH_DATA_SHORT")
        id_len = int.from_bytes(blob[pos + 16:pos + 18], "big")
        pos += 18
        cred_id = blob[pos:pos + id_len]
        pos += id_len
        if len(cred_id) != id_len:
            raise PasskeyError("AUTH_DATA_SHORT")
        cose, _end = _cbor_item(blob, pos)
        if not isinstance(cose, dict):
            raise PasskeyError("COSE_NOT_MAP")
        out["credential"] = {"id": cred_id, "cose": cose}
    return out


def parse_cose_key(cose: dict) -> dict[str, Any]:
    """Accept ES256 (P-256) and EdDSA (Ed25519) keys only."""
    if not isinstance(cose, dict):
        raise PasskeyError("KEY_UNSUPPORTED: not a map")
    kty, alg = cose.get(1), cose.get(3)
    if alg == -7 and kty == 2 and cose.get(-1) == 1:
        x, y = cose.get(-2), cose.get(-3)
        if (isinstance(x, bytes) and isinstance(y, bytes)
                and len(x) == 32 and len(y) == 32):
            return {"alg": -7, "x": x, "y": y}
    elif alg == -8 and kty == 1 and cose.get(-1) == 6:
        x = cose.get(-2)
        if isinstance(x, bytes) and len(x) == 32:
            return {"alg": -8, "x": x}
    raise PasskeyError("KEY_UNSUPPORTED: only ES256/Ed25519")


def verify_signature(key: dict[str, Any], data: bytes,
                     sig: bytes) -> bool:
    """ECDSA/EdDSA check (never raises; False without the package)."""
    if not _CRYPTO:
        return False
    try:
        if key.get("alg") == -7:
            if len(bytes(sig)) != 64:
                return False
            numbers = ec.EllipticCurvePublicNumbers(
                int.from_bytes(key["x"], "big"),
                int.from_bytes(key["y"], "big"), ec.SECP256R1())
            der = utils.encode_dss_signature(
                int.from_bytes(bytes(sig[:32]), "big"),
                int.from_bytes(bytes(sig[32:]), "big"))
            numbers.public_key().verify(
                der, bytes(data), ec.ECDSA(hashes.SHA256()))
            return True
        if key.get("alg") == -8:
            ed25519.Ed25519PublicKey.from_public_bytes(
                bytes(key["x"])).verify(bytes(sig), bytes(data))
            return True
        return False
    except (InvalidSignature, ValueError):
        return False


# -- challenges + ceremonies ----------------------------------------------


def _challenge(store, username: str, purpose: str) -> tuple[str, str]:
    cid = secrets.token_hex(16)
    raw = _b64e(secrets.token_bytes(32))
    store.save_passkey_challenge(
        cid, {"user": username, "purpose": purpose, "challenge": raw,
              "exp": time.time() + CHALLENGE_TTL_SECONDS})
    return cid, raw


def _take_challenge(store, cid: str, username: str,
                    purpose: str) -> dict[str, Any]:
    rec = store.take_passkey_challenge(cid or "")
    if rec is None:
        raise PasskeyError("CHALLENGE_UNKNOWN: spent or unknown")
    if rec.get("user") != username or rec.get("purpose") != purpose:
        raise PasskeyError("CHALLENGE_FOREIGN")
    if float(rec.get("exp", 0)) < time.time():
        raise PasskeyError("CHALLENGE_EXPIRED")
    return rec


def _client_data_hash(raw: bytes, expected_type: str, challenge: str,
                      origin: str) -> bytes:
    try:
        data = json.loads(bytes(raw).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise PasskeyError("CLIENT_DATA_MALFORMED")
    if not isinstance(data, dict) or data.get("type") != expected_type:
        raise PasskeyError("CLIENT_DATA_TYPE")
    if data.get("challenge") != challenge:
        raise PasskeyError("CHALLENGE_MISMATCH")
    if data.get("origin") != origin:
        raise PasskeyError("ORIGIN_MISMATCH")
    return hashlib.sha256(bytes(raw)).digest()


def registration_options(store, username: str, display_name: str,
                         rp_id: str) -> dict[str, Any]:
    """PublicKeyCredentialCreationOptions + staged challenge id."""
    cid, challenge = _challenge(store, username, "register")
    existing = [{"type": "public-key", "id": c["credential_id"]}
                for c in store.passkeys_for(username)]
    return {
        "challenge_id": cid,
        "rp": {"id": rp_id, "name": RP_NAME},
        "user": {"id": _b64e(username.encode()), "name": username,
                 "displayName": display_name or username},
        "challenge": challenge,
        "pubKeyCredParams": [{"type": "public-key", "alg": alg}
                             for alg in SUPPORTED_ALGS],
        "timeout": 60000, "attestation": "none",
        "excludeCredentials": existing,
        "authenticatorSelection": {"userVerification": "preferred"}}


def verify_registration(store, username: str, response: dict[str, Any],
                        rp_id: str, rp_origin: str,
                        challenge_id: str) -> dict[str, Any]:
    """Validate a registration ceremony; store the credential."""
    if not isinstance(response, dict) or \
            response.get("type") != "public-key":
        raise PasskeyError("RESPONSE_TYPE")
    rec = _take_challenge(store, challenge_id, username, "register")
    inner = response.get("response")
    if not isinstance(inner, dict):
        raise PasskeyError("RESPONSE_MALFORMED")
    client_raw = _b64d(inner.get("clientDataJSON", ""))
    client_hash = _client_data_hash(client_raw, "webauthn.create",
                                    rec["challenge"], rp_origin)
    attestation = cbor_decode(_b64d(inner.get("attestationObject", "")))
    if not isinstance(attestation, dict):
        raise PasskeyError("ATTESTATION_MALFORMED")
    fmt = attestation.get("fmt")
    auth_data = parse_auth_data(attestation.get("authData", b""))
    if auth_data["rp_id_hash"] != hashlib.sha256(rp_id.encode()).digest():
        raise PasskeyError("RP_MISMATCH")
    if not auth_data["up"]:
        raise PasskeyError("USER_NOT_PRESENT")
    if not auth_data["at"] or auth_data["credential"] is None:
        raise PasskeyError("CREDENTIAL_MISSING")
    key = parse_cose_key(auth_data["credential"]["cose"])
    statement = attestation.get("attStmt")
    if fmt == "none":
        if statement != {}:
            raise PasskeyError("ATTESTATION_UNEXPECTED")
    elif fmt == "packed":
        if not isinstance(statement, dict):
            raise PasskeyError("ATTESTATION_MALFORMED")
        if "x5c" in statement:
            raise PasskeyError("ATTESTATION_CA_UNSUPPORTED")
        sig = statement.get("sig")
        if not isinstance(sig, bytes) or not verify_signature(
                key, attestation["authData"] + client_hash, sig):
            raise PasskeyError("ATTESTATION_SIG_INVALID")
    else:
        raise PasskeyError("ATTESTATION_UNSUPPORTED: %s" % (fmt,))
    credential_id = _b64e(auth_data["credential"]["id"])
    if store.passkey_credential(credential_id) is not None:
        raise PasskeyError("CREDENTIAL_DUPLICATE")
    return store.save_passkey_credential({
        "credential_id": credential_id, "user": username,
        "cose": {"alg": key["alg"], "x": _b64e(key["x"]),
                 "y": _b64e(key["y"]) if "y" in key else ""},
        "sign_count": auth_data["sign_count"], "created_at": time.time()})


def authentication_options(store, username: str) -> dict[str, Any]:
    """PublicKeyCredentialRequestOptions + staged challenge id."""
    allowed = [{"type": "public-key", "id": c["credential_id"]}
               for c in store.passkeys_for(username)]
    if not allowed:
        raise PasskeyError("CREDENTIALS_NONE")
    cid, challenge = _challenge(store, username, "authenticate")
    return {"challenge_id": cid, "challenge": challenge,
            "allowCredentials": allowed, "timeout": 60000,
            "userVerification": "preferred"}


def verify_assertion(store, username: str, response: dict[str, Any],
                     rp_id: str, rp_origin: str,
                     challenge_id: str) -> dict[str, Any]:
    """Validate an authentication ceremony; returns the credential."""
    if not isinstance(response, dict) or \
            response.get("type") != "public-key":
        raise PasskeyError("RESPONSE_TYPE")
    rec = _take_challenge(store, challenge_id, username, "authenticate")
    inner = response.get("response")
    if not isinstance(inner, dict):
        raise PasskeyError("RESPONSE_MALFORMED")
    credential = store.passkey_credential(str(response.get("id", "")))
    if credential is None or credential.get("user") != username:
        raise PasskeyError("CREDENTIAL_UNKNOWN")
    client_raw = _b64d(inner.get("clientDataJSON", ""))
    client_hash = _client_data_hash(client_raw, "webauthn.get",
                                    rec["challenge"], rp_origin)
    auth_data = parse_auth_data(_b64d(inner.get("authenticatorData", "")))
    if auth_data["rp_id_hash"] != hashlib.sha256(rp_id.encode()).digest():
        raise PasskeyError("RP_MISMATCH")
    if not auth_data["up"]:
        raise PasskeyError("USER_NOT_PRESENT")
    stored_count = int(credential.get("sign_count", 0))
    if stored_count > 0 and auth_data["sign_count"] <= stored_count:
        raise PasskeyError("CLONE_SUSPECTED: sign count did not advance")
    cose = credential.get("cose", {})
    key = {"alg": cose.get("alg"), "x": _b64d(cose.get("x", ""))}
    if cose.get("y"):
        key["y"] = _b64d(cose["y"])
    if not verify_signature(
            key, _b64d(inner.get("authenticatorData", "")) + client_hash,
            _b64d(inner.get("signature", ""))):
        raise PasskeyError("SIGNATURE_INVALID")
    credential["sign_count"] = auth_data["sign_count"]
    store.save_passkey_credential(credential)
    return credential
