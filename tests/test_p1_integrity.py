"""P1 integrity-gate unit tests. Synthetic fixtures only."""
import pytest

from backups import integrity as integrity_mod
from backups import manifest as manifest_mod
from backups import signing as signing_mod


def _manifest(**over):
    kwargs = {
        "backup_id": "csbk-20261030-020000Z", "source": "scratch",
        "schema_version": "5.1.0",
        "dump_sha256": manifest_mod.sha256_hex(b"dump"),
        "dump_bytes": 4, "table_counts": {"cases": 1},
        "risk": {"txn_1": {"transaction": 1, "network": 2}},
        "audit": {"count": 2, "head_id": "audit_0002"},
        "package_hashes": {"p": "c" * 64}, "prev_backup_id": None,
        "age_recipient_fp": "FP", "producer": "manual",
        "created_at": "20261030-020000Z",
    }
    kwargs.update(over)
    return manifest_mod.build_manifest(**kwargs)


def test_dump_sha_gate():
    integrity_mod.verify_dump_sha256(b"dump", manifest_mod.sha256_hex(b"dump"))
    with pytest.raises(integrity_mod.IntegrityError, match="SHA_MISMATCH"):
        integrity_mod.verify_dump_sha256(b"dump", "0" * 64)


def test_cross_copy_gate():
    integrity_mod.verify_cross_copy(b"ab", b"ab")
    with pytest.raises(integrity_mod.IntegrityError,
                       match="CROSS_COPY_MISMATCH"):
        integrity_mod.verify_cross_copy(b"ab", b"ac")
    with pytest.raises(integrity_mod.IntegrityError):
        integrity_mod.verify_cross_copy(b"ab", b"abc")


def test_chain_gate():
    first = _manifest()
    second = _manifest(backup_id="csbk-20261031-020000Z",
                       created_at="20261031-020000Z",
                       prev_backup_id="csbk-20261030-020000Z")
    integrity_mod.verify_manifest_chain(first, second)
    skipped = _manifest(backup_id="csbk-20261101-020000Z",
                        created_at="20261101-020000Z",
                        prev_backup_id="csbk-20261029-020000Z")
    with pytest.raises(integrity_mod.IntegrityError, match="CHAIN_BREAK"):
        integrity_mod.verify_manifest_chain(first, skipped)


def test_signature_gate_and_binding():
    seed, verify = signing_mod.generate_signing_keypair()
    raw = manifest_mod.serialize_manifest(_manifest())
    doc = signing_mod.sign_message(raw.encode(), seed, "csbk-20261030-020000Z")
    integrity_mod.verify_manifest_signature(
        raw, doc, verify, "csbk-20261030-020000Z")
    with pytest.raises(integrity_mod.IntegrityError,
                       match="SIGNATURE_BINDING_MISMATCH"):
        integrity_mod.verify_manifest_signature(
            raw, doc, verify, "csbk-OTHER")
    _, other = signing_mod.generate_signing_keypair()
    with pytest.raises(integrity_mod.IntegrityError, match="BAD_SIGNATURE"):
        integrity_mod.verify_manifest_signature(raw, doc, other,
                                                "csbk-20261030-020000Z")


def test_generation_verdict():
    manifest = _manifest()
    report = integrity_mod.verify_generation(
        manifest=manifest, dump_primary=b"dump", dump_secondary=b"dump")
    assert report == {"manifest_valid": True, "dump_sha256_ok": True,
                      "cross_copy_ok": True}
    with pytest.raises(integrity_mod.IntegrityError):
        integrity_mod.verify_generation(
            manifest=manifest, dump_primary=b"dump",
            dump_secondary=b"tampered!!")
    with pytest.raises(integrity_mod.IntegrityError, match="BAD_MANIFEST"):
        integrity_mod.verify_generation(
            manifest={"bad": True}, dump_primary=b"dump")
