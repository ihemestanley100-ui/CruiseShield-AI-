"""Case transitions, decision labels, terminal states."""
import pytest

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
