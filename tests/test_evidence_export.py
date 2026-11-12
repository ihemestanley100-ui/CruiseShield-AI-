"""EVID-01: evidence-package export + determinism proof.

Socket-free: direct handler calls against tmp_store (runs in every
sandbox; cf. test_flow_direct.py).
"""
import hashlib
import json

import pytest

import app.main as main
from app import evidence as evidence_mod


def test_export_byte_identical_with_matching_hash(tmp_store):
    first = main.export_evidence_package("inv_84721")
    second = main.export_evidence_package("inv_84721")
    assert first.body == second.body
    digest = hashlib.sha256(first.body).hexdigest()
    assert first.headers["x-export-sha256"] == digest
    assert second.headers["x-export-sha256"] == digest


def test_export_envelope_shape(tmp_store):
    resp = main.export_evidence_package("inv_84721")
    assert resp.media_type == "application/json"
    doc = json.loads(resp.body.decode("utf-8"))
    assert doc["version"] == evidence_mod.EXPORT_VERSION
    package = doc["evidence_package"]
    assert package["package_id"].startswith("evidence_pkg_")
    assert package["package_id"] == (
        tmp_store.state["evidence_packages"]["inv_84721"]["package_id"])


def test_export_unknown_investigation(tmp_store):
    with pytest.raises(main.AppError) as exc:
        main.export_evidence_package("inv_nope")
    assert exc.value.code == "UNKNOWN_INVESTIGATION"


def test_canonical_bytes_ignore_key_order(tmp_store):
    package = tmp_store.state["evidence_packages"]["inv_84721"]
    shuffled = {key: package[key] for key in reversed(list(package))}
    assert list(shuffled) != list(package)
    assert (evidence_mod.canonical_export_bytes(shuffled)
            == evidence_mod.canonical_export_bytes(package))
