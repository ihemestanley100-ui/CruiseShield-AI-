"""Adversarial tenant isolation through the real API handlers.

Socket-free: direct handler calls with the tenant resolver seam
patched. tmp_store (conftest) points main.store at a fresh seed.
"""
import pytest
from starlette.requests import Request

import app.main as main
from app import cases as cases_mod
from app.tenancy import (DEFAULT_TENANT, TenantContext, register_tenant)

BETA = "org_beta"


@pytest.fixture(autouse=True)
def _beta():
    register_tenant(BETA)
    yield


def _req():
    return Request({"type": "http", "method": "GET", "headers": [],
                    "path": "/"})


def _as_beta(monkeypatch):
    monkeypatch.setattr(
        main, "_request_ctx",
        lambda request=None: TenantContext(tenant_id=BETA, actor="bob"))


def _beta_case():
    return {"case_id": "case_beta", "investigation_id": "inv_84721",
            "status": "NEW", "tenant_id": BETA}


def _decision_body():
    return {"decision": "Escalate", "target_status": "TRIAGED",
            "reason": "Adversarial tenant probe.", "actor_id": "bob"}


def test_list_excludes_foreign_both_directions(tmp_store, monkeypatch):
    tmp_store.state["cases"].append(_beta_case())
    alpha_ids = {c["case_id"] for c in main.list_cases()["cases"]}
    assert "case_beta" not in alpha_ids and "case_84721" in alpha_ids
    _as_beta(monkeypatch)
    beta_ids = {c["case_id"] for c in main.list_cases()["cases"]}
    assert beta_ids == {"case_beta"}


def test_foreign_case_read_is_404(tmp_store, monkeypatch):
    _as_beta(monkeypatch)
    with pytest.raises(main.AppError) as exc:
        main.get_case("case_84721")
    assert (exc.value.code, exc.value.status) == ("CASE_NOT_FOUND", 404)


def test_own_case_read_ok(tmp_store, monkeypatch):
    tmp_store.state["cases"].append(_beta_case())
    _as_beta(monkeypatch)
    detail = main.get_case("case_beta")
    assert detail["case"]["case_id"] == "case_beta"


def test_foreign_case_audit_is_404(tmp_store, monkeypatch):
    _as_beta(monkeypatch)
    with pytest.raises(main.AppError) as exc:
        main.case_audit("case_84721")
    assert exc.value.status == 404


def test_foreign_investigation_is_404(tmp_store, monkeypatch):
    tmp_store.state["investigations"][0]["tenant_id"] = BETA
    with pytest.raises(main.AppError) as exc:
        main.get_investigation("inv_84721")
    assert exc.value.code == "UNKNOWN_INVESTIGATION"
    _as_beta(monkeypatch)
    got = main.get_investigation("inv_84721")
    assert got["investigation"]["investigation_id"] == "inv_84721"


def test_cross_tenant_decision_is_404_no_oracle(tmp_store, monkeypatch):
    _as_beta(monkeypatch)
    with pytest.raises(main.AppError) as exc:
        main.post_decision("case_84721", _decision_body(), _req())
    assert (exc.value.code, exc.value.status) == ("CASE_NOT_FOUND", 404)
    assert tmp_store.state["decisions"] == []


def test_tenant_denied_maps_to_403():
    from app.tenancy import TenantDeniedError

    err = main._domain_error(TenantDeniedError("TENANT_DENIED: x"))
    assert (err.code, err.status) == ("TENANT_DENIED", 403)


def test_same_tenant_decision_stamped(tmp_store, monkeypatch):
    tmp_store.state["cases"].append(_beta_case())
    _as_beta(monkeypatch)
    out = main.post_decision("case_beta", _decision_body(), _req())
    assert out["decision"]["tenant_id"] == BETA
    assert out["case"]["status"] == "TRIAGED"


def test_default_decision_stamped_default(tmp_store):
    out = main.post_decision("case_84721", _decision_body(), _req())
    assert out["decision"]["tenant_id"] == DEFAULT_TENANT


def test_domain_cross_tenant_write_is_not_found(tmp_store):
    ctx = TenantContext(tenant_id=BETA, actor="bob")
    with pytest.raises(ValueError, match="CASE_NOT_FOUND"):
        cases_mod.record_decision(tmp_store, "case_84721", "Escalate",
                                  "TRIAGED", "probe", "bob", tenant=ctx)
