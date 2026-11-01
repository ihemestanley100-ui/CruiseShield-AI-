"""P1 crypto unit tests. Ephemeral test-only keys; no real key material."""
import pytest

from backups import crypto as crypto_mod


def test_round_trip_single_recipient():
    priv, pub = crypto_mod.generate_keypair()
    blob = crypto_mod.encrypt_bytes(b"backup-bytes", [pub])
    assert crypto_mod.decrypt_bytes(blob, priv) == b"backup-bytes"


def test_round_trip_two_recipients_independently():
    priv_a, pub_a = crypto_mod.generate_keypair()
    priv_b, pub_b = crypto_mod.generate_keypair()
    blob = crypto_mod.encrypt_bytes(b"shared", [pub_a, pub_b])
    assert crypto_mod.decrypt_bytes(blob, priv_a) == b"shared"
    assert crypto_mod.decrypt_bytes(blob, priv_b) == b"shared"


def test_unique_dek_per_encryption():
    _, pub = crypto_mod.generate_keypair()
    first = crypto_mod.encrypt_bytes(b"same", [pub])
    second = crypto_mod.encrypt_bytes(b"same", [pub])
    assert first != second  # fresh ephemeral keypair each time


def test_tampered_ciphertext_rejected():
    priv, pub = crypto_mod.generate_keypair()
    blob = bytearray(crypto_mod.encrypt_bytes(b"data", [pub]))
    blob[-1] ^= 0x01
    with pytest.raises(crypto_mod.CryptoError, match="DECRYPT_FAILED"):
        crypto_mod.decrypt_bytes(bytes(blob), priv)


def test_wrong_key_rejected():
    _, pub = crypto_mod.generate_keypair()
    wrong_priv, _ = crypto_mod.generate_keypair()
    blob = crypto_mod.encrypt_bytes(b"data", [pub])
    with pytest.raises(crypto_mod.CryptoError, match="DECRYPT_FAILED"):
        crypto_mod.decrypt_bytes(blob, wrong_priv)


def test_malformed_envelopes_rejected():
    priv, _ = crypto_mod.generate_keypair()
    for bad in (b"", b"SHORT", b"XXXXX\x01\x01" + b"0" * 40,
                b"CSBK1\x09\x01" + b"0" * 40, b"CSBK1\x01\x00",
                b"CSBK1\x01\x01" + b"0" * 10):
        with pytest.raises(crypto_mod.CryptoError):
            crypto_mod.decrypt_bytes(bad, priv)


def test_bad_inputs_rejected():
    _, pub = crypto_mod.generate_keypair()
    with pytest.raises(crypto_mod.CryptoError, match="BAD_RECIPIENT_COUNT"):
        crypto_mod.encrypt_bytes(b"x", [])
    with pytest.raises(crypto_mod.CryptoError, match="BAD_PUBLIC_KEY"):
        crypto_mod.encrypt_bytes(b"x", [b"short"])
    with pytest.raises(crypto_mod.CryptoError, match="BAD_PRIVATE_KEY"):
        crypto_mod.decrypt_bytes(b"CSBK1\x01\x01", b"short")


def test_fingerprint_stable_and_sized():
    _, pub = crypto_mod.generate_keypair()
    first = crypto_mod.fingerprint(pub)
    assert first == crypto_mod.fingerprint(pub)
    assert len(first) == 32
    with pytest.raises(crypto_mod.CryptoError, match="BAD_PUBLIC_KEY"):
        crypto_mod.fingerprint(b"short")


def test_errors_carry_no_key_material():
    priv, pub = crypto_mod.generate_keypair()
    blob = crypto_mod.encrypt_bytes(b"secret-plaintext", [pub])
    try:
        crypto_mod.decrypt_bytes(blob, b"\x00" * 32)
        raise AssertionError("must fail")
    except crypto_mod.CryptoError as exc:
        assert "secret-plaintext" not in str(exc)
        assert pub.hex() not in str(exc)
        assert priv.hex() not in str(exc)
