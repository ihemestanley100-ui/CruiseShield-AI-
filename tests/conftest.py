"""Shared fixtures: isolated store per test, TestClient bound to it."""
import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.store import Store


@pytest.fixture()
def tmp_store(tmp_path, monkeypatch):
    store = Store(tmp_path / "state.json")
    monkeypatch.setattr(main, "store", store)
    return store


@pytest.fixture()
def client(tmp_store):
    with TestClient(main.app) as http:
        yield http


@pytest.fixture(scope="session", autouse=True)
def _snapshot_live_source():
    """Snapshot the live source once per session (mutation guard).

    Runs after collection-time imports, so in CI (no live file) the
    snapshot covers the import-seeded file and locally it covers the
    real file. The untouched checks compare against this snapshot.
    """
    from _integrity import record_source_snapshot

    record_source_snapshot()


@pytest.fixture(autouse=True)
def _no_live_provider_calls(monkeypatch):
    """Hermetic tests: a test process must never spend owner AI quota.

    J4 fix: config loads ROOT/.env at import, so unsandboxed runs used
    to inherit a real MODEL_API_KEY and the socket-gated full-stack
    test made live provider calls. Every test now starts keyless;
    tests needing a key set it explicitly via monkeypatch.
    """
    import app.config as config_mod
    from app import ai_adapter

    monkeypatch.setattr(ai_adapter, "MODEL_API_KEY", "")
    monkeypatch.setattr(config_mod, "MODEL_API_KEY", "")
