"""Filesystem BackupTarget for drills + self-hosted single-node use.

Stores each artifact as a file under a root directory. Paths are
strictly contained (``..`` / absolute paths rejected) and writes are
atomic (temp file + os.replace). Production selection of this target
is a D-018 decision; the drill script uses it with test keys only.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

from backups import targets as targets_mod


class LocalDirTarget(targets_mod.BackupTarget):
    """BackupTarget backed by a local directory."""

    def __init__(self, root: str | os.PathLike[str]) -> None:
        # Resolve once: _resolve() compares resolved candidates
        # against this root, so a relative root would "escape"
        # itself on every call.
        self._root = Path(root).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, path: str) -> Path:
        candidate = (self._root / path).resolve()
        if candidate != self._root and self._root not in candidate.parents:
            raise targets_mod.TargetError("PATH_ESCAPE", path)
        return candidate

    def put(self, path: str, data: bytes) -> str:
        dest = self._resolve(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".tmp-%d" % os.getpid())
        try:
            with open(tmp, "wb") as handle:
                handle.write(bytes(data))
            os.replace(tmp, dest)
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass
        return "local-sha256:" + hashlib.sha256(data).hexdigest()[:16]

    def get(self, path: str) -> bytes:
        dest = self._resolve(path)
        try:
            with open(dest, "rb") as handle:
                return handle.read()
        except FileNotFoundError:
            raise targets_mod.NotFoundError(path) from None

    def exists(self, path: str) -> bool:
        return self._resolve(path).is_file()
