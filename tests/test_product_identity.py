"""Part 21 gate 5: no unintended demo identity in production surfaces.

Two checks, both socket-free and hermetic:

1. Banned demo-product phrases are absent from the active product doc
   (README.md) and every shipped user-string surface (EN locale,
   Next.js app/components sources, Jinja templates).
2. Every remaining case-insensitive "demo" occurrence in backend
   sources and the frontend API client matches the explicit
   compatibility allowlist (env-contract names, internal role id,
   deprecated alias paths under an approved removal decision, and
   documented prose). A new occurrence fails with its file:line so
   it gets an explicit disposition instead of slipping in.

Out of scope by design: historical docs/evidence (immutable audit
history), isolated test fixtures, and the matrix generator's own
historical row statements. See docs/L13_PHASE0_BASELINE.md section 3
for the full disposition table.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BANNED_PHRASES = (
    "live demo",
    "explore demo",
    "demo sign-in",
    "demo sign in",
    "demo dashboard",
    "demo mode",
    "demo account",
    "demo credentials",
    "synthetic demo",
    "demo-only",
    "demo trial",
    "demo workspace",
    "public demo",
    "demo project",
    "demo-grade",
    "demo flow",
    "demo steps",
)

USER_STRING_PATHS = (
    ROOT / "README.md",
    ROOT / "frontend" / "lib" / "i18n" / "locales" / "en.ts",
    ROOT / "frontend" / "lib" / "api.ts",
)

USER_STRING_DIRS = (
    ROOT / "frontend" / "app",
    ROOT / "frontend" / "components",
    ROOT / "templates",
)

# Allowlist for "demo" occurrences in backend + API-client sources.
# Each entry is a regex that must match the full offending line.
ALLOWLIST = (
    r".*\bDEMO_USERS\b.*",
    r".*\bDEMO_WRITE_TOKEN\b.*",
    r".*\bNEXT_PUBLIC_DEMO_WRITE_TOKEN\b.*",
    r".*\bdemo_viewer\b.*",
    r".*\bDEMO_VIEWER\b.*",
    r".*/api/v1/demo/.*",  # deprecated aliases, REL-02/D-019b removal path
    r".*\bdemonstrat\w*\b.*",  # ordinary prose ("demonstrate"), not branding
    r".*\bdemo-scale\b.*",  # perf-smoke capacity note, not branding
    r".*\bdemo-token\b.*",  # remediation shorthand in comments/identifiers
    r".*\bdemo_token\b.*",
)
ALLOWLIST_RES = [re.compile(p, re.IGNORECASE) for p in ALLOWLIST]

SOURCE_SCAN_DIRS = (
    ROOT / "app",
    ROOT / "frontend" / "lib",
)


def _iter_files(dirs, suffixes):
    for top in dirs:
        if not top.is_dir():
            continue
        for path in sorted(top.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix not in suffixes:
                continue
            name = path.name
            if "test" in name or name.endswith((".test.ts", ".test.tsx")):
                continue
            if "node_modules" in path.parts or ".next" in path.parts:
                continue
            yield path


def test_banned_demo_phrases_absent_from_user_strings():
    offenders = []
    targets = [p for p in USER_STRING_PATHS if p.is_file()]
    targets += list(_iter_files(USER_STRING_DIRS, {".ts", ".tsx", ".html"}))
    assert targets, "product-identity scan found no files to check"
    for path in targets:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for phrase in BANNED_PHRASES:
            if phrase in lowered:
                offenders.append(f"{path.relative_to(ROOT)}: {phrase!r}")
    assert not offenders, "banned demo-product phrases in user strings:\n" + \
        "\n".join(offenders)


def test_backend_demo_occurrences_are_allowlisted():
    unlisted = []
    checked = 0
    files = list(_iter_files(SOURCE_SCAN_DIRS, {".py", ".ts"}))
    assert files, "product-identity scan found no sources to check"
    for path in files:
        for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1):
            if "demo" not in line.lower():
                continue
            checked += 1
            if not any(rx.match(line) for rx in ALLOWLIST_RES):
                unlisted.append(
                    f"{path.relative_to(ROOT)}:{lineno}: {line.strip()}")
    assert checked > 0, "expected some allowlisted demo references"
    assert not unlisted, \
        "unlisted demo occurrences need a disposition:\n" + "\n".join(unlisted)
