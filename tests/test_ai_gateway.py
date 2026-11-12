"""D-047 AI gateway: registry, routing, fallback, quotas. Socket-free."""
import hashlib

import pytest

import app.main as main
from app import ai_adapter, ai_gateway
from app import config as config_mod
from app.models import EvidencePackage

TODAY = "2026-11-06"


class FakeProvider(ai_gateway.BaseProvider):
    """Test-double lane. Never a live claim: routing proof only."""

    def __init__(self, name="fake", fail_code="", tasks=("analysis",)):
        self._name = name
        self.fail_code = fail_code
        self._tasks = tasks
        self.seen = {}

    @property
    def name(self):
        return self._name

    def models(self):
        return ["%s-model-1" % self._name]

    def tasks(self):
        return self._tasks

    def configured(self):
        return True

    async def analyze(self, package, summary, trace_id, run_id,
                      timeout=30, transport=None, question="",
                      prior_context=""):
        self.seen.update(timeout=timeout, question=question)
        if self.fail_code:
            raise ai_adapter.AIError(self.fail_code, "fake failure")
        return {"agent_run_id": run_id, "provider": self._name,
                "model_id": "%s-model-1" % self._name,
                "status": "SUCCEEDED",
                "schema_validation_status": "VALIDATED",
                "evidence_reference_validation_status": "VALIDATED",
                "usage": {"prompt_tokens": 10, "completion_tokens": 5,
                          "total_tokens": 15},
                "latency_ms": 7}


@pytest.fixture()
def isolated():
    saved_reg = dict(ai_gateway._REGISTRY)
    saved_routes = {k: list(v)
                    for k, v in ai_gateway.ROUTES.items()}
    yield
    ai_gateway._REGISTRY.clear()
    ai_gateway._REGISTRY.update(saved_reg)
    ai_gateway.ROUTES.clear()
    ai_gateway.ROUTES.update(saved_routes)


@pytest.fixture()
def no_key(monkeypatch):
    monkeypatch.setattr(ai_adapter, "MODEL_API_KEY", "")
    monkeypatch.setattr(config_mod, "AI_PROVIDER_DAILY_LIMIT", 0)
    return monkeypatch


def _pump(coro):
    try:
        coro.send(None)
    except StopIteration as exc:
        return exc.value
    raise AssertionError("coroutine suspended on real I/O")


def _package(store):
    return EvidencePackage.model_validate(
        store.state["evidence_packages"]["inv_84721"])


def test_meta_registered_with_honest_status(no_key):
    names = [p.name for p in ai_gateway.providers()]
    assert "meta" in names
    entry = [e for e in ai_gateway.model_registry()
             if e["provider"] == "meta"][0]
    assert entry["tasks"] == ["analysis", "followup"]
    assert entry["status"] == "blocked-no-credential"
    assert "price" not in str(entry).lower()


def test_second_provider_addable(isolated, no_key):
    ai_gateway.register(FakeProvider())
    assert "fake" in [p.name for p in ai_gateway.providers()]
    assert any(e["provider"] == "fake"
               for e in ai_gateway.model_registry())
    with pytest.raises(ValueError):
        ai_gateway.register(FakeProvider())
    assert ai_gateway.unregister("fake") is True
    assert ai_gateway.get_provider("fake") is None


def test_route_reports_credentials_and_skips_dead_lanes(isolated,
                                                         no_key):
    ai_gateway.register(FakeProvider(tasks=()))
    ai_gateway.ROUTES["analysis"] = ["meta", "fake", "ghost"]
    decision = ai_gateway.route("analysis", [], TODAY)
    by_name = {c["provider"]: c for c in decision["candidates"]}
    assert by_name["meta"]["ok"] is True
    assert by_name["meta"]["credential"] is False
    assert by_name["fake"]["reason"] == "task-unsupported"
    assert by_name["ghost"]["reason"] == "not-registered"
    assert decision["order"] == [
        {"provider": "meta", "model": by_name["meta"]["model"]}]
    assert decision["selected"] == decision["order"][0]
    assert ai_gateway.route("nope", [], TODAY)["selected"] is None


