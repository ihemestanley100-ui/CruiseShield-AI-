"""GAP-004: offline golden eval harness for model-output validation.

No live model, no network, no key: golden fixtures pin the exact
verdicts of parse_response_text + validate_model_output so prompt,
schema, or validator drift fails loudly here instead of silently
changing what a live response would be judged as. Live quality/drift
(GAP-014) remains a separate, owner-gated lane.
"""
import copy
import json

from app import ai_adapter

SENT_IDS = {"evidence_txn_84721", "evidence_edge_0002"}

GOLDEN_VALID = {
    "summary": "Two accounts share device dev_04 within the window.",
    "key_findings": [{
        "finding": "dev_04 links acct_11 and acct_27.",
        "evidence_ids": ["evidence_edge_0002"],
        "confidence_label": "high",
        "caveat": "Synthetic fixture.",
    }],
    "alternative_explanations": ["Shared household device."],
    "missing_information": ["Device ownership records."],
    "suggested_next_steps": [{
        "action": "Request device ownership records.",
        "rationale": "Confirm or rule out shared control.",
        "evidence_ids": ["evidence_txn_84721"],
        "requires_human_approval": True,
    }],
    "conclusion": "requires_review",
    "disclaimer": "Advisory only; synthetic evaluation fixture.",
}


def _validate(payload: dict) -> tuple[str, str, list[str]]:
    text = json.dumps(payload, sort_keys=True)
    return ai_adapter.validate_model_output(
        ai_adapter.parse_response_text(text), set(SENT_IDS))


def test_golden_valid_output_fully_validated():
    schema, refs, problems = _validate(GOLDEN_VALID)
    assert (schema, refs, problems) == ("VALIDATED", "VALIDATED", [])


def test_golden_unknown_evidence_id_rejected():
    bad = copy.deepcopy(GOLDEN_VALID)
    bad["key_findings"][0]["evidence_ids"] = ["evidence_invented_9"]
    schema, refs, problems = _validate(bad)
    assert schema == "VALIDATED_SCHEMA"
    assert refs == "INVALID"
    assert any("unknown evidence ID" in p for p in problems)


def test_golden_missing_critical_field_invalid():
    bad = copy.deepcopy(GOLDEN_VALID)
    del bad["conclusion"]
    schema, refs, _ = _validate(bad)
    assert (schema, refs) == ("INVALID", "NOT_CHECKED")


def test_golden_banned_score_field_invalid():
    bad = copy.deepcopy(GOLDEN_VALID)
    bad["risk_score"] = 87
    schema, refs, problems = _validate(bad)
    assert (schema, refs) == ("INVALID", "NOT_CHECKED")
    assert any("invented numeric score" in p for p in problems)


def test_golden_enforcement_language_invalid():
    bad = copy.deepcopy(GOLDEN_VALID)
    bad["key_findings"][0]["finding"] = "Freeze the account now."
    schema, refs, _ = _validate(bad)
    assert (schema, refs) == ("INVALID", "NOT_CHECKED")


def test_golden_step_without_human_approval_invalid():
    bad = copy.deepcopy(GOLDEN_VALID)
    bad["suggested_next_steps"][0]["requires_human_approval"] = False
    schema, refs, _ = _validate(bad)
    assert (schema, refs) == ("INVALID", "NOT_CHECKED")


def test_golden_bad_conclusion_invalid():
    bad = copy.deepcopy(GOLDEN_VALID)
    bad["conclusion"] = "guilty"
    schema, refs, _ = _validate(bad)
    assert (schema, refs) == ("INVALID", "NOT_CHECKED")


def test_golden_prose_wrapped_json_still_parses():
    wrapped = "Here is the analysis:\n```json\n%s\n```" % json.dumps(
        GOLDEN_VALID, sort_keys=True)
    schema, refs, problems = ai_adapter.validate_model_output(
        ai_adapter.parse_response_text(wrapped), set(SENT_IDS))
    assert (schema, refs, problems) == ("VALIDATED", "VALIDATED", [])
