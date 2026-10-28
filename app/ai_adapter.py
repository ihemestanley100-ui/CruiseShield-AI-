"""Server-side Meta Model API adapter (Muse Spark).

The application computes risk and assembles evidence independently; the model
only interprets the supplied evidence package. The API key lives server-side
and is never logged, returned, or persisted.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import httpx

from app.config import META_BASE_URL, META_MODEL_ID, MODEL_API_KEY
from app.models import EvidencePackage

SYSTEM_INSTRUCTION = (
    "You are CruiseShield AI's evidence-grounded investigation assistant. "
    "Use only facts in the supplied synthetic evidence package. Do not invent "
    "transactions, entities, relationships, event IDs, timestamps, metrics or "
    "evidence. Do not calculate the authoritative risk score. Separate observed "
    "facts, interpretations, uncertainty and suggested next steps. Cite evidence "
    "IDs for material factual findings. If evidence is insufficient, say so. "
    "Consider alternative explanations. Do not declare criminal intent from a "
    "risk signal. Recommendations are advisory and require authorized human "
    "review. Always reply with a single raw JSON object and nothing else."
)

PROMPT_VERSION = "cs-prompt-v2"
REQUIRED_FIELDS = {"summary", "key_findings", "alternative_explanations",
                   "missing_information", "suggested_next_steps",
                   "conclusion", "disclaimer"}
CONCLUSIONS = {"insufficient_evidence", "requires_review",
               "evidence_supports_escalation"}
CONFIDENCE_LABELS = {"low", "medium", "high"}


def configured() -> bool:
    return bool(MODEL_API_KEY)


class AIError(Exception):
    def __init__(self, code: str, message: str, detail: dict | None = None,
                 run: dict | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.detail = detail or {}
        self.run = run


RESPONSE_SCHEMA_SPEC = """\
Required JSON structure (exact top-level field names, all required):
{
  "summary": "string: 1-3 sentence overview grounded only in the evidence",
  "key_findings": [
    {"finding": "string",
     "evidence_ids": ["evidence_id values copied from the package below"],
     "confidence_label": "low|medium|high", "caveat": "string"}
  ],
  "alternative_explanations": ["string"],
  "missing_information": ["string"],
  "suggested_next_steps": [
    {"action": "string", "rationale": "string",
     "evidence_ids": ["evidence_id values copied from the package below"],
     "requires_human_approval": true}
  ],
  "conclusion": "insufficient_evidence|requires_review|evidence_supports_escalation",
  "disclaimer": "string: advisory-only, synthetic-data notice"
}
Rules: use only evidence IDs listed in the package below; never invent IDs,
transactions, timestamps, or metrics; do not compute a risk score; output raw
JSON only with no markdown fences and no commentary."""


def build_messages(package: EvidencePackage, summary: str) -> list[dict]:
    payload = {"investigation_summary": summary,
               "evidence_package": package.model_dump()}
    return [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": (
            "Analyze this synthetic investigation.\n\n"
            + RESPONSE_SCHEMA_SPEC + "\n\nEVIDENCE PACKAGE (JSON):\n"
            + json.dumps(payload, sort_keys=True))},
    ]


def _extract_json_block(text: str) -> str | None:
    """Return the first balanced {...} block, else None. String-aware."""
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        elif ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def parse_response_text(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    candidates = [cleaned]
    block = _extract_json_block(cleaned)
    if block and block != cleaned:
        candidates.append(block)
    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
    raise AIError("MALFORMED_RESPONSE",
                  "Model response contains no JSON object")


def validate_model_output(data: dict, sent_ids: set[str]) -> tuple[str, str, list[str]]:
    """Return (schema_status, reference_status, problems)."""
    problems: list[str] = []
    missing = REQUIRED_FIELDS - set(data.keys())
    critical = {"summary", "key_findings", "conclusion"} & missing
    if critical:
        problems.append(f"missing critical fields: {sorted(critical)}")
        return "INVALID", "NOT_CHECKED", problems
    if missing:
        problems.append(f"missing non-critical fields: {sorted(missing)}")
    findings = data.get("key_findings", [])
    if not isinstance(findings, list):
        problems.append("key_findings must be a list")
        return "INVALID", "NOT_CHECKED", problems
    for i, finding in enumerate(findings):
        if not isinstance(finding, dict):
            problems.append(f"key_findings[{i}] must be an object")
            return "INVALID", "NOT_CHECKED", problems
        if not finding.get("finding"):
            problems.append(f"key_findings[{i}] missing finding text")
            return "INVALID", "NOT_CHECKED", problems
        for eid in finding.get("evidence_ids", []):
            if eid not in sent_ids:
                problems.append(f"unknown evidence ID cited: {eid}")
                return "VALIDATED_SCHEMA", "INVALID", problems
        label = finding.get("confidence_label", "")
        if label and label not in CONFIDENCE_LABELS:
            problems.append(f"key_findings[{i}] bad confidence_label: {label}")
            return "INVALID", "NOT_CHECKED", problems
    for step in data.get("suggested_next_steps", []):
        if isinstance(step, dict):
            for eid in step.get("evidence_ids", []):
                if eid not in sent_ids:
                    problems.append(f"unknown evidence ID cited: {eid}")
                    return "VALIDATED_SCHEMA", "INVALID", problems
    if data.get("conclusion") not in CONCLUSIONS:
        problems.append(f"bad conclusion: {data.get('conclusion')}")
        return "INVALID", "NOT_CHECKED", problems
    schema_status = "PARTIALLY_VALIDATED" if missing else "VALIDATED"
    return schema_status, "VALIDATED", problems


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


EXCERPT_LIMIT = 2000

STRUCTURED_OUTPUT_BODY = {"type": "json_object"}


def build_request_body(package: EvidencePackage, summary: str,
                       use_structured_output: bool = True) -> dict:
    body: dict = {"model": META_MODEL_ID,
                  "messages": build_messages(package, summary)}
    if use_structured_output:
        body["response_format"] = dict(STRUCTURED_OUTPUT_BODY)
    return body


def should_retry_without_structured(status_code: int, body_text: str) -> bool:
    return (status_code == 400
            and "response_format" in (body_text or "").lower())


def interpret_provider_body(body: dict, sent_ids: set[str]) -> tuple[dict, dict]:
    """Parse + validate a chat-completions body. Returns (data, meta).

    Raises AIError with explicit codes for refusal, truncation, malformed
    envelopes, malformed JSON, and schema/reference violations. `meta`
    carries bounded diagnostics only (never credentials).
    """
    meta: dict = {"request_id": "", "finish_reason": "", "usage": {},
                  "content_length": 0, "top_level_keys": [],
                  "response_excerpt": ""}
    if not isinstance(body, dict):
        raise AIError("MALFORMED_RESPONSE",
                      "Model API body must be a JSON object")
    meta["request_id"] = str(body.get("id", ""))
    usage = body.get("usage", {})
    if isinstance(usage, dict):
        meta["usage"] = {k: usage.get(k) for k in
                         ("prompt_tokens", "completion_tokens", "total_tokens")
                         if usage.get(k) is not None}
    choices = body.get("choices", [])
    if not choices or not isinstance(choices[0], dict):
        raise AIError("MALFORMED_RESPONSE",
                      "Model API response lacks choices[0]")
    choice = choices[0]
    meta["finish_reason"] = str(choice.get("finish_reason", "") or "")
    message = choice.get("message", {})
    if not isinstance(message, dict):
        raise AIError("MALFORMED_RESPONSE",
                      "Model API response lacks a message object")
    content = message.get("content", "")
    if not isinstance(content, str):
        content = "" if content is None else str(content)
    meta["content_length"] = len(content)
    meta["response_excerpt"] = content[:EXCERPT_LIMIT]
    if meta["finish_reason"] == "length":
        raise AIError("MODEL_RESPONSE_TRUNCATED",
                      "Model response was cut off (finish_reason=length)",
                      detail=dict(meta))
    if not content.strip():
        refusal = message.get("refusal", "")
        if refusal:
            raise AIError("MODEL_REFUSED",
                          f"Model refused the request: {str(refusal)[:500]}",
                          detail=dict(meta))
        raise AIError("MALFORMED_RESPONSE",
                      "Model API response lacks choices[0].message.content",
                      detail=dict(meta))
    try:
        data = parse_response_text(content)
    except AIError as exc:
        raise AIError(exc.code, str(exc), detail=dict(meta)) from exc
    meta["top_level_keys"] = sorted(data.keys())
    schema_status, ref_status, problems = validate_model_output(data, sent_ids)
    meta["schema_validation_status"] = schema_status
    meta["evidence_reference_validation_status"] = ref_status
    if schema_status == "INVALID" or ref_status == "INVALID":
        raise AIError("MODEL_OUTPUT_INVALID", "; ".join(problems),
                      detail=dict(meta))
    return data, meta


async def analyze(package: EvidencePackage, summary: str, trace_id: str,
                  run_id: str, timeout: int = 30,
                  transport: httpx.AsyncBaseTransport | None = None) -> dict:
    if not configured():
        raise AIError("MODEL_NOT_CONFIGURED",
                      "MODEL_API_KEY is not configured on the server")
    started = _now()
    t0 = time.monotonic()
    run: dict = {
        "agent_run_id": run_id, "provider": "meta", "model_id": META_MODEL_ID,
        "prompt_version": PROMPT_VERSION, "request_id": "", "trace_id": trace_id,
        "evidence_package_id": package.package_id,
        "evidence_ids_sent": sorted(i.evidence_id for i in package.items),
        "started_at": started, "completed_at": "", "latency_ms": 0,
        "status": "FAILED", "response_reference": "",
        "schema_validation_status": "NOT_VALIDATED",
        "evidence_reference_validation_status": "NOT_VALIDATED",
        "error_code": "", "synthetic_data_flag": True, "result": {},
        "structured_output": True, "finish_reason": "", "usage": {},
        "diagnostics": {},
    }

    def fail_exc(code: str, message: str, detail: dict | None = None) -> AIError:
        run.update(completed_at=_now(),
                   latency_ms=int((time.monotonic() - t0) * 1000),
                   status="FAILED", error_code=code)
        if detail:
            run["diagnostics"] = detail
            run["request_id"] = detail.get("request_id", run["request_id"])
            run["finish_reason"] = detail.get("finish_reason", "")
            run["usage"] = detail.get("usage", {})
            run["schema_validation_status"] = detail.get(
                "schema_validation_status", run["schema_validation_status"])
            run["evidence_reference_validation_status"] = detail.get(
                "evidence_reference_validation_status",
                run["evidence_reference_validation_status"])
        return AIError(code, message, detail=detail or {}, run=run)
    async def post(use_structured: bool) -> httpx.Response:
        async with httpx.AsyncClient(base_url=META_BASE_URL, timeout=timeout,
                                     transport=transport) as client:
            return await client.post(
                "/chat/completions",
                headers={"Authorization": f"Bearer {MODEL_API_KEY}"},
                json=build_request_body(package, summary, use_structured))

    try:
        response = await post(use_structured=True)
        if should_retry_without_structured(response.status_code, response.text):
            run["structured_output"] = False
            response = await post(use_structured=False)
    except httpx.TimeoutException as exc:
        raise fail_exc("MODEL_TIMEOUT",
                       f"Model request timed out: {exc}") from exc
    except httpx.HTTPError as exc:
        raise fail_exc("MODEL_PROVIDER_UNAVAILABLE",
                       f"Model provider unreachable: {exc}") from exc
    latency_ms = int((time.monotonic() - t0) * 1000)
    if response.status_code in (401, 403):
        raise fail_exc("MODEL_AUTH_FAILED",
                       "Model API rejected the server credentials")
    if response.status_code >= 400:
        raise fail_exc("MODEL_PROVIDER_ERROR",
                       f"Model API error: HTTP {response.status_code}")
    try:
        body = response.json()
    except ValueError:
        raise fail_exc("MALFORMED_RESPONSE",
                       "Model API returned a non-JSON body")
    try:
        data, meta = interpret_provider_body(
            body, set(run["evidence_ids_sent"]))
    except AIError as exc:
        raise fail_exc(exc.code, str(exc), exc.detail)
    run.update(completed_at=_now(), latency_ms=latency_ms, result=data,
               request_id=meta["request_id"],
               response_reference=meta["request_id"] or run_id,
               finish_reason=meta["finish_reason"], usage=meta["usage"],
               diagnostics={"content_length": meta["content_length"],
                            "top_level_keys": meta["top_level_keys"]},
               schema_validation_status=meta["schema_validation_status"],
               evidence_reference_validation_status=meta[
                   "evidence_reference_validation_status"],
               status="SUCCEEDED")
    return run
