"""Master S14: capability registry resolves against live code."""
import app.main as main
from app import capabilities as cap_mod


def test_registry_has_15_graded_entries():
    entries = cap_mod.registry()
    assert [e["id"] for e in entries] == list("ABCDEFGHIJKLMNO")
    for entry in entries:
        assert entry["status"] in ("HAVE", "PARTIAL", "MISSING")
        assert entry["name"].strip()
        if entry["status"] == "MISSING":
            assert entry["next"].strip(), entry["id"]
            assert entry["implements"] == []
        else:
            assert entry["implements"], entry["id"]
            assert entry["evidence"], entry["id"]


def test_verify_resolves_every_claim():
    report = cap_mod.verify()
    assert report["failures"] == []
    assert report["verified"] is True
    assert report["counts"] == {"HAVE": 8, "PARTIAL": 6, "MISSING": 1}


def test_translation_engine_honestly_missing():
    entry = next(e for e in cap_mod.registry() if e["id"] == "D")
    assert entry["status"] == "MISSING"
    assert "pilot" in entry["next"]


def test_endpoint_shape():
    body = main.capabilities_registry()
    assert len(body["capabilities"]) == 15
    assert body["verification"]["verified"] is True
