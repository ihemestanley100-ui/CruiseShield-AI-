"""T-011/T-014: model-output validation; honest failure without a key."""
import asyncio
import json

import httpx
import pytest

from app import ai_adapter
from app.models import EvidencePackage
from app.store import Store
from env_probe import CAN_LOOP


def _package(tmp_path):
    store = Store(tmp_path / "state.json")
    return EvidencePackage.model_validate(
        store.state["evidence_packages"]["inv_84721"])


def _valid_output(package):
    first = package.items[0].evidence_id
    return {
        "summary": "Seeded network shows shared infrastructure.",
        "key_findings": [{"finding": "Device sharing observed.",
                          "evidence_ids": [first],
                          "confidence_label": "high", "caveat": "Demo data."}],
        "alternative_explanations": ["Shared household device."],
        "missing_information": ["None for demo."],
        "suggested_next_steps": [{"action": "Review device owner.",
                                  "rationale": "Confirm sharing.",
                                  "evidence_ids": [first],
                                  "requires_human_approval": True}],
        "conclusion": "requires_review",
        "disclaimer": "Advisory only; synthetic data.",
    }


def test_valid_output_passes(tmp_path):
    package = _package(tmp_path)
    schema, refs, problems = ai_adapter.validate_model_output(
        _valid_output(package), {i.evidence_id for i in package.items})
    assert (schema, refs, problems) == ("VALIDATED", "VALIDATED", [])


def test_unknown_evidence_id_rejected(tmp_path):
    package = _package(tmp_path)
    bad = _valid_output(package)
    bad["key_findings"][0]["evidence_ids"] = ["evidence_fake_999"]
    schema, refs, problems = ai_adapter.validate_model_output(
        bad, {i.evidence_id for i in package.items})
    assert refs == "INVALID"
    assert any("evidence_fake_999" in p for p in problems)


def test_malformed_response_rejected():
    with pytest.raises(ai_adapter.AIError) as exc:
        ai_adapter.parse_response_text("not json {{{")
    assert exc.value.code == "MALFORMED_RESPONSE"


def test_missing_critical_field_invalid(tmp_path):
    package = _package(tmp_path)
    bad = _valid_output(package)
    del bad["conclusion"]
    schema, _, _ = ai_adapter.validate_model_output(
        bad, {i.evidence_id for i in package.items})
    assert schema == "INVALID"


def test_missing_key_blocks_honestly(tmp_path, monkeypatch):
    package = _package(tmp_path)
    monkeypatch.setattr(ai_adapter, "MODEL_API_KEY", "")
    assert ai_adapter.configured() is False
    # The fail-fast raise executes before any await: drive the coroutine
    # manually so this runs without an event loop.
    coro = ai_adapter.analyze(package, "summary", "trace_x", "agentrun_1")
    with pytest.raises(ai_adapter.AIError) as exc:
        coro.send(None)
    assert exc.value.code == "MODEL_NOT_CONFIGURED"


@pytest.mark.skipif(
    not CAN_LOOP,
    reason="no event loop in this sandbox; runs in CI/user envs")
def test_success_path_with_mock_transport(tmp_path, monkeypatch):
    package = _package(tmp_path)
    monkeypatch.setattr(ai_adapter, "MODEL_API_KEY", "test-key")
    body = {"id": "req_test_123",
            "choices": [{"message": {"content": json.dumps(_valid_output(package))}}]}

    def handler(request):
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(200, json=body)

    run = asyncio.run(ai_adapter.analyze(
        package, "summary", "trace_x", "agentrun_9",
        transport=httpx.MockTransport(handler)))
    assert run["status"] == "SUCCEEDED"
    assert run["request_id"] == "req_test_123"
    assert run["schema_validation_status"] == "VALIDATED"
    assert run["evidence_reference_validation_status"] == "VALIDATED"
    assert run["latency_ms"] >= 0
    assert "test-key" not in json.dumps(run)


def _body(content=None, finish_reason="stop", request_id="req_1", **message_extra):
    message = {"role": "assistant"}
    if content is not None:
        message["content"] = content
    message.update(message_extra)
    return {"id": request_id,
            "usage": {"prompt_tokens": 10, "completion_tokens": 5,
                      "total_tokens": 15},
            "choices": [{"finish_reason": finish_reason, "message": message}]}


def test_prompt_contains_exact_schema(tmp_path):
    # Root-cause regression: the v1 prompt referenced "the required schema"
    # without ever naming its fields, so the model guessed wrong key names.
    package = _package(tmp_path)
    assert ai_adapter.PROMPT_VERSION == "cs-prompt-v2"
    user_text = ai_adapter.build_messages(package, "summary")[1]["content"]
    for field in ("summary", "key_findings", "alternative_explanations",
                  "missing_information", "suggested_next_steps",
                  "conclusion", "disclaimer"):
        assert f'"{field}"' in user_text, field
    for conclusion in ("insufficient_evidence", "requires_review",
                       "evidence_supports_escalation"):
        assert conclusion in user_text
    assert package.package_id in user_text


def test_interpret_wrong_field_names_reproduces_live_error(tmp_path):
    package = _package(tmp_path)
    body = _body(json.dumps({"findings": ["something"], "verdict": "bad"}))
    with pytest.raises(ai_adapter.AIError) as exc:
        ai_adapter.interpret_provider_body(
            body, {i.evidence_id for i in package.items})
    assert exc.value.code == "MODEL_OUTPUT_INVALID"
    assert "missing critical fields: ['conclusion', 'key_findings', 'summary']" \
        in str(exc.value)
    assert exc.value.detail["top_level_keys"] == ["findings", "verdict"]


