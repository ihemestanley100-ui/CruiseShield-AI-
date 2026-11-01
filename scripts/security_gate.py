"""Reproducible security gate: pins, hashes, audit, secrets (P2.2D).

Checks, in order:
1. lock_covers_requirements: every requirements.txt pin is in
   requirements.lock at the identical version.
2. installed_matches_lock: every locked pin is installed at the
   identical version; anything else installed must be documented
   audit/installer tooling (TOOLING_ALLOWLIST) or pip/setuptools/wheel.
3. lockfile_hashes: every locked pin carries at least one
   ``--hash=sha256:<64hex>`` entry.
4. pip_check: ``python -m pip check`` reports no conflicts.
5. pip_audit: ``python -m pip_audit -r requirements.lock
   --disable-pip --format=json`` reports zero vulnerabilities, or only
   ones listed in an approved exceptions file (``--exceptions`` JSON:
   [{"id": "PYSEC-...", "owner": ..., "reason": ...,
   "review_date": ...}]).
6. secret_scan: no real-credential shapes anywhere in the scanned tree.

Exit 0 only when every check passes. ``--skip-audit`` marks the audit
SKIPPED (offline use); CI never passes it. Never modifies anything and
never upgrades any dependency.
"""
from __future__ import annotations

import argparse
import importlib.metadata as metadata
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS = ROOT / "requirements.txt"
LOCK = ROOT / "requirements.lock"

# Audit/installer tooling deliberately installed outside the lock
# (pip-audit closure as resolved 2026-10-30). Review on any change.
TOOLING_ALLOWLIST = frozenset({
    "boolean-py", "cachecontrol", "charset-normalizer",
    "cyclonedx-python-lib", "defusedxml", "filelock",
    "license-expression", "markdown-it-py", "mdurl", "msgpack",
    "packageurl-python", "pip", "pip-api", "pip-audit",
    "pip-requirements-parser", "platformdirs", "pyparsing",
    "py-serializable", "requests", "rich", "setuptools",
    "sortedcontainers", "tomli", "tomli-w", "wheel",
})

HASH_RE = re.compile(r"--hash=sha256:[0-9a-f]{64}\s*\\?\s*$")
PIN_RE = re.compile(r"^([A-Za-z0-9_.\-]+)==([^\s;#]+)")

