"""Case transitions, decision labels, terminal states."""
import pytest

import app.main as main
from app import cases as cases_mod
from app.store import Store


def test_allowed_transitions_follow_lifecycle(tmp_path):
    store = Store(tmp_path / "state.json")
    assert cases_mod.allowed_transitions("NEW") == ["TRIAGED", "FALSE_POSITIVE"]
    assert cases_mod.allowed_transitions("CLOSED") == []
    record, _ = cases_mod.record_decision(
        store, "case_84721", "Monitor", "TRIAGED", "Triage for review.", "inv1")
    assert record["decision_id"] == "decision_0001"
    assert store.get_case("case_84721")["status"] == "TRIAGED"
    with pytest.raises(ValueError, match="INVALID_TRANSITION"):
        cases_mod.record_decision(
            store, "case_84721", "Close Case", "CLOSED", "Skip ahead.", "inv1")


def test_invalid_decision_label_rejected(tmp_path):
    store = Store(tmp_path / "state.json")
    with pytest.raises(ValueError, match="INVALID_DECISION"):
        cases_mod.record_decision(
            store, "case_84721", "Delete Everything", "TRIAGED", "Nope.", "inv1")


def test_oversized_reason_rejected_without_state_change(tmp_path):
    store = Store(tmp_path / "state.json")
    before = (store.get_case("case_84721")["status"],
              len(store.state["decisions"]), len(store.state["audits"]))
    with pytest.raises(ValueError, match="REASON_TOO_LONG"):
        cases_mod.record_decision(store, "case_84721", "Monitor", "TRIAGED",
                                  "x" * 10001, "inv1")
    after = (store.get_case("case_84721")["status"],
             len(store.state["decisions"]), len(store.state["audits"]))
    assert before == after


def test_oversized_actor_and_recommendation_rejected(tmp_path):
    store = Store(tmp_path / "state.json")
    with pytest.raises(ValueError, match="ACTOR_ID_TOO_LONG"):
        cases_mod.record_decision(store, "case_84721", "Monitor", "TRIAGED",
                                  "Fine.", "i" * 257)
    with pytest.raises(ValueError, match="RECOMMENDATION_TOO_LONG"):
        cases_mod.record_decision(store, "case_84721", "Monitor", "TRIAGED",
                                  "Fine.", "inv1", recommendation="r" * 10001)


def test_false_positive_is_terminal(tmp_path):
    store = Store(tmp_path / "state.json")
    cases_mod.record_decision(store, "case_84721", "Mark False Positive",
                              "FALSE_POSITIVE", "Unconnected transfer.", "inv1")
    with pytest.raises(ValueError, match="INVALID_TRANSITION"):
        cases_mod.record_decision(store, "case_84721", "Monitor", "TRIAGED",
                                  "Reopen.", "inv1")


def test_audit_chain_is_sequential(tmp_path):
    store = Store(tmp_path / "state.json")
    ids = [a["audit_event_id"] for a in store.state["audits"]]
    assert ids == ["audit_0001", "audit_0002"]
    cases_mod.record_decision(store, "case_84721", "Monitor", "TRIAGED",
                              "Triage.", "inv1", trace_id="trace_test")
    assert store.state["audits"][-1]["audit_event_id"] == "audit_0003"
    assert store.state["audits"][-1]["trace_id"] == "trace_test"


def _ai_run(package_id: str, run_id: str) -> dict:
    return {
        "agent_run_id": run_id, "provider": "meta",
        "model_id": "muse-spark-1.3", "prompt_version": "cs-prompt-v2",
        "evidence_package_id": package_id, "status": "SUCCEEDED",
        "schema_validation_status": "VALIDATED",
        "evidence_reference_validation_status": "VALIDATED",
        "latency_ms": 1500, "completed_at": "2026-10-29T00:00:00Z",
        "result": {
            "summary": "Shared infrastructure.",
            "key_findings": [{
                "finding": "dev_04 shared.",
                "confidence_label": "high",
                "evidence_ids": ["evidence_edge_0002"],
                "caveat": "Synthetic.",
            }],
            "alternative_explanations": [],
            "missing_information": ["Device ownership records."],
            "conclusion": "requires_review",
            "disclaimer": "Advisory only.",
        },
    }


def test_case_detail_reports_no_ai_run(tmp_store):
    detail = main.get_case("case_84721")
    assert detail["latest_ai_run"] is None
    assert detail["case"]["status"] == "NEW"


def test_case_detail_reports_latest_ai_run(tmp_store):
    package_id = tmp_store.state["evidence_packages"]["inv_84721"]["package_id"]
    before = {k: len(v) for k, v in tmp_store.state.items()
              if isinstance(v, list)}
    tmp_store.save_ai_run(_ai_run("other_pkg", "agentrun_1"))
    tmp_store.save_ai_run(_ai_run(package_id, "agentrun_2"))
    detail = main.get_case("case_84721")
    latest = detail["latest_ai_run"]
    assert latest["agent_run_id"] == "agentrun_2"
    assert latest["conclusion"] == "requires_review"
    assert latest["missing_information"] == ["Device ownership records."]
    assert latest["key_findings"][0]["evidence_ids"] == ["evidence_edge_0002"]
    assert latest["key_findings"][0]["confidence_label"] == "high"
    assert latest["schema_validation_status"] == "VALIDATED"
    # Read-only: scores, case, decisions, audits untouched by the read.
    assert tmp_store.state["risk"]["txn_84721"]["network"]["score"] == 84
    assert tmp_store.get_case("case_84721")["status"] == "NEW"
    after = {k: len(v) for k, v in tmp_store.state.items()
             if isinstance(v, list)}
    assert after["decisions"] == before["decisions"]
    assert after["audits"] == before["audits"]
