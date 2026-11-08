"""Production environment guard: no synthetic seed/reset in prod.

CS_ENV=production fails closed (refusal), every other value keeps
development behavior. Socket-free, tmp-path stores only.
"""
import pytest

from app import config as config_mod
from app.store import Store


def test_is_production_parsing(monkeypatch):
    monkeypatch.setattr(config_mod, "CS_ENV", "production")
    assert config_mod.is_production() is True
    monkeypatch.setattr(config_mod, "CS_ENV", "  PRODUCTION ")
    assert config_mod.is_production() is True
    for value in ("development", "staging", "", "prod", "Productionx"):
        monkeypatch.setattr(config_mod, "CS_ENV", value)
        assert config_mod.is_production() is False


def test_reset_refused_in_production(tmp_path, monkeypatch):
    monkeypatch.setattr(config_mod, "CS_ENV", "development")
    store = Store(tmp_path / "state.json")
    monkeypatch.setattr(config_mod, "CS_ENV", "production")
    with pytest.raises(ValueError, match="^PRODUCTION_REFUSED"):
        store.reset("scn_primary")


def test_reset_allowed_outside_production(tmp_path, monkeypatch):
    for value in ("development", "staging", ""):
        monkeypatch.setattr(config_mod, "CS_ENV", value)
        store = Store(tmp_path / ("s-%s.json" % (value or "empty")))
        assert store.reset("scn_primary")["scenario_id"] == "scn_primary"


def test_missing_file_raises_in_production(tmp_path, monkeypatch):
    monkeypatch.setattr(config_mod, "CS_ENV", "production")
    with pytest.raises(RuntimeError, match="refuses synthetic seed"):
        Store(tmp_path / "absent.json")


def test_missing_file_seeds_outside_production(tmp_path, monkeypatch):
    monkeypatch.setattr(config_mod, "CS_ENV", "staging")
    store = Store(tmp_path / "absent.json")
    assert store.state["scenario_id"] == "scn_primary"


def test_domain_mapping_is_403():
    import app.main as main

    err = main._domain_error(ValueError("PRODUCTION_REFUSED: nope"))
    assert (err.code, err.status) == ("PRODUCTION_REFUSED", 403)
