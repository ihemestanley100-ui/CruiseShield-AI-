"""Loader audit gate: sealed-chain verification before any PG write.

Hermetic: a recording stub connection proves the gate fires before
the first cursor use. No PostgreSQL required.
"""
import json
from unittest.mock import MagicMock

import pytest

from migrations import loader as loader_mod

KEY = b"g" * 32


def _sealed_state(tmp_store, tamper=False):
    tmp_store.audit_chain_key = KEY
    tmp_store.append_audit("human", "u1", "case.decision", "case",
                           "c1", "NEW", "TRIAGED", "r", "t", "t")
    tmp_store.append_audit("human", "u1", "case.decision", "case",
                           "c1", "TRIAGED", "CLOSED", "r", "t", "t")
    if tamper:
        tmp_store.state["audits"][-1]["reason"] = "forged"
    return tmp_store.state


def test_tampered_chain_blocks_before_any_write(tmp_store):
    state = _sealed_state(tmp_store, tamper=True)
    conn = MagicMock()
    with pytest.raises(loader_mod.MigrationError) as exc:
        loader_mod.migrate_state(state, conn, audit_keyring={"k1": KEY})
    assert exc.value.code == "AUDIT_CHAIN_INVALID"
    conn.cursor.assert_not_called()


def test_valid_chain_passes_gate(tmp_store):
    state = _sealed_state(tmp_store)
    conn = MagicMock()
    try:
        loader_mod.migrate_state(state, conn, audit_keyring={"k1": KEY})
    except loader_mod.MigrationError as exc:
        # The mock cannot satisfy reconciliation; the gate itself
        # passed iff failure came from a LATER check.
        assert exc.code != "AUDIT_CHAIN_INVALID"
    conn.cursor.assert_called()


def test_gate_off_without_keyring(tmp_store):
    state = _sealed_state(tmp_store, tamper=True)
    conn = MagicMock()
    try:
        loader_mod.migrate_state(state, conn)
    except loader_mod.MigrationError as exc:
        assert exc.code != "AUDIT_CHAIN_INVALID"
    conn.cursor.assert_called()


def test_keyring_loader_accepts_hex_map(tmp_path):
    path = tmp_path / "keyring.json"
    path.write_text(json.dumps({"k1": KEY.hex(),
                                "k2": ("b" * 32).encode().hex()}),
                    encoding="utf-8")
    assert loader_mod.load_audit_keyring(path) == {
        "k1": KEY, "k2": b"b" * 32}


@pytest.mark.parametrize(("payload", "code", "secret"), [
    ("{not-json", "KEYRING_NOT_JSON", None),
    ("[]", "KEYRING_BAD_SHAPE", None),
    ("{}", "KEYRING_BAD_SHAPE", None),
    (json.dumps({"": KEY.hex()}), "KEYRING_BAD_KEY_ID", None),
    (json.dumps({"k1": 42}), "KEYRING_BAD_KEY", None),
    (json.dumps({"k1": "not-hex!!"}), "KEYRING_BAD_KEY", "not-hex!!"),
    (json.dumps({"k1": "abcd"}), "KEYRING_KEY_TOO_SHORT", "abcd"),
])
def test_keyring_loader_rejects_bad_files(tmp_path, payload, code,
                                          secret):
    path = tmp_path / "keyring.json"
    path.write_text(payload, encoding="utf-8")
    with pytest.raises(loader_mod.MigrationError) as exc:
        loader_mod.load_audit_keyring(path)
    assert exc.value.code == code
    if secret is not None:
        assert secret not in str(exc.value)


def test_keyring_loader_missing_file(tmp_path):
    with pytest.raises(loader_mod.MigrationError) as exc:
        loader_mod.load_audit_keyring(tmp_path / "missing.json")
    assert exc.value.code == "KEYRING_NOT_FOUND"


def test_cli_passes_loaded_keyring(tmp_path, monkeypatch, capsys):
    path = tmp_path / "keyring.json"
    path.write_text(json.dumps({"k1": KEY.hex()}), encoding="utf-8")
    seen = {}

    def _fake(source, database_url, expected_hash=None,
              init_schema=True, audit_keyring=None):
        seen.update(source=source, database_url=database_url,
                    expected_hash=expected_hash,
                    init_schema=init_schema,
                    audit_keyring=audit_keyring)
        return {"passed": True}

    monkeypatch.setattr(loader_mod, "run_migration", _fake)
    assert loader_mod.main(["--source", "copy.json",
                            "--database-url", "scratch",
                            "--audit-keyring", str(path)]) == 0
    assert seen["audit_keyring"] == {"k1": KEY}
    assert json.loads(capsys.readouterr().out) == {"passed": True}


def test_cli_keyring_optional(tmp_path, monkeypatch):
    seen = {}

    def _fake(source, database_url, expected_hash=None,
              init_schema=True, audit_keyring="unset"):
        seen["audit_keyring"] = audit_keyring
        return {"passed": True}

    monkeypatch.setattr(loader_mod, "run_migration", _fake)
    assert loader_mod.main(["--source", "copy.json",
                            "--database-url", "scratch"]) == 0
    assert seen["audit_keyring"] is None


def test_cli_rejects_bad_keyring_before_migration(tmp_path, monkeypatch,
                                                  capsys):
    path = tmp_path / "keyring.json"
    path.write_text(json.dumps({"k1": "not-hex!!"}), encoding="utf-8")

    def _must_not_run(*args, **kwargs):
        raise AssertionError("migration must not start")

    monkeypatch.setattr(loader_mod, "run_migration", _must_not_run)
    assert loader_mod.main(["--source", "copy.json",
                            "--database-url", "scratch",
                            "--audit-keyring", str(path)]) == 1
    err = capsys.readouterr().err
    assert "KEYRING_BAD_KEY" in err
    assert "not-hex!!" not in err
