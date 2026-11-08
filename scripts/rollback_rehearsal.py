"""Rollback rehearsal (read-only): prove the rollback TARGET exists.

Master directive §17 demands executed drills, not paper procedures —
but an actual rollback (checkout/redeploy) needs owner authorization.
This rehearsal verifies, without changing anything:

1. HEAD resolves and a previous commit (the rollback target) exists.
2. The working-tree state is recorded (informational, never fails).
3. The canonical state file parses, with its sha256 + record counts.
4. The current Store loads that state (compatibility probe).
5. The application tree imports (app.main smoke).

Exit 0 + "verdict": "REHEARSED" means the drill verified its
preconditions. It does NOT mean a rollback was performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _git(*args: str) -> str:
    out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                         text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError("git %s failed: %s"
                           % (" ".join(args), out.stderr.strip()[:200]))
    return out.stdout.strip()


def rehearse(state_path: Path) -> dict:
    """Run every check; raise RuntimeError on the first failure."""
    report: dict = {"checks": {}}
    head = _git("rev-parse", "HEAD")
    prev = _git("rev-parse", "HEAD~1")
    report["checks"]["head_resolves"] = head[:12]
    report["previous"] = {
        "sha": prev,
        "subject": _git("log", "-1", "--format=%s", prev),
        "date": _git("log", "-1", "--format=%cI", prev),
    }
    status = _git("status", "--short")
    entries = [line for line in status.splitlines() if line.strip()]
    report["worktree"] = {"clean": not entries, "entries": len(entries)}
    raw = state_path.read_bytes()
    state = json.loads(raw.decode("utf-8"))
    report["state"] = {
        "path": str(state_path.relative_to(ROOT)),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "top_keys": sorted(state.keys()),
        "transactions": len(state.get("transactions", [])),
        "audits": len(state.get("audits", [])),
    }
    sys.path.insert(0, str(ROOT))
    try:
        from app.store import Store

        store = Store(state_path)
        report["checks"]["store_loads"] = (
            len(store.state.get("transactions", []))
            == report["state"]["transactions"])
        import app.main  # noqa: F401  (import smoke)

        report["checks"]["app_imports"] = True
    finally:
        sys.path.remove(str(ROOT))
    if not report["checks"]["store_loads"]:
        raise RuntimeError("store probe count mismatch")
    report["verdict"] = "REHEARSED"
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only rollback rehearsal.")
    parser.add_argument("--state", default="data/state.json",
                        help="state file relative to repo root")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(rehearse(ROOT / args.state), indent=2))
    except (RuntimeError, OSError, ValueError) as exc:
        print(json.dumps({"verdict": "FAILED", "error": str(exc)[:300]}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
