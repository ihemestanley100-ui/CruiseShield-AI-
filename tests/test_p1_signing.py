"""P1 signing unit tests. Ephemeral test-only keys.

NOTE: minisign-CLI byte interop was VERIFIED in P2.2C (CLI 0.12, five
tests, synthetic fixtures; see the phase report). These tests prove
unforgeability, tamper binding, and wrong-key rejection of this
implementation, with all Ed25519 inside libsodium.
"""
import pytest

from backups import signing as signing_mod

MESSAGE = b'{"backup_id":"csbk-20261030-020000Z"}'


def test_round_trip_returns_trusted_comment():
    seed, verify = signing_mod.generate_signing_keypair()
    doc = signing_mod.sign_message(MESSAGE, seed, "csbk-20261030-020000Z")
    assert signing_mod.verify_message(MESSAGE, doc, verify) == \
        "csbk-20261030-020000Z"


def test_tampered_message_rejected():
    seed, verify = signing_mod.generate_signing_keypair()
    doc = signing_mod.sign_message(MESSAGE, seed, "t")
    with pytest.raises(signing_mod.SignatureError, match="VERIFY_FAILED"):
        signing_mod.verify_message(MESSAGE + b"!", doc, verify)


def test_tampered_signature_rejected():
    seed, verify = signing_mod.generate_signing_keypair()
    lines = signing_mod.sign_message(MESSAGE, seed, "t").splitlines()
    tampered = lines[1][:-2] + ("AA" if not lines[1].endswith("AA") else "BB")
    doc = "\n".join([lines[0], tampered, lines[2], lines[3]]) + "\n"
    with pytest.raises(signing_mod.SignatureError):
        signing_mod.verify_message(MESSAGE, doc, verify)


def test_trusted_comment_binding_enforced():
    seed, verify = signing_mod.generate_signing_keypair()
    doc = signing_mod.sign_message(MESSAGE, seed, "backup-A")
    swapped = doc.replace("trusted comment: backup-A",
                          "trusted comment: backup-B")
    with pytest.raises(signing_mod.SignatureError):
        signing_mod.verify_message(MESSAGE, swapped, verify)


def test_wrong_key_rejected():
    seed, _ = signing_mod.generate_signing_keypair()
    _, other_verify = signing_mod.generate_signing_keypair()
    doc = signing_mod.sign_message(MESSAGE, seed, "t")
    with pytest.raises(signing_mod.SignatureError):
        signing_mod.verify_message(MESSAGE, doc, other_verify)


def test_malformed_documents_rejected():
    _, verify = signing_mod.generate_signing_keypair()
    for bad in ("", "one line\n", "a\nb\nc\n",
                "untrusted comment: x\n!!!\ntrusted comment: t\n!!!\n"):
        with pytest.raises(signing_mod.SignatureError):
            signing_mod.verify_message(MESSAGE, bad, verify)


def test_multiline_comments_rejected():
    seed, _ = signing_mod.generate_signing_keypair()
    with pytest.raises(signing_mod.SignatureError, match="BAD_COMMENT"):
        signing_mod.sign_message(MESSAGE, seed, "a\nb")


def test_public_key_document_shape():
    _, verify = signing_mod.generate_signing_keypair()
    doc = signing_mod.public_key_document(verify)
    assert doc.startswith("untrusted comment: ")
    assert len(signing_mod.fingerprint(verify)) == 32


def test_wrong_key_id_rejected():
    seed, verify = signing_mod.generate_signing_keypair()
    doc = signing_mod.sign_message(MESSAGE, seed, "t")
    with pytest.raises(signing_mod.SignatureError, match="KEY_MISMATCH"):
        signing_mod.verify_message(MESSAGE, doc, verify,
                                    expected_key_id=b"\x00" * 8)
    with pytest.raises(signing_mod.SignatureError, match="BAD_KEY_ID"):
        signing_mod.verify_message(MESSAGE, doc, verify,
                                    expected_key_id=b"short")


def test_cli_style_key_id_accepted_when_trusted():
    import base64

    seed, verify = signing_mod.generate_signing_keypair()
    lines = signing_mod.sign_message(MESSAGE, seed, "t").splitlines()
    packet = bytearray(base64.b64decode(lines[1]))
    cli_keynum = b"\xb7\x91\xfd\x9f\x35\x83\xe1\x6c"  # random, like CLI -G
    packet[2:10] = cli_keynum
    lines[1] = base64.b64encode(bytes(packet)).decode("ascii")
    doc = "\n".join(lines) + "\n"
    with pytest.raises(signing_mod.SignatureError, match="KEY_MISMATCH"):
        signing_mod.verify_message(MESSAGE, doc, verify)
    assert signing_mod.verify_message(
        MESSAGE, doc, verify, expected_key_id=cli_keynum) == "t"


def test_legacy_74byte_global_rejected_no_downgrade():
    import base64

    seed, verify = signing_mod.generate_signing_keypair()
    lines = signing_mod.sign_message(MESSAGE, seed, "t").splitlines()
    legacy_global = base64.b64encode(
        b"Ed" + signing_mod.key_id(verify)
        + base64.b64decode(lines[3])).decode("ascii")
    doc = "\n".join([lines[0], lines[1], lines[2], legacy_global]) + "\n"
    with pytest.raises(signing_mod.SignatureError,
                        match="BAD_SIGNATURE_DOC"):
        signing_mod.verify_message(MESSAGE, doc, verify)


def test_exact_byte_verification():
    seed, verify = signing_mod.generate_signing_keypair()
    doc = signing_mod.sign_message(MESSAGE, seed, "t")
    for variant in (MESSAGE + b"\n", MESSAGE[:-1], MESSAGE + b" "):
        with pytest.raises(signing_mod.SignatureError,
                            match="VERIFY_FAILED"):
            signing_mod.verify_message(variant, doc, verify)


def test_comment_alteration_semantics():
    seed, verify = signing_mod.generate_signing_keypair()
    doc = signing_mod.sign_message(MESSAGE, seed, "backup-A")
    swapped = doc.replace("trusted comment: backup-A",
                          "trusted comment: backup-B")
    with pytest.raises(signing_mod.SignatureError):
        signing_mod.verify_message(MESSAGE, swapped, verify)
    retitled = doc.replace("untrusted comment: signature from cruiseshield",
                           "untrusted comment: anything at all")
    assert signing_mod.verify_message(MESSAGE, retitled, verify) == \
        "backup-A"
