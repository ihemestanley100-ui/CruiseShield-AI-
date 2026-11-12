"""L13 Part 21 / L14: automated quality gates (socket-free, hermetic).

Gate 1: no exact-duplicate canonical source files (generated
bytecode caches excluded -- they legitimately repeat across
interpreter/pytest versions).
Gate 9: every /api route path or its handler is referenced by tests.
Gate 16: every decision code cited in code is recorded in the log.
"""
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SCOPED_DIRS = ("app", "migrations", "scripts", "tests", "templates",
               "frontend/app", "frontend/components", "frontend/lib")


def _source_files():
    for dirname in SCOPED_DIRS:
        base = ROOT / dirname
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            if "__pycache__" in path.parts:
                continue
            if path.suffix in {".pyc", ".pyo"}:
                continue
            yield path


def test_no_duplicate_canonical_source_files():
    seen = {}
    dupes = []
    checked = 0
    for path in _source_files():
        checked += 1
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rel = str(path.relative_to(ROOT))
        if digest in seen:
            dupes.append((rel, seen[digest]))
        else:
            seen[digest] = rel
    assert checked > 100, "expected a real source tree, saw %d" % checked
    assert not dupes, "duplicate source files: %r" % (dupes[:5],)


def test_decision_codes_have_log_entries():
    bodies = []
    for dirname in ("app", "tests"):
        for path in sorted((ROOT / dirname).rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            bodies.append(path.read_text(encoding="utf-8",
                                         errors="replace"))
    codes = sorted(set(re.findall(r"D-\d+[a-z]?", "\n".join(bodies))))
    assert codes, "expected decision-code references in code"
    log = (ROOT / "CRUISESHIELD-AI-DECISION-LOG.md").read_text(
        encoding="utf-8", errors="replace")
    missing = [code for code in codes if code not in log]
    assert not missing, \
        "decision codes without log entries: %r" % (missing,)


def test_api_routes_have_test_references():
    import sys

    sys.path.insert(0, str(ROOT))
    from app.main import app as fastapi_app

    haystack = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in sorted((ROOT / "tests").glob("*.py")))
    uncovered = []
    count = 0
    for route in fastapi_app.routes:
        path = getattr(route, "path", "")
        if "/api/" not in path:
            continue
        count += 1
        # Concrete-ID URLs in tests match the templated route path.
        pattern = re.sub(r"\{[^}]+\}", r"[^/\"']+", path)
        handler = getattr(getattr(route, "endpoint", None),
                          "__qualname__", "")
        if (re.search(pattern, haystack) is None
                and handler not in haystack):
            uncovered.append(path)
    assert count > 0, "expected /api routes"
    assert not uncovered, \
        "routes without test references: %r" % (uncovered,)
