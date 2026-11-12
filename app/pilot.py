"""Industry pilot-readiness evaluator (Level 14 §6/PHASE H).

A module moves TESTING -> PILOT only when every readiness check passes
*and* promotion evidence is supplied. Checks assert the profile against
the live engine (real rule IDs), the live app (real METHOD+path steps),
and the honesty gates (no claimed certifications, external data gaps
declared). BLOCKED_EXTERNAL data requirements are reported as external
dependencies — they inform the pilot scope but do not fail readiness,
because every module truthfully declares them.
"""
from __future__ import annotations

from typing import Any


def _engine_rule_ids() -> set[str]:
    from app import rules as rules_mod

    return {r.rule_id for r in rules_mod.RULES}


def _route_table() -> dict[str, set[str]]:
    from app import main as main_mod

    table: dict[str, set[str]] = {}
    for route in main_mod.app.routes:
        table.setdefault(route.path, set()).update(
            getattr(route, "methods", None) or set())
    return table


def _role_set() -> set[str]:
    from app import auth as auth_mod

    return set(auth_mod.ROLES)


def evaluate(ident: str) -> dict[str, Any]:
    """Evaluate one module. Raises ValueError on unknown id.

    Returns {id, status, ready, checks, gaps, external}. `ready` is True
    only for TESTING modules with zero gaps.
    """
    from app import industries as ind_mod

    if ind_mod.get_module(ident) is None:
        raise ValueError("INDUSTRY_UNKNOWN: %s" % ident)
    status, _ = ind_mod.module_status(ident)
    profile = ind_mod.get_profile(ident)
    checks: dict[str, bool] = {}
    gaps: list[str] = []
    external: list[str] = []

    def check(name: str, ok: bool, gap: str = "") -> None:
        checks[name] = ok
        if not ok and gap:
            gaps.append(gap)

    check("profile_registered", profile is not None,
          "no profile registered" if profile is None else "")
    if profile is None:
        profile = {}
    rules = _engine_rule_ids()
    routes = _route_table()
    roles = _role_set()

    taxonomy = profile.get("risk_taxonomy", [])
    bad_tax = [row for row in taxonomy
               if not isinstance(row, dict) or not row.get("code")
               or not row.get("label") or not row.get("rules")]
    unknown_tax = sorted({r for row in taxonomy if isinstance(row, dict)
                          for r in (row.get("rules") or [])
                          if r not in rules})
    check("taxonomy_mapped", bool(taxonomy) and not bad_tax
          and not unknown_tax,
          ("taxonomy rows missing code/label/rules or unknown engine "
           "rules: %s" % ",".join(unknown_tax)) if
          (not taxonomy or bad_tax or unknown_tax) else "")

    scenarios = profile.get("threat_scenarios", [])
    unknown_scn = sorted({r for row in scenarios
                          if isinstance(row, dict)
                          for r in (row.get("rules") or [])
                          if r not in rules})
    check("scenarios_mapped", bool(scenarios) and not unknown_scn,
          ("threat scenarios empty or unknown engine rules: %s"
           % ",".join(unknown_scn)) if
          (not scenarios or unknown_scn) else "")

    det_rules = [r.get("rule_id") for r in
                 profile.get("detection_rules", [])
                 if isinstance(r, dict)]
    unknown_det = sorted({r for r in det_rules if r not in rules})
    check("detection_rules_valid", bool(det_rules) and not unknown_det,
          ("detection rules empty or unknown engine rules: %s"
           % ",".join(str(r) for r in unknown_det)) if
          (not det_rules or unknown_det) else "")

    steps = [s for flow in profile.get("workflows", [])
             if isinstance(flow, dict)
             for s in (flow.get("steps") or [])]
    bad_steps = [s for s in steps if not _step_resolves(s, routes)]
    check("workflows_routed", bool(steps) and not bad_steps,
          ("workflow steps empty or unresolvable: %s"
           % ";".join(bad_steps[:3])) if
          (not steps or bad_steps) else "")

    sources = [r.get("source") for r in profile.get("reports", [])
               if isinstance(r, dict)]
    bad_sources = [s for s in sources if not _step_resolves(s, routes)]
    check("reports_routed", bool(sources) and not bad_sources,
          ("report sources empty or unresolvable: %s"
           % ";".join(str(s) for s in bad_sources[:3])) if
          (not sources or bad_sources) else "")

    perms = profile.get("permissions", {})
    bad_roles = sorted({r for rs in perms.values() for r in (rs or [])}
                       - roles) if isinstance(perms, dict) else ["?"]
    check("permissions_valid",
          isinstance(perms, dict) and bool(perms) and not bad_roles,
          ("permissions empty or unknown roles: %s"
           % ",".join(bad_roles)) if
          (not isinstance(perms, dict) or not perms or bad_roles)
          else "")

    reqs = profile.get("data_requirements", [])
    bad_reqs = [r for r in reqs
                if not isinstance(r, dict) or not r.get("field")
                or not r.get("status")]
    external = sorted(r["field"] for r in reqs
                      if isinstance(r, dict)
                      and r.get("status") == "BLOCKED_EXTERNAL")
    check("data_declared", bool(reqs) and not bad_reqs,
          "data requirements empty or missing field/status" if
          (not reqs or bad_reqs) else "")

    compliance = profile.get("compliance", [])
    claimed = [c.get("id", "?") for c in compliance
               if isinstance(c, dict)
               and c.get("certification") not in (None, "NOT_CLAIMED")]
    check("compliance_honest", bool(compliance) and not claimed,
          ("compliance empty or certification claimed: %s"
           % ",".join(str(c) for c in claimed)) if
          (not compliance or claimed) else "")

    ready = status == "TESTING" and all(checks.values())
    if status != "TESTING":
        gaps.insert(0, "status is %s, promotion requires TESTING" % status)
    return {"id": ident, "status": status, "ready": ready, "checks": checks,
            "gaps": gaps, "external": external}


def _step_resolves(step: Any, routes: dict[str, set[str]]) -> bool:
    if not isinstance(step, str) or " " not in step:
        return False
    method, _, path = step.partition(" ")
    return path in routes and method in routes[path]


def evaluate_all() -> list[dict[str, Any]]:
    """Evaluate all 45 registered modules in catalogue order."""
    from app import industries as ind_mod

    return [evaluate(entry["id"]) for entry in ind_mod.registry()]


def promote(ident: str, evidence: str) -> dict[str, Any]:
    """Promote a TESTING module to PILOT. Raises ValueError on any gap.

    Error codes: INDUSTRY_UNKNOWN, INDUSTRY_EVIDENCE_REQUIRED,
    PILOT_STATUS (not TESTING), PILOT_NOT_READY (gaps listed).
    """
    from app import industries as ind_mod

    if ind_mod.get_module(ident) is None:
        raise ValueError("INDUSTRY_UNKNOWN: %s" % ident)
    if not (evidence or "").strip():
        raise ValueError("INDUSTRY_EVIDENCE_REQUIRED: promotion needs "
                         "a verifiable evidence reference")
    report = evaluate(ident)
    if report["status"] != "TESTING":
        raise ValueError("PILOT_STATUS: %s is %s, requires TESTING"
                         % (ident, report["status"]))
    if not report["ready"]:
        raise ValueError("PILOT_NOT_READY: %s" % "; ".join(report["gaps"]))
    entry = ind_mod.set_status(ident, "PILOT", evidence.strip())
    report["status"] = "PILOT"
    report["ready"] = False
    report["gaps"] = ["status is PILOT, promotion requires TESTING"]
    report["entry"] = entry
    return report
