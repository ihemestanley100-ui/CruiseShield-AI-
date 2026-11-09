"""M3 orchestration edges: approval pause/resume, budgets, failures.

Covers the offline-testable branches that the full suite misses:
resume error paths, tool-budget exhaustion, approval-gated pause,
step failure, second-step arg chaining, and defensive metrics rows.
"""
import pytest

from app import agents as agents_mod
from app import orchestration as orch


def _subject(role="investigator", user="judge"):
    return {"kind": "session", "user": user, "role": role,
            "tenant": "org_primary"}


def _gated(monkeypatch):
    monkeypatch.setattr(orch, "PIPELINES",
                        {"TRANSACTION_SEARCH": ("fraud-detection",
                                                ("txn.search",))})


def test_approval_pause_then_resume_completes(tmp_store, monkeypatch):
    _gated(monkeypatch)
    paused = orch.start(tmp_store, "show transfers", _subject())
    assert paused["state"] == "APPROVAL_REQUIRED"
    plan_id = paused["pending"]["plan_id"]
    agents_mod.approve(tmp_store, plan_id, _subject("admin", "boss"))
    done = orch.resume(tmp_store, paused["execution_id"], _subject())
    assert done["state"] == "COMPLETED"
    assert done["steps"][0]["status"] == "OK"
    assert done["pending"] is None


def test_resume_unknown_execution(tmp_store):
    with pytest.raises(ValueError, match="EXECUTION_UNKNOWN"):
        orch.resume(tmp_store, "exec_nope", _subject())


def test_resume_wrong_state(tmp_store):
    done = orch.start(tmp_store, "monitoring status", _subject())
    assert done["state"] == "COMPLETED"
    with pytest.raises(ValueError, match="EXECUTION_STATE"):
        orch.resume(tmp_store, done["execution_id"], _subject())


def test_resume_without_approved_run(tmp_store, monkeypatch):
    _gated(monkeypatch)
    paused = orch.start(tmp_store, "show transfers", _subject())
    with pytest.raises(ValueError, match="EXECUTION_NO_RUN"):
        orch.resume(tmp_store, paused["execution_id"], _subject())


def test_budget_exceeded_partial_without_tool_calls(tmp_store,
                                                    monkeypatch):
    calls = []
    monkeypatch.setattr(agents_mod, "propose",
                        lambda *a, **k: calls.append(1))
    record = {"execution_id": "exec_x", "steps": [{"s": 1}] * 8,
              "state": "EXECUTING", "error": ""}
    orch._continue(tmp_store, record, _subject(), {},
                   ["txn.search"] * 9, 0)
    assert record["state"] == "PARTIAL"
    assert "BUDGET_EXCEEDED" in record["error"]
    assert calls == []


def test_step_failed_partial_on_error_run(tmp_store, monkeypatch):
    def fake_propose(store, manifest, tool, args, subject):
        return ({"plan_id": "p9"},
                {"status": "ERROR", "run_id": "r9", "output": {}})
    monkeypatch.setattr(agents_mod, "propose", fake_propose)
    out = orch.start(tmp_store, "monitoring status", _subject())
    assert out["state"] == "PARTIAL"
    assert "STEP_FAILED" in out["error"]


def test_step_args_chaining_branches():
    assert orch._step_args("txn.search", {"q": "x"}, {"steps": []}) == {
        "q": "x"}
    assert orch._step_args("txn.search", {}, {"steps": []}) == {}
    record = {"steps": [{"output": {"signals": ["s1"]}}]}
    assert orch._step_args("typology.match", {}, record) == {
        "typology_id": "T-01"}
    record = {"steps": [{"output": {}}]}
    built = orch._step_args("report.build",
                            {"investigation_id": "inv_1",
                             "report_type": "fraud"},
                            record)
    assert built == {"investigation_id": "inv_1",
                     "report_type": "fraud"}
    namespaced = orch._step_args(
        "report.build",
        {"report.build": {}, "investigation_id": "inv_1"}, record)
    assert namespaced == {"report_type": "transaction",
                          "investigation_id": "inv_1"}


def test_metrics_skips_non_dict_rows():
    class Stub:
        def agent_executions(self):
            return ["junk", {"state": "COMPLETED",
                             "classification": {"intent": "TRACE"},
                             "steps": [{}, {}]}]
    metrics = orch.metrics(Stub())
    assert metrics["total"] == 2
    assert metrics["by_state"] == {"COMPLETED": 1}
    assert metrics["tool_calls"] == 2