# Real-credential shapes only; short test fixtures must not match.
SECRET_PATTERNS = {
    "private-key-block": re.compile(
        r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    "aws-access-key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "github-token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    "slack-token": re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b"),
    "age-secret-key": re.compile(
        r"\bAGE-SECRET-KEY-1[A-Z0-9]{55,}\b"),
    "aws-secret-value": re.compile(
        r"aws_secret_access_key.{0,8}[A-Za-z0-9/+=]{40}"),
}
SCAN_SKIP_DIRS = {".git", ".venv", ".venv.bak-retired", "__pycache__",
                  ".pytest_cache", "node_modules", ".next"}
SCAN_SKIP_SUFFIXES = {".pyc", ".png", ".jpg", ".ico", ".woff2"}


def _norm(name: str) -> str:
    return name.strip().lower().replace("_", "-").replace(".", "-")


def parse_pins(path: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = PIN_RE.match(line.strip())
        if match:
            pins[_norm(match.group(1))] = match.group(2).strip().rstrip("\\")
    return pins


def check_lock_covers_requirements() -> tuple[bool, str]:
    wanted = parse_pins(REQUIREMENTS)
    locked = parse_pins(LOCK)
    missing = {k: v for k, v in wanted.items() if k not in locked}
    drifted = {k: (wanted[k], locked[k]) for k in wanted
               if k in locked and locked[k] != wanted[k]}
    if missing or drifted:
        return False, f"missing={sorted(missing)} drifted={drifted}"
    return True, f"{len(wanted)} direct pins locked exactly"


def check_installed_matches_lock() -> tuple[bool, str]:
    locked = parse_pins(LOCK)
    installed = {_norm(d.metadata["Name"]): d.version
                 for d in metadata.distributions()}
    mismatched = {k: (locked[k], installed.get(k)) for k in locked
                  if installed.get(k) != locked[k]}
    extras = {k: v for k, v in installed.items()
              if k not in locked and k not in TOOLING_ALLOWLIST}
    if mismatched or extras:
        return False, f"mismatched={mismatched} unexpected={extras}"
    tooling = sorted(k for k in installed if k not in locked)
    return True, (f"{len(locked)} pins installed exactly; "
                  f"tooling present: {tooling}")


def check_lockfile_hashes() -> tuple[bool, str]:
    lines = LOCK.read_text(encoding="utf-8").splitlines()
    current: str | None = None
    hashes: dict[str, int] = {}
    for line in lines:
        stripped = line.strip()
        match = PIN_RE.match(stripped)
        if match and not stripped.startswith("#"):
            current = _norm(match.group(1))
            hashes.setdefault(current, 0)
        elif stripped.startswith("--hash=") and current:
            if HASH_RE.match(stripped):
                hashes[current] += 1
            else:
                return False, f"malformed hash line: {stripped[:60]}"
    bare = sorted(k for k, n in hashes.items() if n == 0)
    if bare:
        return False, f"pins without hashes: {bare}"
    total = sum(hashes.values())
    return True, f"{len(hashes)} pins, {total} sha256 hashes"


def _run(*argv: str) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(argv, capture_output=True, text=True,
                              cwd=ROOT, timeout=600)
    except (subprocess.TimeoutExpired, OSError):
        return None


def check_pip_check() -> tuple[bool, str]:
    proc = _run(sys.executable, "-m", "pip", "check")
    if proc is None:
        return False, "pip check timed out or failed to start"
    out = (proc.stdout + proc.stderr).strip()
    if proc.returncode != 0:
        return False, out[:500]
    return True, "no broken requirements"


def check_pip_audit(exceptions_path: str | None,
                    skip: bool) -> tuple[bool, str]:
    if skip:
        return True, "SKIPPED by --skip-audit (offline mode)"
    allowed: dict[str, dict] = {}
    if exceptions_path:
        entries = json.loads(Path(exceptions_path).read_text("utf-8"))
        allowed = {e["id"]: e for e in entries}
    proc = _run(sys.executable, "-m", "pip_audit", "-r", str(LOCK),
                "--disable-pip", "--format=json")
    if proc is None:
        return False, "audit unreachable (timeout): OSV query did not " \
            "complete; rerun with network or use --skip-audit explicitly"
    if proc.returncode not in (0, 1):
        return False, f"audit tool failed: {(proc.stderr or '')[:300]}"
    try:
        report = json.loads(proc.stdout or "{}")
        deps = report.get("dependencies", [])
    except (json.JSONDecodeError, AttributeError):
        return False, f"unparseable audit output: {proc.stdout[:200]}"
    open_vulns: list[str] = []
    excepted: list[str] = []
    for dep in deps:
        for vuln in dep.get("vulns", []):
            ids = [vuln.get("id", "")] + list(vuln.get("aliases", []))
            key = next((i for i in ids if i in allowed), None)
            label = (f"{dep.get('name')} {dep.get('version')} "
                     f"{vuln.get('id')} fix={vuln.get('fix_versions')}")
            if key:
                excepted.append(f"{label} (excepted: "
                                f"{allowed[key].get('owner')})")
            else:
                open_vulns.append(label)
    if open_vulns:
        return False, "OPEN: " + "; ".join(open_vulns)[:800]
    suffix = f"; excepted: {len(excepted)}" if excepted else ""
    return True, f"no open vulnerabilities{suffix}"


def check_secret_scan() -> tuple[bool, str]:
    hits: list[str] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() in SCAN_SKIP_SUFFIXES:
            continue
        if any(part in SCAN_SKIP_DIRS for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for name, pattern in SECRET_PATTERNS.items():
                if pattern.search(line):
                    hits.append(f"{path.relative_to(ROOT)}:{lineno}"
                                f":{name}")
    if hits:
        return False, "hits: " + "; ".join(hits[:10])
    return True, "no real-credential shapes found"


CHECKS = (
    ("lock_covers_requirements", check_lock_covers_requirements),
    ("installed_matches_lock", check_installed_matches_lock),
    ("lockfile_hashes", check_lockfile_hashes),
    ("pip_check", check_pip_check),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-audit", action="store_true")
    parser.add_argument("--exceptions", default=None)
    args = parser.parse_args(argv)
    failed = False
    for name, check in CHECKS:
        ok, detail = check()
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
        failed = failed or not ok
    ok, detail = check_pip_audit(args.exceptions, args.skip_audit)
    print(f"[{'PASS' if ok else 'FAIL'}] pip_audit: {detail}")
    failed = failed or not ok
    ok, detail = check_secret_scan()
    print(f"[{'PASS' if ok else 'FAIL'}] secret_scan: {detail}")
    failed = failed or not ok
    print("GATE " + ("PASS" if not failed else "FAIL"))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