def test_route_selects_configured_lane(isolated, no_key):
    fake = FakeProvider()
    ai_gateway.register(fake)
    ai_gateway.ROUTES["analysis"] = ["meta", "fake"]
    decision = ai_gateway.route("analysis", [], TODAY)
    assert decision["selected"] == {"provider": "fake",
                                    "model": "fake-model-1"}


def test_run_falls_back_then_receipts(isolated, no_key):
    bad = FakeProvider("flaky", fail_code="MODEL_TIMEOUT")
    good = FakeProvider("steady")
    ai_gateway.register(bad)
    ai_gateway.register(good)
    ai_gateway.ROUTES["analysis"] = ["flaky", "steady"]
    run = _pump(ai_gateway.run(
        "analysis", None, "s", "trace", "agentrun_1", [],
        timeout=9, today=TODAY))
    assert run["provider"] == "steady"
    assert run["gateway"]["attempts"] == [
        {"provider": "flaky", "model": "flaky-model-1",
         "error": "MODEL_TIMEOUT"},
        {"provider": "steady", "model": "steady-model-1",
         "error": ""}]
    assert good.seen["timeout"] == 9


def test_run_fast_codes_do_not_fall_back(isolated, no_key):
    bad = FakeProvider("bad", fail_code="MODEL_OUTPUT_INVALID")
    good = FakeProvider("good")
    ai_gateway.register(bad)
    ai_gateway.register(good)
    ai_gateway.ROUTES["analysis"] = ["bad", "good"]
    with pytest.raises(ai_adapter.AIError) as exc:
        _pump(ai_gateway.run("analysis", None, "s", "trace",
                             "agentrun_2", [], today=TODAY))
    assert exc.value.code == "MODEL_OUTPUT_INVALID"
    assert good.seen == {}


def test_run_no_credential_fails_closed(isolated, no_key):
    with pytest.raises(ai_adapter.AIError) as exc:
        _pump(ai_gateway.run("analysis", None, "s", "trace",
                             "agentrun_3", [], today=TODAY))
    assert exc.value.code == "MODEL_NOT_CONFIGURED"
    assert exc.value.detail["gateway_attempts"] == [
        {"provider": "meta",
         "model": exc.value.detail["route"]["order"][0]["model"],
         "error": "MODEL_NOT_CONFIGURED"}]
    with pytest.raises(ai_adapter.AIError) as exc:
        _pump(ai_gateway.run("nope", None, "s", "trace",
                             "agentrun_4", [], today=TODAY))
    assert exc.value.code == "AI_ROUTE_UNKNOWN"


def test_not_configured_failure_falls_through(isolated, no_key):
    flaky = FakeProvider("flaky-key",
                         fail_code="MODEL_NOT_CONFIGURED")
    good = FakeProvider("second")
    ai_gateway.register(flaky)
    ai_gateway.register(good)
    ai_gateway.ROUTES["analysis"] = ["flaky-key", "second"]
    run = _pump(ai_gateway.run("analysis", None, "s", "trace",
                               "agentrun_9", [], today=TODAY))
    assert run["provider"] == "second"
    assert run["gateway"]["attempts"] == [
        {"provider": "flaky-key", "model": "flaky-key-model-1",
         "error": "MODEL_NOT_CONFIGURED"},
        {"provider": "second", "model": "second-model-1",
         "error": ""}]


def test_provider_quota_skip_and_exhausted(isolated, no_key):
    no_key.setattr(config_mod, "AI_PROVIDER_DAILY_LIMIT", 1)
    fake = FakeProvider()
    ai_gateway.register(fake)
    ai_gateway.ROUTES["analysis"] = ["fake"]
    runs = [{"provider": "fake",
             "started_at": TODAY + "T10:00:00Z"}]
    assert ai_gateway.provider_calls_today(runs, "fake",
                                           TODAY) == 1
    decision = ai_gateway.route("analysis", runs, TODAY)
    assert decision["candidates"][0]["reason"] == "quota-exhausted"
    with pytest.raises(ai_adapter.AIError) as exc:
        _pump(ai_gateway.run("analysis", None, "s", "trace",
                             "agentrun_5", runs, today=TODAY))
    assert exc.value.code == "AI_PROVIDER_QUOTA_EXHAUSTED"
    no_key.setattr(config_mod, "AI_PROVIDER_DAILY_LIMIT", 0)
    assert ai_gateway.quota_ok("fake", runs, TODAY) is True


