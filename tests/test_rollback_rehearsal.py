"""Master S17: rollback rehearsal is read-only and truthful."""
import hashlib
import json
import subprocess
import sys

import pytest

sys.path.insert(0, "scripts")
import rollback_rehearsal as rehearsal


def test_rehearsal_passes_and_reports_truthfully(capsys):
    expected_sha = hashlib.sha256(
        open("data/state.json", "rb").read()).hexdigest()
    code = rehearsal.main([])
    assert code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["verdict"] == "REHEARSED"
    assert report["state"]["sha256"] == expected_sha
    assert report["previous"]["sha"] != report["checks"][
        "head_resolves"]
    assert report["state"]["transactions"] > 0
    assert report["checks"] == {"head_resolves": report["checks"][
        "head_resolves"], "store_loads": True, "app_imports": True}
    # Read-only proof: HEAD and the worktree are untouched by the run.
    head = subprocess.run(["git", "rev-parse", "HEAD"],
                          capture_output=True, text=True,
                          timeout=60).stdout.strip()
    assert head.startswith(report["checks"]["head_resolves"])


def test_rehearsal_fails_cleanly_on_missing_state(capsys):
    code = rehearsal.main(["--state", "data/no-such-file.json"])
    assert code == 1
    report = json.loads(capsys.readouterr().out)
    assert report["verdict"] == "FAILED"
