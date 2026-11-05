"""Banking pilot: profile integrity asserted against engine + routes."""
import pytest

import app.main as main
from app import auth as auth_mod
from app import industries as ind_mod
from app import rules as rules_mod
from app.industries_banking import PROFILE

RULE_IDS = {r.rule_id for r in rules_mod.RULES}
ROUTES: dict[str, set[str]] = {}
for route in main.app.routes:
    ROUTES.setdefault(route.path, set()).update(
        getattr(route, "methods", None) or set())


def test_profile_registers_and_walks_to_testing():
    ind_mod.register_profile("banking", PROFILE)
    assert ind_mod.module_status("banking")[0] == "DESIGNED"
    with pytest.raises(ValueError, match="TRANSITION_ILLEGAL"):
        ind_mod.set_status("banking", "PILOT", "skip")
    ind_mod.set_status("banking", "IN_DEVELOPMENT", "slice-5 build")
    with pytest.raises(ValueError, match="EVIDENCE_REQUIRED"):
        ind_mod.set_status("banking", "TESTING", "  ")
    entry = ind_mod.set_status(
        "banking", "TESTING", "tests/test_industry_banking.py green")
    assert entry["status"] == "TESTING"
    assert ind_mod.get_profile("banking")["id"] == "banking"


def test_every_mapped_rule_exists_in_engine():
    mapped = set()
    for row in PROFILE["risk_taxonomy"]:
        mapped.update(row["rules"])
    for row in PROFILE["threat_scenarios"]:
        mapped.update(row["rules"])
    mapped.update(r["rule_id"] for r in PROFILE["detection_rules"])
    assert mapped and mapped <= RULE_IDS


def test_every_workflow_and_report_step_resolves_to_route():
    steps = [s for flow in PROFILE["workflows"] for s in flow["steps"]]
    steps += [r["source"] for r in PROFILE["reports"]]
    assert steps
    for step in steps:
        method, _, path = step.partition(" ")
        assert path in ROUTES, step
        assert method in ROUTES[path], step


def test_permissions_use_real_roles():
    assert PROFILE["permissions"]
    for roles in PROFILE["permissions"].values():
        assert set(roles) <= set(auth_mod.ROLES)


def test_external_gaps_declared_not_filled():
    blocked = [d for d in PROFILE["data_requirements"]
               if d["status"] == "BLOCKED_EXTERNAL"]
    assert {d["field"] for d in blocked} == {
        "KYC identity records", "sanctions/watchlist feed"}


def test_no_compliance_certification_claimed():
    assert PROFILE["compliance"]
    assert all(c["certification"] == "NOT_CLAIMED"
               for c in PROFILE["compliance"])


def test_other_44_modules_still_not_started():
    rest = [m for m in ind_mod.registry() if m["id"] != "banking"]
    assert len(rest) == 44
    assert {m["status"] for m in rest} == {"NOT_STARTED"}
