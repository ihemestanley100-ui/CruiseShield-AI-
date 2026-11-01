"""Phase 5.4C: backup manifest build/validate/serialize/chain (stdlib only).

No providers, keys, secrets, or execution. Pure unit tests.
"""
import json

import pytest

from backups.manifest import (
    REQUIRED_KEYS,
    build_manifest,
    chain_ok,
    parse_manifest,
    serialize_manifest,
    sha256_hex,
    validate_manifest,
)


def _good(**over):
    kwargs = {
        "backup_id": "csbk-20261030-020000Z",
        "source": "scratch",
        "schema_version": "5.1.0",
        "dump_sha256": "a" * 64,
        "dump_bytes": 101417,
        "table_counts": {"audit_events": 5, "cases": 1},
        "risk": {"txn_84721": {"transaction": 35, "network": 84}},
        "audit": {"count": 5, "head_id": "audit_0005"},
        "package_hashes": {"evidence_pkg_scn_primary_v1": "b" * 64},
        "prev_backup_id": None,
        "age_recipient_fp": "FP:TEST:ONLY",
        "producer": "manual",
        "created_at": "20261030-020000Z",
    }
    kwargs.update(over)
    return kwargs


def test_build_accepts_valid_manifest():
    manifest = build_manifest(**_good())
    assert set(manifest) == set(REQUIRED_KEYS)
    assert validate_manifest(manifest) == []


def test_build_rejects_each_bad_field():
    bad_cases = [
        {"backup_id": "nope"},
        {"source": "tape"},
        {"schema_version": ""},
        {"dump_sha256": "ZZZ"},
        {"dump_bytes": -1},
        {"table_counts": {}},
        {"table_counts": {"cases": -2}},
        {"risk": {}},
        {"risk": {"txn_1": {"transaction": 101, "network": 0}}},
        {"risk": {"txn_1": {"transaction": 0}}},
        {"audit": {"count": -1, "head_id": "x"}},
        {"audit": {"count": 1, "head_id": ""}},
        {"package_hashes": {}},
        {"package_hashes": {"p": "short"}},
        {"prev_backup_id": "csbk-broken"},
        {"age_recipient_fp": ""},
        {"producer": "cron"},
        {"created_at": "yesterday"},
    ]
    for bad in bad_cases:
        with pytest.raises(ValueError, match="MANIFEST_INVALID"):
            build_manifest(**_good(**bad))


def test_validate_reports_missing_keys_without_raising():
    assert validate_manifest({}) != []
    assert validate_manifest("not-a-dict") == ["manifest must be an object"]
    assert validate_manifest(None) == ["manifest must be an object"]


def test_serialize_is_canonical_and_deterministic():
    first = serialize_manifest(build_manifest(**_good()))
    second = serialize_manifest(build_manifest(**_good()))
    assert first == second
    assert json.loads(first)["backup_id"] == "csbk-20261030-020000Z"
    with pytest.raises(ValueError, match="MANIFEST_INVALID"):
        serialize_manifest({"backup_id": "bad"})


def test_parse_round_trip_and_rejections(tmp_path):
    raw = serialize_manifest(build_manifest(**_good()))
    assert parse_manifest(raw)["dump_bytes"] == 101417
    with pytest.raises(ValueError, match="MANIFEST_NOT_JSON"):
        parse_manifest("{broken")
    with pytest.raises(ValueError, match="MANIFEST_INVALID"):
        parse_manifest(json.dumps({"backup_id": "bad"}))


def test_sha256_hex_matches_hashlib():
    import hashlib

    assert sha256_hex(b"cruiseshield") == hashlib.sha256(b"cruiseshield").hexdigest()
    assert len(sha256_hex(b"")) == 64


def test_chain_linkage_ok_and_gap():
    first = build_manifest(**_good())
    second = build_manifest(**_good(backup_id="csbk-20261031-020000Z",
                                    created_at="20261031-020000Z",
                                    prev_backup_id="csbk-20261030-020000Z"))
    assert chain_ok(first, second) is True
    skipped = build_manifest(**_good(backup_id="csbk-20261101-020000Z",
                                     created_at="20261101-020000Z",
                                     prev_backup_id="csbk-20261029-020000Z"))
    assert chain_ok(first, skipped) is False
    assert chain_ok({"nope": 1}, second) is False  # invalid never chains
    assert chain_ok(first, {"nope": 1}) is False


def test_manifest_carries_no_secrets():
    manifest = build_manifest(**_good())
    blob = serialize_manifest(manifest)
    for secret in ("postgresql://", "BEGIN ", "PRIVATE", "sk-",
                   "AKIA", "Bearer", "password", "secret"):
        assert secret not in blob
