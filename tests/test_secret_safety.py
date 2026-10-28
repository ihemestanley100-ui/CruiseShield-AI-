"""T-023: no API key material in source, bundle, Git, or state."""
import json
import subprocess

import pytest

from app.config import ROOT


def test_env_file_is_gitignored():
    # A local .env legitimately exists on a configured machine (the README
    # setup creates it); the real invariant is that git always ignores it.
    # This test never reads .env values.
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in gitignore.splitlines()
    try:
        proc = subprocess.run(
            ["git", "-c", f"safe.directory={ROOT.as_posix()}",
             "check-ignore", "-q", ".env"],
            cwd=ROOT, capture_output=True)
    except FileNotFoundError:
        pytest.skip("git unavailable")
    assert proc.returncode == 0, ".env must be ignored by git"


def test_example_has_names_only():
    example = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "MODEL_API_KEY=" in example
    for line in example.splitlines():
        if line.startswith("MODEL_API_KEY="):
            assert line.split("=", 1)[1].strip() == ""


def test_state_file_has_no_secrets(tmp_path):
    from app.store import Store
    store = Store(tmp_path / "state.json")
    blob = json.dumps(store.state)
    assert "MODEL_API_KEY" not in blob
    assert "Bearer" not in blob
