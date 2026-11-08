"""Geointel API contracts: endpoints, gates, tenancy, audit."""
import json

import pytest
from starlette.requests import Request

import app.main as main
from app import auth as auth_mod
from app import config as config_mod
from app import intel_common as common
from app import ratelimit as rl
from app import tenancy as tenancy_mod

PURPOSE = "AUTHORIZED_FRAUD_INVESTIGATION"
SECRET = "test-secret-geointel-032-chars-ok"
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
        "boss:admin:%s,inv:investigator:%s,aud:auditor:%s,"
        "viewer:demo_viewer:%s" % (RECORD, RECORD, RECORD, RECORD))
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "")
    monkeypatch.setattr(config_mod, "FOUNDER_USER", "")


def _req(cookie=None, method="GET"):
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


def _approve(tmp_store, subject, purpose=PURPOSE):
    from app import intel_auth as authz_mod

    authz = authz_mod.create_authorization(
        tmp_store, "org_primary", "inv_84721", "investigator-1",
        subject, purpose, "NDPA s.25", "NG", "verification")
    return authz_mod.decide_authorization(
        tmp_store, authz["authorization_id"], "boss", True, "r")


def test_identity_flow_open_mode(tmp_store):
    _approve(tmp_store, "ID-OPEN-1")
    record = main.identity_verify_create(
        {"verify_type": "passport", "subject_ref": "ID-OPEN-1",
         "country": "NG", "purpose": PURPOSE,
         "investigation_id": "inv_84721"}, _req(method="POST"))
    assert record["verification_status"] == "UNAVAILABLE"
    view = main.identity_verify_get(record["verification_id"])
    assert view["integrity"] == "ok"
    assert view["masked_view"] is False
    digest = common.subject_hash("ID-OPEN-1")
    listed = main.identity_verify_list(digest)
    assert len(listed["verifications"]) == 1
    with pytest.raises(main.AppError):
        main.identity_verify_list("")
    with pytest.raises(main.AppError) as exc:
        main.identity_verify_get("idv_999999")
    assert exc.value.status == 404


def test_identity_tenant_isolated(tmp_store, monkeypatch):
    _approve(tmp_store, "ID-TEN-1")
    record = main.identity_verify_create(
        {"verify_type": "passport", "subject_ref": "ID-TEN-1",
         "country": "NG", "purpose": PURPOSE}, _req(method="POST"))
    tenancy_mod.register_tenant("org_other")
    monkeypatch.setattr(main, "_request_ctx", lambda req:
                        tenancy_mod.TenantContext("org_other", "x"))
    with pytest.raises(main.AppError) as exc:
        main.identity_verify_get(record["verification_id"])
    assert exc.value.status == 404


def test_device_relationships_and_observations(tmp_store):
    rels = main.device_relationships("dev_04")
    assert rels["relationships"]
    assert all(r["strength"] == "OBSERVED"
               for r in rels["relationships"])
    obs = main.device_observations("dev_04")
    assert obs["observations"]
    with pytest.raises(main.AppError) as exc:
        main.device_relationships("dev_99")
    assert exc.value.status == 404
    with pytest.raises(main.AppError) as exc:
        main.device_observations("bogus id!")
    assert exc.value.status == 400


def test_ip_lookup_flow_and_shape(tmp_store):
    body = main.ip_lookup_create(
        {"ip_address": "8.8.8.8", "investigation_id": "inv_84721",
         "purpose": "TRANSACTION_RISK_ASSESSMENT"},
        _req(method="POST"))
    assert body["status"] == "ESTIMATED"
    assert body["observation_id"].startswith("net_")
    assert set(body["location"]) == {"country_code", "region",
                                     "city", "latitude",
                                     "longitude", "accuracy_km"}
    assert "8.8.8.8" not in json.dumps(tmp_store.state)
    body = main.ip_lookup_create(
        {"ip_address": "10.0.0.1", "purpose": PURPOSE},
        _req(method="POST"))
    assert body["status"] == "NOT_APPLICABLE"
    with pytest.raises(main.AppError):
        main.ip_lookup_create(
            {"ip_address": "8.8.8.8", "purpose": "BOGUS"},
            _req(method="POST"))
    with pytest.raises(main.AppError) as exc:
        main.ip_lookup_create(
            {"ip_address": "8.8.8.8", "purpose": PURPOSE,
             "investigation_id": "inv_nope"}, _req(method="POST"))
    assert exc.value.status == 404


