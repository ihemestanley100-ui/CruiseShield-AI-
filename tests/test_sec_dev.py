"""SEC-DEV: trusted-device register + revocation."""
from __future__ import annotations

import pytest
from starlette.requests import Request

import app.main as main
from app import auth as auth_mod
from app import config as config_mod
from app import trusted_devices as dev_mod

SECRET = "test-secret-not-a-real-credential"
RECORD = auth_mod.hash_password("demo-pass-1")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def _users(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(config_mod, "SESSION_SECRET_PREVIOUS", "")
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "")
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:investigator:%s,boss:admin:%s" % (RECORD, RECORD))


def _req(cookie=None, ua=UA):
    headers = [(b"host", b"t"), (b"user-agent", ua.encode())]
    if cookie is not None:
        headers.append((b"cookie", ("csai_session=%s" % cookie).encode()))
    return Request({"type": "http", "method": "POST", "scheme": "http",
                    "server": ("t", 80), "client": ("9.9.9.9", 1234),
                    "path": "/x", "query_string": b"", "headers": headers})


def _login_cookie():
    resp = main.auth_login({"username": "judge",
                            "password": "demo-pass-1"}, _req())
    raw = resp.headers["set-cookie"]
    part = [p for p in raw.split(";") if "csai_session=" in p][0]
    return part.split("csai_session=", 1)[1]


def test_touch_and_revoke(tmp_store):
    row = dev_mod.touch(tmp_store, "judge", "desktop", "net_1")
    assert row["first_seen"] and row["trusted"] is False
    assert dev_mod.revoked(tmp_store, "judge", "desktop", "net_1") is False
    dev_mod.set_trusted(tmp_store, "judge", row["device_key"], True)
    assert tmp_store.device_get(row["device_key"])["trusted"] is True
    dev_mod.revoke(tmp_store, "judge", row["device_key"])
    assert dev_mod.revoked(tmp_store, "judge", "desktop", "net_1") is True
    with pytest.raises(ValueError):
        dev_mod.revoke(tmp_store, "judge", "nope")
    with pytest.raises(ValueError):
        dev_mod.set_trusted(tmp_store, "boss", row["device_key"], True)


def test_login_registers_device(tmp_store, monkeypatch):
    _users(monkeypatch)
    _login_cookie()
    devices = tmp_store.user_devices("judge")
    assert len(devices) == 1
    assert devices[0]["last_seen"]


def test_revoked_device_denied(tmp_store, monkeypatch):
    _users(monkeypatch)
    cookie = _login_cookie()
    key = tmp_store.user_devices("judge")[0]["device_key"]
    main.revoke_my_device({"device_key": key}, _req(cookie=cookie))
    with pytest.raises(main.AppError) as exc:
        main.auth_login({"username": "judge",
                         "password": "demo-pass-1"}, _req())
    assert exc.value.code == "DEVICE_REVOKED"
    audits = [a for a in main.store.state.get("audits", [])
              if isinstance(a, dict)
              and a.get("action") == "auth.login.device_revoked"]
    assert audits
    other = main.auth_login({"username": "judge",
                             "password": "demo-pass-1"},
                            _req(ua="curl/8.0"))
    assert other.status_code == 200


def test_device_routes(tmp_store, monkeypatch):
    _users(monkeypatch)
    cookie = _login_cookie()
    out = main.list_my_devices(_req(cookie=cookie))
    assert len(out["devices"]) == 1
    key = out["devices"][0]["device_key"]
    row = main.trust_my_device({"device_key": key, "trusted": True},
                               _req(cookie=cookie))
    assert row["trusted"] is True
    with pytest.raises(main.AppError):
        main.list_my_devices(_req())
    with pytest.raises(main.AppError):
        main.trust_my_device({"device_key": "nope"},
                             _req(cookie=cookie))
