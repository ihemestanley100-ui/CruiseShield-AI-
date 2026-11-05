"""Access-revocation semantics: deprovision, role change, logout, epoch.

verify_session_live is the cross-backend gate; a stub store keeps these
unit tests hermetic (the JSON/PG backends' revoke/epoch persistence is
covered in test_auth.py + the PG suites).
"""
from app import auth as auth_mod

SECRET = "test-secret-32-chars-minimum-ok!!"


class StubStore:
    def __init__(self):
        self.revoked = set()
        self.epochs = {}

    def is_revoked(self, nonce, now=None):
        return nonce in self.revoked

    def epoch_of(self, user):
        return self.epochs.get(user, 0)


def _live(store, token, users):
    return auth_mod.verify_session_live(token, SECRET, store, users)


def test_valid_session_live():
    store, users = StubStore(), {"judge": ("investigator", "hash")}
    token = auth_mod.create_session("judge", "investigator", SECRET)
    assert _live(store, token, users)["user"] == "judge"


def test_deprovisioned_user_rejected():
    store = StubStore()
    token = auth_mod.create_session("judge", "investigator", SECRET)
    assert _live(store, token, {}) is None


def test_role_change_rejected():
    store = StubStore()
    users = {"judge": ("investigator", "hash")}
    token = auth_mod.create_session("judge", "investigator", SECRET)
    users["judge"] = ("admin", "hash")
    assert _live(store, token, users) is None


def test_revoked_nonce_rejected():
    store, users = StubStore(), {"judge": ("investigator", "hash")}
    token = auth_mod.create_session("judge", "investigator", SECRET)
    claims = auth_mod.parse_session(token, SECRET)
    store.revoked.add(claims["nonce"])
    assert _live(store, token, users) is None


def test_pre_epoch_token_rejected_logout_all():
    store, users = StubStore(), {"judge": ("investigator", "hash")}
    token = auth_mod.create_session("judge", "investigator", SECRET)
    store.epochs["judge"] = 2_000_000_000  # epoch bumped past iat
    assert _live(store, token, users) is None
