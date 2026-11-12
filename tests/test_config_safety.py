"""J3-P1: env-numeric parsing must fail safe, never crash boot."""
import importlib

from app import config as config_mod


def test_safe_int_accepts_clean_values():
    assert config_mod._safe_int("12", 5) == 12
    assert config_mod._safe_int(" 7 ", 5) == 7


def test_safe_int_falls_back_on_garbage():
    assert config_mod._safe_int("garbage", 5) == 5
    assert config_mod._safe_int("", 5) == 5
    assert config_mod._safe_int(None, 5) == 5
    assert config_mod._safe_int("4.5", 30) == 30


def test_pg_timeout_default_is_sane():
    # Import-time value with no PG var set in this env: positive int.
    assert isinstance(config_mod.PG_CONNECT_TIMEOUT, int)
    assert config_mod.PG_CONNECT_TIMEOUT > 0


def test_max_output_tokens_default_is_bounded():
    # Import-time value with no AI var set in this env: exactly 4096.
    assert config_mod.AI_MAX_OUTPUT_TOKENS == 4096


def test_max_output_tokens_rejects_unsafe_env(monkeypatch):
    """Garbage, zero, and negative values fall back to 4096, never crash."""
    for raw in ("garbage", "", "0", "-5", "4.5"):
        monkeypatch.setenv("AI_MAX_OUTPUT_TOKENS", raw)
        importlib.reload(config_mod)
        assert config_mod.AI_MAX_OUTPUT_TOKENS == 4096
    monkeypatch.setenv("AI_MAX_OUTPUT_TOKENS", "1024")
    importlib.reload(config_mod)
    assert config_mod.AI_MAX_OUTPUT_TOKENS == 1024
    # Restore the no-env default for the rest of the suite.
    monkeypatch.delenv("AI_MAX_OUTPUT_TOKENS")
    importlib.reload(config_mod)
    assert config_mod.AI_MAX_OUTPUT_TOKENS == 4096


def test_session_secret_strength_predicates(monkeypatch):
    """R09-F2: 32-char minimum; weak fails closed, unset stays open."""
    monkeypatch.setattr(config_mod, "SESSION_SECRET", "")
    assert config_mod.session_auth_armed() is False
    assert config_mod.session_secret_misconfigured() is False
    monkeypatch.setattr(config_mod, "SESSION_SECRET", "short")
    assert config_mod.session_auth_armed() is False
    assert config_mod.session_secret_misconfigured() is True
    monkeypatch.setattr(config_mod, "SESSION_SECRET", "x" * 31)
    assert config_mod.session_auth_armed() is False
    assert config_mod.session_secret_misconfigured() is True
    monkeypatch.setattr(config_mod, "SESSION_SECRET", "x" * 32)
    assert config_mod.session_auth_armed() is True
    assert config_mod.session_secret_misconfigured() is False
