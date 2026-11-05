"""Loader audit gate: sealed-chain verification before any PG write.

Hermetic: a recording stub connection proves the gate fires before
the first cursor use. No PostgreSQL required.
"""
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
