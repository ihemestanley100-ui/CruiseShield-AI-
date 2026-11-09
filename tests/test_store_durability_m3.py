"""M3 store durability edges: atomic saves, reload persistence, prune rules."""
import json
import threading

import pytest

from app.store import Store


def _store(tmp_path):
    return Store(tmp_path / "state.json")


def test_concurrent_saves_keep_valid_json(tmp_path):
    store = _store(tmp_path)
    errors = []

    def worker(n):
        try:
            for i in range(20):
                key = "w%d_%d" % (n, i)
                store.state.setdefault("probe", {})[key] = i
                store._save()
        except Exception as exc:  # pragma: no cover - surfaced below
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    raw = (tmp_path / "state.json").read_text(encoding="utf-8")
    reloaded = json.loads(raw)  # must always parse: tmp+replace is atomic
    assert len(reloaded["probe"]) == 200
    assert list(tmp_path.glob("*.tmp")) == []  # no litter left behind


def test_revocation_survives_store_reload(tmp_path):
    store = _store(tmp_path)
    store.revoke_session("nonce-abc", exp=4100000000, now=1700000000.0)
    assert store.is_revoked("nonce-abc", now=1700000000.0) is True
    fresh = Store(tmp_path / "state.json")
    assert fresh.is_revoked("nonce-abc", now=1700000000.0) is True
    assert fresh.is_revoked("nonce-unknown", now=1700000000.0) is False


def test_expired_revocations_pruned_and_epochs_persist(tmp_path):
    store = _store(tmp_path)
    store.revoke_session("old", exp=100, now=200.0)
    store.revoke_session("live", exp=9999999999, now=200.0)
    nonces = [r["nonce"] for r in store.state["revoked_sessions"]]
    assert nonces == ["live"]
    store.revoke_session("live", exp=9999999999, now=200.0)
    assert [r["nonce"] for r in store.state["revoked_sessions"]] == ["live"]
    epoch = store.bump_epoch("judge", now=1700000000.0)
    fresh = Store(tmp_path / "state.json")
    assert fresh.epoch_of("judge") == epoch


def test_corrupt_state_fails_closed_not_silent_reseed(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("{truncated", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        Store(path)
