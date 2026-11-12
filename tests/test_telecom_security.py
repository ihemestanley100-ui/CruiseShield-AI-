"""Telecom security: RBAC, consent, rate limits, retention, PII minimization."""
import json
import time

import pytest
from starlette.requests import Request

import app.main as main
from app import auth as auth_mod
from app import config as config_mod
from app import ratelimit as rl
from app import tenancy as tenancy_mod
from app import telecom_verify as tv

E164 = "+2348031234567"
PURPOSE = "fraud-investigation-case-3"
SECRET = "test-secret-telecom-sec-032-ok!!"
RECORD = auth_mod.hash_password("demo-pass-1")


@pytest.fixture(autouse=True)
def _buckets():
    rl.reset()
    yield
    rl.reset()


@pytest.fixture()
def armed(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "boss:admin:%s,inv:investigator:%s,viewer:demo_viewer:%s"
        % (RECORD, RECORD, RECORD))
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "")
    monkeypatch.setattr(config_mod, "FOUNDER_USER", "")


def _req(cookie=None, method="POST"):
    headers = [(b"host", b"t")]
    if cookie is not None:
        headers.append((b"cookie",
                        ("csai_session=%s" % cookie).encode()))
    return Request({"type": "http", "method": method, "scheme": "http",
                    "server": ("t", 80), "client": ("9.9.9.9", 1234),
                    "path": "/x", "query_string": b"",
                    "headers": headers})


def _login(user):
    resp = main.auth_login({"username": user, "password": "demo-pass-1"},
                           _req())
    raw = resp.headers["set-cookie"]
    part = [p for p in raw.split(";") if "csai_session=" in p][0]
    return part.split("csai_session=", 1)[1]


def test_viewer_role_denied_investigator_allowed(tmp_store, armed):
    with pytest.raises(main.AppError) as exc:
        main.telecom_verify_create(
            {"verify_type": "tenure", "e164": E164, "purpose": PURPOSE},
            _req(_login("viewer")))
    assert exc.value.status == 403
    record = main.telecom_verify_create(
        {"verify_type": "tenure", "e164": E164, "purpose": PURPOSE},
        _req(_login("inv")))
    assert record["user"] == "inv"
    assert record["org"] == "org_primary"


def test_actor_attribution_server_derived(tmp_store, armed):
    record = main.telecom_verify_create(
        {"verify_type": "tenure", "e164": E164, "purpose": PURPOSE,
         "user": "mallory", "org": "evil"},
        _req(_login("boss")))
    assert record["user"] == "boss"
    assert record["org"] == "org_primary"


def test_actor_rate_limit_429(tmp_store, armed, monkeypatch):
    monkeypatch.setattr(config_mod, "TELECOM_ACTOR_PER_MIN", 2)
    cookie = _login("inv")
    for _ in range(2):
        main.telecom_verify_create(
            {"verify_type": "tenure", "e164": E164, "purpose": PURPOSE},
            _req(cookie))
    with pytest.raises(main.AppError) as exc:
        main.telecom_verify_create(
            {"verify_type": "tenure", "e164": E164, "purpose": PURPOSE},
            _req(cookie))
    assert exc.value.status == 429


def test_subject_daily_quota_429(tmp_store, monkeypatch):
    monkeypatch.setattr(config_mod, "TELECOM_SUBJECT_PER_DAY", 1)
    main.telecom_verify_create(
        {"verify_type": "tenure", "e164": E164, "purpose": PURPOSE},
        _req())
    with pytest.raises(main.AppError) as exc:
        main.telecom_verify_create(
            {"verify_type": "tenure", "e164": E164, "purpose": PURPOSE},
            _req())
    assert exc.value.status == 429


def test_consent_expiry_enforced(tmp_store, monkeypatch):
    main.telecom_consent_create(
        {"e164": E164, "purpose": PURPOSE, "expires_days": 1},
        _req())
    record = tv.run_verification(
        tmp_store, tmp_store.state, "kyc_match", E164, PURPOSE,
        "org_primary", "u", "org_primary",
        now=time.time() + 2 * 86400)
    assert record["state"] == tv.CONSENT_REQUIRED


def test_global_consent_mode_gates_all_types(tmp_store, monkeypatch):
    monkeypatch.setattr(config_mod, "TELECOM_CONSENT_REQUIRED", "1")
    record = main.telecom_verify_create(
        {"verify_type": "tenure", "e164": E164, "purpose": PURPOSE},
        _req())
    assert record["state"] == tv.CONSENT_REQUIRED


def test_retention_purge_deletes_only_expired(tmp_store):
    now = time.time()
    old = tv.run_verification(
        tmp_store, tmp_store.state, "tenure", E164, PURPOSE,
        "org_primary", "u", "org_primary", now=now - 100 * 86400)
    fresh = tv.run_verification(
        tmp_store, tmp_store.state, "tenure", "+2348021234567",
        PURPOSE, "org_primary", "u", "org_primary", now=now)
    dropped = tmp_store.telecom_purge_expired(now - 90 * 86400)
    assert dropped == 1
    assert tmp_store.telecom_get(old["verification_id"]) is None
    assert tmp_store.telecom_get(fresh["verification_id"]) is not None


def test_raw_e164_never_persisted(tmp_store, armed):
    main.telecom_verify_create(
        {"verify_type": "carrier_identification", "e164": E164,
         "purpose": PURPOSE}, _req(_login("boss")))
    main.telecom_consent_create(
        {"e164": E164, "purpose": PURPOSE}, _req(_login("boss")))
    assert E164 not in json.dumps(tmp_store.state)


def test_cross_tenant_history_hidden(tmp_store, monkeypatch):
    main.telecom_verify_create(
        {"verify_type": "carrier_identification", "e164": E164,
         "purpose": PURPOSE}, _req())
    tenancy_mod.register_tenant("org_other")
    monkeypatch.setattr(main, "_request_ctx", lambda req:
                        tenancy_mod.TenantContext("org_other", "x"))
    body = main.telecom_summary(subject=E164)
    assert body["history_count"] == 0
    assert body["allocation"]["operator_id"] == "mtn-ng"  # public data
