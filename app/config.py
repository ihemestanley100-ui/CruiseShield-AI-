"""Project configuration. Reads environment + local .env (names only, never logged)."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("DATA_DIR", ROOT / "data"))


def load_dotenv() -> list[str]:
    """Load KEY=VALUE lines from ROOT/.env without overriding real env vars.

    Returns the loaded key names only (never values).
    """
    loaded: list[str] = []
    path = ROOT / ".env"
    if not path.exists():
        return loaded
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")
            loaded.append(key)
    return loaded


load_dotenv()

MODEL_API_KEY = os.environ.get("MODEL_API_KEY", "")
META_MODEL_ID = os.environ.get("META_MODEL_ID", "muse-spark-1.3")
META_BASE_URL = os.environ.get("META_BASE_URL", "https://api.meta.ai/v1")

STATE_PATH = DATA_DIR / "state.json"
