"""v14.0 S04/SF: connector registry, lifecycle, health, audit."""
import json

import pytest
from starlette.requests import Request

import app.main as main
from app import config as config_mod
from app import connectors as conn_mod
from app import tenancy as tenancy_mod

BANKING_PARAMS = {"base_url": "https://bank.example", "institution_id": "x"}
SECRET_VALUE = "sup3r-secret-value-for-connector-test"


def _scope(path, method="GET", token=None):
    headers = [(b"host", b"t")]
    if token is not None:
        headers.append((b"authorization", ("Bearer %s" % token).encode()))
    return {"type": "http", "method": method, "scheme": "http",
            "server": ("t", 80), "client": ("9.9.9.9", 1234),
            "path": path, "query_string": b"", "headers": headers}


def _req(path, method="POST", token=None):
    return Request(_scope(path, method=method, token=token))


def _body(resp):
    return json.loads(resp.body.decode())


def test_registry_lists_32_adapters_plus_harness():
    # 15 financial + 8 telecom + 9 intelligence + harness.
    body = main.connectors_registry()
    assert body["count"] == 33
    specs = {s["adapter"]: s for s in body["connectors"]}
    assert specs["loopback"]["synthetic"] is True
    real = [s for s in body["connectors"] if not s["synthetic"]]
    assert len(real) == 32
    for adapter in ("camara-number-verification", "camara-sim-swap",
                    "camara-device-swap", "camara-kyc-match",
                    "camara-number-recycling", "camara-device-identifier",
                    "mtn-sim-verification", "hlr-lookup",
                    "identity-document", "identity-kyc",
                    "address-validation", "ip-geolocation",
                    "ip-reputation", "mapping-tiles", "mapping-geocode",
                    "location-operator", "location-consented-app"):
        assert adapter in specs
    for spec in body["connectors"]:
        assert spec["name"] and spec["category"] and spec["auth"]
        assert spec["capabilities"]
        assert isinstance(spec["config_params"], list)
        assert isinstance(spec["secret_refs"], list)


def test_create_unknown_adapter_400(tmp_store):
    with pytest.raises(main.AppError) as exc:
        main.connection_create({"adapter": "nope", "name": "x"},
                               _req("/api/v1/connections"))
    assert exc.value.code == "CONNECTOR_UNKNOWN"
    assert exc.value.status == 400


def test_loopback_full_lifecycle(tmp_store):
    created = _body(main.connection_create(
        {"adapter": "loopback", "name": "harness-1"},
        _req("/api/v1/connections")))
    cid = created["id"]
    assert created["status"] == "DRAFT"
    assert created["synthetic"] is True

    configured = _body(main.connection_configure(
        cid, {"params": {}}, _req("/x")))
    assert configured["status"] == "CONFIGURED"

    verified = _body(main.connection_verify(cid, _req("/x")))
    assert verified == {"id": cid, "ok": True, "status": "CONNECTED",
                        "reason": "harness echo ok"}

    health = _body(main.connection_health(cid, _req("/x")))
    assert health["ok"] is True and health["status"] == "CONNECTED"
    assert health["auto_suspended"] is False
    assert isinstance(health["latency_ms"], int)

    suspended = _body(main.connection_suspend(
        cid, {"reason": "maintenance window"}, _req("/x")))
    assert suspended["status"] == "SUSPENDED"

    reverified = _body(main.connection_verify(cid, _req("/x")))
    assert reverified["status"] == "CONNECTED"

    revoked = _body(main.connection_revoke(
        cid, {"reason": "harness retired"}, _req("/x")))
    assert revoked["status"] == "REVOKED"

    with pytest.raises(main.AppError) as exc:
        main.connection_verify(cid, _req("/x"))
    assert exc.value.code == "CONNECTOR_STATUS"
    assert exc.value.status == 409

    actions = [e.get("action")
               for e in tmp_store.state.get("audits", [])]
    for expected in ("connector.create", "connector.configure",
                     "connector.verify", "connector.health",
                     "connector.suspend", "connector.revoke"):
        assert expected in actions


def test_real_adapter_verify_honest_without_credentials(tmp_store):
    created = _body(main.connection_create(
        {"adapter": "banking-rest", "name": "bank-1"},
        _req("/api/v1/connections")))
    cid = created["id"]
    main.connection_configure(cid, {"params": BANKING_PARAMS}, _req("/x"))
    result = _body(main.connection_verify(cid, _req("/x")))
    assert result["ok"] is False
    assert result["status"] == "FAILED"
    assert "CS_CONN_BANKING_KEY" in result["reason"]
    assert "awaiting credentials" in result["reason"]


def test_credentials_present_but_no_fake_connection(monkeypatch,
                                                    tmp_store):
    monkeypatch.setenv("CS_CONN_BANKING_KEY", SECRET_VALUE)
    created = _body(main.connection_create(
        {"adapter": "banking-rest", "name": "bank-2"},
        _req("/api/v1/connections")))
    cid = created["id"]
    main.connection_configure(cid, {"params": BANKING_PARAMS}, _req("/x"))
    result = _body(main.connection_verify(cid, _req("/x")))
    assert result["ok"] is False
    assert result["status"] == "FAILED"
    assert "partner endpoint authorization" in result["reason"]
    detail = main.connection_detail(cid)
    assert detail["secret_present"] == {"CS_CONN_BANKING_KEY": True}
    # The VALUE never persists and never appears in any output.
    blob = json.dumps(tmp_store.state)
    assert SECRET_VALUE not in blob
    assert SECRET_VALUE not in json.dumps(detail)
    assert SECRET_VALUE not in json.dumps(result)


