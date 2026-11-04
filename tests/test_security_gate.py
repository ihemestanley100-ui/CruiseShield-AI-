"""J3-P11: security-gate unit tests (pure helpers + live scan contract).

Full-gate runs stay in CI (pip-audit needs network); these pin the
gate's own parsing/matching logic socket-free.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import security_gate as gate


def test_norm_canonicalizes_names():
    assert gate._norm("  FastAPI ") == "fastapi"
    assert gate._norm("psycopg[binary]") == "psycopg[binary]"
    assert gate._norm("a_b.c") == "a-b-c"


def test_parse_pins_reads_pins_only(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_text(
        "# comment\nfastapi==0.133.0\nuvicorn==0.40.0 \\\n"
        "not-a-pin\nhttpx>=1  \n",
        encoding="utf-8")
    assert gate.parse_pins(req) == {
        "fastapi": "0.133.0", "uvicorn": "0.40.0"}


def test_secret_patterns_catch_shapes_and_spare_fixtures():
    # Shapes are assembled at runtime so this file itself stays scan-clean.
    bodies = {
        "key": "-----BEGIN " + "RSA PRIVATE KEY-----\nx",
        "aws": "key " + "AKIA" + "IOSFODNN7EXAMPLE here",
        "gh": "token ghp_" + "a" * 36 + " end",
        "fixture": 'FAKE_SECRET = "TEST-ONLY-NOT-A-CREDENTIAL"',
    }
    matched = {name for name, text in bodies.items()
               for rx in gate.SECRET_PATTERNS.values()
               if rx.search(text)}
    assert {"key", "aws", "gh"} <= matched
    assert "fixture" not in matched


def test_live_tree_scan_passes():
    ok, detail = gate.check_secret_scan()
    assert ok, detail
