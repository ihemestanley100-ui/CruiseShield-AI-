"""M3 security edges: revocation durability and store trust boundaries."""
import time

from app.store import Store


def test_revoked_nonce_denied_after_reload(tmp_path):
    path = tmp_path / "state.json"
    store = Store(path)
    exp = int(time.time()) + 3600
    store.revoke_session("nonce-1", exp=exp)
    assert store.is_revoked("nonce-1") is True
    fresh = Store(path)
    assert fresh.is_revoked("nonce-1") is True
    assert fresh.is_revoked("nonce-other") is False


def test_logout_all_epoch_survives_reload(tmp_path):
    path = tmp_path / "state.json"
    store = Store(path)
    epoch = store.bump_epoch("judge")
    assert Store(path).epoch_of("judge") == epoch
    assert Store(path).epoch_of("stranger") == 0


def test_revocation_list_stays_bounded(tmp_path):
    store = Store(tmp_path / "state.json")
    for n in range(50):
        store.revoke_session("n%d" % n, exp=100, now=200.0)
    store.revoke_session("keeper", exp=9999999999, now=200.0)
    assert [r["nonce"] for r in
            store.state["revoked_sessions"]] == ["keeper"]
