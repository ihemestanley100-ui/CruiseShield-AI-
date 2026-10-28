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
