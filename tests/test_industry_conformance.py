"""Industry conformance: 45-profile sweep + honesty/promote gates."""
import copy
import importlib
import json
import pathlib

import pytest
from starlette.requests import Request

import app.main as main
from app import industries as ind_mod
from app import pilot as pilot_mod
from app.industries_banking import PROFILE as BANKING_PROFILE

APP = pathlib.Path(main.__file__).resolve().parent


def _req():
    return Request({"type": "http", "method": "POST", "path": "/x",
                    "headers": [(b"host", b"t")]})


def _walk_banking_to_testing():
    ind_mod.register_profile("banking", BANKING_PROFILE)
    current, _ = ind_mod.module_status("banking")
    if current == "TESTING":
        return
    if current == "PILOT":
        ind_mod.set_status("banking", "TESTING", "conformance")
        return
    order = ("DISCOVERY", "DESIGNED", "IN_DEVELOPMENT", "TESTING")
    start = order.index(current) + 1 if current in order else 0
    for status in order[start:]:
        ind_mod.set_status("banking", status, "conformance")


def test_all_45_profiles_conform_to_keys():
    ids = {entry["id"] for entry in ind_mod.registry()}
    seen = set()
    modules = sorted(p for p in APP.glob("industries_*.py")
                     if p.name != "industries.py")
    assert len(modules) == 45
    for path in modules:
        profile = importlib.import_module("app." + path.stem).PROFILE
        missing = [k for k in ind_mod.PROFILE_KEYS if k not in profile]
        assert not missing, (path.name, missing)
        assert profile["id"] in ids, path.name
        seen.add(profile["id"])
    assert seen == ids


def test_honesty_gate_rejects_claimed_certification():
    original = copy.deepcopy(BANKING_PROFILE)
    ind_mod.register_profile("banking", original)
    mutated = copy.deepcopy(original)
    if not mutated["compliance"]:
        mutated["compliance"] = [{"id": "x",
                                  "certification": "CLAIMED-CERT"}]
    else:
        mutated["compliance"][0]["certification"] = "CLAIMED-CERT"
    try:
        ind_mod.register_profile("banking", mutated)
        report = pilot_mod.evaluate("banking")
    finally:
        ind_mod.register_profile("banking", original)
    assert report["checks"]["compliance_honest"] is False
    assert any("certification claimed" in g for g in report["gaps"])
    assert report["ready"] is False


def test_promote_route_errors(tmp_store):
    with pytest.raises(main.AppError) as exc:
        main.industry_promote("nope", {"evidence": "x"}, _req())
    assert (exc.value.code, exc.value.status) == ("INDUSTRY_UNKNOWN", 404)
    with pytest.raises(main.AppError) as exc:
        main.industry_promote("banking", {"evidence": "  "}, _req())
    assert (exc.value.code, exc.value.status) == (
        "INDUSTRY_EVIDENCE_REQUIRED", 400)


def test_promote_route_success_and_audit(tmp_store):
    _walk_banking_to_testing()
    report = pilot_mod.evaluate("banking")
    assert report["ready"] is True
    try:
        resp = main.industry_promote(
            "banking", {"evidence": "charter-conformance-1"}, _req())
    finally:
        current, _ = ind_mod.module_status("banking")
        if current == "PILOT":
            ind_mod.set_status("banking", "TESTING", "conformance restore")
    assert resp.status_code == 200
    assert json.loads(resp.body) == {"id": "banking", "status": "PILOT"}
    assert any(a["action"] == "industry.promote" and
               a["target_id"] == "banking"
               for a in tmp_store.state["audits"])
