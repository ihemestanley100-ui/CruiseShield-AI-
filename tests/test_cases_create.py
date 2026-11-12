"""D-036 case creation API: validation, tenancy, audit. Socket-free."""
import pytest
from starlette.requests import Request

import app.config as config_mod
import app.main as main
from app import auth as auth_mod
from app.tenancy import DEFAULT_TENANT, TenantContext, register_tenant

SECRET = "test-secret-case-create-032-chars!!"
TOKEN = "test-platform-token-case-not-secret"
RECORD = auth_mod.hash_password("pw-case")


def _req(headers=None):
    scope = {"type": "http", "method": "POST", "path": "/api/v1/cases",
             "headers": [(b"host", b"t")] + list(headers or [])}
    return Request(scope)


def _as_beta(monkeypatch):
    register_tenant("beta")
    monkeypatch.setattr(
        main, "_request_ctx",
        lambda request=None: TenantContext(tenant_id="beta", actor="bob"))


def _as_default(monkeypatch):
    monkeypatch.setattr(
        main, "_request_ctx",
        lambda request=None: TenantContext(tenant_id=DEFAULT_TENANT,
                                           actor="anonymous"))


def test_create_minimal(tmp_store):
    body = main.post_case({"title": "Follow up on txn_84721"}, _req())
    case = body["case"]
    assert case["status"] == "NEW"
    assert case["case_id"].startswith("case_")
    assert case["priority"] == "MEDIUM"
    assert body["audit"]["action"] == "case.opened"
    assert body["audit"]["target_id"] == case["case_id"]
    stored = tmp_store.get_case(case["case_id"])
    assert stored["title"] == "Follow up on txn_84721"


def test_create_full_fields(tmp_store):
    inv = tmp_store.state["investigations"][0]["investigation_id"]
    body = main.post_case({
        "title": "Mule ring", "description": "Three-account fan-in",
        "priority": "HIGH", "assignee": "judge",
        "due_date": "2026-12-01", "notes": "Start with device graph",
        "investigation_id": inv}, _req())
    case = body["case"]
    assert (case["priority"], case["assignee"],
            case["due_date"]) == ("HIGH", "judge", "2026-12-01")
    assert case["investigation_id"] == inv
    assert "device graph" in case["notes"]
    assert case["description"] == "Three-account fan-in"


def test_create_rejects_bad_input(tmp_store):
    bad = [
        ({}, "TITLE_REQUIRED", 400),
        ({"title": "   "}, "TITLE_REQUIRED", 400),
        ({"title": "t" * 201}, "TITLE_TOO_LONG", 400),
        ({"title": "t", "priority": "URGENT"}, "PRIORITY_UNKNOWN", 400),
        ({"title": "t", "due_date": "12/01/2026"}, "DUE_DATE_INVALID", 400),
        ({"title": "t", "due_date": "2026-13-99"}, "DUE_DATE_INVALID", 400),
        ({"title": "t", "investigation_id": "inv_nope"},
         "INVESTIGATION_NOT_FOUND", 404),
        ({"title": "t", "assignee": "a" * 257}, "ASSIGNEE_TOO_LONG", 400),
        ({"title": "t", "notes": "n" * 10001}, "NOTES_TOO_LONG", 400),
    ]
    for payload, code, status in bad:
        with pytest.raises(main.AppError) as exc:
            main.post_case(payload, _req())
        assert (exc.value.code, exc.value.status) == (code, status)
    with pytest.raises(main.AppError) as exc:
        main.post_case(["not", "a", "dict"], _req())
    assert (exc.value.code, exc.value.status) == ("INVALID_BODY", 400)
    assert len(tmp_store.state["cases"]) == 1


def test_create_tenant_isolated(tmp_store, monkeypatch):
    _as_beta(monkeypatch)
    body = main.post_case({"title": "beta case"}, _req())
    assert body["case"]["tenant_id"] == "beta"
    _as_default(monkeypatch)
    with pytest.raises(main.AppError) as exc:
        main.get_case(body["case"]["case_id"], _req())
    assert (exc.value.code, exc.value.status) == ("CASE_NOT_FOUND", 404)


def test_create_armed_write_gate(tmp_store, monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(
        config_mod, "DEMO_USERS", "judge:investigator:%s" % RECORD)
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", TOKEN)
    with pytest.raises(main.AppError) as exc:
        main.post_case({"title": "t"}, _req())
    assert (exc.value.code, exc.value.status) == (
        "WRITE_TOKEN_REQUIRED", 401)
    authed = main.post_case(
        {"title": "t"},
        _req([(b"authorization", b"Bearer " + TOKEN.encode())]))
    assert authed["audit"]["actor_id"] == "platform-token"


def test_created_case_in_detail_and_audit_view(tmp_store):
    case_id = main.post_case({"title": "t"}, _req())["case"]["case_id"]
    detail = main.get_case(case_id, _req())
    assert detail["case"]["title"] == "t"
    assert detail["allowed_transitions"] == ["TRIAGED", "FALSE_POSITIVE"]
    audits = main.case_audit(case_id, _req())["audits"]
    assert any(a["action"] == "case.opened" and
               a["target_id"] == case_id for a in audits)
