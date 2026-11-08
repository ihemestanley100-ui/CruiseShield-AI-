"""Phase A forensic inventory generator (Level 14 v14.0 §02).

Regenerates docs/FORENSIC_INVENTORY.json from live repository state:
tracked files (size + sha256), worktree status, API routes, frontend
routes, backend test node IDs, environment variable names, and
dependency manifests. Deterministic output (sorted keys).

Usage: python scripts/forensic_inventory.py [--check]
  --check verifies the committed JSON matches a fresh generation.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "FORENSIC_INVENTORY.json"


def run_git(*args: str) -> str:
    out = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True,
        check=True)
    return out.stdout


def sha_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_files() -> list[dict]:
    items = []
    for rel in sorted(run_git("ls-files").splitlines()):
        if not rel:
            continue
        path = ROOT / rel
        try:
            size = path.stat().st_size
        except OSError:
            items.append({"path": rel, "size": -1, "sha256": "MISSING"})
            continue
        items.append({"path": rel, "size": size, "sha256": sha_of(path)})
    return items


def worktree() -> list[dict]:
    items = []
    for line in run_git("status", "--short",
                        "--untracked-files=normal").splitlines():
        if not line.strip():
            continue
        items.append({"code": line[:2], "path": line[3:]})
    return sorted(items, key=lambda r: r["path"])


def api_routes() -> list[dict]:
    sys.path.insert(0, str(ROOT))
    import app.main as main  # noqa: E402

    routes = []
    for route in main.app.routes:
        if route.__class__.__name__ != "APIRoute":
            continue
        routes.append({"path": route.path,
                       "methods": sorted(route.methods or ()),
                       "handler": route.endpoint.__name__})
    routes.sort(key=lambda r: (r["path"], ",".join(r["methods"])))
    return routes


def frontend_routes() -> list[str]:
    pages = sorted(
        str(p.relative_to(ROOT)).replace("\\", "/")
        for p in (ROOT / "frontend" / "app").rglob("page.tsx"))
    return pages


def backend_tests() -> dict[str, list[str]]:
    out = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "--collect-only",
         "-q", "-p", "no:cacheprovider"], cwd=ROOT, capture_output=True,
        text=True)
    per_file: dict[str, list[str]] = {}
    for line in out.stdout.splitlines():
        line = line.strip()
        if "::" not in line or not line.startswith("tests/"):
            continue
        path, _, node = line.partition("::")
        per_file.setdefault(path, []).append(node)
    return {k: per_file[k] for k in sorted(per_file)}


def env_names() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for rel in (".env.example", "frontend/.env.example"):
        names = []
        for line in (ROOT / rel).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            names.append(line.split("=", 1)[0].strip())
        result[rel] = names
    return result


def manifests() -> list[str]:
    candidates = ["requirements.txt", "requirements.lock",
                  "frontend/package.json", "frontend/package-lock.json",
                  "Dockerfile", "render.yaml", "netlify.toml"]
    return [c for c in candidates if (ROOT / c).exists()]


def generate() -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"),
        "head": run_git("rev-parse", "HEAD").strip(),
        "branch": run_git("branch", "--show-current").strip(),
        "repo_files": repo_files(),
        "worktree": worktree(),
        "api_routes": api_routes(),
        "frontend_routes": frontend_routes(),
        "backend_tests": backend_tests(),
        "env_names": env_names(),
        "manifests": manifests(),
    }


def main() -> int:
    data = generate()
    text = json.dumps(data, indent=2, sort_keys=False) + "\n"
    if "--check" in sys.argv:
        current = json.loads(OUT.read_text(encoding="utf-8"))
        for key in ("repo_files", "api_routes", "frontend_routes",
                    "backend_tests", "env_names", "manifests"):
            if current.get(key) != data[key]:
                print(f"DRIFT: {key} differs from {OUT.name}")
                return 1
        print("inventory matches")
        return 0
    OUT.write_text(text, encoding="utf-8")
    files = len(data["repo_files"])
    routes = len(data["api_routes"])
    tests = sum(len(v) for v in data["backend_tests"].values())
    print(f"wrote {OUT.name}: {files} files, {routes} API routes, "
          f"{tests} tests, {len(data['worktree'])} worktree entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
