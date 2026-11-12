"""Telecom HTTP contracts: shapes, audit, tenancy, admin config."""
import json

import pytest
from starlette.requests import Request

import app.main as main
from app import auth as auth_mod
from app import config as config_mod
from app import ratelimit as rl
from app import tenancy as tenancy_mod
from app import telecom_verify as tv

E164 = "+2348031234567"
PURPOSE = "fraud-investigation-case-2"
SECRET = "test-secret-telecom-032-chars-ok"
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
        "boss:admin:%s,viewer:demo_viewer:%s" % (RECORD, RECORD))
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "")
    monkeypatch.setattr(config_mod, "FOUNDER_USER", "")


@pytest.fixture()
def armed_admin(tmp_store, armed):
    resp = main.auth_login({"username": "boss",
                            "password": "demo-pass-1"}, _req())
    raw = resp.headers["set-cookie"]
    part = [p for p in raw.split(";") if "csai_session=" in p][0]
    cookie = part.split("csai_session=", 1)[1]
    headers = [(b"host", b"t"),
               (b"cookie", ("csai_session=%s" % cookie).encode())]
    return Request({"type": "http", "method": "GET", "scheme": "http",
                    "server": ("t", 80), "client": ("9.9.9.9", 1234),
                    "path": "/x", "query_string": b"",
                    "headers": headers})


def _req(path="/x", method="GET", token=None):
    headers = [(b"host", b"t")]
    if token is not None:
        headers.append((b"authorization", ("Bearer %s" % token).encode()))
    return Request({"type": "http", "method": method, "scheme": "http",
                    "server": ("t", 80), "client": ("9.9.9.9", 1234),
                    "path": path, "query_string": b"", "headers": headers})


def test_operators_registry_contract(tmp_store):
    body = main.telecom_operators()
    assert body["count"] == 13
    assert body["registry"]["version"] == "1.0"
    assert {op["country"] for op in
            main.telecom_operators("ng")["operators"]} == {"NG"}
    op = main.telecom_operator("mtn-ng")
    assert op["country"] == "NG"
    with pytest.raises(main.AppError) as exc:
        main.telecom_operator("nope")
    assert exc.value.status == 404


def test_parse_contract(tmp_store):
    body = main.telecom_parse("+2348031234567")
    assert body["operator_id"] == "mtn-ng"
    assert body["e164_masked"].startswith("+234")
    assert "0312345" not in body["e164_masked"]
    with pytest.raises(main.AppError) as exc:
        main.telecom_parse("bogus")
    assert exc.value.status == 400


def test_verify_create_persists_masked_and_audits(tmp_store):
    record = main.telecom_verify_create(
        {"verify_type": "carrier_identification", "e164": E164,
         "purpose": PURPOSE}, _req(method="POST"))
    assert record["verification_id"].startswith("tvrf_")
    assert record["state"] == tv.PARTIALLY_VERIFIED
    assert E164 not in json.dumps(tmp_store.state)
    audits = [a for a in tmp_store.state["audits"]
              if a["action"] == "telecom.verify"]
    assert len(audits) == 1
    assert E164 not in json.dumps(audits)
    assert audits[0]["target_id"] == record["verification_id"]


def test_verify_create_validates_input(tmp_store):
    with pytest.raises(main.AppError) as exc:
        main.telecom_verify_create(
            {"verify_type": "nope", "e164": E164, "purpose": PURPOSE},
            _req(method="POST"))
    assert exc.value.status == 400
    with pytest.raises(main.AppError):
        main.telecom_verify_create(
            {"verify_type": "tenure", "e164": E164, "purpose": ""},
            _req(method="POST"))


def test_verify_get_stale_and_integrity_view(tmp_store):
    import time as _time

    record = tv.run_verification(
        tmp_store, tmp_store.state, "number_verification", E164,
        PURPOSE, "org_primary", "u", "org_primary",
        now=_time.time() - 7200)
    view = main.telecom_verify_get(record["verification_id"])
    assert view["state"] == tv.STALE_RESULT
    assert view["previous_state"] == tv.UNAVAILABLE
    assert view["integrity"] == "ok"
    stored = tmp_store.telecom_get(record["verification_id"])
    assert stored["state"] == tv.UNAVAILABLE  # evidence immutable
    with pytest.raises(main.AppError) as exc:
        main.telecom_verify_get("tvrf_999999")
    assert exc.value.status == 404


def test_verify_get_tenant_isolated(tmp_store, monkeypatch):
    record = main.telecom_verify_create(
        {"verify_type": "carrier_identification", "e164": E164,
         "purpose": PURPOSE}, _req(method="POST"))
    tenancy_mod.register_tenant("org_other")
    monkeypatch.setattr(main, "_request_ctx", lambda req:
                        tenancy_mod.TenantContext("org_other", "x"))
    with pytest.raises(main.AppError) as exc:
        main.telecom_verify_get(record["verification_id"])
    assert exc.value.status == 404  # no oracle


def test_summary_contract(tmp_store):
    main.telecom_verify_create(
        {"verify_type": "carrier_identification", "e164": E164,
         "purpose": PURPOSE}, _req(method="POST"))
    body = main.telecom_summary(subject=E164, phone_label="phn_01")
    assert body["allocation"]["operator_id"] == "mtn-ng"
    assert body["history_count"] == 1
    assert body["history"][0]["stale"] is False
    assert "devices" in body["co_signals"]
    assert E164 not in json.dumps(body)
    with pytest.raises(main.AppError):
        main.telecom_summary(subject="bogus")


def test_consent_create_contract(tmp_store):
    consent = main.telecom_consent_create(
        {"e164": E164, "purpose": PURPOSE, "expires_days": 7},
        _req(method="POST"))
    assert consent["consent_id"].startswith("tcon_")
    assert consent["granted_by"] == "anonymous"
    assert E164 not in json.dumps(consent)
    record = main.telecom_verify_create(
        {"verify_type": "kyc_match", "e164": E164, "purpose": PURPOSE},
        _req(method="POST"))
    assert record["state"] == tv.UNAVAILABLE  # consent ok, no provider


def test_admin_config_contract(tmp_store, armed_admin):
    body = main.telecom_config(armed_admin)
    assert body["registry"]["version"] == "1.0"
    assert len(body["verify_types"]) == 11
    assert body["live_integrations"] == []
    assert all(p["live"] is False for p in body["providers"])
    assert all("secret" not in json.dumps(p).lower()
               or "secret_refs" in json.dumps(p) or
               "secret_present" in json.dumps(p)
               for p in body["providers"])
    audits = [a for a in tmp_store.state["audits"]
              if a["action"] == "telecom.config.read"]
    assert len(audits) == 1


def test_admin_config_requires_admin(tmp_store):
    with pytest.raises(main.AppError) as exc:
        main.telecom_config(_req())
    assert exc.value.status == 403