def test_interpret_prose_wrapped_json(tmp_path):
    package = _package(tmp_path)
    wrapped = ("Here is the analysis:\n"
               + json.dumps(_valid_output(package)) + "\nHope this helps.")
    data, meta = ai_adapter.interpret_provider_body(
        _body(wrapped), {i.evidence_id for i in package.items})
    assert meta["schema_validation_status"] == "VALIDATED"
    assert meta["evidence_reference_validation_status"] == "VALIDATED"
    assert meta["request_id"] == "req_1"
    assert meta["usage"] == {"prompt_tokens": 10, "completion_tokens": 5,
                             "total_tokens": 15}
    assert data["conclusion"] == "requires_review"


def test_interpret_refusal_is_explicit(tmp_path):
    package = _package(tmp_path)
    body = _body("", refusal="I cannot help with that.")
    with pytest.raises(ai_adapter.AIError) as exc:
        ai_adapter.interpret_provider_body(
            body, {i.evidence_id for i in package.items})
    assert exc.value.code == "MODEL_REFUSED"
    assert "refused" in str(exc.value).lower()


def test_interpret_truncation_is_explicit(tmp_path):
    package = _package(tmp_path)
    body = _body('{"summary": "cut off', finish_reason="length")
    with pytest.raises(ai_adapter.AIError) as exc:
        ai_adapter.interpret_provider_body(
            body, {i.evidence_id for i in package.items})
    assert exc.value.code == "MODEL_RESPONSE_TRUNCATED"


def test_interpret_missing_content(tmp_path):
    package = _package(tmp_path)
    with pytest.raises(ai_adapter.AIError) as exc:
        ai_adapter.interpret_provider_body(
            _body(None), {i.evidence_id for i in package.items})
    assert exc.value.code == "MALFORMED_RESPONSE"


def test_request_body_structured_flag(tmp_path):
    package = _package(tmp_path)
    structured = ai_adapter.build_request_body(package, "s", True)
    assert structured["response_format"] == {"type": "json_object"}
    assert structured["model"] == ai_adapter.META_MODEL_ID
    plain = ai_adapter.build_request_body(package, "s", False)
    assert "response_format" not in plain


def test_retry_predicate():
    predicate = ai_adapter.should_retry_without_structured
    assert predicate(400, '{"error": "unsupported response_format"}') is True
    assert predicate(400, "bad request") is False
    assert predicate(401, "response_format whatever") is False
    assert predicate(200, "") is False


def test_failure_excerpt_is_bounded(tmp_path):
    package = _package(tmp_path)
    big = json.dumps({"wrong": "x" * 5000})
    with pytest.raises(ai_adapter.AIError) as exc:
        ai_adapter.interpret_provider_body(
            _body(big), {i.evidence_id for i in package.items})
    assert exc.value.code == "MODEL_OUTPUT_INVALID"
    assert exc.value.detail["content_length"] == len(big)
    assert len(exc.value.detail["response_excerpt"]) == ai_adapter.EXCERPT_LIMIT
    assert exc.value.detail["top_level_keys"] == ["wrong"]


@pytest.mark.skipif(
    not CAN_LOOP,
    reason="no event loop in this sandbox; runs in CI/user envs")
def test_analyze_sends_structured_output(tmp_path, monkeypatch):
    package = _package(tmp_path)
    monkeypatch.setattr(ai_adapter, "MODEL_API_KEY", "test-key")
    seen = {}

    def handler(request):
        seen.update(json.loads(request.content))
        return httpx.Response(200, json=_body(
            json.dumps(_valid_output(package)), request_id="req_struct"))

    run = asyncio.run(ai_adapter.analyze(
        package, "summary", "trace_x", "agentrun_20",
        transport=httpx.MockTransport(handler)))
    assert seen["response_format"] == {"type": "json_object"}
    assert run["status"] == "SUCCEEDED"
    assert run["structured_output"] is True
    assert run["finish_reason"] == "stop"
    assert "test-key" not in json.dumps(run)


@pytest.mark.skipif(
    not CAN_LOOP,
    reason="no event loop in this sandbox; runs in CI/user envs")
def test_analyze_falls_back_when_structured_rejected(tmp_path, monkeypatch):
    package = _package(tmp_path)
    monkeypatch.setattr(ai_adapter, "MODEL_API_KEY", "test-key")
    calls = []

    def handler(request):
        calls.append("response_format" in json.loads(request.content))
        if len(calls) == 1:
            return httpx.Response(
                400, json={"error": "unsupported response_format field"})
        return httpx.Response(200, json=_body(
            json.dumps(_valid_output(package)), request_id="req_fb"))

    run = asyncio.run(ai_adapter.analyze(
        package, "summary", "trace_x", "agentrun_21",
        transport=httpx.MockTransport(handler)))
    assert calls == [True, False]
    assert run["status"] == "SUCCEEDED"
    assert run["structured_output"] is False


@pytest.mark.skipif(
    not CAN_LOOP,
    reason="no event loop in this sandbox; runs in CI/user envs")
def test_analyze_no_retry_on_other_400(tmp_path, monkeypatch):
    package = _package(tmp_path)
    monkeypatch.setattr(ai_adapter, "MODEL_API_KEY", "test-key")
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(400, json={"error": "bad request"})

    with pytest.raises(ai_adapter.AIError) as exc:
        asyncio.run(ai_adapter.analyze(
            package, "summary", "trace_x", "agentrun_22",
            transport=httpx.MockTransport(handler)))
    assert exc.value.code == "MODEL_PROVIDER_ERROR"
    assert len(calls) == 1
    assert exc.value.run["structured_output"] is True