def test_configure_validates_params(tmp_store):
    cid = _body(main.connection_create(
        {"adapter": "banking-rest", "name": "bank-3"},
        _req("/api/v1/connections")))["id"]
    with pytest.raises(main.AppError) as exc:
        main.connection_configure(cid, {"params": {"base_url": "x"}},
                                  _req("/x"))
    assert exc.value.code == "CONNECTOR_CONFIG"
    with pytest.raises(main.AppError) as exc:
        main.connection_configure(
            cid, {"params": dict(BANKING_PARAMS, api_key="smuggled")},
            _req("/x"))
    assert exc.value.code == "CONNECTOR_CONFIG"


def test_illegal_transitions_rejected(tmp_store):
    cid = _body(main.connection_create(
        {"adapter": "loopback", "name": "harness-2"},
        _req("/api/v1/connections")))["id"]
    with pytest.raises(main.AppError) as exc:
        main.connection_health(cid, _req("/x"))
    assert exc.value.code == "CONNECTOR_STATUS"
    with pytest.raises(main.AppError) as exc:
        main.connection_suspend(cid, {"reason": "x"}, _req("/x"))
    assert exc.value.code == "CONNECTOR_STATUS"
    main.connection_configure(cid, {"params": {}}, _req("/x"))
    main.connection_verify(cid, _req("/x"))
    with pytest.raises(main.AppError) as exc:
        main.connection_verify(cid, _req("/x"))
    assert exc.value.code == "CONNECTOR_STATUS"
    assert exc.value.status == 409
    main.connection_revoke(cid, {"reason": "done"}, _req("/x"))
    with pytest.raises(main.AppError) as exc:
        main.connection_revoke(cid, {"reason": "again"}, _req("/x"))
    assert exc.value.code == "CONNECTOR_STATUS"


def test_suspend_revoke_require_reason(tmp_store):
    cid = _body(main.connection_create(
        {"adapter": "loopback", "name": "harness-3"},
        _req("/api/v1/connections")))["id"]
    main.connection_configure(cid, {"params": {}}, _req("/x"))
    with pytest.raises(main.AppError) as exc:
        main.connection_suspend(cid, {"reason": "  "}, _req("/x"))
    assert exc.value.code == "CONNECTOR_REASON_REQUIRED"
    with pytest.raises(main.AppError) as exc:
        main.connection_revoke(cid, {}, _req("/x"))
    assert exc.value.code == "CONNECTOR_REASON_REQUIRED"


def test_health_auto_suspends_after_3_failures(monkeypatch, tmp_store):
    monkeypatch.setattr(conn_mod, "probe_connection",
                        lambda record: (False, "timeout", 5))
    cid = _body(main.connection_create(
        {"adapter": "loopback", "name": "harness-4"},
        _req("/api/v1/connections")))["id"]
    main.connection_configure(cid, {"params": {}}, _req("/x"))
    # Verify uses the handshake path (unpatched); only probes fail.
    main.connection_verify(cid, _req("/x"))
    first = _body(main.connection_health(cid, _req("/x")))
    assert first["consecutive_failures"] == 1
    assert first["auto_suspended"] is False
    main.connection_health(cid, _req("/x"))
    third = _body(main.connection_health(cid, _req("/x")))
    assert third["consecutive_failures"] == 3
    assert third["auto_suspended"] is True
    assert third["status"] == "SUSPENDED"


def test_write_gated(monkeypatch, tmp_store):
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "tok-123")
    with pytest.raises(main.AppError) as exc:
        main.connection_create({"adapter": "loopback", "name": "x"},
                               _req("/api/v1/connections"))
    assert exc.value.code == "WRITE_TOKEN_REQUIRED"
    created = _body(main.connection_create(
        {"adapter": "loopback", "name": "x"},
        _req("/api/v1/connections", token="tok-123")))
    assert created["status"] == "DRAFT"


def test_unknown_connection_404(tmp_store):
    with pytest.raises(main.AppError) as exc:
        main.connection_detail("conn_nope")
    assert exc.value.code == "CONNECTION_NOT_FOUND"
    assert exc.value.status == 404
    with pytest.raises(main.AppError) as exc:
        main.connection_verify("conn_nope", _req("/x"))
    assert exc.value.code == "CONNECTION_NOT_FOUND"


def test_failed_can_reconfigure_and_retry(tmp_store):
    cid = _body(main.connection_create(
        {"adapter": "banking-rest", "name": "bank-4"},
        _req("/api/v1/connections")))["id"]
    main.connection_configure(cid, {"params": BANKING_PARAMS}, _req("/x"))
    first = _body(main.connection_verify(cid, _req("/x")))
    assert first["status"] == "FAILED"
    retry = _body(main.connection_configure(
        cid, {"params": BANKING_PARAMS}, _req("/x")))
    assert retry["status"] == "CONFIGURED"
    second = _body(main.connection_verify(cid, _req("/x")))
    assert second["status"] == "FAILED"


def test_list_and_tenant_recorded(tmp_store):
    first = _body(main.connection_create(
        {"adapter": "loopback", "name": "a"}, _req("/x")))["id"]
    second = _body(main.connection_create(
        {"adapter": "loopback", "name": "b"}, _req("/x")))["id"]
    body = main.connections_list()
    assert body["count"] == 2
    assert {c["id"] for c in body["connections"]} == {first, second}
    assert {c["tenant"] for c in body["connections"]} == {
        tenancy_mod.DEFAULT_TENANT}
