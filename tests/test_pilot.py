"""PHASE H: pilot-readiness evaluator + TESTING->PILOT promotion."""
import copy
import importlib
import json
import pkgutil

import pytest
from starlette.requests import Request

import app as _app_pkg
import app.main as main
from app import config as config_mod
from app import industries as ind_mod
from app import pilot as pilot_mod


def _profile_map():
    mapping = {}
    for info in pkgutil.iter_modules(_app_pkg.__path__, "app."):
        if ".industries_" not in info.name:
            continue
        profile = importlib.import_module(info.name).PROFILE
        mapping[profile["id"]] = profile
    return mapping


PROFILES = _profile_map()


def _ensure_testing(ident):
    """Register + walk a module to TESTING (idempotent, order-safe)."""
    ind_mod.register_profile(ident, PROFILES[ident])
    for target in ("IN_DEVELOPMENT", "TESTING"):
        if ind_mod.module_status(ident)[0] not in ("TESTING", "PILOT",
                                                   "OPERATIONAL",
                                                   "VERIFIED"):
            try:
                ind_mod.set_status(ident, target, "test setup")
            except ValueError:
                break
    return ident


def _scope(path, method="GET", token=None):
    headers = [(b"host", b"t")]
    if token is not None:
        headers.append((b"authorization", ("Bearer %s" % token).encode()))
    return {"type": "http", "method": method, "scheme": "http",
            "server": ("t", 80), "client": ("9.9.9.9", 1234),
            "path": path, "query_string": b"", "headers": headers}


def test_profile_map_covers_all_45():
    assert len(PROFILES) == 45
    assert {e["id"] for e in ind_mod.registry()} == set(PROFILES)


def test_evaluate_banking_ready_with_declared_externals():
    _ensure_testing("banking")
    report = pilot_mod.evaluate("banking")
    assert report["status"] == "TESTING"
    assert report["ready"] is True
    assert report["gaps"] == []
    assert all(report["checks"].values())
    assert set(report["checks"]) == {
        "profile_registered", "taxonomy_mapped", "scenarios_mapped",
        "detection_rules_valid", "workflows_routed", "reports_routed",
        "permissions_valid", "data_declared", "compliance_honest"}
    # External deps inform pilot scope; they do not fail readiness.
    assert set(report["external"]) == {
        "KYC identity records", "sanctions/watchlist feed"}


def test_evaluate_unknown_module():
    with pytest.raises(ValueError, match="INDUSTRY_UNKNOWN"):
        pilot_mod.evaluate("no-such-industry")


def test_evaluate_detects_gaps(monkeypatch):
    _ensure_testing("fintech-payments")
    bad = copy.deepcopy(PROFILES["fintech-payments"])
    bad["risk_taxonomy"][0]["rules"] = ["R-999"]
    bad["workflows"][0]["steps"] = ["GET /api/v1/no-such-route"]
    bad["permissions"] = {"triage": ["superuser"]}
    bad["compliance"] = [{"id": "X", "certification": "CLAIMED"}]
    real_get = ind_mod.get_profile
    monkeypatch.setattr(ind_mod, "get_profile",
                        lambda ident: bad if ident == "fintech-payments"
                        else real_get(ident))
    report = pilot_mod.evaluate("fintech-payments")
    assert report["ready"] is False
    assert report["checks"]["taxonomy_mapped"] is False
    assert report["checks"]["workflows_routed"] is False
    assert report["checks"]["permissions_valid"] is False
    assert report["checks"]["compliance_honest"] is False
    assert any("R-999" in gap for gap in report["gaps"])
    assert any("no-such-route" in gap for gap in report["gaps"])


def test_promote_happy_path_audited(tmp_store):
    _ensure_testing("hospitality")
    req = Request(_scope("/api/v1/industries/hospitality/promote",
                         method="POST"))
    resp = main.industry_promote(
        "hospitality", {"evidence": "pilot charter PC-001 signed"}, req)
    assert resp.status_code == 200
    assert json.loads(resp.body.decode()) == {"id": "hospitality",
                                              "status": "PILOT"}
    assert ind_mod.module_status("hospitality")[0] == "PILOT"
    actions = [e.get("action")
               for e in tmp_store.state.get("audits", [])]
    assert "industry.promote" in actions


def test_promote_blocked_when_gaps(monkeypatch, tmp_store):
    _ensure_testing("environmental")
    bad = copy.deepcopy(PROFILES["environmental"])
    bad["detection_rules"] = []
    real_get = ind_mod.get_profile
    monkeypatch.setattr(ind_mod, "get_profile",
                        lambda ident: bad if ident == "environmental"
                        else real_get(ident))
    req = Request(_scope("/api/v1/industries/environmental/promote",
                         method="POST"))
    with pytest.raises(main.AppError) as exc:
        main.industry_promote("environmental", {"evidence": "x"}, req)
    assert exc.value.code == "PILOT_NOT_READY"
    assert exc.value.status == 409
    assert ind_mod.module_status("environmental")[0] == "TESTING"


def test_promote_rejects_non_testing_and_unknown(monkeypatch, tmp_store):
    _ensure_testing("media")
    real_status = ind_mod.module_status
    monkeypatch.setattr(ind_mod, "module_status",
                        lambda ident: ("DESIGNED", "")
                        if ident == "media" else real_status(ident))
    req = Request(_scope("/api/v1/industries/media/promote",
                         method="POST"))
    with pytest.raises(main.AppError) as exc:
        main.industry_promote("media", {"evidence": "x"}, req)
    assert exc.value.code == "PILOT_STATUS"
    with pytest.raises(main.AppError) as exc:
        main.industry_promote(
            "no-such-industry", {"evidence": "x"}, req)
    assert exc.value.code == "INDUSTRY_UNKNOWN"
    assert exc.value.status == 404


def test_promote_requires_evidence(tmp_store):
    _ensure_testing("transport")
    req = Request(_scope("/api/v1/industries/transport/promote",
                         method="POST"))
    with pytest.raises(main.AppError) as exc:
        main.industry_promote("transport", {"evidence": "  "}, req)
    assert exc.value.code == "INDUSTRY_EVIDENCE_REQUIRED"
    assert exc.value.status == 400


def test_promote_write_gated(monkeypatch, tmp_store):
    _ensure_testing("retail")
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "tok-123")
    denied = Request(_scope("/api/v1/industries/retail/promote",
                            method="POST"))
    with pytest.raises(main.AppError) as exc:
        main.industry_promote("retail", {"evidence": "charter"}, denied)
    assert exc.value.code == "WRITE_TOKEN_REQUIRED"
    allowed = Request(_scope("/api/v1/industries/retail/promote",
                             method="POST", token="tok-123"))
    resp = main.industry_promote("retail", {"evidence": "charter"},
                                 allowed)
    assert resp.status_code == 200


def test_readiness_endpoint_shape():
    _ensure_testing("banking")
    body = main.industries_pilot_readiness()
    assert body["total"] == 45
    assert len(body["modules"]) == 45
    assert body["ready_count"] == len(body["ready_ids"])
    for row in body["modules"]:
        assert set(row) >= {"id", "status", "ready", "checks", "gaps",
                            "external"}
    banking = next(r for r in body["modules"] if r["id"] == "banking")
    assert banking["ready"] is True
