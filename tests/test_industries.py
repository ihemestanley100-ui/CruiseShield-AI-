"""Industry registry contract: 45 modules, unique IDs, valid statuses."""
from app import industries as ind_mod
from app.main import industries_catalog

CAPS = {"transaction-monitoring", "risk-scoring", "graph-intelligence",
        "case-management", "evidence-management", "ai-explanation"}


def test_registry_has_45_unique_ids():
    items = ind_mod.registry()
    assert len(items) == 45
    ids = [e["id"] for e in items]
    assert len(set(ids)) == 45


def test_entry_schema():
    for entry in ind_mod.registry():
        assert set(entry) == {"id", "name", "status", "shared_reuse",
                              "note"}
        assert entry["status"] in ind_mod.STATUSES
        assert entry["shared_reuse"], entry["id"]
        assert set(entry["shared_reuse"]) <= CAPS, entry["id"]
        assert entry["note"].strip(), entry["id"]


def test_all_not_started_until_evidenced():
    # Fail-loud gate: a module leaves NOT_STARTED only with an
    # implementation + test update citing its evidence.
    started = [e["id"] for e in ind_mod.registry()
               if e["status"] != "NOT_STARTED"]
    assert started == []


def test_get_module_roundtrip():
    hit = ind_mod.get_module("banking")
    assert hit is not None and hit["name"] == "Banking"
    assert ind_mod.get_module("no-such-industry") is None


def test_endpoint_shape_direct():
    body = industries_catalog()
    assert body["count"] == 45
    assert len(body["industries"]) == 45
    assert body["industries"][0]["id"] == "banking"


def test_directive_groups_cover_all_45_ids():
    groups = ind_mod.directive_groups()
    assert len(groups) == 45
    assert [g["group"] for g in groups] == ["%02d" % n for n in range(
        1, 46)]
    coverage = ind_mod.group_coverage()
    assert coverage == {"groups": 45, "distinct_ids": 45, "missing": [],
                        "unknown": []}


def test_shared_and_split_groups_documented():
    by_group = {g["group"]: g["modules"]
                for g in ind_mod.directive_groups()}
    assert by_group["02"] == by_group["03"] == ["fintech-payments"]
    assert by_group["12"] == by_group["13"] == ["law-enforcement"]
    assert by_group["44"] == ["maritime", "transport"]
    assert by_group["45"] == ["ngo", "charities", "hospitality",
                              "environmental"]