def test_location_crud_and_masking(tmp_store, armed):
    _approve(tmp_store, "SUBJ-API-1")
    record = main.location_observation_create(
        {"observation": {"source_type": "terminal-data",
                         "latitude": 6.5, "longitude": 3.4,
                         "observed_at": "2026-11-01T00:00:00Z",
                         "received_at": "2026-11-01T00:01:00Z"},
         "subject_ref": "SUBJ-API-1", "purpose": PURPOSE,
         "investigation_id": "inv_84721"}, _req(method="POST"))
    assert record["observation_id"].startswith("loc_")
    full = main.location_observation_get(record["observation_id"],
                                         _req(_login("inv")))
    assert full["latitude"] == 6.5
    assert full["masked_view"] is False
    masked = main.location_observation_get(record["observation_id"],
                                           _req(_login("aud")))
    assert masked["coordinates"] == "MASKED"
    assert "latitude" not in masked
    with pytest.raises(main.AppError) as exc:
        main.location_observation_get(record["observation_id"],
                                      _req(_login("viewer")))
    assert exc.value.status == 403
    with pytest.raises(main.AppError) as exc:
        main.location_observation_get(record["observation_id"], _req())
    assert exc.value.status == 401
    listed = main.location_observation_list(
        "inv_84721", _req(_login("boss")))
    assert len(listed["observations"]) == 1


def test_address_flow_and_masking(tmp_store, armed):
    _approve(tmp_store, "CUST-API-1",
             purpose="CUSTOMER_IDENTITY_VERIFICATION")
    address = {"country": "NG", "city": "Lagos",
               "street": "5 Broad Street"}
    created = main.address_verify_create(
        {"address": address, "subject_ref": "CUST-API-1",
         "method": "kyc-record-match",
         "purpose": "CUSTOMER_IDENTITY_VERIFICATION"},
        _req(method="POST"))
    assert created["verification_status"] == "UNAVAILABLE"
    full = main.address_verify_get(created["verification_id"],
                                   _req(_login("boss")))
    assert full["address"]["street"] == "5 Broad Street"
    masked = main.address_verify_get(created["verification_id"],
                                     _req(_login("aud")))
    assert "address" not in masked
    assert masked["address_masked"]["city"] == "Lagos"


def test_map_locations_relationships(tmp_store, armed):
    body = main.investigation_map("inv_84721", _req(_login("inv")))
    assert len(body["layers"]) == 12
    assert body["masked_view"] is False
    masked = main.investigation_map("inv_84721", _req(_login("aud")))
    assert masked["masked_view"] is True
    locs = main.investigation_locations(
        "inv_84721", request=_req(_login("inv")))
    assert locs["locations"] == []
    rels = main.investigation_relationships("inv_84721")
    assert len(rels["relationships"]) == 30
    with pytest.raises(main.AppError) as exc:
        main.investigation_map("inv_nope", _req(_login("inv")))
    assert exc.value.status == 404


def test_providers_coverage_metrics(tmp_store, armed):
    body = main.intel_providers()
    assert body["count"] == 33
    one = main.intel_provider_get("identity-document")
    assert one["integration_status"] == "DISCOVERED"
    with pytest.raises(main.AppError) as exc:
        main.intel_provider_get("nope")
    assert exc.value.status == 404
    health = main.intel_provider_health("identity-document")
    assert health["status"] == "NO_CONNECTION"
    cov = main.intel_coverage()
    assert cov["count"] == 7
    assert cov["map_provider"] == "none"
    metrics = main.intel_metrics(_req(_login("boss"), method="GET"))
    assert "identity_verifications" in metrics["counts"]
    with pytest.raises(main.AppError) as exc:
        main.intel_metrics(_req(_login("inv"), method="GET"))
    assert exc.value.status == 403


