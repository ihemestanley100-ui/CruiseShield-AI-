"""R06 secret scan. Prints ONLY locations + pattern names, NEVER values.

Scans: git history patches, tracked files, .env var NAMES, built frontend
chunks. Each hit: path:line:pattern:fixture_hint. fixture_hint=true when
the line mentions test/fake/example/mock/demo/fixture.
"""
import re
import subprocess

PATTERNS = {
    "model_api_key": re.compile(r"MODEL_API_KEY"),
    "api_key_assign": re.compile(r"(?i)api[_-]?key\s*[:=]"),
    "secret_assign": re.compile(r"(?i)\bsecret\s*[:=]"),
    "session_secret_val": re.compile(r"SESSION_SECRET\s*=\s*\S+"),
    "password_val": re.compile(r"(?i)password\s*[:=]\s*\S+"),
    "bearer_token": re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*"),
    "private_key": re.compile(r"BEGIN [A-Z0-9 ]*PRIVATE KEY"),
    "gh_token": re.compile(r"gh[pousr]_[A-Za-z0-9]+"),
    "sk_key": re.compile(r"\bsk-[A-Za-z0-9]+"),
    "pg_url_creds": re.compile(r"postgres(ql)?://[^/\s]*:[^/\s]*@"),
    "demo_users_val": re.compile(r"DEMO_USERS\s*=\s*\S+"),
}
FIXTURE = re.compile(r"(?i)test|fake|example|mock|demo|fixture|placeholder|changeme|xxx")
SKIP_PATHS = ("node_modules/", ".next/cache", ".git/", "__pycache__/",
              ".venv", "pytest-of-HP", ".pytest_cache")


def check_line(line):
    return [name for name, rx in PATTERNS.items() if rx.search(line)]


def scan_text(path, text):
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        for name in check_line(line):
            hint = bool(FIXTURE.search(line))
            hits.append(f"{path}:{i}:{name}:fixture_hint={hint}")
    return hits


all_hits = []
# 1. git history (all refs, patches)
log = subprocess.run(["git", "log", "--all", "-p", "--no-color",
                      "--no-ext-diff", "--no-textconv"],
                     capture_output=True, text=True, errors="replace")
cur = "history"
for i, line in enumerate(log.stdout.splitlines(), 1):
    if line.startswith("+++ b/"):
        cur = "history:" + line[6:]
        continue
    if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
        for name in check_line(line):
            hint = bool(FIXTURE.search(line))
            all_hits.append(f"{cur}:patchline:{name}:fixture_hint={hint}")
# 2. tracked files
files = subprocess.run(["git", "ls-files"], capture_output=True, text=True)
for f in files.stdout.split():
    if f.startswith(SKIP_PATHS) or f.endswith((".png", ".ico", ".woff2")):
        continue
    try:
        with open(f, encoding="utf-8", errors="replace") as fh:
            all_hits += scan_text(f, fh.read())
    except OSError:
        pass
# 3. .env var NAMES only (untracked-in-spirit; never values)
import glob
for f in glob.glob(".env*") + glob.glob("frontend/.env*"):
    try:
        with open(f, encoding="utf-8", errors="replace") as fh:
            names = sorted({ln.split("=", 1)[0].strip() for ln in fh
                            if "=" in ln and not ln.startswith("#")})
        print(f"ENV_NAMES {f}: {','.join(names)}")
    except OSError:
        pass
# 4. built frontend chunks (untracked build output)
for f in glob.glob("frontend/.next/static/**/*.js", recursive=True):
    try:
        with open(f, encoding="utf-8", errors="replace") as fh:
            all_hits += scan_text(f, fh.read())
    except OSError:
        pass
print(f"HITS_TOTAL={len(all_hits)}")
for h in sorted(set(all_hits))[:80]:
    print("HIT", h)
