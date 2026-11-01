"""Phase 6: AI cost controls — daily cap, timeout, audit. Socket-free."""
import pytest

import app.main as main
from app import ai_adapter
from app import config as config_mod
from app.models import EvidencePackage

TODAY = ai_adapter._now()[:10]


def _pump(coro):
    try:
        coro.send(None)
    except StopIteration as exc:
        return exc.value
    raise AssertionError("coroutine suspended on real I/O")


def _package(store):
    return EvidencePackage.model_validate(
        store.state["evidence_packages"]["inv_84721"])


def test_attempts_today_counts_and_ignores_malformed():
    runs = [{"started_at": TODAY + "T10:00:00Z"},
            {"started_at": TODAY + "T11:00:00Z"},
            {"started_at": "2020-01-01T00:00:00Z"},
            {"started_at": "garbage"},
            {"started_at": None},
            {},
            "not-a-dict"]
    assert ai_adapter.attempts_today(runs, TODAY) == 2
    assert ai_adapter.attempts_today([], TODAY) == 0
    assert ai_adapter.attempts_today(None, TODAY) == 0


def test_daily_cap_rejects_with_audit_and_no_run(tmp_store, monkeypatch):
    monkeypatch.setattr(config_mod, "AI_DAILY_CALL_LIMIT", 1)
    tmp_store.state["ai_runs"].append({"started_at": TODAY + "T10:00:00Z"})
    package = _package(tmp_store)
    audits_before = len(tmp_store.state["audits"])
    with pytest.raises(main.AppError) as exc:
        _pump(main._run_ai(package, "summary", "agentrun_99", "trace_cap"))
    assert (exc.value.code, exc.value.status) == (
        "AI_DAILY_LIMIT_EXCEEDED", 429)
    assert len(tmp_store.state["ai_runs"]) == 1  # no run persisted
    assert len(tmp_store.state["audits"]) == audits_before + 1
    assert tmp_store.state["audits"][-1]["action"] == "ai.run.rejected"


def test_daily_cap_allows_under_limit(tmp_store, monkeypatch):
    monkeypatch.setattr(config_mod, "AI_DAILY_CALL_LIMIT", 5)
    monkeypatch.setattr(ai_adapter, "MODEL_API_KEY", "")
    package = _package(tmp_store)
    # Reaches analyze() (no key -> honest 503), proving the cap passed.
    with pytest.raises(main.AppError) as exc:
        _pump(main._run_ai(package, "summary", "agentrun_99", "trace_ok"))
    assert exc.value.code == "MODEL_NOT_CONFIGURED"


def test_daily_cap_zero_disables(tmp_store, monkeypatch):
    monkeypatch.setattr(config_mod, "AI_DAILY_CALL_LIMIT", 0)
    monkeypatch.setattr(ai_adapter, "MODEL_API_KEY", "")
    tmp_store.state["ai_runs"].extend(
        {"started_at": TODAY + "T10:00:00Z"} for _ in range(10))
    package = _package(tmp_store)
    with pytest.raises(main.AppError) as exc:
        _pump(main._run_ai(package, "summary", "agentrun_99", "trace_zero"))
    assert exc.value.code == "MODEL_NOT_CONFIGURED"


def test_timeout_passed_to_provider_call(tmp_store, monkeypatch):
    monkeypatch.setattr(config_mod, "AI_DAILY_CALL_LIMIT", 0)
    monkeypatch.setattr(config_mod, "AI_TIMEOUT_SECONDS", 12)
    seen = {}

    async def stub(package, summary, trace_id, run_id, **kwargs):
        seen.update(kwargs)
        return {"agent_run_id": run_id, "model_id": "stub",
                "status": "SUCCEEDED",
                "schema_validation_status": "VALIDATED",
                "evidence_reference_validation_status": "VALIDATED"}

    monkeypatch.setattr(ai_adapter, "analyze", stub)
    package = _package(tmp_store)
    run = _pump(main._run_ai(package, "summary", "agentrun_7", "trace_t"))
    assert seen["timeout"] == 12
    assert run["status"] == "SUCCEEDED"
    assert tmp_store.state["audits"][-1]["action"] == "ai.run.succeeded"