def test_evidence_resolver(tmp_store):
    _approve(tmp_store, "ID-EV-1")
    record = main.identity_verify_create(
        {"verify_type": "passport", "subject_ref": "ID-EV-1",
         "country": "NG", "purpose": PURPOSE}, _req(method="POST"))
    view = main.intel_evidence_get(record["verification_id"])
    assert view["evidence_kind"] == "identity"
    with pytest.raises(main.AppError) as exc:
        main.intel_evidence_get("ev_nope")
    assert exc.value.status == 404


def test_authorization_lifecycle(tmp_store, armed):
    created = main.intel_authorization_create(
        {"subject_ref": "ID-LC-1", "purpose": PURPOSE,
         "legal_basis": "court order", "country": "NG",
         "scope": "check"}, _req(_login("inv"), method="POST"))
    assert created["authorization_status"] == "PENDING"
    decided = main.intel_authorization_decide(
        created["authorization_id"], {"approve": True, "reference": "c"},
        _req(_login("boss"), method="POST"))
    assert decided["authorization_status"] == "APPROVED"
    fetched = main.intel_authorization_get(
        created["authorization_id"], _req(_login("boss")))
    assert fetched["authorization_id"] == created["authorization_id"]
    actions = {a["action"] for a in tmp_store.state["audits"]}
    assert "intel.authz.request" in actions
    assert "intel.authz.decide" in actions
    with pytest.raises(main.AppError) as exc:
        main.intel_authorization_decide(
            created["authorization_id"], {"approve": True},
            _req(_login("boss"), method="POST"))
    assert exc.value.status == 400
    with pytest.raises(main.AppError) as exc:
        main.intel_authorization_create(
            {"subject_ref": "x", "purpose": PURPOSE,
             "legal_basis": "b", "country": "NG", "scope": "s"},
            _req(_login("aud"), method="POST"))
    assert exc.value.status == 403


def test_consent_lifecycle(tmp_store):
    created = main.intel_consent_create(
        {"subject_ref": "SUBJ-C-1", "purpose": PURPOSE,
         "consent_method": "signed form F-7"}, _req(method="POST"))
    assert created["consent_id"].startswith("tcon_")
    assert created["consent_method"] == "signed form F-7"
    out = main.intel_consent_withdraw(
        {"subject_ref": "SUBJ-C-1", "purpose": PURPOSE},
        _req(method="POST"))
    assert out["revoked"] is True
    with pytest.raises(main.AppError) as exc:
        main.intel_consent_withdraw(
            {"subject_ref": "SUBJ-C-1", "purpose": PURPOSE},
            _req(method="POST"))
    assert exc.value.status == 404


def test_rate_limits_and_purpose_gates(tmp_store, monkeypatch):
    monkeypatch.setattr(config_mod, "GEO_ACTOR_PER_MIN", 1)
    main.ip_lookup_create(
        {"ip_address": "8.8.8.8", "purpose": PURPOSE},
        _req(method="POST"))
    with pytest.raises(main.AppError) as exc:
        main.ip_lookup_create(
            {"ip_address": "8.8.8.8", "purpose": PURPOSE},
            _req(method="POST"))
    assert exc.value.status == 429
    rl.reset()
    with pytest.raises(main.AppError) as exc:
        main.identity_verify_create(
            {"verify_type": "passport", "subject_ref": "x",
             "country": "NG", "purpose": "BOGUS"},
            _req(method="POST"))
    assert exc.value.status == 400


def test_audits_and_purge(tmp_store):
    _approve(tmp_store, "ID-AU-1")
    main.identity_verify_create(
        {"verify_type": "passport", "subject_ref": "ID-AU-1",
         "country": "NG", "purpose": PURPOSE}, _req(method="POST"))
    actions = {a["action"] for a in tmp_store.state["audits"]}
    assert "intel.identity.verify" in actions
    import time as _time

    dropped = tmp_store.intel_purge_expired(
        "identity_verifications", _time.time() + 31 * 86400)
    assert dropped == 1
    assert tmp_store.intel_purge_expired(
        "identity_verifications", _time.time()) == 0
