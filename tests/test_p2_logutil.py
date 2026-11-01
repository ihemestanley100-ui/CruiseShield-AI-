"""P2 logutil tests. Synthetic secrets only; assert none ever leak."""
import logging
import re

import pytest

from backups import logutil as log_mod


@pytest.fixture()
def records():
    entries: list[str] = []

    class _Handler(logging.Handler):
        def emit(self, record):
            entries.append(record.getMessage())

    logger = logging.getLogger("test-p2-logutil")
    logger.handlers = [_Handler()]
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    return logger, entries


def test_redactor_replaces_exact_secrets_longest_first():
    redactor = log_mod.SecretRedactor(["abc", "abcdef"])
    assert redactor.redact("x abcdef y abc z") == (
        f"x {log_mod.REDACTED} y {log_mod.REDACTED} z")


def test_redactor_ignores_empty_and_masks_bearer():
    redactor = log_mod.SecretRedactor(["", "tok-seed-1"])
    line = redactor.redact("Authorization: Bearer ghp_Xyz123 head tok-seed-1")
    assert "ghp_Xyz123" not in line
    assert "tok-seed-1" not in line
    assert line.count(log_mod.REDACTED) == 2


def test_format_event_is_single_line_and_redacted():
    redactor = log_mod.SecretRedactor(["s3cr3t"])
    line = log_mod.format_event("put", redactor, target="c2",
                                note="key s3cr3t here")
    assert "\n" not in line
    assert line.startswith("event=put ")
    keys = re.findall(r"(?:^| )([A-Za-z_]+)=", line)
    assert keys == ["event", *sorted(keys[1:])]
    assert "s3cr3t" not in line
    assert log_mod.REDACTED in line


def test_format_event_quotes_values_with_spaces():
    line = log_mod.format_event("note", memo="two words")
    assert 'memo="two words"' in line


def test_log_event_emits_structured_record(records):
    logger, entries = records
    log_mod.log_event(logger, logging.INFO, "upload",
                      target="c2", attempt=2)
    assert entries == ["event=upload attempt=2 target=c2"]


def test_heartbeat_ok_is_info_and_failure_is_error(records):
    logger, entries = records
    with _level_capture(logger) as levels:
        log_mod.heartbeat(logger, backup_id="csbk-1", target="c2", ok=True,
                          latency_ms=12, attempt=1)
        log_mod.heartbeat(logger, backup_id="csbk-1", target="c3", ok=False,
                          attempt=3, detail="boom")
    assert levels == [logging.INFO, logging.ERROR]
    assert "event=heartbeat" in entries[0]
    assert "ok=true" in entries[0] and "latency_ms=12" in entries[0]
    assert "ok=false" in entries[1] and "attempt=3" in entries[1]


def test_heartbeat_redacts_detail(records):
    logger, entries = records
    redactor = log_mod.SecretRedactor(["app-key-9"])
    log_mod.heartbeat(logger, backup_id="b", target="c2", ok=False,
                      detail="key app-key-9 failed", redactor=redactor)
    assert "app-key-9" not in entries[0]
    assert log_mod.REDACTED in entries[0]


def test_get_logger_is_idempotent_and_non_propagating():
    first = log_mod.get_logger("test-p2-logger")
    second = log_mod.get_logger("test-p2-logger")
    assert first is second
    assert len(first.handlers) == 1
    assert first.propagate is False


class _level_capture:
    def __init__(self, logger):
        self._logger = logger
        self.levels: list[int] = []

    def __enter__(self):
        real_log = self._logger.log

        def spy(level, *args, **kwargs):
            self.levels.append(level)
            return real_log(level, *args, **kwargs)

        self._real = real_log
        self._logger.log = spy
        return self.levels

    def __exit__(self, *exc):
        self._logger.log = self._real
        return False
