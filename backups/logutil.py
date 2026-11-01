"""Structured logging, secret redaction, and heartbeats (Phase 5.4F/P2).

Stdlib only. Every P2 log line is a single ``event=<name> k=v ...`` record
so monitors can grep without a JSON parser. All values pass through a
:class:`SecretRedactor` before emission: known secret values are replaced
by exact match (longest first) and ``Authorization: Bearer`` tokens by
pattern. Redaction is defense-in-depth - callers must still never place
secrets in log fields; tests assert both properties.
"""
from __future__ import annotations

import logging
import re
from typing import Iterable

REDACTED = "***REDACTED***"

_BEARER_RE = re.compile(r"Bearer\s+[A-Za-z0-9._~+/-]+=*")


class SecretRedactor:
    """Exact-match + Bearer-pattern secret redaction."""

    def __init__(self, secrets: Iterable[str] = ()) -> None:
        self._secrets: list[str] = []
        for secret in secrets:
            self.add(secret)

    def add(self, secret: str) -> None:
        """Register one secret value for redaction (empties ignored)."""
        if secret:
            self._secrets.append(secret)

    def redact(self, text: str) -> str:
        """Replace every registered secret and Bearer token."""
        redacted = _BEARER_RE.sub(f"Bearer {REDACTED}", text)
        for secret in sorted(self._secrets, key=len, reverse=True):
            if secret:
                redacted = redacted.replace(secret, REDACTED)
        return redacted


def _quote(value: object) -> str:
    text = str(value)
    if any(char.isspace() for char in text) or "=" in text or not text:
        return '"' + text.replace('"', "'") + '"'
    return text


def format_event(event: str,
                 redactor: SecretRedactor | None = None,
                 **fields: object) -> str:
    """Render one structured log line (redaction applied last)."""
    parts = [f"event={_quote(event)}"]
    for key in sorted(fields):
        parts.append(f"{key}={_quote(fields[key])}")
    line = " ".join(parts)
    return redactor.redact(line) if redactor else line


def get_logger(name: str, *, level: int = logging.INFO) -> logging.Logger:
    """Stdlib logger with a single plain-message handler (idempotent)."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger


def log_event(logger: logging.Logger, level: int, event: str,
              redactor: SecretRedactor | None = None,
              **fields: object) -> None:
    """Emit one structured, redacted log record."""
    logger.log(level, format_event(event, redactor, **fields))


def heartbeat(logger: logging.Logger, *, backup_id: str, target: str,
              ok: bool, latency_ms: int | None = None, attempt: int = 1,
              detail: str = "",
              redactor: SecretRedactor | None = None) -> None:
    """Emit a monitor heartbeat (INFO when ok, ERROR otherwise)."""
    fields: dict[str, object] = {
        "backup_id": backup_id, "target": target,
        "ok": str(ok).lower(), "attempt": attempt,
    }
    if latency_ms is not None:
        fields["latency_ms"] = latency_ms
    if detail:
        fields["detail"] = detail
    log_event(logger, logging.INFO if ok else logging.ERROR,
              "heartbeat", redactor, **fields)
