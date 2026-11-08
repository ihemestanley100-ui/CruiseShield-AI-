"""Session-scope live-source mutation guard (snapshot semantics).

The live ``data/state.json`` is gitignored: CI checkouts do not contain
it (collection-time import seeding creates a fresh one instead), so a
fixed size/hash anchor cannot hold everywhere. Instead, the suite
snapshots the source file once per session (existence + SHA-256) and the
``test_live_source_untouched`` checks assert the tests never mutated
what they found. Any test that writes the live file fails loudly with a
before/after diagnosis.
"""
from __future__ import annotations

import hashlib

SNAPSHOT: dict = {}


def _digest(path) -> tuple[bool, str]:
    if not path.exists():
        return False, "MISSING"
    return True, hashlib.sha256(path.read_bytes()).hexdigest().upper()


def record_source_snapshot() -> dict:
    """Snapshot the live source once per test session."""
    from app import config as config_mod

    exists, digest = _digest(config_mod.STATE_PATH)
    SNAPSHOT["exists"] = exists
    SNAPSHOT["sha256"] = digest
    SNAPSHOT["path"] = str(config_mod.STATE_PATH)
    return SNAPSHOT


def assert_source_unmutated() -> None:
    """Fail if the live source changed since the session snapshot."""
    from app import config as config_mod

    if not SNAPSHOT:
        record_source_snapshot()
    exists, digest = _digest(config_mod.STATE_PATH)
    assert exists == SNAPSHOT["exists"], (
        f"live source existence changed: started "
        f"{'present' if SNAPSHOT['exists'] else 'MISSING'} "
        f"({SNAPSHOT['path']}), now "
        f"{'present' if exists else 'MISSING'} - STOP")
    assert digest == SNAPSHOT["sha256"], (
        f"live source bytes changed during tests: started "
        f"{SNAPSHOT['sha256']}, now {digest} - STOP")
