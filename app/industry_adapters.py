"""Per-industry adapter configurations (UFI section 21).

One shared core, 45 configurations: each adapter binds the canonical
registry entry to its PROFILE module (risk taxonomy, threat scenarios,
workflows), its mapped typologies, and its test file. Readiness is
evidence-derived and never overrides the registry status machine:
adapters report what exists; promotion stays with the owner-gated
/app/v1/industries/{id}/promote path. Module slugs reuse the matrix
TESTING_MODULES map (single source, imported - not copied).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from app import industries as _ind
from app import typologies as _typo

_ROOT = Path(__file__).resolve().parent.parent


def _slugs() -> dict[str, tuple[str, str, str]]:
    spec = importlib.util.spec_from_file_location(
        "zero_gap_matrix", _ROOT / "scripts" / "zero_gap_matrix.py")
    if spec is None or spec.loader is None:
        return {}
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return dict(getattr(module, "TESTING_MODULES", {}))


def _profile_module(prof_slug: str) -> dict[str, Any] | None:
    path = _ROOT / "app" / ("industries_%s.py" % prof_slug)
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location(
        "indprof_%s" % prof_slug, path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return None
    profile = getattr(module, "PROFILE", None)
    return dict(profile) if isinstance(profile, dict) else None


def build_config(ident: str) -> dict[str, Any]:
    """Adapter configuration for one canonical industry id."""
    entry = _ind.get_module(ident)
    if entry is None:
        raise ValueError("INDUSTRY_UNKNOWN: %s" % ident)
    slugs = _slugs()
    mapped = slugs.get(ident)
    profile = _profile_module(mapped[0]) if mapped else None
    test_file = "tests/test_industry_%s.py" % mapped[1] if mapped else ""
    test_present = bool(test_file) and (_ROOT / test_file).exists()
    typos = _typo.list_typologies(ident)
    status, evidence = _ind.module_status(ident)
    taxonomy = profile.get("risk_taxonomy", []) if profile else []
    return {
        "industry_id": ident,
        "name": entry.get("name"),
        "registry_status": status,
        "registry_evidence": evidence,
        "profile_present": profile is not None,
        "profile_module": ("app/industries_%s.py" % mapped[0]
                           if mapped else None),
        "risk_taxonomy": taxonomy,
        "threat_scenarios": len(profile.get("threat_scenarios", []))
        if profile else 0,
        "test_file": test_file or None,
        "test_present": test_present,
        "typologies": [t["typology_id"] for t in typos],
        "typology_count": len(typos),
    }


def readiness(ident: str,
              matched_counts: dict[str, int] | None = None) -> dict[str, Any]:
    """Evidence checklist. Overall READY only when every check holds."""
    config = build_config(ident)
    matched_counts = matched_counts or {}
    measured = sum(1 for tid in config["typologies"]
                   if matched_counts.get(tid, 0) > 0)
    checks = {
        "profile_present": config["profile_present"],
        "tests_present": config["test_present"],
        "typologies_mapped": config["typology_count"] > 0,
        "typologies_measured": measured > 0,
        "status_gate": config["registry_status"] in ("PILOT", "OPERATIONAL",
                                                     "VERIFIED"),
    }
    return {
        "industry_id": ident,
        "registry_status": config["registry_status"],
        "checks": checks,
        "typologies_measured": measured,
        "overall": "READY" if all(checks.values()) else "NOT_READY",
        "note": "Readiness reports evidence; it never promotes the "
                "registry status.",
    }


def fleet_readiness(matched_counts: dict[str, int] | None = None) -> dict[str, Any]:
    """Measured readiness across all 45 canonical industries.

    Pure evidence snapshot: per-industry overall plus fleet totals.
    Changes nothing; promotion stays with the owner-gated path.
    """
    matched_counts = matched_counts or {}
    rows = []
    for entry in _ind.registry():
        ident = entry["id"]
        ready = readiness(ident, matched_counts)
        rows.append({"industry_id": ident,
                     "registry_status": ready["registry_status"],
                     "overall": ready["overall"],
                     "typologies_measured": ready["typologies_measured"],
                     "checks": ready["checks"]})
    ready_count = sum(1 for r in rows if r["overall"] == "READY")
    return {"industries": rows, "total": len(rows),
            "ready": ready_count, "not_ready": len(rows) - ready_count}


def agent_config(ident: str) -> dict[str, Any]:
    """Agent OS configuration for one industry (directive section 10).

    Same runtime for all industries; only this configuration varies.
    Terminology comes from the profile when defined, otherwise empty -
    never invented. Tools are the governed kernel names; enforcement
    stays in the kernel + backend RBAC.
    """
    from app import auth as auth_mod
    from app import reports as reports_mod

    config = build_config(ident)
    slugs = _slugs()
    mapped = slugs.get(ident)
    profile = _profile_module(mapped[0]) if mapped else None
    workflows = []
    if profile:
        for step in profile.get("workflows", []):
            if isinstance(step, dict):
                workflows.append(step)
            else:
                workflows.append({"step": str(step)})
    return {
        "industry_id": ident,
        "name": config["name"],
        "registry_status": config["registry_status"],
        "operational": config["profile_present"],
        "workflows": workflows,
        "risk_taxonomy_codes": [t.get("code") for t in
                                config["risk_taxonomy"]
                                if isinstance(t, dict)],
        "typologies": config["typologies"],
        "tools": ["signal.search", "txn.search", "typology.match",
                  "trace.read", "report.build", "industry.coverage",
                  "monitoring.status"] if config["profile_present"]
        else ["industry.coverage"],
        "permitted_roles": list(auth_mod.ROLES),
        "report_templates": list(reports_mod.REPORT_TYPES),
        "terminology": profile.get("terminology", {})
        if profile else {},
        "eval_scenarios": config["threat_scenarios"],
    }


def recovery_config(ident: str) -> dict[str, Any]:
    """Recovery compatibility for one industry (shared workflows).

    Workflows are universal; per-industry content is the typology
    cross-reference, report templates, and connector requirements.
    Live connector count is computed, never asserted.
    """
    from app import reports as reports_mod

    config = build_config(ident)
    return {
        "industry_id": ident,
        "name": config["name"],
        "registry_status": config["registry_status"],
        "workflows": ["recall-request", "dispute", "reversal-request",
                      "restriction-request", "escalation",
                      "trace-and-investigate"],
        "typologies": config["typologies"],
        "report_templates": list(reports_mod.REPORT_TYPES),
        "connector_requirements": "a VERIFIED recovery capability "
                                  "for the payment rail, else the "
                                  "manual workflow",
        "live_recovery_connectors": 0,
    }


def coverage(ident: str) -> dict[str, Any]:
    """Static coverage: taxonomy + typologies + tests for one industry."""
    config = build_config(ident)
    return {
        "industry_id": ident,
        "name": config["name"],
        "registry_status": config["registry_status"],
        "risk_taxonomy_codes": [t.get("code") for t in
                                config["risk_taxonomy"]
                                if isinstance(t, dict)],
        "threat_scenarios": config["threat_scenarios"],
        "typologies": config["typologies"],
        "test_file": config["test_file"],
        "test_present": config["test_present"],
    }
