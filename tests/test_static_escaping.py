"""H2: legacy static/app.js must escape untrusted text before innerHTML.

Model strings, server messages, and ids are interpolated into innerHTML on
the legacy server-rendered pages. Every such interpolation must pass
through the esc() helper so markup in model output cannot execute.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

APP_JS = Path(__file__).resolve().parent.parent / "static" / "app.js"

# Fields carrying model output or server messages; must never be
# interpolated raw into an innerHTML template.
MODEL_FIELDS = ("f.finding", "r.summary", "r.conclusion", "r.disclaimer",
                "e.message", "run.model_id", "run.status")


def _source():
    return APP_JS.read_text(encoding="utf-8")


def test_esc_helper_defined():
    assert "function esc(value)" in _source()


def test_model_fields_never_interpolated_raw():
    text = _source()
    for field in MODEL_FIELDS:
        raw = re.findall(r"\$\{\s*" + re.escape(field) + r"\b", text)
        assert raw == [], f"raw interpolation of {field}: {raw}"
    # And the escaped forms are actually used.
    assert text.count("esc(") >= len(MODEL_FIELDS)


def _extract_esc():
    match = re.search(r"function esc\(value\) \{.*?\n\}", _source(),
                      re.DOTALL)
    assert match, "esc() helper missing from static/app.js"
    return match.group(0)


@pytest.mark.skipif(shutil.which("node") is None,
                    reason="node unavailable for JS harness")
def test_esc_neutralizes_html_fixture(tmp_path):
    fixture = ('<script>alert(1)</script><img src=x onerror=alert(2)>'
               '"quoted" & \'single\'')
    harness = (
        _extract_esc()
        + "\nconst out = esc(process.argv[2]);\n"
        + "if (/[<>'\"]/.test(out)) { console.error('RAW: ' + out); "
        + "process.exit(1); }\n"
        + "console.log(JSON.stringify(out));\n"
    )
    script = tmp_path / "esc_harness.js"
    script.write_text(harness, encoding="utf-8")
    proc = subprocess.run(["node", str(script), fixture], capture_output=True,
                          text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == (
        "&lt;script&gt;alert(1)&lt;/script&gt;"
        "&lt;img src=x onerror=alert(2)&gt;"
        "&quot;quoted&quot; &amp; &#39;single&#39;")
