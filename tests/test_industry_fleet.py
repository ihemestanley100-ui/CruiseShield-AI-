"""45-industry fleet integrity: every registry entry resolves to a
tested adapter configuration with valid rule references."""
from __future__ import annotations

import re
from pathlib import Path

from app import industries as ind
from app import industry_adapters as adapters

ROOT = Path(__file__).resolve().parent.parent
RULE_IDS = {"R-001", "R-002", "R-003", "R-004",
            "R-005", "R-006", "R-007", "R-008"}


def test_registry_count_and_ids():
    entries = ind.registry()
    assert len(entries) == 45
    ids = [e["id"] for e in entries]
    assert len(set(ids)) == 45
    assert all(e["name"] and e["status"] for e in entries)


def test_every_industry_builds_config():
    failures = []
    for entry in ind.registry():
        try:
            config = adapters.build_config(entry["id"])
        except Exception as exc:  # noqa: BLE001 - collected, not hidden
            failures.append((entry["id"], repr(exc)))
            continue
        assert config["industry_id"] == entry["id"]
        assert config["registry_status"] == entry["status"]
    assert failures == []


def test_profile_rule_refs_valid():
    bad = []
    for module in sorted((ROOT / "app").glob("industries_*.py")):
        text = module.read_text(encoding="utf-8")
        refs = set(re.findall(r"R-0\d\d", text))
        unknown = refs - RULE_IDS
        if unknown:
            bad.append((module.name, sorted(unknown)))
    assert bad == []


def test_profile_test_files_present():
    missing = []
    for entry in ind.registry():
        config = adapters.build_config(entry["id"])
        if config["profile_present"] and not config["test_present"]:
            missing.append(entry["id"])
    assert missing == []


def test_typology_industry_refs_resolve():
    known = {e["id"] for e in ind.registry()}
    from app import typologies as typo
    bad = []
    for row in typo.list_typologies():
        for ref in row["industries"]:
            if ref not in known:
                bad.append((row["typology_id"], ref))
    assert bad == []


def test_fleet_snapshot_shape():
    snap = adapters.fleet_readiness({"T-01": 2})
    assert snap["total"] == 45
    assert snap["ready"] + snap["not_ready"] == 45
    for row in snap["industries"]:
        assert set(row["checks"]) == {"profile_present", "tests_present",
                                      "typologies_mapped",
                                      "typologies_measured",
                                      "status_gate"}