def test_usage_and_stats_observe_only():
    runs = [
        {"provider": "meta", "status": "SUCCEEDED",
         "started_at": TODAY + "T10:00:00Z", "latency_ms": 100,
         "usage": {"prompt_tokens": 10, "completion_tokens": 5,
                   "total_tokens": 15}, "error_code": ""},
        {"provider": "meta", "status": "FAILED",
         "started_at": TODAY + "T11:00:00Z", "latency_ms": 50,
         "usage": {"prompt_tokens": 7}, "error_code": "MODEL_TIMEOUT"},
        {"provider": "meta", "status": "FAILED",
         "started_at": "2020-01-01T00:00:00Z"},
        "not-a-dict", {},
    ]
    totals = ai_gateway.usage_totals(runs, "meta", TODAY)
    assert totals == {"calls": 2, "prompt_tokens": 17,
                      "completion_tokens": 5, "total_tokens": 15}
    stats = ai_gateway.provider_stats(runs, "meta", TODAY)
    assert stats["calls"] == 2
    assert stats["success_rate"] == 0.5
    assert stats["avg_latency_ms"] == 75.0
    assert stats["error_codes"] == {"MODEL_TIMEOUT": 1}
    assert stats["tokens"]["total_tokens"] == 15
    empty = ai_gateway.provider_stats([], "meta", TODAY)
    assert empty["calls"] == 0
    assert empty["success_rate"] is None
    assert empty["avg_latency_ms"] is None
    assert empty["error_codes"] == {}


def test_prompt_registry_pins_live_instructions():
    registry = ai_gateway.prompt_registry()
    assert set(registry) == {ai_adapter.PROMPT_VERSION,
                             ai_adapter.FOLLOWUP_PROMPT_VERSION}
    assert registry[ai_adapter.PROMPT_VERSION][
        "instruction_sha256"] == hashlib.sha256(
            ai_adapter.SYSTEM_INSTRUCTION.encode()).hexdigest()
    assert registry[ai_adapter.FOLLOWUP_PROMPT_VERSION][
        "instruction_sha256"] == hashlib.sha256(
            ai_adapter.FOLLOWUP_INSTRUCTION.encode()).hexdigest()


def test_run_ai_routes_via_gateway_with_receipt(tmp_store,
                                                monkeypatch):
    monkeypatch.setattr(config_mod, "AI_DAILY_CALL_LIMIT", 0)
    monkeypatch.setattr(config_mod, "AI_PROVIDER_DAILY_LIMIT", 0)
    monkeypatch.setattr(config_mod, "AI_TIMEOUT_SECONDS", 30)
    monkeypatch.setattr(ai_adapter, "MODEL_API_KEY", "test-key")

    async def stub(package, summary, trace_id, run_id, **kwargs):
        assert kwargs["timeout"] == 30
        return {"agent_run_id": run_id, "provider": "meta",
                "model_id": "stub", "status": "SUCCEEDED",
                "schema_validation_status": "VALIDATED",
                "evidence_reference_validation_status": "VALIDATED"}

    monkeypatch.setattr(ai_adapter, "analyze", stub)
    run = _pump(main._run_ai(_package(tmp_store), "summary",
                             "agentrun_7", "trace_gw"))
    assert run["gateway"]["provider"] == "meta"
    assert run["gateway"]["task"] == "analysis"
    assert tmp_store.state["audits"][-1]["action"] == \
        "ai.run.succeeded"


def test_run_ai_no_credential_persists_route(tmp_store, no_key):
    no_key.setattr(config_mod, "AI_DAILY_CALL_LIMIT", 0)
    with pytest.raises(main.AppError) as exc:
        _pump(main._run_ai(_package(tmp_store), "summary",
                             "agentrun_8", "trace_gw2"))
    assert exc.value.code == "MODEL_NOT_CONFIGURED"
    saved = tmp_store.state["ai_runs"][-1]
    assert saved["provider"] == "meta"
    assert saved["route"]["task"] == "analysis"
    assert saved["route"]["candidates"][0]["credential"] is False
