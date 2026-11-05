"""Scratch-load path for verified restore plans (GAP-003).

Loads a restore plan's plaintext into a FRESH scratch Store file and
checks record counts against the backup manifest. The live
STATE_PATH is refused structurally (resolved-path comparison), and
an existing destination is never overwritten. No database, no
network, no production writes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import STATE_PATH


class LoadError(Exception):
    """Scratch load refused or verification failed. Fail closed."""


def _resolve(path: str | Path) -> Path:
    try:
        return Path(path).resolve()
    except OSError:
        return Path(path).absolute()


def load_plan_into_scratch(plan: Any, dest: str | Path) -> dict[str, Any]:
    """Write plan.plaintext to fresh scratch `dest`; verify counts."""
    target = _resolve(dest)
    if target == _resolve(STATE_PATH):
        raise LoadError("LIVE_PATH_REFUSED")
    if target.exists():
        raise LoadError(f"DEST_EXISTS: {target}")
    try:
        state = json.loads(bytes(plan.plaintext).decode("utf-8"))
    except (ValueError, TypeError, UnicodeDecodeError) as exc:
        raise LoadError(f"PLAINTEXT_INVALID: {exc}") from None
    if not isinstance(state, dict) or "scenario_id" not in state:
        raise LoadError("STATE_SHAPE_INVALID")
    manifest = plan.manifest if isinstance(plan.manifest, dict) else {}
    expected = manifest.get("table_counts", {})
    mismatches: dict[str, list[int]] = {}
    for key, want in expected.items():
        if key in state and isinstance(state[key], list):
            got = len(state[key])
            if got != want:
                mismatches[key] = [want, got]
    if mismatches:
        raise LoadError(f"COUNT_MISMATCH: {mismatches}")
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp-scratch")
    tmp.write_bytes(bytes(plan.plaintext))
    tmp.replace(target)
    return {"dest": str(target), "scenario_id": state["scenario_id"],
            "bytes": len(bytes(plan.plaintext)),
            "checked_tables": sorted(k for k in expected
                                     if k in state
                                     and isinstance(state[k], list))}
