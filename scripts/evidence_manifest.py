"""Evidence integrity manifest: SHA-256 over release-evidence files.

Usage:
  python scripts/evidence_manifest.py            verify (exit 1 on drift)
  python scripts/evidence_manifest.py --write    regenerate manifest

Covered files are governance evidence (matrix, registers, audit
records, lockfile) — NOT source or tests, which the test suite
guards. History is git (every regeneration is a tracked diff);
nothing here claims tamper-proof storage.
"""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "EVIDENCE_MANIFEST.json"

COVERED = [
    "docs/ZERO_GAP_MATRIX.json",
    "scripts/zero_gap_matrix.py",
    "docs/PRODUCTION_CLOSURE_REGISTER.md",
    "docs/RELEASE_CLOSURE_PACKAGE.md",
    "docs/DEMO_PRODUCTION_AUDIT.md",
    "docs/LIVE_EVIDENCE_INDEX.md",
    "docs/LEVEL14_OWNER_APPROVAL_PACKAGES.md",
    "docs/LEAFLET_TILE_POLICY_REVIEW.md",
    "CRUISESHIELD-AI-DECISION-LOG.md",
    "docs/PROJECT_EXECUTION_STATE.md",
    "requirements.lock",
]


def digest(path: Path) -> dict:
    data = path.read_bytes()
    # Normalize line endings so the tripwire is stable across
    # Windows (CRLF worktree) and Linux CI (LF checkout) bytes.
    data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return {"sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data)}


def head() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
            capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return out.stdout.strip() or "unknown"


def build() -> dict:
    files = {}
    for rel in COVERED:
        files[rel] = digest(ROOT / rel)
    return {"generated_at": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"),
            "head": head(), "files": files}


def main() -> int:
    if "--write" in sys.argv:
        OUT.write_text(json.dumps(build(), indent=2) + "\n",
                       encoding="utf-8")
        print("wrote %s (%d files)" % (OUT.name, len(COVERED)))
        return 0
    if not OUT.exists():
        print("manifest missing: run with --write")
        return 1
    want = json.loads(OUT.read_text(encoding="utf-8"))["files"]
    have = build()["files"]
    drift = [k for k in want
             if want[k] != have.get(k, {})]
    missing = [k for k in want if k not in have]
    if drift or missing:
        print("DRIFT: %s" % (drift + missing))
        return 1
    print("manifest ok: %d files" % len(want))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
