"""UFI frontend/backend contract parity (runnable without node).

Parses the UFI components + api.ts helpers and asserts every imported
helper is exported and every referenced /api/v1 path exists in the
live FastAPI route table. This does not replace vitest execution.
"""
from __future__ import annotations

import re
from pathlib import Path

import app.main as main

ROOT = Path(__file__).resolve().parent.parent
API = ROOT / "frontend" / "lib" / "api.ts"
COMPONENTS = [
    ROOT / "frontend" / "components" / "tracing-section.tsx",
    ROOT / "frontend" / "components" / "monitoring-section.tsx",
    ROOT / "frontend" / "components" / "industry-section.tsx",
    ROOT / "frontend" / "components" / "assistant-shell.tsx",
    ROOT / "frontend" / "components" / "recovery-section.tsx",
]


def _norm(path: str) -> str:
    return re.sub(r"\{[^}]*\}", "{}", path)


def test_component_imports_resolve():
    api_text = API.read_text(encoding="utf-8")
    exports = set(re.findall(r"export (?:async )?function (\w+)", api_text))
    exports |= set(re.findall(r"export interface (\w+)", api_text))
    for comp in COMPONENTS:
        text = comp.read_text(encoding="utf-8")
        for match in re.finditer(
                r'import (?:type )?\{([^}]*)\} from "\.\./lib/api"',
                text):
            for name in match.group(1).split(","):
                name = name.strip()
                if name:
                    assert name in exports, (comp.name, name)


def test_helper_paths_exist_in_backend():
    api_text = API.read_text(encoding="utf-8")
    backend = {_norm(r.path) for r in main.app.routes
               if hasattr(r, "path")}
    used = set()
    for match in re.finditer(r'"/api/v1/[^"]*"', api_text):
        path = match.group(0).strip('"')
        path = re.sub(r"\$\{[^}]*\}", "{x}", path)
        used.add(_norm(path.split("?")[0]))
    ufi_prefixes = ("/api/v1/tracing", "/api/v1/fraud",
                    "/api/v1/transactions", "/api/v1/monitoring",
                    "/api/v1/industries", "/api/v1/reports",
                    "/api/v1/payment", "/api/v1/altpayments",
                    "/api/v1/institutions", "/api/v1/agent-os",
                    "/api/v1/conversations", "/api/v1/recovery")
    ufi_used = {p for p in used
                if p.split("{")[0].rstrip("/").startswith(ufi_prefixes)}
    assert ufi_used, "no UFI paths found; parser drift?"
    missing = {p for p in ufi_used if p not in backend}
    assert not missing, missing
