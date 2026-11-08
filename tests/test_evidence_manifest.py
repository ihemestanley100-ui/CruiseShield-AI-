"""Evidence manifest tripwire: covered files must match manifest.

Regenerate after intentional governance edits:
  python scripts/evidence_manifest.py --write
"""
import subprocess
import sys


def test_manifest_verifies():
    out = subprocess.run(
        [sys.executable, "scripts/evidence_manifest.py"],
        capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stdout + out.stderr
    assert "manifest ok" in out.stdout
